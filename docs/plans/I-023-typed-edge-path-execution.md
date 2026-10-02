# I-023 plan — typed unvalued TF edge-path execution

Issue: #244  
Parent: P-004 #202, Workstream B  
Reviewed research: `docs/research/I-023-edge-path-execution-reconciliation.md`  
Valued-edge follow-up: I-024 #249  
Baseline: main `1146f48ed22844203a8af1e86681246e2c9a4059`

## Exit condition

TFont can execute one reviewed, fully typed, **unvalued** native TF edge path
against already-loaded Text-Fabric / Context-Fabric APIs.

The executable source form is exactly:

```json
{
  "component_id": "fixture-tf",
  "node_type": "word",
  "execution_shape": "edge-path",
  "steps": [
    {
      "edge": "word_line",
      "direction": "outgoing",
      "result_node_type": "line",
      "valued": false
    }
  ]
}
```

Binding-level `node_type` is the start traversal domain. Each step's
`result_node_type` is the type returned by that directed traversal step:
native target type for outgoing traversal and native source type for incoming
traversal.

The first slice executes only `valued=false`. I-024 #249 owns any
`valued=true` execution/result contract.

No production ontology mapping is added merely to exercise this runtime path.

## Source-contract amendment

### Typed edge step

Change `$defs.edgeStep` in
`src/tfont/schemas/mapping.schema.json` from the current two-field object to
an exact four-field object.

Required:

- `edge`: non-empty string;
- `direction`: exactly `outgoing | incoming`;
- `result_node_type`: non-empty string;
- `valued`: exactly `false` in I-023.

Unknown step fields remain rejected by `additionalProperties: false`.

A step without `result_node_type` or `valued` is invalid. A step with
`valued=true` is invalid under I-023 rather than being accepted and rejected
later.

### Closed edge-path binding

Add a dedicated `execution_shape == "edge-path"` branch to
`$defs.nativeBinding.allOf`.

Required:

- `component_id`;
- `node_type`;
- non-empty `steps`;
- `execution_shape="edge-path"`.

Forbidden:

- `feature`;
- `value`;
- `closed_values`;
- `values`;
- top-level `edge`;
- top-level `direction`;
- `interpretation`.

Top-level `edge + direction` is not one-step sugar. `steps` is the sole
canonical path representation.

### Schema version and shipped compatibility

Do not bump mapping schema version or digest algorithms solely for this closure.

Reviewed I-023 evidence proves that all 48 packaged production executable
bindings are `value-predicate | value-set-predicate`, with zero shipped
`membership` or `edge-path` bindings. The source change therefore closes an
already-named but previously non-executable branch without changing any
shipped binding semantics.

Tests must prove:

- all packaged production sources still validate;
- existing mapping/projection semantic digests remain byte-for-byte unchanged;
- frozen I-020 fingerprints remain unchanged.

Any contrary result is a blocker and requires a plan amendment.

## IR amendment

Extend `EdgeStepIR` in `src/tfont/semantic_ir.py` to:

```python
@dataclass(frozen=True)
class EdgeStepIR:
    edge: str
    direction: str
    result_node_type: str
    valued: bool
```

Update `_native_binding()` so validated source steps compile all four fields
in source order.

Do not sort path steps: order is semantic.

Do not add a separate edge-path binding class. `NativeBindingIR.steps`
continues to carry an ordered tuple of typed `EdgeStepIR`.

`native_binding_identity()` already hashes the full canonical source object.
The new step fields therefore naturally participate in native identity.

## Resolver reconstruction and forged-IR boundary

Update `_native_binding_projection()` in
`src/tfont/semantic_resolver.py` so reconstructed step source includes all
four fields.

For every compiled `EdgeStepIR`, require:

- exact `EdgeStepIR` type;
- non-empty exact-string `edge`;
- `direction in {"outgoing", "incoming"}`;
- non-empty exact-string `result_node_type`;
- `valued is False` exactly.

Malformed or forged steps fail `invalid_compiled_ir` before plan trust or
fingerprint reconstruction succeeds.

Existing source/compiled `native_binding_identity` comparisons remain
authoritative. No new plan-fingerprint algorithm is introduced.

## Semantic dependency authority

Add an edge-path authority validator alongside the current membership
dependency-authority validator in `src/tfont/semantic_validation.py`.

Apply it to all native execution binding owners already covered by membership:

- mapping `native_binding`;
- projection `native_execution_binding`;
- external-reference `native_binding`.

For each `execution_shape="edge-path"` binding, require the mapping's declared
`native_dependencies` to contain:

### Start domain

At least one exact matching `node-type-present` dependency with:

- same `component_id`;
- `assertion.node_type == binding.node_type`.

### Step result domains

For every distinct `step.result_node_type`, at least one exact matching
`node-type-present` dependency with:

- same `component_id`;
- `assertion.node_type == step.result_node_type`.

Do not infer authorization from a feature dependency, component presence, edge
label, or runtime `otype` result.

### Ordered path

At least one exact matching `path-present` dependency with:

- same `component_id`;
- `assertion.steps` equal to the binding's ordered sequence after projecting
  each typed step to only `edge + direction`.

The dependency remains a mechanical loaded-path assertion. Endpoint types and
`valued=false` remain reviewed binding semantics, are included in binding
identity/digests, and are revalidated during execution.

Missing/wrong domain or path authority fails semantic validation with stable
`dependency_authority`.

Do not broaden `path-present` in P-002 during I-023.

## Runtime binding validator

Add a private validator in `src/tfont/semantic_execution.py`, conceptually:

```python
_validate_edge_path_binding(plan) -> NativeBindingIR
```

Require:

- exact `NativeBindingIR`;
- non-empty `component_id`;
- non-empty start `node_type`;
- `execution_shape == "edge-path"`;
- `steps` is a non-empty exact tuple;
- every step is exact `EdgeStepIR`;
- every step has valid non-empty edge/result type, valid direction, and
  `valued is False`;
- `feature is None`;
- `value_present is False`;
- `value is None`;
- `closed_values is None`;
- `values is None`;
- top-level `edge is None`;
- top-level `direction is None`;
- `interpretation is None`.

Any mismatch is `unsupported_native_binding`.

This defensive layer is mandatory even after schema/semantic validation
because compiled Python IR objects can be forged.

## Loaded API boundary

Execution uses only the already-loaded component API.

Required:

- `api.F.otype.s(start_node_type)`;
- `api.F.otype.v(node)`;
- `api.Eall()`;
- `api.E.<edge>`;
- `edge_api.f(node)` for outgoing;
- `edge_api.t(node)` for incoming;
- `edge_api.doValues`.

Do not call loaders, `TF.load()`, `E.oslots`, `L.*`, search templates,
network APIs, ontology APIs, or any corpus acquisition path.

Do not add Text-Fabric as an ordinary runtime dependency.

### Edge availability

For each step, at execution time:

1. obtain loaded edge names through `Eall()`;
2. require a well-formed iterable of exact non-empty strings;
3. require the reviewed edge name to be present;
4. obtain the edge API and requested `f/t` method;
5. require the traversal method callable;
6. require `type(edge_api.doValues) is bool`;
7. require `edge_api.doValues is False`.

Failures in loaded inventory/API/valuedness are `loaded_api_unavailable`
unless a more specific existing runtime category is already established by the
implementation tests.

Do not autoload a missing edge.

## Start frontier

Use:

`api.F.otype.s(binding.node_type)`

and the existing node-normalization boundary.

The initial selector must be non-empty after fresh prerequisite authorization:

- empty during prerequisite evaluation -> resolver not authorized;
- non-empty during prerequisite evaluation but empty at execution -> runtime
  drift, fail `invalid_result_nodes`.

Validate every start node using `F.otype.v(node)` and require exact equality
to the reviewed start `node_type`.

Unlike value predicates, wrong start-domain nodes are not silently filtered.

## Step traversal

For each step in order:

1. traverse every node in the current frontier with `f` or `t`;
2. normalize each returned iterable using the same positive-integer / bool /
   duplicate safety semantics as existing node-result normalization;
3. validate every returned node has
   `F.otype.v(node) == step.result_node_type`;
4. append nodes to the next frontier in first-discovery order;
5. de-duplicate nodes reached from multiple current nodes by first discovery.

A duplicate inside one raw edge traversal result remains malformed and fails
closed if it violates the existing normalizer contract. Duplication caused by
two different source nodes converging on the same result node is legitimate
graph fan-in and is de-duplicated at the path-frontier layer.

If `F.otype.v` is missing, raises, or returns malformed data, fail
`loaded_api_unavailable`. A well-formed but wrong node type fails
`invalid_result_nodes`.

### Empty traversal result

After at least one step, an empty next frontier is a valid successful empty
path result.

A loaded path dependency means the edge APIs exist; it does not assert that
the current source nodes have outgoing/incoming edges.

Once a frontier becomes empty, the executor may return an empty final result
without calling later edge traversals. The reviewed plan still records the
full path.

## Deterministic ordering

Do not numerically sort graph results and do not access Text-Fabric internal
`C.rank`.

Pinned Text-Fabric returns each `f/t` call in canonical TF order. Start nodes
come from canonical `F.otype.s()` order.

The path result order is therefore stable first discovery:

- start nodes in selector order;
- current frontier in first-discovery order;
- each edge result in loaded API order;
- first occurrence of a target wins.

Tests must include fan-out and fan-in to freeze this policy.

## Result-domain helper and conjunction safety

Current I-015 conjunction code assumes
`(binding.component_id, binding.node_type)` is every constituent's result
domain. That is false for edge-path because `binding.node_type` is its start
domain.

Add one private shape-aware result-domain helper used by conjunction validation:

- `value-predicate` -> `(component_id, node_type)`;
- `value-set-predicate` -> same;
- `membership` -> same;
- `edge-path` -> `(component_id, steps[-1].result_node_type)`;
- malformed/unsupported shape -> fail closed.

Exact and approximate conjunction must still require one common final
component/node type per corpus before native intersections execute.

Do not compare path start domains for conjunction compatibility. Two reviewed
constituents may start from different native domains yet legitimately return
the same reviewed final domain.

## Shared execution dispatch

Add `edge-path` dispatch wherever a fresh reviewed native plan is currently
executed:

1. exact semantic execution;
2. approximate semantic execution;
3. shared exact/approximate conjunction constituent execution;
4. exact/approximate authority execution;
5. identity execution;
6. identifier execution.

Reuse one private `_execute_edge_path(...)` primitive.

Do not add a public caller-plan executor. The trust sequence remains:

fresh loaded observation -> prerequisite evaluation -> resolver -> fresh
reviewed plan -> native execution.

## Runtime prerequisite boundary

I-023 does not change the P-002 dependency contract or
`LoadedTFObservation.path()`.

Fresh prerequisite evaluation continues to prove:

- start and result node types are present through separate
  `node-type-present` records;
- the ordered `edge + direction` sequence is loaded through
  `path-present`.

Execution then revalidates the stronger typed and unvalued binding against the
actual loaded APIs.

This split avoids claiming that `path-present` carries semantics it does not
currently encode.

## Valued-edge fail-closed boundary

I-023 never executes `valued=true`.

Schema rejects it, resolver reconstruction rejects forged true values, and
runtime rejects any actual loaded edge whose `doValues` is true.

This triple boundary is intentional.

I-024 #249 owns:

- native edge-value identity/canonicalization;
- lossless path/value result provenance;
- value predicates, if justified;
- conjunction semantics for valued traces;
- any additional source/IR fields.

Do not pre-design I-024 inside I-023 production code.

## Extent and ontology boundary

I-023 does not execute or inspect:

- `oslots`;
- `textualExtent`;
- `occurrenceSet`;
- `technicalAnchor`;
- `noSlot`.

Native edge labels and native endpoint types acquire no CRM, CRMtex, POWLA,
OLiA, OntoLex, LRMoo, CRMinf, or other domain meaning without a separately
reviewed semantic projection.

The ORACC/BHSA/TLHdig fixtures are mechanical evidence only.

## Research reconciliation after implementation

The I-023 research probe is historical evidence plus a current-state guard.
After GREEN implementation, update the current-state portions only.

At minimum the probe/evidence must record:

- shape-only edge-path invalid;
- steps-only edge-path invalid;
- old two-field edge steps invalid;
- top-level one-step alias invalid;
- feature/interpretation polluted edge-path invalid;
- typed four-field unvalued edge-path valid;
- `valued=true` invalid;
- edge-path runtime support present;
- shape-aware conjunction final-domain support present;
- accepted R-007 requirements still detected;
- packaged production structural binding count remains zero;
- no Text-Fabric runtime dependency.

Keep the research document's historical finding that the contract was
under-specified; add a short post-implementation current-state note rather than
rewriting history.

## TDD RED gate

After this plan is independently reviewed and merged, create a dedicated
implementation branch. Add tests/workflow **before** production changes and
observe actual failing CI on the exact tests-only head.

Use `tests/i023/` and a focused I-023 workflow.

### Schema RED

Prove failures before implementation for:

1. shape-only edge-path must reject;
2. steps-only edge-path must reject;
3. old two-field step must reject;
4. exact typed unvalued path must validate;
5. missing `result_node_type` rejects;
6. missing `valued` rejects;
7. `valued=true` rejects;
8. top-level `edge + direction` alias rejects;
9. path plus feature/value/value-set/interpretation fields rejects;
10. unknown step/binding fields reject.

### Dependency authority RED

11. exact start + all result node-type dependencies + ordered path dependency
    validates;
12. missing start node-type authority rejects;
13. missing intermediate/final result type authority rejects;
14. wrong component/type rejects;
15. edge-present alone does not replace path-present;
16. reordered/wrong-direction/wrong-edge path-present rejects;
17. mapping, projection and external-reference owners all enforce the same
    authority.

### IR / identity / resolver RED

18. typed steps compile all four fields in order;
19. source key order does not change binding identity;
20. step order / result type / direction / edge / valuedness changes binding
    identity;
21. resolver reconstructs all four fields;
22. forged/malformed step fails compiled-IR validation;
23. existing packaged mapping/projection digests and frozen fingerprints remain
    unchanged.

### Exact runtime RED

24. ORACC-style `word -> line -> column` two-step outgoing execution works;
25. incoming traversal returns the declared source-domain type;
26. mixed incoming/outgoing typed path works on a fixture;
27. fan-out preserves loaded order;
28. fan-in de-duplicates by first discovery;
29. empty post-step frontier succeeds empty;
30. empty start after fresh prerequisite pass fails drift;
31. wrong result node type fails;
32. malformed/invalid/duplicate raw edge nodes fail appropriately.

### Loaded API / valuedness RED

33. missing/malformed `Eall` fails closed;
34. unloaded edge fails closed and never autoloads;
35. missing/non-callable `f/t` fails;
36. missing/malformed `doValues` fails;
37. `doValues=True` fails before tuple values can be stripped;
38. traversal exception fails loaded-API category;
39. missing/malformed `F.otype.s/v` fails;
40. no access to `E.oslots`, loaders, network or Text-Fabric search.

### Surface and conjunction RED

41. exact semantic execution supports edge-path;
42. approximate semantic execution supports reviewed edge-path;
43. exact/approximate authority execution supports it;
44. identity/identifier execution supports it;
45. exact conjunction uses final result domain, not start domain;
46. approximate conjunction uses final result domain;
47. two paths with different starts but same final domain can intersect;
48. same starts but different final domains reject;
49. path plus membership/predicate can intersect only when final domains match.

### Real-data controls

50. committed ORACC inventory proves `word_line -> line_column` endpoint types
    and unvaluedness;
51. BHSA `mother` demonstrates that edge labels may span multiple endpoint
    domains, so result type cannot be inferred from edge name;
52. TLHdig valued edges remain negative controls and cannot execute in I-023.

Observe RED on the tests-only head before touching production source.

## Minimal GREEN boundary

Expected production changes:

- `src/tfont/schemas/mapping.schema.json`;
- `src/tfont/semantic_ir.py`;
- `src/tfont/semantic_validation.py`;
- `src/tfont/semantic_resolver.py`;
- `src/tfont/semantic_execution.py`.

Expected non-production changes:

- `tests/i023/**`;
- `.github/workflows/i023-edge-path-execution.yml`;
- I-023 research probe/evidence current-state reconciliation;
- a short post-implementation note in the I-023 research document.

No expected production change to:

- dependency schema / `path-present` record shape;
- `runtime_tf_observation.py`;
- digest algorithms;
- public request/result dataclasses;
- package exports;
- production mappings/profiles;
- ontology resources;
- pyproject runtime dependencies.

A need outside this boundary requires plan amendment before code.

## Focused exact-head CI

The I-023 workflow must run on Python 3.10 and 3.12 and include:

1. all `tests/i023`;
2. relevant mapping schema/semantic validation controls;
3. I-005 compiler/IR identity controls;
4. I-006 exact resolver;
5. I-008 exact execution;
6. I-015 conjunction;
7. I-020 approximate execution/fingerprint anchors;
8. I-021 authority/identity/identifier execution;
9. I-022 membership compatibility;
10. reproducible I-023 current-state research probe against pinned Text-Fabric;
11. isolated wheel build/import;
12. assertion that Text-Fabric is not a runtime dependency.

The authoritative Full repository suite must pass on the exact final head.

## Fresh implementation adversarial review

Before merge, a logically-independent review of the exact implementation head
must challenge at minimum:

- schema closure and absence of one-step alias;
- exact typed step compilation/reconstruction;
- binding/digest/fingerprint authority against forged IR;
- start and every result-domain dependency authority;
- exact ordered path-present matching;
- incoming/outgoing endpoint orientation;
- loaded edge inventory and no-autoload behavior;
- `doValues=False` enforcement and TLHdig valued-edge rejection;
- positive/unique node normalization;
- wrong-type start/intermediate/final nodes;
- fan-in/fan-out ordering and de-duplication;
- valid empty traversal frontier versus invalid stale empty start;
- shape-aware conjunction final-domain safety;
- exact/approximate/reference execution reuse;
- no `oslots` or ontology inference;
- no production mapping/digest regressions;
- no Text-Fabric runtime dependency.

Merge only with expected exact head SHA.

## Post-merge readback

From `main`:

1. validate one exact typed unvalued edge-path source;
2. execute an outgoing two-step fixture;
3. execute an incoming fixture;
4. confirm `valued=true` remains rejected;
5. confirm shape-only/old-step/one-step-alias source forms reject;
6. confirm conjunction uses final typed domain;
7. confirm existing production digests/fingerprint anchors unchanged;
8. confirm no Text-Fabric runtime dependency.

Close #244 after this readback. Continue the structural runtime roadmap with
I-024 #249 only when its valued-edge research gate is intentionally taken.
