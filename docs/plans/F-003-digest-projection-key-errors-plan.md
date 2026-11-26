# F-003 digest projection key error implementation plan

**Issue:** #26  
**Research:** `docs/research/F-003-digest-projection-key-errors.md` at `f76f7b41dc11a7c3536db18e196665f176d61549`  
**Baseline:** merged I-002 on current `main`

## 1. Goal

Restore the promised stable `DigestError` boundary when public digest/projection helpers receive exact dictionaries containing non-string keys.

The change must not alter any valid semantic projection or any all-string missing/unknown-field diagnostic.

## 2. Production change

Modify only `_check_source_keys()` in `src/ontotf/digests.py`.

Before set subtraction, sorting, or message formatting, reject any key whose exact type is not `str`:

```python
if any(type(key) is not str for key in source):
    _fail(
        "projection_error",
        "projection object keys must be exact strings",
        path,
    )
```

Then retain the existing code for required/unknown string keys unchanged.

Do not add broad exception handling or key coercion.

## 3. Error contract

For `_check_source_keys()` callers:

```text
category: projection_error
message: projection object keys must be exact strings
path: existing object path passed to `_check_source_keys()`
```

Expected examples:

- top-level evidence/mapping/profile object: `path == ()`;
- candidate record: `("candidate_projections", index)`;
- mapping evidence binding: `("evidence", index)`;
- profile ontology lock: `("ontology_locks", index)`;
- profile mapping identity: `("mappings", index)`;
- profile review readiness: `("review_readiness", index)`.

`canonical_json_bytes()` is explicitly outside this change and continues to report non-string JSON object keys as `non_json_value`.

`_normalize_record_set()` is also outside this change because it does not use `_check_source_keys()` and already reaches `_validate_json()`.

## 4. RED tests

Add `tests/i002/test_projection_key_error_boundary.py` before modifying production code.

The test module will construct minimal valid shapes and assert `DigestError(category="projection_error")` rather than raw exceptions for:

1. `evidence_record_projection()` with one integer unknown key;
2. `mapping_semantic_projection()` with both an unknown string key and an integer key, specifically exercising the current mixed-key `sorted()` failure;
3. a nested candidate projection record with a tuple key, expecting path `("candidate_projections", 0)` after repair;
4. `profile_semantic_digest()` top-level projection with an integer key;
5. a nested ontology lock record with an integer key, expecting path `("ontology_locks", 0)` after repair.

Controls:

6. an unknown string field still yields `projection_error` with its current object path;
7. a missing required field still yields `projection_error` with its current object path;
8. `canonical_json_bytes({1: "x"})` still yields `non_json_value`.

The RED head must leave `src/ontotf/digests.py` untouched. At least cases 1-5 should error/fail because the current implementation leaks `TypeError`; controls should already pass.

## 5. Fixtures

Keep fixtures local to the regression module and small.

### Minimal normalized evidence

```python
{
    "evidence_id": "evidence:test",
    "kind": "native-doc",
    "source_uri": "https://example.org/source",
    "content_mode": "normalized-record",
    "reviewed_content": {"statement": "test"},
}
```

### Minimal mapping

Reuse the accepted I-002 semantic field shape with:

- empty `native_dependencies`, `candidate_projections`, and `evidence` where structurally sufficient for the digest helper;
- scalar placeholders for target/assessment/applicability fields.

The helper is not a schema validator, so the regression should test only the projection boundary required to reach `_check_source_keys()`.

### Minimal assembled profile projection

Provide all eleven required top-level fields with empty set-like collections where accepted by the digest helper. For nested ontology-lock coverage, use one otherwise complete lock identity.

## 6. Workflow

Add `.github/workflows/f003-digest-projection-key-errors.yml` with push trigger for branch `fix/digest-projection-key-errors` and pull-request triggers on:

```text
.github/workflows/f003-digest-projection-key-errors.yml
docs/research/F-003-digest-projection-key-errors.md
docs/plans/F-003-digest-projection-key-errors-plan.md
src/ontotf/digests.py
tests/i002/**
pyproject.toml
```

Use Python 3.12 and:

```text
python -m pip install -e .
python -m unittest tests.i002.test_projection_key_error_boundary -v
python -m unittest discover -s tests/i002 -v
python -m unittest discover -s tests -v
```

RED should fail in the focused F-003 module before production changes. GREEN must pass all three test stages on the exact final head.

## 7. GREEN implementation

After exact-head RED is recorded:

1. add the one shared non-string-key guard in `_check_source_keys()`;
2. do not edit projection algorithms or public APIs;
3. run exact-head CI;
4. inspect the diff to verify production change is limited to the guard.

No new dependency is required.

## 8. Adversarial review checklist

Fresh independent review must attempt to falsify:

- integer key as the only unknown key;
- mixed string/integer unknown keys;
- tuple/custom non-string keys;
- nested path preservation;
- no key stringification/coercion;
- no category drift for all-string missing/unknown fields;
- no change to `canonical_json_bytes()` non-string-key category;
- no semantic digest/projection changes;
- exact-head focused/full CI.

## 9. Non-goals

No schema changes, I-003 parent identity, I-004+ semantic validation, compatibility evaluation, IR/runtime work, or corpus mappings.

## 10. Acceptance

- research precedes this plan;
- this plan precedes RED tests;
- RED demonstrates the raw-exception leak on exact head;
- GREEN uses the minimal shared guard;
- focused I-002/F-003 and full suite pass on exact head;
- fresh logically-independent adversarial exact-head review has no blockers before merge.
