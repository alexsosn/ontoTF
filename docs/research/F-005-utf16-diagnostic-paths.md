# F-005 UTF-16 ordering diagnostic paths research

**Issue:** #30  
**Recorded:** 2026-09-06  
**Baseline:** `main` at `2dc7ab12781226566d0ec1eb49c99872990902c7`

## Question

I-002 deliberately rejects lone-surrogate / non-UTF-8 strings as `unicode_domain` and uses UTF-16 code-unit ordering for set-like semantic identifiers. Does every UTF-16 ordering failure retain the source location already known by the normalizer?

## Accepted contract

The accepted I-002 plan (`docs/plans/I-002-canonicalization-digest-plan.md`) defines:

```python
@dataclass(frozen=True)
class DigestProblem:
    category: str
    message: str
    path: tuple[str | int, ...] = ()
```

It makes `unicode_domain` the stable category for lone surrogates / otherwise non-UTF-8-serializable strings and states that tests assert ontoTF category/path. The same plan makes UTF-16 code-unit ordering normative for set-like semantic strings; valid ordering semantics therefore must not change in a diagnostics fix.

## Current implementation

`src/ontotf/digests.py` currently has:

```python
def _utf16_sort_key(value: str) -> bytes:
    try:
        return value.encode("utf-16be")
    except UnicodeEncodeError as exc:
        _fail("unicode_domain", str(exc))
```

Because `_fail()` receives no path, an encoding failure here always produces `DigestProblem.path == ()`, even where the caller previously had a precise item/field path.

`_require_nonempty_string(value, path=...)` verifies exact non-empty `str`, but intentionally does not test Unicode scalar validity. Therefore a lone surrogate can reach `_utf16_sort_key()`.

## Call-site audit

### 1. `_normalize_unique_strings(value, path=...)` — vulnerable

Used for:

- mapping `native_dependencies`;
- profile `semantic_domains`;
- ontology-lock `terms_used`.

The function enumerates the authored list and already knows `path + (index,)`, but appends only the string and later calls:

```python
sorted(result, key=_utf16_sort_key)
```

A surrogate therefore loses the original item path during sort.

Natural diagnostic paths include:

- `("native_dependencies", index)`;
- `("semantic_domains", index)`;
- `("ontology_locks", lock_index, "terms_used", term_index)`.

### 2. `_normalize_evidence_bindings(value, path=...)` — vulnerable

During iteration it already knows:

```text
item_path + ("evidence_id",)
item_path + ("content_digest",)
```

but stores only normalized strings and later computes both UTF-16 keys in a sort lambda. A surrogate in either field therefore reports `()` instead of the specific binding field.

This affects top-level mapping evidence and candidate-projection evidence.

### 3. `_normalize_record_set(..., id_field, path)` — already path-safe for Unicode

This function calls:

```python
_validate_json(obj, path=item_path)
```

before sorting by `_utf16_sort_key(item[id_field])`.

`_validate_json()` validates every string using UTF-8 encoding and preserves the recursive field path. A surrogate `dependency_id` (or any other string in the record) therefore fails before the later sort and already reports the authored path. F-005 should not rewrite this path solely for consistency.

### 4. `_normalize_ontology_lock_identities()` — partially vulnerable

`lock_id` is checked only by `_require_nonempty_string()` and is sorted with `_utf16_sort_key()` before the assembled profile reaches final `_validate_json()`. A surrogate `lock_id` therefore loses:

```text
("ontology_locks", index, "lock_id")
```

`terms_used` is separately vulnerable through `_normalize_unique_strings()` as above.

Other scalar fields are not UTF-16 sort keys and belong to ordinary JSON-domain validation, not this ticket.

### 5. `_normalize_mapping_identities()` — vulnerable

A surrogate `mapping_id` reaches the UTF-16 sort before final `_validate_json()` and loses:

```text
("mappings", index, "mapping_id")
```

`mapping_semantic_digest` is not a sort key and is outside F-005.

### 6. `_normalize_review_readiness()` — vulnerable

A surrogate `mapping_id` reaches the UTF-16 sort before final `_validate_json()` and loses:

```text
("review_readiness", index, "mapping_id")
```

### 7. `_normalize_candidates()` — not an `_utf16_sort_key()` problem

Candidates are sorted by already computed JCS bytes. `canonical_json_bytes(item)` can itself reject invalid strings, but its path behavior is a separate canonical-projection diagnostic question. F-005 must not expand into that boundary.

## Minimal safe design direction

The original authored index must be retained **before sorting**. Adding only an optional `path` parameter to `_utf16_sort_key()` is insufficient for sort lambdas over already-normalized records because the original list index has been discarded.

The narrow approach is to compute UTF-16 keys while each vulnerable function still owns the original path, then sort keyed records:

- unique-string lists: collect `(utf16_key, value)` while enumerating;
- evidence bindings: compute `evidence_id_key` and `content_digest_key` while `item_path` is known, retain them only as private sort metadata, then return the same public record shape;
- ontology/mapping/review identity collections: compute the identifier key during the original enumeration, pair it with the normalized record, sort by the private key, and return records only.

`_utf16_sort_key()` can accept a keyword-only `path=()` so each key computation converts `UnicodeEncodeError` into `DigestError(unicode_domain, path=<authored field path>)`.

No private sort key may enter canonical JSON or any digest projection.

## Compatibility constraints

F-005 must preserve all valid-input semantics:

- exact same UTF-16BE bytes used as the ordering key;
- exact same ordering for valid Unicode, including non-BMP strings;
- exact same public projection shapes;
- exact same duplicate detection and duplicate diagnostic paths;
- exact same fixed digest vectors;
- no Unicode normalization, replacement, coercion, or relaxation;
- no source-bundle/path, schema, parent-identity, or I-004+ behavior.

The private helper is not part of the package-root public API, but its default top-level path should remain deterministic for any internal call that genuinely lacks source provenance.

## Regression matrix for the plan

At minimum RED should establish current path loss for:

1. mapping `native_dependencies[1]` -> expected `("native_dependencies", 1)`;
2. profile `semantic_domains[1]` -> expected `("semantic_domains", 1)`;
3. mapping evidence binding `evidence[1].evidence_id` (and preferably `content_digest`) -> exact field path;
4. profile `ontology_locks[1].lock_id`;
5. profile `mappings[1].mapping_id`;
6. profile `review_readiness[1].mapping_id`.

A control should confirm `_normalize_record_set()`/dependency IDs already retain their field path and therefore need no production change.

Existing UTF-16 non-BMP ordering regressions and fixed semantic digest vectors must stay green.

## Conclusion

This is a diagnostic-provenance defect, not an identity-semantics defect. The accepted I-002 contract already supplies precise caller paths before vulnerable UTF-16 sorts; current implementation discards those paths. The fix should attach path information when computing private sort keys while the original authored index is still available, without changing any canonical projection or digest for valid input.
