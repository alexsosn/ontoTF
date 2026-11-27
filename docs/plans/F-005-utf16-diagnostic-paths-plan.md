# F-005 UTF-16 ordering diagnostic paths implementation plan

**Issue:** #30  
**Recorded:** 2026-09-06  
**Research dependency:** `docs/research/F-005-utf16-diagnostic-paths.md` at `0eec0030187b49e6c194f397c1a0b4eda532ce77`  
**Baseline:** `main` at `2dc7ab12781226566d0ec1eb49c99872990902c7`

## 1. Scope

F-005 repairs only `DigestProblem.path` provenance for `unicode_domain` failures that arise while computing normative UTF-16 ordering keys in I-002 semantic set normalization.

It does not change:

- Unicode validity rules;
- UTF-16 code-unit ordering;
- semantic projection membership;
- public projection shapes;
- canonical JSON bytes;
- valid digest vectors;
- source-bundle path rules;
- I-003 or I-004+ semantics.

## 2. Affected production boundary

Only `src/ontotf/digests.py` changes.

The private helper becomes conceptually:

```python
def _utf16_sort_key(
    value: str,
    *,
    path: tuple[str | int, ...] = (),
) -> bytes:
    ...
```

It must still return exactly `value.encode("utf-16be")` for valid strings. On `UnicodeEncodeError` it raises `DigestError` category `unicode_domain` with the supplied path.

A helper parameter alone is not enough: vulnerable list/record normalizers must compute keys while the original authored index/field path is still known, before sorting discards that provenance.

## 3. Path matrix

Required exact paths for lone-surrogate sort keys:

| Input | Expected `DigestProblem.path` |
| --- | --- |
| mapping `native_dependencies[1]` | `("native_dependencies", 1)` |
| mapping `evidence[1].evidence_id` | `("evidence", 1, "evidence_id")` |
| mapping `evidence[1].content_digest` | `("evidence", 1, "content_digest")` |
| candidate `candidate_projections[0].evidence[1].evidence_id` | `("candidate_projections", 0, "evidence", 1, "evidence_id")` |
| profile `semantic_domains[1]` | `("semantic_domains", 1)` |
| profile `ontology_locks[1].terms_used[1]` | `("ontology_locks", 1, "terms_used", 1)` |
| profile `ontology_locks[1].lock_id` | `("ontology_locks", 1, "lock_id")` |
| profile `mappings[1].mapping_id` | `("mappings", 1, "mapping_id")` |
| profile `review_readiness[1].mapping_id` | `("review_readiness", 1, "mapping_id")` |

Control: profile `dependencies[1].dependency_id` is already rejected by `_validate_json(obj, path=item_path)` before the later sort and must remain `("dependencies", 1, "dependency_id")` without production changes to `_normalize_record_set()`.

## 4. Minimal implementation design

### 4.1 Unique-string collections

`_normalize_unique_strings()` will compute the UTF-16 key during enumeration:

```text
(index, item)
 -> validate exact non-empty string
 -> duplicate check
 -> _utf16_sort_key(item, path=path + (index,))
 -> store (key, item)
 -> sort by key
 -> return items only
```

This preserves duplicate behavior and output values while attaching the pre-sort source path to encoding failures.

### 4.2 Evidence bindings

During enumeration, after exact-string/duplicate checks, compute:

- evidence ID key with `item_path + ("evidence_id",)`;
- content-digest key with `item_path + ("content_digest",)`.

Store private `(evidence_id_key, content_digest_key, normalized_record)` tuples, sort by the first two keys, and return records only. Private keys never enter canonical JSON.

### 4.3 Profile identity collections

For ontology locks, mapping identities, and review readiness, compute the primary identifier key during original enumeration with the exact field path, retain `(key, record)` privately, sort by key, and return records.

For ontology `terms_used`, reuse the repaired `_normalize_unique_strings()`.

### 4.4 Already-safe record sets

Do not alter `_normalize_record_set()`. Its existing `_validate_json(obj, path=item_path)` runs before the identifier sort and already catches lone surrogates with the correct recursive field path.

## 5. RED tests

Create `tests/i002/test_utf16_diagnostic_paths.py` before production changes.

Use public digest/projection APIs and real source-shaped fixtures, not direct calls to the private helper. A small local fixture builder may mirror the existing `SemanticDigestTests` data but must not depend on test-class internals.

The focused RED suite must assert:

- category is `unicode_domain`;
- exact path matches the matrix above for every vulnerable call-site family;
- dependency-ID control already reports its exact path on the RED head.

At least one failing assertion must demonstrate current `()` path loss; ideally all vulnerable cases fail for the same intended reason.

## 6. Semantic controls

The F-005 focused test file also includes valid-input controls:

1. valid UTF-16 ordering pair whose Python code-point order differs from UTF-16 order (U+1F600 vs U+E000) remains order-invariant under mapping/profile digests;
2. existing I-002 fixed-vector suite remains authoritative and must pass unchanged after GREEN;
3. duplicate set identifiers retain existing `projection_error` behavior/path.

No expected digest constant is changed.

## 7. CI / RED-GREEN gate

Add `.github/workflows/f005-utf16-diagnostic-paths.yml` before production changes. It triggers on the F-005 branch, PRs touching the F-005 surface, and relevant files.

Python 3.12 is sufficient because the change is pure Python and I-002's supported floor remains independently exercised by existing gates. Steps:

```text
checkout
setup-python 3.12
pip install --upgrade pip
pip install -e .
python -m unittest tests.i002.test_utf16_diagnostic_paths -v
python -m unittest discover -s tests/i002 -v
python -m unittest discover -s tests -v
```

RED exact head must fail in the focused F-005 step after install succeeds and before production is modified. GREEN exact head must pass focused F-005, full I-002, and full repository suites.

Existing I-001/I-002/F-002/F-003/F-004 workflows may also trigger from `src/ontotf/digests.py`; all triggered exact-head checks must be green before review.

## 8. Implementation gate

Only after RED is recorded:

1. add path-aware `_utf16_sort_key()`;
2. convert the vulnerable normalizers to precompute private sort keys with authored paths;
3. leave `_normalize_record_set()` unchanged;
4. run exact-head CI;
5. inspect the final diff for accidental projection/digest changes.

No opportunistic refactor.

## 9. Independent review attack surface

Fresh reviewer must independently try to falsify:

- original pre-sort index preservation (especially second/later entries);
- evidence ID vs content-digest field distinction;
- nested candidate evidence path composition;
- ontology lock ID versus terms-used paths;
- accidental post-sort index reporting;
- accidental ordering change for U+1F600/U+E000;
- private key leakage into canonical projections;
- duplicate behavior drift;
- fixed digest-vector drift;
- unnecessary change to already-safe `_normalize_record_set()`.

Any material head change after review invalidates the review.

## 10. Acceptance trace

- Research `0eec0030...` precedes this plan.
- This plan must precede RED tests.
- RED must prove diagnostic-path loss with production unchanged.
- GREEN must preserve all valid digest semantics.
- Fresh logically-independent adversarial exact-head PASS is mandatory before merge.
