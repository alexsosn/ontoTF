# I-022 plan — close and execute native node-kind membership

Issue: #242  
Parent: P-004 #202, Workstream B  
Reviewed research: `docs/research/I-022-structural-execution-reconciliation.md`  
Edge/path follow-up: I-023 #244  
Baseline: main `0995576c838503f93a7be30192e4072436c6251d`

## Exit condition

TFont can execute a reviewed native binding whose execution shape is exactly
`membership` against an already-loaded TF/Context-Fabric API.

The first structural execution slice means one thing only:

> select all nodes of the reviewed native `node_type` in the reviewed
> `component_id`.

The implementation uses the loaded API's `F.otype.s(node_type)`, validates
the returned node IDs and exact `F.otype.v(node)` domain, preserves TF's
canonical selector order, and returns the nodes through the existing exact,
approximate, conjunction and I-021 reference execution result types.

I-022 does **not** execute:

- `edge-path`;
- generic `edge + direction`;
- `oslots`/extent traversal;
- `identity-key`;
- `inspection-only`.

I-023 #244 owns the missing edge/path source and execution contract.

No new production corpus mapping is introduced by I-022.

## Source-contract amendment

The current mapping schema v2 names `membership` but does not define its
field contract. Reviewed I-022 research proves that even:

```json
{"execution_shape": "membership"}
```

is currently schema-valid.

Amend `$defs.nativeBinding` so
`execution_shape == "membership"` has a closed shape.

### Required fields

Exactly these execution-relevant fields are required:

- `component_id`: non-empty string;
- `node_type`: non-empty string;
- `execution_shape`: exactly `membership`.

### Forbidden fields for membership

The membership branch rejects presence of:

- `feature`;
- `value`;
- `closed_values`;
- `values`;
- `edge`;
- `direction`;
- `steps`;
- `interpretation`.

No field is silently ignored.

The generic schema's `additionalProperties: false` remains authoritative for
unknown fields.

### Required node-type prerequisite authority

A closed binding shape is not sufficient. A membership binding must also be
covered by the mapping's reviewed dependency set.

For every membership binding on a mapping, projection, or external reference,
semantic validation must require at least one dependency named by that
mapping's `native_dependencies` whose reviewed record is exactly:

- `kind == "node-type-present"`;
- the same `component_id` as the binding;
- `assertion.node_type` equal to the binding's `node_type`.

If no such dependency exists, semantic validation fails closed with a stable
`dependency_authority` diagnostic at the membership binding.

Do not infer this authority from:

- `component-present` alone;
- a feature dependency that happens to name the same node type;
- the parent manifest's general list of node types;
- `F.otype.s()` returning a non-empty result.

This link is necessary because I-007 already evaluates
`node-type-present` against fresh loaded state. Without the reviewed
dependency, an unknown native node type could be mistaken for a legitimate
empty membership result.

Multiple semantically equivalent node-type-present dependencies are not a new
execution composition mechanism; at least one exact matching dependency is
sufficient, and all ordinary prerequisite results retain their existing
fail-closed behavior.

### Why no mapping-schema version bump

This is a closure of an already-named but previously unexecutable/undefined
execution-shape branch, not a change to the meaning of a shipped executable
binding.

The reviewed machine inventory proves that all 48 execution bindings in
packaged production mapping resources are exactly:

- `value-predicate`; or
- `value-set-predicate`.

There are zero shipped `membership` or `edge-path` bindings.

Therefore:

- every packaged production source remains valid byte-for-byte;
- existing mapping/projection semantic digests remain unchanged;
- no digest algorithm changes;
- no profile/mapping migration is required.

Tests must prove this exact packaged-resource compatibility. If a previously
unshipped source relied on an under-specified membership object, it now fails
closed instead of acquiring inferred execution semantics.

## IR boundary

Do not change `NativeBindingIR`.

It already carries all fields required by the closed membership source shape:

- `component_id`;
- `node_type`;
- `execution_shape`;
- normalized absence of feature/value/edge/path/interpretation fields.

Do not add a membership-specific IR class.

`native_binding_identity()` already binds all source binding fields. Existing
identity/digest algorithms remain unchanged.

## Runtime membership validator

Add one private membership validator in `semantic_execution.py`.

Conceptually:

```python
_validate_membership_binding(plan) -> NativeBindingIR
```

It must require the fresh resolver plan's binding to have:

- exact `NativeBindingIR` type;
- non-empty exact-string `component_id`;
- non-empty exact-string `node_type`;
- `execution_shape == "membership"`;
- `feature is None`;
- `value_present is False`;
- `value is None`;
- `closed_values is None`;
- `values is None`;
- `edge is None`;
- `direction is None`;
- `steps is None`;
- `interpretation is None`.

Any mismatch is `unsupported_native_binding`.

This defensive check is required even though structurally validated source
should already satisfy the schema: public Python IR objects can be forged or
replaced after compilation.

## Loaded API contract

Membership execution uses only the already-loaded component API.

Required methods:

- `api.F.otype.s(node_type)`;
- `api.F.otype.v(node)`.

Do not call:

- corpus/application loaders;
- `TF.load()`;
- network APIs;
- ontology APIs;
- `E.oslots`;
- `L.*`;
- Text-Fabric search templates.

No ordinary `text-fabric` package dependency is added to `pyproject.toml`.

### Availability checks

If `api.F.otype`, `.s`, or `.v` is missing/non-callable, execution fails
`loaded_api_unavailable`.

If the selector itself raises, translate to `loaded_api_unavailable`.

I-022 does not autoload warp features; already-loaded TF/Context-Fabric APIs
are the runtime boundary.

## Node normalization and ordering

Call:

`raw_nodes = api.F.otype.s(binding.node_type)`.

Pass that iterable through the existing `_normalize_result_nodes()` helper.

This provides the existing fail-closed rules:

- result must be iterable;
- boolean is not a node ID;
- each node must implement integer index semantics;
- normalized node IDs are positive;
- duplicates are invalid.

Do **not** numerically re-sort the result.

Pinned Text-Fabric documents `F.otype.s()` as canonical TF node order. The
existing scalar predicate path already preserves loaded selector order through
`_normalize_result_nodes()`.

Under the current I-007 observation contract, an empty
`F.otype.s(node_type)` means that `node-type-present` is **absent**, so a
stable authorized membership execution cannot legitimately be empty.

The fresh prerequisite evaluation calls `F.otype.s(node_type)` first:

- empty there -> dependency fails and the resolver is never authorized;
- non-empty there followed by empty at execution time -> loaded state changed
  between prerequisite evaluation and execution and must fail closed as
  `invalid_result_nodes`.

Do not turn either case into a successful empty membership result.

### Domain verification

For every normalized node:

`api.F.otype.v(node)`

must return an exact non-empty string equal to
`binding.node_type`.

- malformed node-type API result -> `loaded_api_unavailable`;
- well-formed but wrong node type -> `invalid_result_nodes`.

Do not silently filter a wrong-domain membership result. A membership selector
claiming to return exactly one node type must fail closed if it violates that
contract.

## Shared execution dispatch

The membership path is execution-shape support, not a new semantic resolver
mode.

Reuse existing fresh plans and add `membership` dispatch to all places where
a fresh reviewed native binding is executed:

1. exact semantic execution;
2. approximate semantic execution;
3. exact/approximate conjunction execution through the shared plan executor;
4. I-021 exact/approximate authority execution;
5. I-021 identity execution;
6. I-021 identifier execution.

Do not add a public `execute_membership(plan, ...)` function.

The public caller still supplies:

- compiled IR;
- typed semantic/reference request;
- loaded contexts.

The executor still performs:

fresh loaded runtime evaluation -> resolver -> fresh plan -> native execution.

A caller-created plan remains non-authoritative.

## Resolver and fingerprint compatibility

Do not change resolver selection logic merely because a binding is membership.

Exact/approximate/reference resolvers already carry
`native_execution_binding` and its identity into plan/fingerprint data.

Existing plans/results therefore need no new fields.

Regression anchors must prove that all current I-020 exact/approximate
fingerprints and I-021 behavior remain unchanged for existing mappings.

New membership plans naturally receive their own deterministic plan/result
fingerprints because their reviewed native binding identity is different.

No fingerprint algorithm constant changes.

## Conjunction behavior

I-015 node-domain safety remains authoritative.

A membership plan carries the same reviewed:

- `component_id`;
- `node_type`;

as other executable plans, so the existing per-corpus conjunction domain check
continues to require one shared component/node type across required atoms.

No conjunction-specific membership exception is added.

The existing conjunction intersection ordering remains unchanged; I-022 only
changes how a constituent plan obtains its native node set.

## Extent/anchor boundary

I-022 membership never calls `E.oslots.s()`.

The reviewed structural modes:

- `textualExtent`;
- `occurrenceSet`;
- `technicalAnchor`;
- `noSlot`;

remain dependency/provenance semantics and are not membership execution
operators.

Because `interpretation` is forbidden in the membership native binding,
node-kind execution cannot accidentally acquire slot/extent semantics through
a binding field.

A node returned by membership may be represented by any of those reviewed
extent states elsewhere in the source contract; membership itself asserts only
its native TF node type.

## Edge/path fail-closed boundary

I-022 must preserve the current refusal for:

- `edge-path`;
- any structural binding whose shape is not one of the explicitly supported
  runtime shapes;
- `identity-key`;
- `inspection-only`.

Do not add a one-step special case for `edge` / `direction`.

Do not reinterpret `node_type` as an edge-path start selector.

I-023 #244 owns the next research/plan cycle.

## Research reconciliation update

The merged I-022 research probe currently records the pre-implementation fact
that membership shape-only input is schema-valid.

Because the research workflow intentionally watches
`mapping.schema.json`, the implementation must update only the
membership-related current-state evidence after the source amendment.

Update the probe so it mechanically derives the membership closure from test
instances rather than hard-coding it.

At minimum record:

- shape-only membership is invalid;
- typed `component_id + node_type + membership` is valid;
- membership plus each forbidden field is invalid;
- edge-path shape-only remains valid and therefore still blocked;
- runtime supported shapes now include membership;
- packaged production mapping inventory remains 48 bindings with zero shipped
  structural bindings;
- no ordinary Text-Fabric runtime dependency exists.

Keep the research document's historical reasoning intact; add a short
post-implementation reconciliation note rather than rewriting why the ticket
was opened.

## TDD RED

After this plan is independently reviewed and merged, create a dedicated
implementation branch and `tests/i022/` **before** production changes.

Tests-only RED must include at least:

### Source shape

1. shape-only membership is rejected;
2. exact `component_id + node_type + membership` validates;
3. membership with each forbidden field is rejected independently;
4. unknown fields remain rejected;
5. membership without a matching reviewed `node-type-present` dependency
   fails semantic validation as `dependency_authority`;
6. component-present alone does not authorize membership;
7. a matching node-type-present dependency for the wrong component or wrong
   node type does not authorize membership;
8. all packaged production mappings remain valid;
9. all packaged production mapping/projection digests remain unchanged.

### Compiler / identity

10. a validated membership source compiles to the existing
   `NativeBindingIR` with exact membership fields and normalized absence of
   all forbidden fields;
11. source key order does not change native binding identity;
12. adding/changing node type or component changes native binding identity.

### Exact execution

13. exact semantic membership selects all nodes of the requested native type;
14. selector order is preserved;
15. slot-type membership works;
16. an absent node type fails fresh `node-type-present` prerequisite authorization
    before native membership execution;
17. if `F.otype.s(node_type)` was non-empty during fresh prerequisite evaluation
    but is empty when membership executes, fail `invalid_result_nodes` as
    runtime drift; do not return a successful empty membership result.

### Loaded API failure

18. missing/non-callable `F.otype.s` fails `loaded_api_unavailable`;
19. missing/non-callable `F.otype.v` fails `loaded_api_unavailable`;
20. selector exception fails `loaded_api_unavailable`;
21. non-iterable result fails `invalid_result_nodes`;
22. bool/non-index/zero/negative/duplicate node IDs fail;
23. wrong-domain returned node fails `invalid_result_nodes`;
24. malformed `otype.v` result fails `loaded_api_unavailable`.

### Trust / unsupported shape

25. forged membership IR carrying a forbidden field fails
    `unsupported_native_binding`;
26. stale/incompatible loaded state prevents membership execution authorization;
27. no public caller-plan execution path exists;
28. edge-path remains `unsupported_native_binding`;
29. inspection-only remains unsupported;
30. execution does not touch `E.oslots` or trigger loading/network access.

### Existing surfaces

31. exact semantic execution handles membership;
32. approximate semantic execution handles exact membership with no loss;
33. an authorized approximate semantic membership binding preserves I-020 loss
    records while executing membership;
34. exact/approximate conjunction can execute membership constituents under
    existing node-domain safety;
35. exact/approximate authority execution can execute a reviewed membership
    binding;
36. identity/identifier execution can execute a reviewed membership binding
    without weakening I-021 review/index checks.

### Compatibility

37. frozen I-020 fingerprint anchors remain exact;
38. I-021 resolver/execution adversarial suite remains green;
39. I-005/I-006/I-008/I-015 exact controls remain green;
40. pyproject still has no Text-Fabric runtime dependency.

Observe actual RED on the exact tests-only head before changing schema/runtime.

## Minimal GREEN implementation

Expected production changes:

- `src/tfont/schemas/mapping.schema.json` — close membership shape only;
- `src/tfont/semantic_validation.py` — require matching reviewed
  `node-type-present` dependency authority for every membership binding;
- `src/tfont/semantic_execution.py` — private validator/API helper/executor
  and membership dispatch only.

Expected non-production changes:

- `tests/i022/**`;
- `.github/workflows/i022-membership-execution.yml`;
- `scripts/research/i022_structural_execution_reconciliation.py`;
- `docs/research/data/generated/i022/structural-runtime-reconciliation.json`;
- short post-implementation note in
  `docs/research/I-022-structural-execution-reconciliation.md`.

No expected changes to:

- `semantic_ir.py`;
- `semantic_resolver.py`;
- semantic digest algorithms;
- public package exports;
- production profiles/mappings;
- ontology resources;
- coverage manifests;
- runtime prerequisite evaluator;
- pyproject runtime dependencies.

Any need outside this boundary requires a plan amendment before code.

## Focused exact-head CI

Add `.github/workflows/i022-membership-execution.yml`.

On Python 3.10 and 3.12:

1. install TFont normally;
2. run all `tests/i022`;
3. rerun source/schema controls relevant to native bindings;
4. rerun I-005 compiler controls;
5. rerun I-006 exact resolver;
6. rerun I-008 exact execution;
7. rerun I-015 conjunction;
8. rerun I-020 approximate execution;
9. rerun I-021 reference resolver/execution/adversarial tests;
10. reproduce the updated I-022 current-state evidence using the pinned
    research-only Text-Fabric dependency;
11. build an isolated wheel and verify existing public APIs import;
12. verify wheel metadata does not add Text-Fabric as a runtime dependency.

The authoritative Full repository suite must pass on the exact final head.

## Fresh final adversarial review

The implementation exact head requires a new logically-independent review
grounded in the final code, schema, fixture APIs and real corpus evidence.

At minimum challenge:

- whether membership schema closure really rejects every extraneous structural
  field;
- whether every membership binding is backed by an exact reviewed
  `node-type-present` dependency and fresh I-007 evaluation;
- whether absent node type fails at fresh prerequisite evaluation and whether
  a later empty selector is treated as runtime drift rather than success;
- whether defensive runtime validation catches forged IR despite schema
  validation;
- whether `F.otype.s/v` is used exactly as pinned upstream documents;
- selector-order preservation;
- empty/slot/non-slot behavior;
- malformed/wrong-domain selector output;
- stale runtime state before native API access;
- no caller-plan trust;
- no `oslots`/extent semantic inference;
- edge-path still unsupported;
- I-015 conjunction domain safety;
- I-020 exact/approximate fingerprint immutability;
- I-021 reference trust/payload/index isolation;
- all 48 packaged production bindings still valid with unchanged digests;
- no Text-Fabric runtime dependency;
- no new production mappings or ontology promotion.

Merge only with the reviewed exact head SHA.

## Post-merge readback

From `main`:

1. validate one exact membership source;
2. execute one membership fixture and confirm node order/domain;
3. confirm absent node type fails prerequisite authorization and a post-check
   empty selector fails closed;
4. confirm shape-only membership rejects;
5. confirm edge-path remains rejected at execution;
6. re-read frozen I-020 anchors;
7. verify packaged production mapping inventory still reports zero structural
   bindings.

Close #242 after this readback. Continue Workstream B with I-023 #244.
