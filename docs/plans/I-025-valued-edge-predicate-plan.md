# I-025 plan — exact valued-edge predicates and dependency-contract v2

**Issue:** #253  
**Research:** `docs/research/I-025-valued-edge-predicate-domain-authority.md`  
**Baseline:** merged I-025 research `7b55d0879e7f00f2db3416b80707b6bf687f945b`

## Scope

Productionize the smallest reviewed value-sensitive extension to I-024
edge-path execution:

- an optional set-like `match_values` predicate on a valued path step;
- exact native equality/membership only;
- initial matching only for `value_role=semantic-qualifier`;
- a new reviewed `edge-value-domain` dependency in dependency-contract v2;
- loaded-runtime verification of the complete reviewed edge-value domain;
- identical filtering across exact, approximate, authority, identity,
  identifier, and conjunction execution through the shared I-024 path executor.

The implementation must preserve every I-023/I-024 unfiltered path and all
dependency-contract v1 profiles unchanged.

## Non-goals

Do not add:

- fuzzy, normalized, range, regex, ordering, or substring edge-value matching;
- matching on `source-evidence` or `technical` values;
- a `None`/missing-value predicate;
- ontology meaning inferred from an edge name or literal;
- a second path executor or a second path-evidence contract;
- corpus autoload, network access, source-format access, `oslots` inference,
  or a Text-Fabric runtime dependency;
- production mapping promotion merely to exercise the new capability.

## 1. Source step contract

Extend `$defs.edgeStep` in
`src/tfont/schemas/mapping.schema.json` with:

```json
"match_values": {
  "type": "array",
  "minItems": 1,
  "uniqueItems": true
}
```

Conditional rules:

1. `valued=false`
   - forbids `value_type`, `value_role`, and `match_values`;
   - remains source-compatible with I-023.
2. `valued=true` without `match_values`
   - remains exactly the I-024 contract;
   - permits all existing value roles.
3. `match_values` present
   - requires `valued=true`;
   - requires `value_role=semantic-qualifier`;
   - if `value_type=str`, every member is a JSON string;
   - if `value_type=int`, every member is a JSON integer in
     `[-9007199254740991, 9007199254740991]`;
   - `null` and booleans are forbidden.

A singleton means exact equality. Multiple values mean exact OR membership.
Order is semantically irrelevant.

Keep mapping schema version 2.

## 2. Dependency-contract v2

Extend `src/tfont/schemas/profile.schema.json`.

The profile schema version remains 2, but
`dependency_contract_version` becomes `1 | 2`.

Add `edge-value-domain` only to dependency contract v2. Contract v1 must
continue to accept exactly the pre-I-025 dependency language.

Recommended assertion:

```json
{
  "edge": "witness_resolution",
  "source_node_type": "line",
  "target_node_type": "fragment",
  "value_type": "str",
  "value_role": "semantic-qualifier",
  "values": ["ambiguous", "unique"],
  "domain_semantics": "closed-reviewed"
}
```

Exact v2 assertion rules:

- exact object; no undeclared fields;
- non-empty edge/source/target strings;
- `value_type=str|int`;
- `value_role` is exactly `semantic-qualifier`;
- `domain_semantics` is exactly `closed-reviewed`;
- `values` is non-empty, unique, set-like;
- values obey the declared type and safe-JCS integer bound;
- dependency evidence is mandatory and non-empty.

The assertion is expressed in **native edge orientation** and carries no
traversal direction.

Top-level schema version gating must make an `edge-value-domain` record
invalid when `dependency_contract_version=1`, even if the generic dependency
definition knows the v2 kind.

Existing v1 source artifacts must remain byte-for-byte valid.

## 3. Source dependency authority

Extend semantic validation of edge-path bindings.

For every binding occurrence already checked by
`_validate_edge_path_dependency_authority()`:

- mapping native binding;
- projection native execution binding;
- executable external-reference native binding;

walk the ordered steps while tracking the current node domain:

```text
current_type = binding.node_type
for step:
    result_type = step.result_node_type
    if outgoing:
        native_source = current_type
        native_target = result_type
    else:
        native_source = result_type
        native_target = current_type
    current_type = result_type
```

For a step with `match_values`:

- the active profile must use dependency contract v2;
- one dependency listed by that mapping must have kind
  `edge-value-domain`;
- component, edge, native source/target types, `value_type`, and
  `value_role` must match exactly;
- its domain must be `closed-reviewed`;
- its single reviewed `values` set must contain **all** requested
  `match_values`.

Do not union several partial dependencies to authorize one predicate.

Existing node-type and ordered `path-present` authority remains mandatory and
unchanged. `edge-value-domain` is additional value authority, not a
replacement for path mechanics authority.

## 4. Dependency version validation

Change source and runtime validation from "exactly v1" to explicit support for
`{1, 2}`.

Fail closed on every other integer/version/type.

Runtime reconstruction must independently enforce version-kind coherence:

- v1: old kinds only;
- v2: old kinds plus `edge-value-domain`.

A forged compiled v1 release containing an edge-value-domain must fail even if
source-schema validation was bypassed.

The existing profile-release fingerprint algorithm remains unchanged because it
already binds:

- `dependency_contract_version`;
- canonical dependency records.

A v2 release therefore receives a different release fingerprint naturally.

## 5. Semantic IR and canonical identity

Append to `EdgeStepIR`:

```python
match_values: tuple[str | int, ...] | None = None
```

This preserves the I-024 positional constructor prefix.

Compilation:

- no authored `match_values` -> `None`;
- authored values -> tuple sorted by `canonical_json_bytes`;
- no coercion or normalization of literals.

Update both semantic identity paths:

1. add `match_values` to
   `semantic_digest_v2._SET_LIKE_LIST_FIELDS`;
2. make `native_binding_identity()` sort nested
   `steps[*].match_values` while preserving ordered step sequence.

Do not change mapping semantic, projection semantic, or native-binding identity
algorithm tokens. The new field is currently forbidden by the closed schema,
so no previously valid binding changes identity.

Dependency record canonicalization already treats a field named `values` as
set-like; preserve that behavior for the new v2 assertion.

## 6. Resolver defensive reconstruction

Extend `_native_binding_projection()` and execution-side
`_validate_edge_path_binding()`.

For every `EdgeStepIR`:

- `match_values` is either exact `None` or exact non-empty `tuple`;
- duplicate values by canonical JSON identity fail;
- if present, `valued is True`;
- if present, `value_role == "semantic-qualifier"`;
- every value has the exact declared Python type;
- bool is rejected for int;
- integer values are safe-JCS;
- `None` is rejected;
- no subclasses/coercions are accepted.

Projection back to canonical plan identity includes
`"match_values": [...] ` only when the tuple is present.

No resolver mode or plan fingerprint algorithm changes.

## 7. Loaded edge-value observation

Extend the `RuntimeObservation` protocol with a narrow method:

```python
edge_values(
    component_id: str,
    edge: str,
    source_node_type: str,
    target_node_type: str,
) -> tuple[str, str | None, tuple[str | int, ...], int]
```

Interpretation:

```text
(state, declared_value_type, present_values, missing_count)
```

where state is `complete | absent | unknown`.

Implement it in `LoadedTFObservation` using only already-loaded APIs.

Required mechanics:

1. resolve the already-present component;
2. require the edge in loaded `Eall()`;
3. require loaded `E.<edge>`;
4. require exact `doValues=True`;
5. require exact dict metadata with `valueType=str|int`;
6. require callable/public `items()`;
7. iterate the complete loaded edge mapping;
8. validate source/target node IDs as positive exact ints;
9. obtain native node types from loaded `F.otype.v`;
10. validate **all native edge values** against the feature's global
    `valueType` before using source/target domains to collect the reviewed
    domain;
11. for int, count `None` as missing rather than a value;
12. for str, `None` is malformed/unknown;
13. require present integers inside the safe-JCS range;
14. collect unique present values only when both native source and target
    node types match the requested domain;
15. return values in canonical JCS order.

Validating values globally is intentional: TF `valueType` is feature-global
and the same reviewed edge-domain dependency can authorize incoming or outgoing
traversal. A malformed value elsewhere in that loaded valued feature indicates
a broken loaded feature rather than a trustworthy closed domain.

### Observation cache

Complete observation is O(edge size). Memoize the immutable result per
`LoadedTFObservation` using the key:

```text
(component_id, edge, source_node_type, target_node_type)
```

Repeated dependencies in one runtime evaluation must reuse the scan.

The cache is local to the observation object. It must not persist across
different loaded contexts or act as authority independent of current loaded
data.

Pinned TF `freqList(from,to)` remains corroborating API evidence only; do not
use it as the normative validator because aggregation is weaker for raw-shape
and missing-value checks.

## 8. Runtime prerequisite evaluation

Add evaluator rule token:

```text
tfont-runtime-edge-value-domain-v1
```

Validate the v2 assertion defensively from the canonical dependency record.

Evaluation:

- component missing -> known fail;
- edge unloaded/unreadable/malformed -> unknown or known fail according to the
  existing observation-state convention;
- complete observation with declared value type different from reviewed
  `value_type` -> fail;
- complete observation with any present observed value outside the
  closed-reviewed set -> fail;
- otherwise -> pass;
- missing integer values do not participate in the domain and do not fail the
  domain merely by being missing.

A reviewed allowed value does **not** need to be observed in the current
snapshot. Querying an authorized but absent value is a valid query that may
return an empty result.

Observed evidence digest must bind at least:

- kind/component;
- edge;
- native source/target types;
- declared value type;
- complete present-value set;
- missing count;
- closed-reviewed domain semantics.

Keep runtime report and prerequisite fingerprint contract tokens unchanged;
the generic result shape already binds evaluator rule + evidence digest.

## 9. Shared execution filter

Do not create a filtered-edge executor.

Extend the shared I-024 `_execute_edge_path()`.

For each valued raw row, preserve the current order:

1. exact pair-shape validation;
2. exact positive neighbor-node validation;
3. native value type/presence validation;
4. loaded `otype` lookup and `result_node_type` filtering;
5. if `match_values` exists, exact membership comparison;
6. for a matching accepted neighbor, safe-JCS evidence-node validation;
7. append accepted evidence observation and stable-first frontier node.

Consequences:

- malformed values on off-domain neighbors still fail before domain filtering;
- well-formed off-domain neighbors are omitted;
- well-formed in-domain non-matching values are omitted;
- an oversized node that is off-domain or non-matching is not rejected merely
  for evidence JCS bounds because it does not enter evidence;
- duplicate raw neighbor rows retain the I-024 fail-closed behavior before
  filtering;
- int `None` is valid absence but cannot match;
- empty string may match when explicitly reviewed.

If a predicate empties the frontier, return the ordinary valid empty result and
continue I-024 empty trailing layers.

## 10. Evidence and public result compatibility

Do not change `tfont-edge-path-evidence-v1`.

For filtered steps, record only accepted matching native observations.
Each observation already includes the exact value that justified the accepted
edge.

Plan/evidence identity remains sufficient because `match_values` participates
in:

- native binding identity;
- mapping/projection semantic identity;
- resolver plan fingerprint;
- edge-path evidence's bound plan fingerprint.

No outer execution result dataclass or contract token changes.

Pure I-023/I-024 unfiltered behavior remains unchanged.

## 11. Surface propagation

Because all current surfaces route through the shared exact plan executor, the
production change must be implemented only once and verified on:

- exact semantic;
- approximate semantic;
- exact authority;
- approximate authority;
- identity;
- identifier;
- exact conjunction;
- approximate conjunction.

Approximate ontology mapping never approximates a native edge literal.
`match_values` comparison remains exact; mapping losses remain separately
reported.

Conjunction intersects only filtered final node sets and retains each
constituent's existing plan-aligned evidence.

## 12. No production profile migration in this ticket

Do not change shipped semantic profiles/mappings merely to exercise the new
feature.

I-025 productionizes the capability and its authority contract. A later
mapping/profile ticket may opt into dependency contract v2 when real reviewed
mappings need `match_values`.

Therefore:

- all currently shipped v1 profiles must remain valid;
- their release fingerprints must remain unchanged;
- their runtime reports and query results must remain unchanged.

## 13. Expected production files

Minimal expected changes:

- `src/tfont/schemas/mapping.schema.json`;
- `src/tfont/schemas/profile.schema.json`;
- `src/tfont/semantic_digest_v2.py`;
- `src/tfont/semantic_ir.py`;
- `src/tfont/semantic_validation.py`;
- `src/tfont/semantic_resolver.py`;
- `src/tfont/runtime_prerequisites.py`;
- `src/tfont/runtime_tf_observation.py`;
- `src/tfont/semantic_execution.py`;
- focused `tests/i025/`;
- `.github/workflows/i025-valued-edge-predicate-execution.yml`;
- post-GREEN I-025 research reconciliation only if the current-state guard must
  advance from research-only assertions to implemented state.

Do not edit production mappings, ontology locks, or dependency evidence
artifacts without a separate reviewed reason.

## 14. Tests-only RED gate

Create a tests-only implementation branch after this plan is merged.

The RED head must change only focused tests/fixtures/workflow and must fail on
Python 3.10 and 3.12 for missing I-025 production support rather than
collection/setup errors.

Required RED coverage:

### Source / IR / identity

1. exact singleton string predicate is source-valid;
2. exact finite-set string predicate is source-valid;
3. integer predicate is source-valid only with int type and safe-JCS values;
4. unvalued step with `match_values` is invalid;
5. source-evidence/technical step with `match_values` is invalid;
6. empty/duplicate/null/bool/wrong-type/unsafe-int match sets are invalid;
7. no-predicate I-024 valued shape remains valid;
8. `EdgeStepIR` old positional prefix remains valid;
9. compiled match tuple is canonical-order insensitive;
10. match values change native binding identity and mapping/projection semantic
    identity;
11. forged IR tuple/list/subclass/duplicates/type mismatch fails resolver and
    execution reconstruction.

### Dependency v2

12. current v1 fixture remains valid unchanged;
13. v1 profile carrying `edge-value-domain` is invalid;
14. v2 accepts all old dependency kinds unchanged;
15. v2 edge domain requires exact fields and non-empty evidence;
16. edge domain is closed to `semantic-qualifier`;
17. value set obeys `value_type` and safe-JCS;
18. matching outgoing step uses current->result as native source->target;
19. matching incoming step reverses current/result to native source/target;
20. one dependency must cover the entire requested match set;
21. mismatched edge/component/node domain/type/role/domain semantics fails
    source authority;
22. forged compiled v1 release with edge domain fails runtime reconstruction.

### Loaded observation / prerequisite

23. complete string edge domain passes;
24. complete integer domain preserves present ints and counts `None`;
25. str `None`, bool-as-int, unsafe int, malformed item/data shape, bad
    `doValues`, bad metadata, unloaded edge, and bad otype observation fail
    closed;
26. unexpected present value fails closed-reviewed compatibility;
27. reviewed-but-absent allowed value still passes compatibility;
28. observation filters collected domain by native source+target type;
29. global malformed value still invalidates observation;
30. repeated identical edge-domain observations reuse one edge scan;
31. runtime report fingerprint changes when observed edge domain changes.

### Execution

32. outgoing singleton filter returns only matching target/evidence;
33. outgoing finite-set OR returns stable matching targets;
34. incoming filter preserves native source->target evidence orientation;
35. valid integer match works;
36. int `None` does not match;
37. explicitly reviewed empty string can match;
38. malformed off-domain value still fails before filtering;
39. well-formed off-domain value is ignored;
40. well-formed in-domain non-match is ignored without evidence-bound failure;
41. duplicate raw neighbors still fail before filtering;
42. fan-in keeps each matching accepted evidence pair while frontier de-dupes;
43. filter-to-empty produces valid empty result plus complete layered evidence;
44. mixed unvalued/valued filtered path remains reconstructible.

### Surface / compatibility

45. exact and approximate semantic surfaces carry the same exact native filter;
46. exact/approximate authority, identity, and identifier carry it;
47. exact/approximate conjunction use filtered nodes and aligned evidence;
48. all-unfiltered I-023/I-024 behavior remains unchanged;
49. existing v1 profile release fingerprints remain unchanged;
50. mapping schema remains v2, profile schema remains v2;
51. existing outer execution/evidence contract tokens remain unchanged;
52. isolated wheel still has no Text-Fabric runtime dependency/autoload.

## 15. GREEN and merge gates

After RED is demonstrated on both supported Python versions:

1. implement the minimal production changes above;
2. run focused I-025 CI on Python 3.10/3.12;
3. run I-023/I-024 regressions;
4. reproduce I-024 and I-025 research evidence where applicable;
5. run the full repository suite on Python 3.10/3.12;
6. verify isolated wheel/runtime dependency boundaries;
7. perform a fresh logically-independent adversarial review on the exact final
   SHA, grounded in production diff, tests, pinned TF source, TLHdig controls,
   and BHSA negative controls;
8. merge only with an expected-head guard and only if no blocker remains.

Any change that enables source-evidence/technical matching, matching missing
values, fuzzy literal semantics, or production-profile migration is outside
this reviewed plan and requires a new plan/review gate.
