# F-020 research — contain invalid explicit schema-root filesystem paths

**Issue:** #95  
**Baseline:** `main` `200dcaba593d02d4d903aa424d6c7fec574f2ff2`  
**Type:** source-validation error-boundary stability

## Question

How should `validate_source(..., schema_root=...)` behave when the caller supplies a path-like schema root whose filesystem spelling cannot be passed to the host filesystem API, for example a string containing an embedded NUL?

## Current boundary

`_read_schema_bytes()` currently does:

```python
schema_path = Path(schema_root) / filename
source_name = str(schema_path)
try:
    return schema_path.read_bytes(), source_name
except OSError as exc:
    _raise("invalid_schema", str(exc), source_name)
```

Normal missing-file, permissions, and other OS failures therefore become the public `SourceValidationError(category="invalid_schema")` family with the concrete schema path as provenance.

The exception boundary is incomplete. `Path.read_bytes()` opens the path using the normal file-opening machinery. Invalid native path spellings can raise `ValueError`, notably an embedded NUL string, before an `OSError` is available. That raw exception currently escapes `validate_source()`.

This is inconsistent with the existing public distinction:

- source document file/read/decode failures -> `decode_error`;
- selected schema file/read/decode/self-validation failures -> `invalid_schema`.

An invalid filesystem spelling for an explicitly selected schema belongs to the second family.

## Python evidence

Python 3.10 and 3.12 document that `Path.read_bytes()` reads by opening the pointed-to file, and concrete `Path` methods may raise filesystem-related exceptions. The `Path` object itself preserves a raw filesystem path string; construction is not proof that the later OS-level spelling is valid.

Primary references:
- Python 3.10 `pathlib.Path.open` / `Path.read_bytes`: https://docs.python.org/3.10/library/pathlib.html
- Python 3.12 `pathlib.Path.open` / `Path.read_bytes`: https://docs.python.org/3.12/library/pathlib.html

F-020 also reuses the more specific CPython filesystem-converter evidence already recorded for the sibling F-019 source-file boundary in `docs/research/F-019-cpython-path-conversion-evidence.md`. That note traces `_io.FileIO` through the platform filesystem converters on Windows and non-Windows builds, records the C-API prohibition on embedded NULs, and identifies `ValueError` as an established path-conversion failure on the supported CPython family. The mechanism is relevant here because `Path.read_bytes()` ultimately reaches the same file-opening/path-conversion boundary; only the ontoTF authority/category differs (`invalid_schema` rather than `decode_error`).

The concrete RED case is an embedded NUL in `schema_root`. The path object/string can be formed, but the subsequent open/read boundary raises a path-conversion exception such as `ValueError` rather than necessarily reaching an `OSError`. ontoTF must not standardize the host exception text or depend on every platform surfacing the same underlying exception class; it must contain the supported boundary in the existing `invalid_schema` family.

## Decision

For a **declared-valid path-like `schema_root`**, translate `ValueError` raised by the schema-file read boundary exactly like `OSError`:

```python
except (OSError, ValueError) as exc:
    _raise("invalid_schema", str(exc), source_name)
```

The category remains `invalid_schema`; `source_name` remains the exact constructed schema path. Do not normalize, strip, resolve, or otherwise rewrite the supplied path.

This is an error-boundary correction, not a new accepted path syntax.

## Type boundary

The public annotation is `schema_root: str | Path | None`. Inputs outside that declared contract (for example an arbitrary integer/object that makes `Path(schema_root)` itself raise `TypeError`) are not made newly valid by F-020.

Do **not** broaden to `except Exception` around `Path(schema_root)` or path joining. Such a catch would hide caller programming errors and change the declared API contract.

If future API work intentionally accepts generic `os.PathLike`, that needs its own contract/research.

## Error precedence

Preserve existing order:

1. resolve the registered schema filename;
2. construct `Path(schema_root) / filename`;
3. attempt to read schema bytes;
4. filesystem/path-spelling failure -> `invalid_schema`;
5. only after bytes are available perform UTF-8/JSON/Draft-2020-12/self-validation checks;
6. only after schema authority succeeds validate/preflight the instance according to F-015.

Therefore an invalid explicit schema filesystem path continues to outrank instance errors. F-020 must not move schema I/O after instance validation.

## Packaged schema resources

When `schema_root is None`, `_read_schema_bytes()` uses `importlib.resources.files("ontotf").joinpath("schemas", filename).read_bytes()`. That path is package-owned rather than a caller-provided native filesystem spelling.

F-020 should not change packaged-resource semantics merely to make both branches syntactically identical. Existing packaged schema loading/wheel tests are controls.

## Interaction with F-015 / F-016 / F-019

- **F-015** adds direct-instance `_plain_json()` preflight after successful schema authority checks. F-020 preserves that precedence and should integrate after F-015 rather than race it in `source_validation.py`.
- **F-016** contains recursion failures in custom schema parsing/validation. F-020 is only the native schema-file read boundary and must not add recursion handling.
- **F-019** handles invalid filesystem paths for source-document loading, mapping them to `decode_error`. F-020 is deliberately separate because explicit schema-file failures map to `invalid_schema`. Its accepted CPython/path-conversion evidence and mandatory cross-platform test precedent are reused here.

Production for F-020 should wait until overlapping `source_validation.py` lanes F-015/F-019 are merged or rebased; research does not need to wait.

## Future RED requirements

After the overlap gate clears, the plan/tests should pin at least:

1. embedded-NUL explicit schema root for a `.json` schema -> `SourceValidationError(category="invalid_schema")`, not raw host `ValueError`;
2. diagnostic `source_name` is the exact constructed schema file path;
3. ordinary missing schema file remains `invalid_schema` with unchanged provenance;
4. invalid schema UTF-8 / malformed JSON / invalid Draft schema retain current `invalid_schema` behavior;
5. packaged schema validation remains unchanged;
6. valid explicit `schema_root` remains unchanged;
7. invalid schema path still takes precedence over malformed direct instance input after F-015;
8. out-of-contract `schema_root` types that fail during `Path(schema_root)` construction remain programming/type errors rather than being relabeled `invalid_schema`.

The RED, GREEN, and final exact-head gate are mandatory on all four supported filesystem-facing cells:

- Ubuntu 24.04 × Python 3.10;
- Ubuntu 24.04 × Python 3.12;
- Windows latest × Python 3.10;
- Windows latest × Python 3.12.

Runner unavailability blocks the missing cell; it does not weaken the matrix. Tests assert only the stable ontoTF category/provenance/precedence contract, not platform-specific CPython exception wording.

## Non-goals

- no schema semantic change;
- no JSON Schema draft/version change;
- no path normalization, sandboxing, resolving, or canonicalization;
- no source-document loading change (F-019);
- no direct-instance preflight change (F-015);
- no schema recursion containment (F-016);
- no broad acceptance of out-of-contract `schema_root` types.

## Conclusion

F-020 is implementable as a narrow public error-boundary repair once overlapping validation work lands. A host path-conversion failure caused by an invalid explicit schema-root filesystem spelling should not escape ontoTF; it should remain in the existing `invalid_schema` authority family with exact schema-path provenance, and that contract must be demonstrated on the complete supported Ubuntu/Windows × Python 3.10/3.12 matrix.