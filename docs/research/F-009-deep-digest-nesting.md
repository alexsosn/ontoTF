# F-009 research: fail closed on excessively deep digest/canonicalization inputs

**Issue:** #69  
**Recorded:** 2026-09-07  
**Baseline:** `main` `3838add7e26c869c3ff4dcc67bc4965cd96844ce`  
**Type:** I-002 stability / diagnostics hardening

## Question

How should ontoTF's I-002 canonicalization/digest API handle an acyclic programmatic JSON value whose nesting is deep enough to exhaust Python recursion, without changing RFC 8785 byte semantics for ordinary accepted values?

## Existing ontoTF contract

Accepted I-002 deliberately wraps the third-party canonicalizer behind a ontoTF-owned error surface. `docs/plans/I-002-canonicalization-digest-plan.md` requires:

- a strict recursive guard over the ontoTF JSON value model before `rfc8785.dumps`;
- stable `DigestError` / `DigestProblem(category, message, path)` diagnostics;
- callers not depending on third-party exception classes;
- rejection of cyclic containers as `non_json_value`;
- unchanged RFC 8785 canonical bytes and versioned digest algorithms for accepted values.

Current `src/ontotf/digests.py::_validate_json()` is recursive and already tracks active container identities for cycle detection, but has no nesting counter and no `RecursionError` translation. Therefore sufficiently deep *acyclic* lists/dicts can escape the public `DigestError` contract as a raw interpreter exception.

This is distinct from F-006 #32: F-006 owns parsing/plain-JSON source loading in `source_validation.py`; F-009 owns programmatic values passed directly into I-002 canonicalization and semantic digest projections.

## External evidence

### RFC 8785 requires recursive traversal but defines no implementation stack limit

RFC 8785 §3.2.3 requires object properties to be sorted recursively and arrays to be scanned recursively for contained objects. It defines canonical byte semantics and I-JSON input constraints, but it does not prescribe a Python recursion limit or a maximum container depth.

Authoritative source: <https://www.rfc-editor.org/rfc/rfc8785.html>

Consequence: a Python-specific recursion ceiling is an implementation concern that ontoTF must make deterministic if it is part of the public acceptance/error contract.

### Python recursion depth is interpreter/platform policy, not a stable application contract

Python documents `sys.setrecursionlimit()` as protection against overflowing the C stack and states that the highest safe limit is platform-dependent. Exceeding the interpreter limit raises `RecursionError`.

Authoritative source: <https://docs.python.org/3/library/sys.html#sys.setrecursionlimit>

Consequence: ontoTF must not define accepted digest input depth as `sys.getrecursionlimit() - N` or expose raw `RecursionError`; that would make the same logical input depend on interpreter/platform settings.

### The pinned RFC 8785 implementation is recursive too

`trailofbits/rfc8785.py` recursively calls `dump()` for list/tuple elements and dict values. Its documented public failures are `CanonicalizationError` subclasses, but the implementation has no independent depth guard around those recursive calls.

Upstream source: <https://github.com/trailofbits/rfc8785.py/blob/main/src/rfc8785/_impl.py>

Consequence: guarding only ontoTF's own validator is necessary but should be paired with a defensive translation boundary around the dependency call. A ontoTF-owned maximum comfortably below normal interpreter limits prevents ordinary accepted inputs from reaching dependency recursion exhaustion.

## Threshold decision

Use the same container-depth ceiling already chosen by F-006:

```python
MAX_JSON_NESTING = 128
```

Counting rule:

- scalar root: depth 0;
- root list/dict: depth 1;
- every nested list/dict increments by one;
- depth 128 is accepted;
- depth 129 is rejected.

Reasons:

1. **End-to-end consistency.** F-006 already defines source-loading depth 128. A source accepted at depth 128 must remain digestible later; using the same ceiling avoids a source/digest mismatch.
2. **Interpreter independence.** 128 is far below ordinary CPython recursion ceilings used by supported 3.10/3.12 CI and does not depend on `sys.getrecursionlimit()`.
3. **No RFC byte change below the boundary.** RFC 8785 serialization of every previously accepted value at depth <=128 remains byte-for-byte identical.
4. **No arbitrary permissiveness race.** Allowing values up to "whatever this interpreter can recurse through" would retain nondeterministic failure behavior.

The constant may remain module-public only if tests/documentation need a shared named contract. F-006 already exposes `MAX_SOURCE_NESTING`; naming the I-002 boundary separately avoids an accidental import dependency between source-validation and digest modules while keeping both values intentionally equal.

## Error category and path

Depth overflow should be:

```text
DigestError
category = non_json_value
message = JSON nesting exceeds maximum depth 128
path = path of the first container whose depth would be 129
```

Rationale:

- the value is generic JSON, but it is outside the accepted **ontoTF JSON model** after adding the deterministic depth constraint;
- `projection_error` is reserved for local projection/source-object shape failures and would be misleading for direct `canonical_json_bytes(value)`;
- adding a new stable category is unnecessary surface expansion when `non_json_value` already means ontoTF JSON-domain violation.

## Cycle-vs-depth precedence

Existing cycle semantics are already accepted and must not be accidentally reclassified.

For a list/dict container:

1. check whether its identity is already active;
2. if yes, fail `non_json_value: recursive ...` at that path;
3. otherwise calculate this container's depth and reject if it exceeds 128;
4. recurse into children with the updated depth.

This preserves the strongest local diagnosis when the same container is revisited, even if that revisit also happens beyond the depth boundary. Acyclic boundary+1 values receive the new stable depth message.

## Defensive dependency boundary

`canonical_json_bytes()` should still catch a `RecursionError` raised by `rfc8785.dumps()` after ontoTF validation and translate it to `DigestError(non_json_value)` rather than leaking the interpreter exception.

This catch is defensive, not the primary policy mechanism. Under the 128-depth contract it should not normally fire on supported Python versions. Do not raise the interpreter recursion limit.

## Digest identity compatibility

No existing digest algorithm identifier needs to change if implementation obeys both rules:

- every accepted value at depth <=128 produces exactly the same canonical bytes as before;
- values deeper than 128 become explicitly outside the accepted ontoTF JSON input domain rather than receiving a different digest.

This changes the fail-closed acceptance boundary, not the projection/serialization bytes associated with any still-accepted input.

Fixed existing RFC vectors, source digests, evidence digests, mapping semantic digests and profile semantic digests must remain unchanged.

## Test strategy

RED should be deterministic and not rely on hitting the host recursion limit. Tests should require the planned public limit/behavior before production implements it:

- list depth 128 accepted and canonical bytes equal a controlled independently generated expected nesting shape;
- list depth 129 raises `DigestError(non_json_value)` with stable path/message;
- dict depth 128 accepted; dict depth 129 rejected;
- a recursive container still reports the existing recursive-container diagnosis;
- ordinary safe integer/float/unicode and source-bundle controls remain unchanged;
- at least one semantic digest projection containing reviewed content nested at the boundary remains stable, if adding such a fixture does not freeze unrelated semantic shape.

Because current main has no maximum constant/guard, focused tests that import/require the new boundary should fail RED before production edits.

## Implementation recommendation

Minimal change in `src/ontotf/digests.py`:

1. add `MAX_JSON_NESTING = 128`;
2. add `depth: int = 0` to `_validate_json()`;
3. for exact list/dict, preserve cycle check first, then compute `container_depth = depth + 1` and fail if `> MAX_JSON_NESTING`;
4. pass `depth=container_depth` to children;
5. catch `RecursionError` around `rfc8785.dumps()` and translate to the same ontoTF-owned category without changing ordinary canonicalization handling.

No iterative serializer, parser change, schema change, recursion-limit mutation, semantic projection redesign, or algorithm-version bump is justified by the evidence.

## Review attack surface

Independent review should challenge:

- off-by-one container counting;
- whether depth 128 source values remain digestible;
- cycle-vs-depth precedence;
- whether a hidden dependency/raw `RecursionError` path remains;
- whether `non_json_value` is the least disruptive category;
- whether any existing canonical bytes/digest vectors changed below the boundary;
- whether tests accidentally encode `sys.getrecursionlimit()` instead of the ontoTF contract.

## Conclusion

F-009 should add a deterministic 128-container ontoTF JSON nesting boundary to I-002 canonicalization, preserve cycle diagnostics, and translate any downstream dependency recursion failure into `DigestError`. This keeps canonical byte semantics unchanged for accepted values while removing interpreter-dependent raw exceptions from the public API.
