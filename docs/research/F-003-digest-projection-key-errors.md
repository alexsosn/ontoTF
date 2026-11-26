# F-003 digest projection non-string key error research

**Issue:** #26  
**Recorded:** 2026-09-06  
**Baseline:** current `main` after merged I-002  
**Scope:** research only; no production behavior changes in this commit.

## 1. Question

I-002 defines a stable `DigestError` / `DigestProblem` boundary for canonicalization and projection failures. Public projection helpers accept caller-constructed Python dictionaries directly. This research checks whether non-string dictionary keys are rejected through that ontoTF error boundary or whether Python implementation exceptions can escape.

## 2. Accepted I-002 contract

`docs/plans/I-002-canonicalization-digest-plan.md` defines:

- strict JSON-domain inputs with exact string object keys;
- `DigestError` with stable categories such as `non_json_value` and `projection_error`;
- projection helpers that reject missing, prohibited, or unknown fields rather than silently coercing them;
- no key coercion/stringification.

`canonical_json_bytes()` already enforces exact string object keys recursively and reports non-string keys as `DigestError(category="non_json_value")` with the relevant path.

Projection helpers intentionally do additional local shape checking before canonicalization and generally use `projection_error` for wrong projection shape. For consistency with their existing local-shape contract, non-string keys discovered by `_check_source_keys()` should be rejected as `projection_error` at the projection object's path rather than leak raw Python exceptions.

## 3. Current implementation

`src/ontotf/digests.py` contains:

```python
def _check_source_keys(source, *, allowed, required, path=()):
    missing = sorted(required - source.keys())
    if missing:
        _fail("projection_error", ...)
    unknown = sorted(source.keys() - allowed)
    if unknown:
        _fail("projection_error", f"unknown projection fields: {', '.join(unknown)}", path)
```

There is no exact-string-key guard before set subtraction, sorting, and string joining.

`_exact_dict()` checks only `type(value) is dict`; it does not inspect keys.

## 4. Confirmed failure modes

The failure is deterministic Python behavior and does not depend on `jsonschema`, `rfc8785`, or corpus data.

For an otherwise valid source with one integer unknown key:

```python
source = {"a": "ok", 1: "x"}
```

`sorted(source.keys() - allowed)` can produce `[1]`, after which `", ".join(unknown)` raises:

```text
TypeError: sequence item 0: expected str instance, int found
```

For mixed string and integer unknown keys:

```python
source = {"a": "ok", "future": "x", 1: "y"}
```

`sorted(...)` itself raises:

```text
TypeError: '<' not supported between instances of 'str' and 'int'
```

Tuple or other non-string unknown keys can likewise survive set subtraction and fail later during formatting.

Therefore the public error contract currently depends on the accidental comparability/formatability of Python key objects.

## 5. `_check_source_keys()` call surface

The shared helper is used by:

1. `evidence_record_projection()` at the top-level normalized evidence object;
2. `_normalize_evidence_bindings()` for nested evidence binding records;
3. `_normalize_candidates()` for candidate projection records;
4. `mapping_semantic_projection()` at the top-level mapping object;
5. `_normalize_ontology_lock_identities()` for profile ontology lock records;
6. `_normalize_mapping_identities()` for profile mapping identity records;
7. `_normalize_review_readiness()` for profile review readiness records;
8. `profile_semantic_digest()` at the top-level assembled profile projection.

All of these may receive caller-constructed dictionaries because the digest/projection APIs are public Python APIs and are not restricted to values returned by `loads_source()`.

`_normalize_record_set()` is different: it does not call `_check_source_keys()` and delegates its record to `_validate_json()`, which already rejects non-string keys through `DigestError(category="non_json_value")`. F-003 should not broaden scope by changing that established path.

## 6. Category and path decision

For objects checked through `_check_source_keys()`, use:

```text
category = projection_error
path = the existing `_check_source_keys(..., path=...)` object path
```

Reasoning:

- these helpers are performing a projection-specific closed-record check;
- missing and unknown string keys already use `projection_error` at that same object path;
- changing these call paths to `non_json_value` would unnecessarily split one local shape contract;
- `canonical_json_bytes()` keeps its existing `non_json_value` behavior when it is the component detecting the invalid key.

The message should be deterministic and must not stringify arbitrary key objects as if they were valid field names. A stable message such as `projection object keys must be exact strings` is sufficient.

## 7. Minimal repair location

The smallest complete fix is inside `_check_source_keys()` before any set arithmetic, sorting, or formatting:

```python
if any(type(key) is not str for key in source):
    _fail("projection_error", "projection object keys must be exact strings", path)
```

This centralizes the contract for all current callers and leaves all-string missing/unknown-field behavior byte-for-byte unchanged.

Rejected alternatives:

- validating keys separately in every caller: duplicates policy and invites drift;
- coercing keys with `str(key)`: changes semantics and can create collisions;
- catching broad `TypeError`: can hide unrelated implementation defects;
- calling `_validate_json(source)` before shape checking: changes categories and may validate payload values that the projection helper intentionally handles later.

## 8. Regression matrix

RED tests should prove raw exceptions currently escape for:

- top-level `evidence_record_projection()` with one integer unknown key;
- top-level `mapping_semantic_projection()` with mixed string + integer unknown keys;
- nested candidate or evidence binding record with a tuple/integer key and verify the nested object path after repair;
- top-level `profile_semantic_digest()` with a non-string key;
- one nested profile identity record checked through `_check_source_keys()`.

Controls should verify:

- unknown **string** fields still produce the existing `projection_error` path/message class;
- missing required fields still produce existing `projection_error` behavior;
- `canonical_json_bytes({1: ...})` remains `non_json_value`, demonstrating that F-003 changes only projection-shape handling.

## 9. Scope boundary

F-003 does not:

- change semantic digest projections;
- change canonical JSON rules;
- change schema validation;
- add coercion or normalization;
- alter I-003 parent identity;
- implement I-004+ semantic validation.

## 10. Research conclusion

The defect is real and localized. `_check_source_keys()` must reject any non-exact-string key before set/sort/join operations. Existing callers already provide the correct object path, so a one-boundary fail-closed guard can restore the promised stable `DigestError` contract without changing valid projection semantics.
