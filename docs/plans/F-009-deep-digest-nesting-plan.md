# F-009 plan: deterministic digest/canonicalization nesting boundary

**Issue:** #69  
**Research:** `docs/research/F-009-deep-digest-nesting.md` at `7919b1d314205f7db3ef3da6bd5be5603b1c786c`  
**Baseline:** `main` `3838add7e26c869c3ff4dcc67bc4965cd96844ce`

## 1. Scope

Harden I-002 programmatic canonicalization/digest inputs against interpreter-dependent recursion failure without changing RFC 8785 bytes for accepted values.

Production scope is limited to `src/ontotf/digests.py` and public re-export only if the new limit is part of the supported module API. Tests live under `tests/f009/` plus existing I-002 controls.

No schema, semantic projection shape, source parser, ontology, compatibility or runtime query behavior changes.

## 2. Public contract

Add:

```python
MAX_JSON_NESTING = 128
```

Container depth counts uniformly:

- scalar root = 0;
- root exact list/dict = 1;
- every nested exact list/dict increments by 1;
- depth `128` is accepted;
- depth `129` fails.

The failure is:

```text
DigestError
problem.category = "non_json_value"
problem.message = "JSON nesting exceeds maximum depth 128"
problem.path = path of the first container at depth 129
```

Do not derive this limit from `sys.getrecursionlimit()` and do not mutate the interpreter recursion limit.

## 3. Diagnostic precedence

For exact list/dict values, preserve current cycle detection as the stronger local diagnostic:

1. if container identity is already active, raise the existing recursive-container `non_json_value` error;
2. otherwise compute `container_depth = depth + 1`;
3. reject if `container_depth > MAX_JSON_NESTING`;
4. recurse into children with `depth=container_depth`.

All existing scalar-domain checks retain their current categories/paths.

## 4. RED sequence

Before production edits:

1. add `tests/f009/__init__.py`;
2. add `tests/f009/test_deep_digest_nesting.py` requiring the not-yet-existing `MAX_JSON_NESTING` contract and boundary behavior;
3. add a focused `.github/workflows/f009-deep-digest-nesting.yml` gate.

The RED test suite must cover:

- list depth 128 accepted;
- list depth 129 rejected with stable category/message/path;
- dict depth 128 accepted;
- dict depth 129 rejected with stable category/message/path;
- a recursive list/dict retains recursive-container diagnosis;
- representative ordinary RFC vector remains unchanged;
- safe-integer/non-finite/unicode controls retain categories;
- source-bundle duplicate-path control remains unchanged.

RED is valid if tests fail because the new constant/depth contract is absent. It must not depend on constructing a structure deep enough to hit the host interpreter recursion limit.

## 5. GREEN implementation

Minimal production edit in `_validate_json()`:

```text
add depth=0 keyword argument
for exact list/dict:
    cycle check first
    container_depth = depth + 1
    if container_depth > MAX_JSON_NESTING:
        _fail(non_json_value, stable message, current path)
    recurse with depth=container_depth
```

In `canonical_json_bytes()`:

- keep `_validate_json(value)` before dependency serialization;
- keep existing RFC 8785 exception translation;
- additionally catch downstream `RecursionError` and translate it to `DigestError(non_json_value)` with a stable dependency-recursion message rather than leaking the interpreter exception.

The deterministic 128 guard is authoritative; the downstream catch is defensive and should not normally fire for accepted values.

## 6. Byte/digest compatibility gate

No `*-v1` algorithm constant changes.

Required invariant:

> For every value accepted both before and after F-009, `canonical_json_bytes()` and every digest derived from it produce byte-for-byte / digest-for-digest identical results.

Existing I-002 fixed vectors are mandatory controls. Do not update expected digests to make tests pass.

## 7. CI gate

Focused workflow triggers on:

- `src/ontotf/digests.py`;
- `src/ontotf/__init__.py` if touched;
- `tests/f009/**`;
- `tests/i002/**`;
- F-009 research/plan;
- workflow itself.

Matrix Python 3.10 and 3.12.

Each job:

1. checks out exact source head (`github.event.pull_request.head.sha || github.sha`);
2. installs editable package;
3. installs `build` so repository packaging tests cannot silently skip when full suite is run;
4. runs `tests/f009`;
5. runs `tests/i002`;
6. runs the full repository suite **only while F-007 #35 has not yet centralized full-suite ownership**.

Integration rule with F-007:

- if F-007 merges before F-009 finalization, rebase and remove any ticket-local generic full-suite step, retaining only F-009 + I-002 focused gates; rely on authoritative `full-suite.yml` for repository-wide coverage;
- if F-009 reaches final review first, its temporary full-suite step may remain only until F-007 integration and must not bypass #35's exactly-one-owner contract.

## 8. Test helpers

Build nested structures iteratively in tests to avoid test-construction recursion.

Suggested helpers:

```python
def nested_list(depth):
    value = 0
    for _ in range(depth):
        value = [value]
    return value


def nested_dict(depth):
    value = 0
    for _ in range(depth):
        value = {"x": value}
    return value
```

Expected overflow path is deterministic:

- list depth 129: 128 integer-zero indices before the rejected container path;
- dict depth 129: 128 `"x"` path elements before the rejected container path.

Tests should compare path length/content without generating recursive expected values.

## 9. Non-goals

F-009 does not:

- change F-006 source parsing/normalization;
- change RFC 8785 ordering or number serialization;
- normalize/truncate deep data;
- use an iterative replacement canonicalizer;
- change schema versions or semantic projection fields;
- raise Python recursion limits;
- define P-003 semantic behavior;
- change digest vectors for accepted values.

## 10. Review gate

After exact-head GREEN, require a fresh logically-independent adversarial review. The authoring/dev context does not count.

Reviewer must specifically challenge:

- 128/129 off-by-one semantics;
- source-loader depth 128 remaining digestible;
- cycle-before-depth diagnostic precedence;
- path correctness at overflow;
- downstream raw `RecursionError` leakage;
- accidental `*-v1` digest changes;
- hidden dependence on interpreter recursion limits;
- F-007 integration / duplicate full-suite ownership if #35 has merged or is concurrently landing.

Any material head change after review restarts exact-head CI and review.
