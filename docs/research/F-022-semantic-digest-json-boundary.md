# F-022 research — restore F-009 JSON boundaries in semantic digest v2 projection

**Issue:** #103  
**Baseline:** `main` at ticket start  
**Type:** public digest API stability / post-I-004 regression hardening

## Question

Do the I-004 semantic digest projection APIs preserve the deterministic ontoTF JSON-model boundary established by F-009, including cycle detection and `MAX_JSON_NESTING=128`, or can their own projection traversal fail before the canonicalization guard runs?

## Accepted prior contract

F-009 explicitly scoped its hardening to programmatic values passed to canonicalization **and semantic digest projections**. Its accepted contract is:

- exact ontoTF JSON values only;
- recursive list/dict aliases fail as `DigestError(category="non_json_value")` rather than raw interpreter exceptions;
- container depth 128 is accepted and depth 129 is rejected deterministically;
- the first over-limit path is reported by the ontoTF-owned JSON guard;
- raw downstream `RecursionError` is not part of the public digest API;
- canonical bytes and digest algorithm identifiers for accepted values are unchanged.

Current `src/ontotf/digests.py` implements that contract in `_validate_json()` and `canonical_json_bytes()` using `MAX_JSON_NESTING = 128`, active-container identity tracking and a defensive `RecursionError` translation around RFC 8785 serialization.

## Regression introduced after F-009

I-004 later added `src/ontotf/semantic_digest_v2.py`. Both public semantic projection families use the same recursive helper:

```python
def _project(value, *, top_level=False, field=None):
    if type(value) is dict:
        ...
        for key, item in value.items():
            if key in excluded:
                continue
            result[key] = _project(item, field=key)
        return result
    if type(value) is list:
        projected = [_project(item) for item in value]
        ...
        return projected
    return value
```

Only **after** that traversal do `mapping_semantic_projection_v2()` and `projection_semantic_projection_v1()` call `canonical_json_bytes()`.

Therefore the F-009 guard is ordered too late for the recursive projection helper itself.

## Deterministic failure class

A recursive container in any semantically included branch is sufficient; no platform timing or host recursion-threshold assumption is needed.

Conceptual reproducer:

```python
mapping = {"mapping_id": "m"}
mapping["included"] = mapping
mapping_semantic_digest_v2(mapping)
```

`_project()` revisits the same exact dict indefinitely before `canonical_json_bytes()` is reached, so current behavior is raw `RecursionError` rather than `DigestError(non_json_value)`.

The same defect exists for `projection_semantic_digest_v1()` because it uses the same `_project()` helper.

Very deep acyclic included branches have the same ordering defect: `_project()` traverses beyond F-009's deterministic depth-128 policy before canonicalization gets a chance to reject depth 129. At sufficiently large host-dependent depth this can also become raw `RecursionError`. The cycle reproducer is the preferred RED because it is deterministic and independent of `sys.getrecursionlimit()`.

## Important compatibility boundary: excluded audit-only branches

A naïve fix such as calling `canonical_json_bytes(mapping)` before projection would change an unrelated contract.

`semantic_digest_v2.py` intentionally excludes audit-only fields from semantic identity:

Top-level exclusions:

- `review`;
- `mapping_semantic_digest`;
- `rationale`;
- `introduced_in`;
- `changed_in`.

Nested exclusions:

- `review`;
- `projection_semantic_digest`.

Current `_project()` skips these values **before traversing them**. Consequently their internal shape is not part of the semantic projection. Structural source validation normally keeps authored artifacts JSON-compatible, but the direct digest projection API should not accidentally make excluded audit metadata semantically authoritative merely to repair the included-branch recursion bug.

The fix should therefore guard the traversal actually performed by `_project()`, after exclusion decisions, rather than validating the entire original object indiscriminately.

## Required projection guard semantics

The semantic projection traversal should mirror the relevant F-009 JSON-model rules for every included list/dict it enters:

1. keep an `active` container-ID set;
2. for an included exact list/dict, check cycle membership before descending;
3. compute container depth using the F-009 counting rule;
4. reject depth greater than `MAX_JSON_NESTING` with `DigestError(non_json_value)` before recursing further;
5. preserve a deterministic path to the repeated/over-limit included container;
6. remove the container ID from `active` on unwind;
7. skip excluded audit-only keys without traversing or counting their subtrees;
8. after projection, retain the existing `canonical_json_bytes()` call as the final JSON/canonicalization authority.

The guard may reuse `MAX_JSON_NESTING` from `ontotf.digests`; the numeric policy must not be duplicated independently.

## Error contract

Reuse F-009's existing public category rather than creating a semantic-v2-specific category:

- cycle: `DigestError`, category `non_json_value`, message equivalent to the existing recursive list/object diagnosis, path at the included repeated container;
- depth overflow: `DigestError`, category `non_json_value`, message `JSON nesting exceeds maximum depth 128`, path at the first included container that would be depth 129.

There is no algorithm-version change: values newly rejected by this fix were already outside the accepted F-009 ontoTF JSON input domain. Accepted semantic projections and their canonical bytes must stay unchanged.

## Set-like sorting interaction

`_canonical_sort()` canonicalizes projected children. The traversal guard must run before a cyclic/deep child can reach sorting. For accepted children, the existing canonical-byte sort order remains unchanged.

No change is needed to the set-like field list or to mapping/projection semantic identity.

## RED strategy

Tests should be added before production edits and should cover both public surfaces.

Mandatory RED:

1. mapping-v2 included recursive object -> owned `DigestError(non_json_value)`, not raw `RecursionError`;
2. projection-v1 included recursive list/object -> same;
3. depth-128 included container nesting accepted when otherwise canonicalizable;
4. depth-129 included nesting rejected at the first over-limit included path;
5. recursive or over-deep content exclusively under a top-level excluded audit field remains untraversed by projection and does not change the semantic digest of the same semantic content without that audit field;
6. nested excluded `review` / authored projection digest content likewise remains excluded;
7. existing mapping-v2/projection-v1 digest vectors and set-like order-invariance controls stay green.

The cycle tests are the primary intended RED on current main. Depth-129 may already eventually become `DigestError` through the late canonicalization call, so RED must not falsely claim every planned assertion currently fails; the defect being fixed is the **pre-canonical recursive traversal boundary**.

## Minimal implementation recommendation

Change only `src/ontotf/semantic_digest_v2.py`:

- import `MAX_JSON_NESTING` and `DigestError`/`DigestProblem` support already used by the module;
- extend `_project()` with `path`, `active`, and `depth` state;
- apply cycle/depth checks only when descending into included exact list/dict values;
- pass field/path state through dict/list recursion;
- preserve exclusion-before-descent semantics;
- leave `_canonical_sort()`, public API names, algorithm identifiers, and final `canonical_json_bytes()` calls unchanged.

No changes are justified in source validation, semantic validation, schemas, RFC 8785 behavior, or digest algorithms.

## Review attack surface

Independent review should challenge:

- cycle-vs-depth precedence against F-009;
- path accounting for dict keys and list indexes;
- whether excluded audit-only subtrees are accidentally traversed/validated;
- off-by-one depth 128/129 behavior;
- shared `active` state cleanup on exceptions;
- canonical sort behavior for accepted set-like children;
- accidental algorithm/digest-vector changes;
- whether both mapping-v2 and projection-v1 public surfaces are covered.

## Conclusion

F-022 is implementable as a narrow post-I-004 regression fix. The defect is not RFC 8785 and not the F-009 guard itself; it is the new semantic projection helper running recursively **before** that guard. Guard only the semantically included traversal, reuse the established depth/category policy, preserve audit-only exclusion, and keep all accepted digest bytes unchanged.