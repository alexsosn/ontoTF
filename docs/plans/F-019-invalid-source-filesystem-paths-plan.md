# F-019 implementation plan — contain invalid source filesystem paths

**Issue:** #94  
**Research:** `docs/research/F-019-invalid-source-filesystem-paths.md` and `docs/research/F-019-cpython-path-conversion-evidence.md`

## 1. Goal

Keep `load_source(path: str | Path)` inside ontoTF's existing typed source-loading error boundary when an otherwise constructed source path is rejected during filesystem I/O with `ValueError`, notably embedded NUL paths.

The change must preserve:

- existing `decode_error` category;
- exact authored `source_name` provenance;
- current file-read + UTF-8-decode before suffix precedence;
- current JSON/YAML parsing behavior;
- type/coercion behavior outside the declared `str | Path` API.

No schema, semantic, digest, identity, path-normalization, or sandboxing behavior changes.

## 2. Public contract

For a valid declared `str | Path` input that reaches `Path.read_bytes()`:

- `OSError` -> existing `SourceValidationError(category="decode_error")`;
- `UnicodeDecodeError` -> existing `decode_error`;
- filesystem/read-time `ValueError` -> the same `decode_error` family;
- `ValidationProblem.source_name` remains `str(Path(path))` exactly.

Do not standardize the platform/Python exception message.

Do not catch arbitrary `Exception`.

Do not broaden the declared API by converting `Path(path)` type/coercion failures for unsupported input objects into `decode_error`.

## 3. Error precedence

Keep the current order exactly:

1. `Path(path)` conversion;
2. `source_name = str(source_path)`;
3. `read_bytes()`;
4. UTF-8-SIG decode;
5. suffix dispatch;
6. JSON/YAML parser.

Consequences that tests must pin:

- missing `missing.txt` fails at filesystem access, not unsupported-suffix dispatch;
- existing valid-UTF8 `source.txt` reaches unsupported-suffix `decode_error`;
- existing invalid-UTF8 `source.txt` fails at UTF-8 decoding **before** unsupported-suffix dispatch;
- embedded-NUL `.json`, `.yaml`, `.yml`, or `.txt` fails at filesystem access before format dispatch.

## 4. Minimal production change

Preferred GREEN is limited to the current `load_source()` I/O/decode exception translation, equivalent to:

```python
try:
    text = source_path.read_bytes().decode("utf-8-sig")
except (OSError, UnicodeDecodeError, ValueError) as exc:
    _raise("decode_error", str(exc), source_name)
```

An equivalent small helper is acceptable only if RED demonstrates a concrete reason to factor it.

Do not alter `loads_source()`'s separate parser-time `ValueError` handling.

Do not include the explicit `schema_root` boundary; that is tracked separately because its existing category is `invalid_schema`.

## 5. RED sequence

Commit tests before changing `source_validation.py` and observe the intended failure.

### RED-A — embedded-NUL containment

On the complete supported matrix (Ubuntu 24.04 and Windows latest; Python 3.10 and 3.12), pin:

1. `load_source("bad\0.json")` raises `SourceValidationError` with category `decode_error`;
2. `.yaml` behaves identically;
3. `.yml` behaves identically as a symmetry control;
4. exact `problem.source_name` retains the authored path including the NUL;
5. raw `ValueError` never escapes.

These should be the only intended RED failures before production. If some matrix cells are temporarily queued/unavailable, RED evidence may arrive incrementally, but missing cells remain an unresolved gate rather than becoming optional.

### RED-B — established precedence controls

Already-green controls must remain green on the tests-only RED head:

1. ordinary missing `.json` -> `decode_error` and exact source path;
2. invalid UTF-8 readable `.json` -> `decode_error`;
3. existing readable valid-UTF8 `.txt` -> unsupported-suffix `decode_error`;
4. missing `.txt` -> filesystem failure before unsupported suffix (assert category/source and distinguish message class without freezing OS wording);
5. invalid-UTF8 readable `.txt` -> decode failure before unsupported suffix;
6. valid JSON and YAML still load unchanged.

### RED-C — propagation and declared-input boundary

1. `load_and_validate()` propagates the typed invalid-path source error before schema validation;
2. an object outside the declared `str | Path` API still raises the existing Python type/coercion failure rather than being relabeled `decode_error`.

## 6. CI

Focused workflow must run all four cells before completion:

- Ubuntu 24.04 × Python 3.10;
- Ubuntu 24.04 × Python 3.12;
- Windows latest × Python 3.10;
- Windows latest × Python 3.12;
- F-019 focused tests;
- I-001 source-loading regressions.

Temporary GitHub runner unavailability blocks the affected RED/GREEN/final gate; it never weakens or removes a matrix cell.

Repository-wide discovery remains owned only by `full-suite.yml`; do not duplicate it in the focused workflow.

During the intentionally RED phase, regression steps must use `if: always()` or separate jobs so established I-001 controls are demonstrably green even when F-019 focused tests fail.

## 7. Independent review gate

After GREEN exact-head CI, perform a fresh review independent of implementation reasoning. Attack at least:

- overly broad `ValueError` catching;
- accidental catch around `Path(path)` conversion;
- suffix-precedence change;
- path normalization or lost NUL/source provenance;
- raw exception leakage through `load_and_validate()`;
- regression of missing-file and invalid-UTF8 behavior;
- unintended changes to `loads_source()` parser errors;
- accidental inclusion of explicit schema-root handling.

Any finding returns to RED -> minimal GREEN -> exact-head CI -> fresh review.

## 8. Exit condition

F-019 is complete only when invalid source filesystem spellings no longer leak raw `ValueError`, existing source-loading precedence/provenance remains compatible, the complete Ubuntu/Windows × Python 3.10/3.12 focused matrix is green on the exact head, the authoritative full suite is green, and the final exact head passes fresh adversarial review.
