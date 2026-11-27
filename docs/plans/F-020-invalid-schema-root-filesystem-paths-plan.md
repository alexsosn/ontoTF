# F-020 implementation plan — contain invalid explicit schema-root filesystem paths

**Issue:** #95  
**Research:** `docs/research/F-020-invalid-schema-root-filesystem-paths.md`  
**Dependency:** F-019 must be merged/integrated before production changes because both touch `src/ontotf/source_validation.py`.

## 1. Goal

Keep `validate_source(..., schema_root=...)` inside ontoTF's existing `invalid_schema` error family when a declared-valid `str | Path` schema root reaches the explicit schema-file read boundary but the native filesystem rejects the path spelling, notably an embedded NUL.

Do not change schema semantics, source-document loading, package-resource loading, path normalization, or accepted input types.

## 2. Public contract

For explicit `schema_root` only:

- `OSError` from reading the selected schema file -> existing `SourceValidationError(category="invalid_schema")`;
- read/open-time filesystem-path `ValueError` -> the same `invalid_schema` family;
- `ValidationProblem.source_name` remains the exact constructed schema-file path `str(Path(schema_root) / filename)`;
- host exception text is not standardized.

Outside the declared contract:

- `Path(schema_root)` construction/coercion failures remain normal programming/type failures;
- do not catch arbitrary `Exception`;
- do not reinterpret generic `os.PathLike` support in this ticket.

## 3. Required precedence

Preserve the current order exactly:

1. resolve registered schema filename;
2. construct `Path(schema_root) / filename` for explicit roots;
3. read schema bytes;
4. translate explicit schema filesystem/path-spelling failures to `invalid_schema`;
5. decode/parse/check the schema as Draft 2020-12;
6. only after schema authority succeeds preflight/validate the instance.

An invalid explicit schema path therefore outranks malformed/non-JSON direct instance data.

## 4. Packaged-resource boundary

When `schema_root is None`, keep the `importlib.resources.files("ontotf").joinpath(...).read_bytes()` branch unchanged.

F-020 must not broaden its catch merely to make packaged and explicit branches syntactically identical. Existing packaging/schema-authority tests are controls.

## 5. RED sequence

Production stays untouched until all mandatory RED cells show the intended failure.

Create `tests/f020/__init__.py` and `tests/f020/test_invalid_schema_root_filesystem_paths.py` plus a focused workflow.

### RED-A — embedded-NUL explicit schema root

For a registered schema such as `profile`, pass an explicit root containing an embedded NUL and assert:

1. `validate_source({}, "profile", schema_root="bad\0root")` raises `SourceValidationError` rather than raw `ValueError`;
2. category is exactly `invalid_schema`;
3. `source_name` is the exact constructed path `str(Path("bad\0root") / SCHEMA_FILES["profile"])`;
4. instance validation is not reached first.

The current production is expected to leak raw `ValueError`; that is the required RED signal.

### RED-B — authority/precedence controls

Already-green controls must stay green on the tests-only RED head:

- missing explicit schema file -> `invalid_schema` with exact schema path;
- invalid UTF-8 explicit schema -> `invalid_schema`;
- malformed JSON explicit schema -> `invalid_schema`;
- structurally invalid Draft schema -> `invalid_schema`;
- valid explicit schema root works unchanged;
- packaged schema validation works unchanged;
- malformed direct instance combined with invalid explicit schema path still fails at schema authority first.

### RED-C — declared-input boundary

- an out-of-contract `schema_root` object that fails during `Path(schema_root)` construction must retain the existing Python type/coercion error;
- no normalization/resolution of the authored schema root;
- no source-document `decode_error` behavior is changed.

## 6. Mandatory CI matrix

Focused RED, GREEN and final verification must run all four cells:

- Ubuntu 24.04 × Python 3.10;
- Ubuntu 24.04 × Python 3.12;
- Windows latest × Python 3.10;
- Windows latest × Python 3.12.

Workflow requirements:

1. exact-head checkout;
2. install editable package/build tooling consistent with current repository CI;
3. run established F-020 controls first;
4. run intended RED/GREEN contract;
5. under `if: always()`, run I-001/source-validation regressions and relevant packaging/schema-authority controls.

Repository-wide discovery remains owned by `full-suite.yml`.

Runner unavailability blocks the affected cell; it never makes Windows/POSIX optional.

## 7. Minimal GREEN

Only after complete RED evidence and F-019 integration, update the explicit `schema_root` read boundary in `_read_schema_bytes()` equivalent to:

```python
try:
    return schema_path.read_bytes(), source_name
except (OSError, ValueError) as exc:
    _raise("invalid_schema", str(exc), source_name)
```

The catch must remain **after** `schema_path = Path(schema_root) / filename` and `source_name = str(schema_path)` so caller type/coercion failures are not swallowed.

No helper/refactor unless RED demonstrates a concrete need.

## 8. Exact-head regression gate

Before final review require:

- all four F-020 OS/Python focused cells green;
- I-001/source-validation regressions green;
- explicit/packaged schema-authority controls green;
- authoritative full repository suite green;
- compare against then-current `main` shows only F-020 research/plan/tests/workflow plus the narrow `_read_schema_bytes()` exception-boundary delta.

If `main` advances materially, integrate it and repeat exact-head CI before review.

## 9. Independent adversarial review

Fresh exact-head review must attack at least:

- catch accidentally surrounding `Path(schema_root)` construction;
- `except Exception` or another over-broad catch;
- wrong category (`decode_error` instead of `invalid_schema`);
- lost/normalized schema-path provenance;
- instance validation running before schema authority;
- packaged-resource branch being changed accidentally;
- source-document `load_source()` behavior being modified again;
- F-016 schema-recursion logic being conflated;
- platform-specific exception text being frozen in tests;
- missing Windows/POSIX matrix cells.

Any finding returns to RED -> minimal GREEN -> exact-head CI -> fresh review.

## 10. Exit condition

F-020 completes only when invalid native filesystem spellings at the explicit schema-file read boundary are contained in the existing `invalid_schema` family with exact schema-path provenance, caller type/coercion and package-resource boundaries remain unchanged, all four supported OS/Python cells plus the full suite are green on the exact current-main head, and fresh adversarial review finds no blocker.