# I-024 plan — lossless valued Text-Fabric edge-path execution

**Issue:** #249  
**Research:** `docs/research/I-024-valued-edge-execution-reconciliation.md`  
**Baseline:** merged I-023 `79ca3bb7d196155dbb048af96a91645d6f8695b0` plus reviewed I-024 research `830a37d53e6bb3e8698f4987ec8e35b6788d6a7b`

## Scope

Implement lossless execution for typed Text-Fabric `edge-path` steps with `valued=true` while preserving the reviewed I-023 semantics for unvalued paths.

The production slice must:

- accept valued steps only when their native `value_type` and reviewed `value_role` are explicit;
- preserve every accepted native edge value and its native source/target orientation;
- keep endpoint filtering tied to reviewed `result_node_type`;
- emit deterministic, content-addressed path evidence bound to the fresh resolver plan;
- propagate that evidence through exact, approximate, authority, identity, identifier and conjunction execution;
- retain current resolver authorization, mapping-v2, dependency-contract-v1 and no-autoload boundaries.

I-024 does **not** add edge-value predicates. I-025 #253 owns value-sensitive selection/domain authority.

## Corpus-native semantics retained

The implementation treats `valued` as a TF storage/mechanics distinction, not as one semantic meaning.

The reviewed real controls remain:

- TLHdig `selected: word -> analysis`: stored selector token is `source-evidence`;
- TLHdig `witness_resolution: line -> fragment`: `unique|ambiguous` is a `semantic-qualifier`;
- TLHdig `joined: fragment -> fragment`: `direct|indirect` is a `semantic-qualifier`, with orientation preserving apparatus order rather than physical direction;
- BHSA `omap@...`: integer correspondence information is `technical`, not ontology authority.

No runtime behavior may infer ontology meaning from the edge name, literal value, value role, or value type.

## Source schema contract

Extend `$defs.edgeStep` in `src/tfont/schemas/mapping.schema.json`.

The common fields remain required:

```json
{
  "edge": "witness_resolution",
  "direction": "outgoing",
  "result_node_type": "fragment",
  "valued": true
}
```

`valued` becomes a boolean discriminator.

For `valued=false`:

- `value_type` is forbidden;
- `value_role` is forbidden;
- existing I-023 four-field authored shapes remain byte-for-byte source-compatible.

For `valued=true`:

- require `value_type` with enum `str | int`;
- require `value_role` with enum `semantic-qualifier | source-evidence | technical`;
- continue to forbid all undeclared properties.

Keep mapping `schema_version: 2`. This is an additive execution-capability extension within the mapping-v2 architecture, following I-010 and I-023.

No new dependency assertion kind is added. Existing reviewed `node-type-present` and ordered `path-present` authority remains the source authorization for path mechanics.

## Semantic IR contract

Extend `EdgeStepIR` by appending defaulted fields:

```python
value_type: str | None = None
value_role: str | None = None
```

The existing positional constructor prefix `(edge, direction, result_node_type, valued)` must remain valid.

Compilation rules:

- unvalued authored steps compile to `value_type=None, value_role=None`;
- valued authored steps preserve the exact reviewed strings;
- no canonicalization/fuzzy spelling/aliasing is introduced;
- `native_binding_identity()` remains the existing JCS/SHA-256 algorithm and naturally includes the new nested authored fields;
- existing mapping/projection semantic digest algorithms remain unchanged and naturally include the new nested fields.

Resolver reconstruction must fail closed if compiled/fabricated step IR violates the same conditional contract, including subclasses/coercions:

- `edge`, `direction`, `result_node_type`, `value_type`, and `value_role` must be exact strings where required;
- `valued` must be exact `bool`;
- allowed directions remain exactly `outgoing|incoming`;
- unvalued steps require both optional value fields to be `None`;
- valued steps require the closed value-type and value-role tokens.

No resolver plan fingerprint algorithm changes. The new step fields already participate through native binding identity and the reviewed semantic digests.

## Evidence model

Add immutable public evidence records in `semantic_execution.py` and export them from `tfont.__init__`:

```python
@dataclass(frozen=True)
class EdgePathObservation:
    source_node: int
    target_node: int
    value_present: bool
    value: str | int | None

@dataclass(frozen=True)
class EdgePathEvidenceLayer:
    step_index: int
    observations: tuple[EdgePathObservation, ...]

@dataclass(frozen=True)
class EdgePathEvidence:
    evidence_contract: str
    plan_fingerprint: str
    native_execution_binding_identity: str
    start_nodes: tuple[int, ...]
    layers: tuple[EdgePathEvidenceLayer, ...]
    final_nodes: tuple[int, ...]
    evidence_fingerprint: str
```

Freeze:

- evidence contract: `tfont-edge-path-evidence-v1`;
- fingerprint algorithm: `tfont-edge-path-evidence-jcs-sha256-v1`.

Add a public deterministic helper `edge_path_evidence_fingerprint(evidence)` that recomputes the fingerprint from all evidence fields except `evidence_fingerprint`. This follows the existing public fingerprint-helper pattern and gives callers a direct verification primitive.

The canonical fingerprint projection includes:

- algorithm token;
- evidence contract;
- fresh `plan_fingerprint`;
- `native_execution_binding_identity`;
- ordered `start_nodes`;
- ordered layers with **zero-based** `step_index`;
- exactly one layer for every reviewed step, including an empty `observations=()` layer when the frontier was already empty;
- ordered observations with native `source_node`, native `target_node`, exact `value_present`, and `value`;
- ordered `final_nodes`.

The plan fingerprint is mandatory even though native binding identity is also present. This prevents replay across different corpus/profile/parent/prerequisite variants that happen to share a binding and local node IDs.

The helper accepts only exact evidence dataclass instances and exact nested tuples/records. Forged/malformed evidence fails closed rather than being normalized into another valid identity.

## Public execution-result compatibility

Append optional/defaulted evidence fields to existing corpus-level result dataclasses. Existing positional prefixes remain unchanged.

Single-plan families gain:

```python
edge_path_evidence: EdgePathEvidence | None = None
```

on:

- `ExactCorpusExecution`;
- `ApproximateCorpusExecution`;
- `ExactAuthorityCorpusExecution`;
- `ApproximateAuthorityCorpusExecution`;
- `IdentityCorpusExecution`;
- `IdentifierCorpusExecution`.

Conjunction families gain:

```python
constituent_edge_path_evidence: tuple[EdgePathEvidence | None, ...] = ()
```

on:

- `ExactConjunctionCorpusExecution`;
- `ApproximateConjunctionCorpusExecution`.

Compatibility rules:

- value predicates, value-set predicates, membership and pure-I-023 unvalued edge paths retain `edge_path_evidence=None`;
- an all-unvalued conjunction retains the legacy default `()`;
- if any conjunction constituent emits valued-path evidence, the tuple has exactly the same length/order as `plans`, with `None` placeholders for constituents without evidence;
- outer execution contract strings remain at their current v1 values; the new semantics are isolated in the nested versioned evidence contract.

No execution result changes its existing `nodes`, `plan(s)`, `runtime_report`, resolution, or ordering semantics.

## Internal execution result

Introduce one private immutable carrier used by every plan execution path:

```python
@dataclass(frozen=True)
class _NativePlanExecution:
    nodes: tuple[int, ...]
    edge_path_evidence: EdgePathEvidence | None = None
```

Refactor exact semantic, approximate semantic, conjunction, authority, identity and identifier call-sites to consume this carrier.

For non-edge-path shapes, wrap the existing node tuple with `edge_path_evidence=None`.

For edge paths, one shared executor produces both nodes and optional evidence. Do not create separate valued-edge traversal implementations for semantic/reference/conjunction surfaces.

## Edge-path binding validation

Generalize `_validate_edge_path_binding()` from I-023's unvalued-only rule to the reviewed conditional step contract.

Binding-level constraints remain unchanged:

- exact `NativeBindingIR`;
- non-empty exact-string `component_id` and start `node_type`;
- `execution_shape == "edge-path"`;
- non-empty exact tuple of `EdgeStepIR`;
- feature/value/closed_values/values/top-level edge/direction/interpretation fields remain absent.

Step validation is defensive and independent of source schema validity so forged IR cannot bypass the contract.

## Full-path loaded-API preflight

Preserve I-023 full-path preflight before traversing the start frontier.

For every reviewed step:

1. the edge name must be present in already-loaded `Eall()`;
2. requested `f` or `t` must exist and be callable;
3. `edge_api.doValues` must be exact `bool` and equal reviewed `step.valued`;
4. for `valued=true`, `edge_api.meta` must expose exact-string `valueType` equal to reviewed `step.value_type`;
5. no corpus loading, feature loading, network access, `oslots` traversal or alternative edge API is attempted.

A later malformed/missing/valuedness-drifted step must fail even if an earlier traversal frontier would be empty.

`value_role` is reviewed semantic provenance and is **not** inferred or rederived from TF metadata at runtime.

## Native value validation

For a valued step, every raw result member must be an exact Python two-tuple `(neighbor, value)`. Lists, mappings, tuple subclasses, non-pairs and other shapes fail closed.

Validation order for every raw pair:

1. validate pair shape exactly;
2. validate/normalize the neighbor node using the existing positive exact-int rules;
3. if the path contains any valued step, require every node ID that will enter evidence—including starts, sources, targets and finals—to fit TFont's JCS safe-integer domain `[-(2^53)+1, 2^53-1]`;
4. validate the value against the reviewed `value_type`;
5. only then perform loaded `otype` lookup and reviewed `result_node_type` filtering.

Value rules:

### `value_type=str`

- accept only exact Python `str`;
- preserve `""` with `value_present=True`;
- reject `None`, subclasses and every non-string value.

### `value_type=int`

- accept exact Python `int` inside TFont's safe-JCS domain;
- reject `bool`, int subclasses and oversized integers;
- accept `None` only for the pinned TF empty-integer valued-edge representation and record `value_present=False, value=None`.

Malformed value/type data on a well-formed off-domain neighbor still fails before domain filtering.

## Traversal and evidence construction

Keep the I-023 traversal-order policy: stable first discovery from canonical start order and native `f/t` order.

For each reviewed step create exactly one zero-based evidence layer when the path contains any valued step. If the current frontier is already empty, append that step's empty layer and continue without calling the traversal method; full-path API validation has already happened during preflight.

For each source in a non-empty current frontier:

- unvalued step: consume plain neighbor IDs exactly as I-023;
- valued step: consume validated `(neighbor, value)` pairs;
- duplicate raw neighbors/pairs within one source-step result fail closed rather than being silently normalized;
- query each well-formed neighbor's loaded `otype`;
- skip well-formed neighbors outside reviewed `result_node_type`;
- accepted neighbors enter the next frontier, de-duplicated by first discovery across fan-in;
- if the path contains at least one valued step, record every accepted edge observation for **all** layers, including intervening unvalued layers.

Observation orientation is always native edge orientation:

- outgoing: `source_node=current`, `target_node=neighbor`;
- incoming: `source_node=neighbor`, `target_node=current`.

For unvalued observations in a mixed path use `value_present=False, value=None`. For a valued integer edge whose native value is `None`, the same observation value fields are used; the corresponding reviewed step in the attached plan distinguishes the valued semantics.

Do not record off-domain neighbors in evidence.

The existing valid-empty post-traversal result remains valid. If any valued step exists, empty final nodes still produce mandatory evidence with exactly `len(binding.steps)` layers; steps after frontier exhaustion contribute empty observation tuples.

## Evidence fingerprint construction

Build evidence only after successful runtime validation/traversal.

Before constructing the final record:

- require exact non-empty `plan.plan_fingerprint`;
- require exact non-empty `plan.native_execution_binding_identity`;
- validate all evidence integers against the safe-JCS boundary explicitly so `DigestError` is not used as normal runtime control flow.

Construct a provisional evidence record with an empty fingerprint, compute `edge_path_evidence_fingerprint()`, then construct the final frozen record.

Deterministic error mapping:

- malformed loaded edge API, pair shape, value metadata or value type -> `loaded_api_unavailable`;
- invalid/duplicate/non-positive node IDs or evidence node integer-domain overflow -> `invalid_result_nodes`;
- forged/malformed evidence supplied directly to the public fingerprint helper -> `TypeError` for wrong top-level/nested record types and `DigestError` for values outside the existing JCS domain, matching current public digest/fingerprint helper conventions.

Runtime-generated evidence must never depend on catching a fingerprint error after traversal; all runtime values are checked first.

## Single-plan execution propagation

Refactor the repeated shape dispatch into one private plan executor that returns `_NativePlanExecution`.

Each corpus-level execution record receives:

- `nodes=result.nodes`;
- `edge_path_evidence=result.edge_path_evidence`.

This must be shared by exact semantic, approximate semantic and reference execution rather than duplicating evidence logic.

Approximate semantic execution preserves native edge values exactly. Mapping-level approximation losses remain separate; no native edge literal is approximately matched or altered.

## Conjunction propagation

The internal conjunction row becomes `(plan, _NativePlanExecution)`.

Intersection continues to use only each constituent's final `nodes`.

Evidence assembly per corpus:

- if every constituent evidence is `None`, store `()`;
- otherwise store one tuple aligned exactly with `plans`, retaining `None` placeholders.

No evidence is intersected, flattened or discarded merely because its constituent final node is later removed by conjunction intersection.

The existing shape-aware final node-domain validation remains unchanged.

## Resolver and dependency authority

No new resolver mode and no new dependency contract.

Existing I-023 semantic validation already proves:

- the start `node_type`;
- every reviewed `result_node_type`;
- the exact ordered `edge + direction` sequence through `path-present`.

I-024 does not reinterpret `path-present` as value-domain authority.

Resolver reconstruction changes only enough to recognize the extended `EdgeStepIR` and keep plan identity verification fail-closed.

I-025 #253 remains responsible for any future dependency that authorizes accepted edge values/value domains.

## Production files expected to change

Minimal expected set:

- `src/tfont/schemas/mapping.schema.json`;
- `src/tfont/semantic_ir.py`;
- `src/tfont/semantic_resolver.py`;
- `src/tfont/semantic_execution.py`;
- `src/tfont/__init__.py`;
- focused `tests/i024/` fixtures/tests;
- `.github/workflows/i024-valued-edge-execution.yml`;
- post-GREEN I-024 current-state/reconciliation evidence only if required to replace the research-only "not yet implemented" assertions.

Do not edit dependency-contract schemas or runtime prerequisite observation unless RED demonstrates a concrete incompatibility with this reviewed plan. Such a change requires a plan amendment before implementation.

## TDD RED gate

Create a tests-only RED head before any production modification. The focused workflow must run on Python 3.10 and 3.12 and fail for missing I-024 production support rather than syntax/import/fixture setup failures.

Required RED coverage:

### Source and IR

1. valid valued `str` and `int` edge steps are accepted;
2. unvalued steps still accept the old four-field shape;
3. valued steps missing `value_type` or `value_role` fail;
4. unvalued steps carrying either value field fail;
5. unknown value-type/value-role tokens fail;
6. authored valued fields participate in native binding identity and mapping/projection semantic digests;
7. `EdgeStepIR(edge, direction, result_node_type, valued)` positional compatibility remains;
8. forged IR using string/bool subclasses, unknown tokens or contradictory optional fields fails in resolver/runtime reconstruction.

### Real mechanics controls

9. TLHdig-shaped `selected`, `witness_resolution`, and `joined` plans cover all three reviewed value-role uses without assigning ontology meaning;
10. BHSA-shaped integer `omap` is accepted as a technical valued edge;
11. valued and unvalued steps may coexist in either order.

### Runtime preflight/value rules

12. full-path preflight catches a bad later step even after an earlier empty frontier;
13. `doValues` mismatch in either direction fails;
14. valued metadata `valueType` mismatch/malformed metadata fails;
15. outgoing valued traversal preserves native source/target/value;
16. incoming valued traversal swaps current/neighbor into native source/target orientation correctly;
17. exact string `""` is preserved as present;
18. string `None` fails;
19. integer `None` is preserved as absent;
20. bool/int-subclass/str-subclass values fail;
21. oversized integer edge values fail without coercion;
22. list/mapping/tuple-subclass/non-pair valued members fail;
23. malformed value on an off-domain neighbor fails before filtering;
24. well-formed off-domain polymorphic neighbor is filtered from frontier and evidence;
25. duplicate raw neighbor/pair inside one source-step response fails;
26. fan-in de-duplicates frontier nodes while evidence retains each accepted native pair;
27. safe-JCS boundary node IDs pass and oversized evidence node IDs fail only for paths that require evidence;
28. pure unvalued I-023 paths retain their existing node-ID/runtime behavior.

### Evidence identity

29. any path containing a valued step emits evidence; a pure unvalued path emits `None`;
30. mixed paths record all reviewed layers, including unvalued layers and empty trailing layers after frontier exhaustion, with zero-based step indices;
31. evidence fingerprint is deterministic;
32. changing plan fingerprint changes evidence fingerprint even with identical binding/node trace;
33. changing native source/target/value/value-presence/layer order/final nodes changes the fingerprint;
34. evidence replay under another plan fingerprint does not verify;
35. public fingerprint helper rejects forged nested record/container types and preserves the safe-JCS contract;
36. valid empty final result still carries valued-path evidence.

### Surface propagation

37. exact semantic carries evidence;
38. approximate semantic carries the same native evidence while loss metadata remains separate;
39. exact and approximate authority carry evidence;
40. identity and identifier carry evidence;
41. exact conjunction all-unvalued case retains `()`;
42. exact mixed conjunction aligns evidence with `plans` using `None`;
43. approximate mixed conjunction does the same;
44. conjunction intersection changes only final result nodes, not constituent evidence.

### Compatibility/regression

45. public corpus-execution dataclass positional construction using existing fields still works and gets default evidence;
46. outer execution contract strings remain unchanged;
47. dependency-contract v1/source authority behavior is unchanged;
48. packaged production mappings remain digest-compatible and no structural production mapping is introduced;
49. built wheel still has no Text-Fabric runtime dependency;
50. existing I-005/I-006/I-008/I-010/I-015/I-020/I-021/I-022/I-023 compatibility suites remain green after GREEN.

The RED commit must contain no production changes.

## Minimal GREEN implementation order

After observing the intended RED:

1. schema conditional valued-step fields;
2. `EdgeStepIR` extension and compiler/reconstruction validation;
3. evidence dataclasses + fingerprint helper;
4. generalized loaded-edge preflight;
5. valued/unvalued shared traversal returning `_NativePlanExecution`;
6. single-plan semantic propagation;
7. authority/identity/identifier propagation;
8. exact/approximate conjunction aligned evidence;
9. public exports;
10. only then reconcile research/current-state artifacts whose assertions changed.

Each step should run the focused tests before proceeding. Avoid unrelated refactors.

## Test gate before final review

Required exact-head evidence:

- focused I-024 tests green on Python 3.10 and 3.12;
- I-023 focused execution tests green on both versions;
- I-005/I-006/I-008/I-010/I-015/I-020/I-021/I-022 compatibility groups green;
- existing reproducible I-023/I-024 research probes green where applicable;
- authoritative full repository suite green on Python 3.10 and 3.12;
- wheel/schema packaging checks green;
- no Text-Fabric runtime dependency added to package metadata.

A test-only fake API may model TF behavior, but final adversarial review must also recheck the implementation against the pinned Text-Fabric `EdgeFeature.f/t`, `doValues`, metadata and parser mechanics plus the real TLHdig/BHSA controls used by research.

## Independent adversarial review gate

Before merging implementation, perform a fresh logically-independent exact-head review grounded in production code, tests, pinned TF mechanics and real corpus evidence.

The review must actively attack:

- silent value stripping;
- `None` vs empty-string conflation;
- bool/int and subclass coercion;
- unsafe-JCS integer handling;
- forged/defaulted `EdgeStepIR`;
- stale-prerequisite or preflight bypass;
- valuedness/metadata drift;
- malformed pair acceptance;
- off-domain evidence leakage;
- incoming orientation reversal;
- fan-in evidence loss;
- plan-replay/fingerprint collisions;
- mixed-conjunction evidence misalignment;
- accidental value-predicate semantics;
- dependency-contract/schema-version drift;
- public dataclass compatibility;
- outer execution-contract churn;
- accidental Text-Fabric dependency/autoload/network/oslots use;
- regressions in pure I-023 unvalued paths.

Any material correction changes the head and requires exact-head CI plus a new independent review.

## Exit condition

I-024 is complete only when a reviewed valued `edge-path` can execute against already-loaded TF APIs without losing native values or typed provenance, all execution surfaces expose deterministic plan-bound evidence, pure unvalued behavior remains compatible, and no edge-value filtering/domain authority has leaked from I-025.
