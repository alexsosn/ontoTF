# F-022 implementation plan — semantic digest projection JSON boundary

**Issue:** #103  
**Research:** `docs/research/F-022-semantic-digest-json-boundary.md`

## 1. Goal

Restore the F-009 ontoTF JSON-model boundary inside the recursive semantic projection helper introduced by I-004, so public mapping-v2 and projection-v1 digest APIs never expose raw recursion for included cyclic/deep containers.

Do not change semantic identity, canonical bytes, digest algorithms, source/schema behavior, or audit-only exclusion.

## 2. Production scope

Only:

- `src/ontotf/semantic_digest_v2.py`

No changes to:

- `src/ontotf/digests.py` other than consuming its existing `MAX_JSON_NESTING` constant;
- schemas;
- source validation;
- semantic bundle validation;
- public names or algorithm identifiers.

## 3. Internal traversal contract

Extend private `_project()` to accept traversal state equivalent to:

```python
def _project(
    value: Any,
    *,
    top_level: bool = False,
    field: str | None = None,
    path: tuple[str | int, ...] = (),
    active: set[int] | None = None,
    depth: int = 0,
) -> Any:
    ...
```

For every included exact dict/list:

1. initialize/reuse one active-container set;
2. check repeated identity first;
3. fail `DigestError(DigestProblem(category="non_json_value", ...))` on cycle;
4. compute `container_depth = depth + 1`;
5. fail if `container_depth > MAX_JSON_NESTING`;
6. add identity to `active`;
7. recursively project included children with updated path/depth;
8. remove identity in `finally`.

Cycle check precedes depth check, matching F-009.

## 4. Exclusion precedence

For dicts, choose the top-level/nested exclusion set exactly as today. For each key:

- if excluded, skip without calling `_project()` on its value;
- if included, recurse with `path + (key,)`.

This is critical compatibility behavior. Recursive/deep values exclusively under ignored review/rationale/authored-digest metadata must not become semantic input errors merely because F-022 exists.

Lists recurse by index with `path + (index,)`.

## 5. Error messages and paths

Reuse F-009 message family:

- recursive list: `recursive list is outside the ontoTF JSON model`;
- recursive object: `recursive object is outside the ontoTF JSON model`;
- depth overflow: `JSON nesting exceeds maximum depth 128` using imported `MAX_JSON_NESTING`.

Category: `non_json_value`.

Path: first repeated or depth-129 **included** container location.

Do not create a new semantic-v2-specific category.

## 6. Canonicalization/sorting

Keep final calls to `canonical_json_bytes()` unchanged. They remain the final authority for scalar JSON/JCS constraints such as integer/float/unicode domain.

Keep `_canonical_sort()` semantics unchanged. It receives already-projected children and sorts by canonical bytes exactly as before.

No set-like field list changes.

## 7. RED tests

Create `tests/f022/__init__.py` and `tests/f022/test_semantic_digest_json_boundary.py` before any production edit.

### Mandatory cycle RED

1. `mapping_semantic_digest_v2()` with a self-reference in an included dict field must raise `DigestError(non_json_value)` and exact included path, not raw `RecursionError`.
2. `projection_semantic_digest_v1()` with a self-referential included list/dict must do the same.

These must fail on current production and are the required RED signal.

### Boundary controls

3. build an included container chain with exactly 128 containers; projection/digest succeeds.
4. depth 129 raises deterministic `DigestError(non_json_value)` with the first over-limit path.

Current production may already reject 129 late through `canonical_json_bytes()`; that is a control, not necessarily intended RED.

### Excluded-field controls

5. add a recursive object as top-level `review`; digest must equal the same mapping without `review` and must not recurse.
6. add recursive/deep data under top-level `rationale` if current projection skips it; digest remains equal.
7. add recursive data under nested projection `review` / authored `projection_semantic_digest`; projection digest remains equal to equivalent semantic content without those fields.

### Compatibility controls

8. preserve known mapping/projection digest outputs from existing I-004 fixtures.
9. preserve set-like ordering invariance for `native_dependencies`, `profiles`, `capabilities`, projections/candidates/references/evidence/losses where existing tests already establish it. Prefer invoking existing I-004 tests in CI over duplicating every vector.
10. direct non-JSON scalar/domain failures remain owned by `canonical_json_bytes()`.

## 8. RED workflow

Add `.github/workflows/f022-semantic-digest-json-boundary.yml` in the RED phase.

Matrix:

- Ubuntu 24.04;
- Python 3.10 and 3.12.

Steps:

1. exact-head checkout;
2. install package + build tooling consistent with current CI;
3. run `tests.f022` focused contract;
4. under `if: always()`, run F-009 tests;
5. under `if: always()`, run I-002 digest regressions;
6. under `if: always()`, run relevant I-004 semantic digest/public-contract regressions.

Do **not** duplicate the repository-wide test command; `full-suite.yml` owns it.

RED is accepted only if cycle tests fail for raw recursion/current behavior while existing F-009/I-002/I-004 controls stay green.

## 9. Minimal GREEN

After RED evidence only:

- import `MAX_JSON_NESTING` from `.digests` alongside existing digest symbols;
- add private projection failure helper if useful, or use existing `_fail()` with path support extended narrowly;
- add cycle/depth/path state to `_project()`;
- preserve exclusion-before-recursion and canonical sorting;
- no other production edits.

If extending `_fail()` to accept a path, preserve all existing projection-error call behavior by defaulting path to `()`.

## 10. Verification

Before final review require exact-head:

- F-022 matrix green on 3.10/3.12;
- F-009 green;
- I-002 green;
- I-004 green;
- centralized full repository suite green;
- compare against current main shows only F-022 research/plan/tests/workflow plus narrow `semantic_digest_v2.py` production delta.

If main moves materially, integrate/rebuild before final review.

## 11. Independent adversarial review

Fresh logically-independent exact-head review must attack:

- cycle-vs-depth precedence;
- dict/list path accounting;
- excluded audit-only subtrees accidentally traversed;
- off-by-one 128/129 behavior;
- active-set cleanup after child errors;
- set-like canonical sorting changes;
- existing digest-vector changes;
- accidental whole-record prevalidation;
- whether both mapping-v2 and projection-v1 public APIs are protected.

Any material finding returns to RED/repair/GREEN/CI and requires a new exact-head review.

## 12. Exit condition

F-022 completes only when included cyclic/deep semantic projection inputs obey the F-009 ontoTF-owned JSON boundary, excluded audit-only metadata remains non-authoritative, accepted digest bytes stay unchanged, exact-head CI is green, and fresh independent review reports no blocker.