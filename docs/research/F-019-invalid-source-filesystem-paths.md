# F-019 research — invalid filesystem paths in file-backed source loading

**Issue:** #94  
**Scope:** `load_source()` / `load_and_validate()` source-document file loading only.  
**Naming note:** issue #94 requested an `F-017-...` research filename, but F-017 is already assigned to in-place mutation research; this report uses the issue's actual identifier F-019.

## 1. Trigger

`load_source(path)` currently does:

```python
source_path = Path(path)
source_name = str(source_path)
try:
    text = source_path.read_bytes().decode("utf-8-sig")
except (OSError, UnicodeDecodeError) as exc:
    _raise("decode_error", str(exc), source_name)
```

Filesystem path APIs can reject a syntactically representable `Path` only when I/O is attempted. One important example on supported CPython builds is a string containing an embedded NUL. `Path("bad\0.json")` can exist as a path object, but the later file open/read raises `ValueError: embedded null byte` rather than `OSError`.

Because the I/O `ValueError` is outside the current exception tuple, the raw Python exception leaks through ontoTF's public source-loading API.

This is inconsistent with the current API shape: ordinary missing/inaccessible files and invalid UTF-8 are already translated to `SourceValidationError(category="decode_error")` with source-path provenance.

## 2. Authoritative Python boundary

Python's `pathlib` documentation states that `Path.open()` opens the pointed-to file like built-in `open()`, and `Path.read_bytes()` returns the binary contents of the pointed-to file. These are concrete filesystem-I/O operations, not pure path manipulation.

References:

- Python 3.10 `pathlib`: https://docs.python.org/3.10/library/pathlib.html#pathlib.Path.read_bytes
- Python 3.12 `pathlib`: https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.read_bytes

Python's `os.fspath()` contract separately establishes the path-like coercion boundary: `str`/`bytes` are returned, otherwise `__fspath__()` must return `str` or `bytes`, and invalid values raise `TypeError`.

Reference:

- https://docs.python.org/3/library/os.html#os.fspath

That distinction matters for ontoTF:

- `load_source` advertises `str | Path`, not arbitrary user-defined objects;
- invalid object/type coercion at `Path(path)` is therefore outside the declared input contract and should not be silently converted into a filesystem `decode_error`;
- a `ValueError` raised by the **file read after a valid `Path` object exists** belongs to the same file-backed source-loading boundary as `OSError`.

## 3. Existing ontoTF error model

The source loader already intentionally groups several pre-parse failures under `decode_error`:

- file I/O `OSError`;
- UTF-8 decoding failure (`UnicodeDecodeError`);
- unsupported source suffix;
- JSON/YAML decode failures inside `loads_source()`.

It does not have a public `filesystem_error` source-loading category analogous to parent-component identity.

Introducing a new category solely for invalid filesystem spelling would therefore be a larger compatibility change than necessary. The smallest consistent behavior is:

> a `ValueError` raised by `source_path.read_bytes()` / the immediately chained UTF-8 decode is translated to the existing `decode_error` category with the same `source_name` provenance.

No schema, semantic, or digest categories change.

## 4. Exact catch boundary

The correction should stay local to the current file-I/O/decode block:

```python
try:
    text = source_path.read_bytes().decode("utf-8-sig")
except (OSError, UnicodeDecodeError, ValueError) as exc:
    _raise("decode_error", str(exc), source_name)
```

Equivalent factoring is acceptable if tests pin the same public behavior.

Important exclusions:

1. Do **not** wrap `source_path = Path(path)` in the same broad catch. Type/coercion failures for values outside `str | Path` are not filesystem read failures under the declared API.
2. Do **not** add a broad `except Exception`; only the demonstrated filesystem/decode family belongs here.
3. Do **not** alter `loads_source()`'s existing `ValueError` handling for JSON numeric constants or decoding. That is a separate in-memory parse boundary that already maps correctly to `decode_error`.

`UnicodeDecodeError` is already handled explicitly; adding `ValueError` is about filesystem/read-path failures and must not change user-visible category selection.

## 5. Source-name provenance

`source_name = str(source_path)` is computed before filesystem access. The correction should preserve this exact authored path representation in `ValidationProblem.source_name`, including unusual characters such as an embedded NUL.

No path normalization, escaping, resolution, or sandboxing is justified by this ticket.

For a path such as `"bad\0.json"`, the typed error should therefore have:

```text
category = decode_error
source_name = "bad\0.json"
```

The exception message remains platform/Python supplied and is not part of a stable cross-platform contract; tests should pin category + source name rather than exact OS wording.

## 6. Suffix precedence must not move

Current `load_source()` reads and UTF-8-decodes the file **before** examining `source_path.suffix`.

That creates two distinct observable cases:

- existing readable `source.txt` -> read succeeds, then `decode_error` for unsupported suffix;
- missing/inaccessible `source.txt` -> filesystem `decode_error` occurs before suffix validation.

F-019 should not move suffix inspection before I/O merely because that would simplify invalid-path handling. Doing so would silently change which error/message wins for missing or unreadable files with unsupported suffixes.

RED must therefore pin both:

1. existing unsupported-suffix file remains unsupported-suffix `decode_error`;
2. missing unsupported-suffix file still fails from filesystem access before suffix rejection.

For embedded-NUL `.json`, `.yaml`, or `.txt`, filesystem rejection likewise occurs before suffix dispatch under the current contract.

## 7. JSON/YAML symmetry

The filesystem failure happens before format selection, so `.json`, `.yaml`, and `.yml` invalid filesystem spellings should behave identically at this layer:

- same `decode_error` category;
- exact source path retained;
- no parser invocation.

At minimum the issue-requested `.json` and `.yaml` cases should be pinned. `.yml` is a useful control because it shares the YAML routing branch.

## 8. `load_and_validate()` propagation

`load_and_validate(path, ...)` first creates a `Path`, then calls `load_source(source_path)`. For valid declared `str | Path` inputs, the corrected typed source-loading error should propagate unchanged and validation/schema loading must not run.

No additional wrapper should translate `SourceValidationError` again.

This ticket does not need a separate `load_and_validate` production branch; a regression test is sufficient to prove propagation if useful.

## 9. Explicit schema-root loading is a separate boundary

Research found the analogous pattern in `_read_schema_bytes(..., schema_root=...)`:

```python
try:
    return schema_path.read_bytes(), source_name
except OSError as exc:
    _raise("invalid_schema", ...)
```

An invalid explicit schema filesystem path can therefore leak `ValueError` too, but its established public category is `invalid_schema`, not `decode_error`.

Mixing both fixes into F-019 would couple two independent error families and broaden the ticket unnecessarily. A separate follow-up issue has been filed for that schema-root boundary.

Packaged-resource schema loading is not part of F-019.

## 10. Cross-platform evidence policy

The implementation fix is intentionally small, but the exact underlying exception/message is an OS/CPython detail. CI should therefore exercise embedded-NUL paths on the supported Python matrix and, where practical, both Ubuntu and Windows.

The stable ontoTF assertions are:

- no raw `ValueError` escapes;
- category is `decode_error`;
- `source_name` is preserved;
- no parser is reached after filesystem failure.

Do not freeze the exact text `"embedded null byte"` as a cross-platform ontoTF API promise.

## 11. Required RED before production

Before changing `source_validation.py`, pin:

1. embedded-NUL `.json` path -> `SourceValidationError/decode_error`, not raw `ValueError`;
2. embedded-NUL `.yaml` path -> same category and provenance;
3. optional `.yml` symmetry control;
4. ordinary missing `.json` remains `decode_error` with exact source name;
5. invalid UTF-8 readable `.json` remains `decode_error`;
6. existing readable unsupported suffix remains the current unsupported-suffix failure;
7. missing unsupported suffix preserves filesystem-before-suffix precedence;
8. valid JSON and YAML source loading remain unchanged;
9. `load_and_validate()` propagates the typed source error without entering schema validation;
10. values outside the declared `str | Path` API are not accidentally reclassified as filesystem decode errors.

The RED should fail only on the embedded-NUL containment cases; existing controls should stay green.

## 12. Minimal implementation

If RED confirms the research hypothesis, the implementation should be one narrow error-boundary change: include filesystem/read-time `ValueError` in the existing `load_source()` translation to `decode_error`.

No changes are needed to:

- source schemas;
- semantic validation;
- digest canonicalization;
- parent-component identity;
- pathname normalization;
- format dispatch;
- parser configuration.

## 13. Scheduling / overlap

F-019 touches `src/ontotf/source_validation.py`, not F-015's `parent_identity.py`, so its **research** is independent of the currently queued F-015 Actions gate.

The issue explicitly allows research in parallel but asks production work to avoid overlapping `source_validation.py` implementation streams. Before RED/implementation, re-check current open PRs and `main` for source-validation changes and rebase/integrate as necessary.

## 14. Conclusion

**A small fail-closed correction is justified.**

The public source-loading API already treats filesystem access and UTF-8 decoding failures as `decode_error`. A `ValueError` raised by filesystem I/O for a syntactically representable `Path` is the same boundary and should not escape raw.

The fix should be deliberately narrow: catch that read-time `ValueError`, preserve the exact source path, keep file-before-suffix precedence, leave invalid input types outside the declared API, and keep schema-root error handling as a separate follow-up.

Proceed to an independent research review before planning or RED.