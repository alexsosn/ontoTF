# I-010 plan: finite value-set native execution

**Issue:** #149  
**Research:** `docs/research/I-010-value-set-predicate.md`  
**Recorded:** 2026-09-11

## Scope

Implement one exact primitive over one loaded TF feature:

```text
feature value ∈ finite reviewed set
```

Canonical source shape:

```json
{
  "component_id": "bhsa-tf",
  "node_type": "word",
  "feature": "sp",
  "values": ["nmpr", "subs"],
  "execution_shape": "value-set-predicate"
}
```

This ticket does not add arbitrary boolean composition, multiple native bindings per projection, approximate execution, query-string generation, network access, corpus loading, or a new runtime dependency type.

## Contract changes

### 1. `mapping.schema.json`

Add optional `values` to `nativeBinding`:

- array, `minItems: 1`, `uniqueItems: true`;
- items use the existing `jsonScalar` definition.

Extend `execution_shape` enum with `value-set-predicate`.

Add shape constraints so:

- `value-predicate` requires `component_id`, `node_type`, `feature`, `value`, and forbids `values`, `closed_values`, edge/path/interpretation fields;
- `value-set-predicate` requires `component_id`, `node_type`, `feature`, `values`, and forbids `value`, `closed_values`, edge/path/interpretation fields.

Existing non-I-010 binding shapes must remain accepted exactly as before.

### 2. `NativeBindingIR`

Add:

```python
values: tuple[str | int | float | bool | None, ...] | None
```

Compilation rules:

- source `values` list -> tuple sorted by `canonical_json_bytes`;
- source duplicates are already schema-invalid; compiler still fails closed if malformed prevalidated objects are injected;
- scalar `value` behavior remains unchanged;
- `closed_values` retains its existing complete-domain meaning and ordering behavior.

Native binding reconstruction/fingerprinting includes canonical `values` when present. Thus authored `values` order must not change the native binding identity, plan fingerprint, or resolution fingerprint.

### 3. Semantic resolver

No new resolution cardinality logic.

The exact resolver accepts `NativeBindingIR` carrying `values` and reconstructs it canonically for identity verification. One matching projection still yields one `ExactNativePlan`.

Malformed compiled IR fails as `invalid_compiled_ir`; there is no fallback to scalar execution.

### 4. Runtime prerequisites

No new dependency kind.

Profiles using a set binding declare one existing `native-value-present` dependency for each selected value. The already-existing I-007 evaluator must remain unchanged unless tests expose a concrete incompatibility.

The resolver still requires the entire declared dependency closure to pass before authorizing exact execution.

### 5. Loaded executor

Generalize the current I-008 value-predicate binding validator into a narrow dispatch for exactly two supported shapes:

- scalar `value-predicate`;
- finite `value-set-predicate`.

For set execution:

1. load feature selector and `otype` lookup using the existing helper;
2. iterate canonical `binding.values`;
3. call the feature selector once per value;
4. normalize each selector result with the existing strict node-ID logic;
5. union node IDs;
6. node-type filter every unique candidate through `F.otype.v`;
7. return ascending numeric node IDs.

Cross-value overlap is deduplicated. Duplicate node IDs inside a *single selector result* keep the existing fail-closed behavior because malformed loaded APIs should not be silently normalized.

Scalar execution output/order and errors must remain unchanged.

## TDD gates

### RED commit

Add focused tests before implementation. The RED head must fail for missing I-010 support, not from malformed fixtures.

Required tests:

1. schema accepts a valid `value-set-predicate` binding;
2. schema rejects empty/duplicate `values`;
3. schema rejects `value + values` and `closed_values + values`;
4. semantic IR canonicalizes authored order (`["subs","nmpr"]` vs `["nmpr","subs"]`) to identical IR/native identity;
5. resolver emits one exact plan with canonical finite values;
6. executor returns deterministic union with cross-value overlap deduplicated and node-type filtering preserved;
7. failed/missing per-value prerequisite prevents exact resolution/execution;
8. malformed selector results retain existing fail-closed behavior;
9. existing scalar execution tests remain green after implementation;
10. no public generic OR/composition API is introduced.

### GREEN commit

Implement only enough production code to satisfy the RED contract.

Likely touched files:

- `src/ontotf/schemas/mapping.schema.json`
- `src/ontotf/semantic_ir.py`
- `src/ontotf/semantic_resolver.py`
- `src/ontotf/semantic_execution.py`
- focused tests for schema/IR/resolver/execution

Do not edit `runtime_prerequisites.py` or `runtime_tf_observation.py` unless a failing test demonstrates a real need; such a change requires a plan amendment explaining why existing `native-value-present` is insufficient.

## Test gate

Before review:

- focused I-010 tests pass;
- complete repository suite passes;
- existing I-006/I-007/I-008 workflows remain green where triggered;
- exact-head diff contains no fixture-only production shortcuts.

## Independent adversarial review

Reviewer must challenge at least:

- whether source-order invariance is actually reflected in binding/plan fingerprints;
- JSON scalar corner cases (`null`, bool vs integer, numeric canonicalization);
- whether shape validation leaves a path for mixed `value`/`values` semantics;
- whether runtime authorization checks every selected value through declared dependencies;
- duplicate result semantics vs malformed-selector duplicate behavior;
- node-type filtering after union;
- accidental expansion into R-018 composition semantics;
- scalar regression and serialized-plan trust boundary.

Any blocker is fixed and re-reviewed at the new exact head before merge.

## Acceptance outcome

After merge, I-009 may author:

```text
BHSA           word.sp in {subs,nmpr} -> olia:Noun exact
ExtraBiblical  word.sp in {subs,nmpr} -> olia:Noun exact
Syriac         word.sp = subs          -> olia:Noun exact
```

provided the production mapping/evidence reviews independently approve those exact corpus mappings. I-010 itself does not approve corpus semantics.