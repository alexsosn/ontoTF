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

An empty selector result is a successful empty result.

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
5. all packaged production mappings remain valid;
6. all packaged production mapping/projection digests remain unchanged.

### Compiler / identity

7. a validated membership source compiles to the existing
   `NativeBindingIR` with exact membership fields and normalized absence of
   all forbidden fields;
8. source key order does not change native binding identity;
9. adding/changing node type or component changes native binding identity.

### Exact execution

10. exact semantic membership selects all nodes of the requested native type;
11. selector order is preserved;
12. slot-type membership works;
13. empty membership is a successful empty result.

### Loaded API failure

14. missing/non-callable `F.otype.s` fails `loaded_api_unavailable`;
15. missing/non-callable `F.otype.v` fails `loaded_api_unavailable`;
16. selector exception fails `loaded_api_unavailable`;
17. non-iterable result fails `invalid_result_nodes`;
18. bool/non-index/zero/negative/duplicate node IDs fail;
19. wrong-domain returned node fails `invalid_result_nodes`;
20. malformed `otype.v` result fails `loaded_api_unavailable`.

### Trust / unsupported shape

21. forged membership IR carrying a forbidden field fails
    `unsupported_native_binding`;
22. stale/incompatible loaded state prevents `F.otype.s` access;
23. no public caller-plan execution path exists;
24. edge-path remains `unsupported_native_binding`;
25. inspection-only remains unsupported;
26. execution does not touch `E.oslots` or trigger loading/network access.

### Existing surfaces

27. exact semantic execution handles membership;
28. approximate semantic execution handles exact membership with no loss;
29. an authorized approximate semantic membership binding preserves I-020 loss
    records while executing membership;
30. exact/approximate conjunction can execute membership constituents under
    existing node-domain safety;
31. exact/approximate authority execution can execute a reviewed membership
    binding;
32. identity/identifier execution can execute a reviewed membership binding
    without weakening I-021 review/index checks.

### Compatibility

33. frozen I-020 fingerprint anchors remain exact;
34. I-021 resolver/execution adversarial suite remains green;
35. I-005/I-006/I-008/I-015 exact controls remain green;
36. pyproject still has no Text-Fabric runtime dependency.

Observe actual RED on the exact tests-only head before changing schema/runtime.

## Minimal GREEN implementation

Expected production changes:

- `src/tfont/schemas/mapping.schema.json` — close membership shape only;
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
- `semantic_validation.py`;
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
3. confirm shape-only membership rejects;
4. confirm edge-path remains rejected at execution;
5. re-read frozen I-020 anchors;
6. verify packaged production mapping inventory still reports zero structural
   bindings.

Close #242 after this readback. Continue Workstream B with I-023 #244.
