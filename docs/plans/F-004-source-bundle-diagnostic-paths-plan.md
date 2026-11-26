# F-004 source-bundle diagnostic path implementation plan

**Issue:** #28  
**Research:** `docs/research/F-004-source-bundle-diagnostic-paths.md` at `03a2a8f07767faab2aab47a1737b68407d4b152d`  
**Baseline:** merged I-002 on current `main`

## 1. Goal

Make every invalid logical-path failure from `source_bundle_digest()` identify the offending tuple field as `(entry_index, 0)` while preserving the current path grammar, categories, messages, and digest semantics.

## 2. Production change

Modify only `src/ontotf/digests.py`:

```python
def _validate_logical_path(
    path: Any,
    *,
    error_path: tuple[str | int, ...] = (),
) -> str:
```

Every existing `_fail("projection_error", ...)` inside the helper gains `error_path` as its path argument.

Change the sole call in `source_bundle_digest()` from:

```python
path = _validate_logical_path(entry[0])
```

to:

```python
path = _validate_logical_path(entry[0], error_path=(index, 0))
```

No other production functions change.

## 3. Diagnostic contract

For any invalid logical-path syntax/type in bundle entry `i`:

```text
category = projection_error
path = (i, 0)
message = existing message for that failure class
```

Controls remain:

```text
malformed entry tuple -> (i,)
duplicate logical path -> (i, 0)
invalid payload type -> (i, 1)
```

The private helper default `error_path=()` preserves deterministic behavior for any future/internal direct use.

## 4. RED regressions

Add `tests/i002/test_source_bundle_diagnostic_paths.py` before production changes.

Tests:

1. traversal path `../a.yaml` at entry 0 expects `(0, 0)`;
2. absolute `/a.yaml` expects `(0, 0)`;
3. backslash `a\\b.yaml` expects `(0, 0)`;
4. wrong logical-path type (e.g. integer) expects `(0, 0)`;
5. invalid path on entry 2 expects `(2, 0)` to prove index propagation;
6. empty/dot-segment representative expects `(0, 0)`.

Controls:

7. duplicate logical path remains `(1, 0)`;
8. non-bytes payload remains `(0, 1)`;
9. malformed tuple remains `(0,)`;
10. existing source-bundle fixed vector remains unchanged.

At RED head, tests 1-6 must fail because current path is `()` while controls pass.

## 5. Workflow

Add `.github/workflows/f004-source-bundle-diagnostic-paths.yml` triggered by:

```text
.github/workflows/f004-source-bundle-diagnostic-paths.yml
docs/research/F-004-source-bundle-diagnostic-paths.md
docs/plans/F-004-source-bundle-diagnostic-paths-plan.md
src/ontotf/digests.py
tests/i002/**
pyproject.toml
```

Push branch: `fix/source-bundle-diagnostic-paths`.

Run Python 3.12:

```text
python -m pip install -e .
python -m unittest tests.i002.test_source_bundle_diagnostic_paths -v
python -m unittest discover -s tests/i002 -v
python -m unittest discover -s tests -v
```

Exact-head RED and GREEN are mandatory.

## 6. GREEN implementation

After RED is recorded:

1. add `error_path` to the private helper;
2. pass it to all three current path-validation `_fail()` branches;
3. pass `(index, 0)` from `source_bundle_digest()`;
4. run focused I-002/full suite;
5. compare against main and verify no digest logic/path grammar changed.

## 7. Adversarial review checklist

Fresh independent review must check:

- all path rejection branches propagate `(index, 0)`;
- later entry indexes are not hard-coded;
- duplicate and payload paths remain unchanged;
- valid fixed vector is unchanged;
- no path normalization/coercion was introduced;
- default helper behavior remains deterministic;
- no I-003/I-004+ scope leakage;
- exact-head focused/full CI is green.

## 8. Non-goals

No digest projection changes, no accepted-path grammar changes, no source normalization changes, no schemas, no parent identity, no semantic validation, no compatibility evaluation.

## 9. Acceptance

Research precedes this plan; this plan precedes RED; RED demonstrates only diagnostic-path mismatch; GREEN is minimal and exact-head tested; independent adversarial review has no blockers before merge.
