# I-022 research — typed TF-native structural execution reconciliation

Issue: #242  
Parent: P-004 #202, Workstream B  
Source-contract dependencies: P-002 #37, R-007 #39  
Execution trust dependency: R-019 #134 / I-008 #143  
Baseline: main `d1da009cc49b3dc812a395e0813c51500c28fa08`

## Research status

Complete; ready for independent adversarial review and, if accepted, a
separate implementation plan.

This branch contains only reconciliation/probe material; it does not change
production source schemas or runtime behavior. Generated evidence is frozen at
`docs/research/data/generated/i022/structural-runtime-reconciliation.json`
and reproduced on Python 3.10/3.12 against pinned Text-Fabric revision
`0c45c386916cb52be84098796ec27ce97e5bf9fc`.

The current evidence already establishes one blocking contract gap: the
mapping schema names `membership` and `edge-path` as execution shapes, but
does not define a closed required/forbidden field shape for either one.
Consequently shape-only objects are currently schema-valid.

The research probe records that fact against the actual schema and also pins:

- the current `NativeBindingIR` field set;
- the current executor's only supported shapes
  (`value-predicate`, `value-set-predicate`);
- all 48 execution bindings in packaged production mapping resources: their
  shape set is exactly `value-predicate | value-set-predicate`, with zero
  `membership` or `edge-path` bindings, so closing the two structural
  source shapes does not invalidate a shipped production mapping;
- the public Text-Fabric mechanics at pinned upstream revision
  `0c45c386916cb52be84098796ec27ce97e5bf9fc`;
- committed CUC, ORACC, TLHdig and BHSA structural inventories.

## Text-Fabric mechanics

Pinned Text-Fabric source provides the mechanics required for a structural
runtime:

- `OtypeFeature.s(node_type)` returns all nodes of one native node type in
  canonical order;
- `EdgeFeature.f(node)` traverses outgoing edges;
- `EdgeFeature.t(node)` traverses incoming edges;
- valued edges return `(node, value)` pairs rather than plain nodes;
- `OslotsFeature.s(node)` returns the native slot set for a node (and the
  singleton itself for a slot).

These calls establish mechanics only. They do not assign CRM, CRMtex, POWLA,
linguistic or other domain meaning to a node type, edge, or slot relationship.

Authoritative upstream sources:

- https://github.com/annotation/text-fabric/blob/0c45c386916cb52be84098796ec27ce97e5bf9fc/tf/core/otypefeature.py
- https://github.com/annotation/text-fabric/blob/0c45c386916cb52be84098796ec27ce97e5bf9fc/tf/core/edgefeature.py
- https://github.com/annotation/text-fabric/blob/0c45c386916cb52be84098796ec27ce97e5bf9fc/tf/core/oslotsfeature.py
- https://github.com/annotation/text-fabric/blob/0c45c386916cb52be84098796ec27ce97e5bf9fc/tf/docs/about/datamodel.md

## Current corpus mechanics

The committed corpus evidence supplies concrete structural test material
without promoting it semantically.

- CUC 0.2.8 has sign slots and no non-warp edge features in the R-005
  inventory. It is useful for native node-kind/warp mechanics.
- ORACC-TF 0.4.0 has sign slots and explicit unvalued typed edges including
  `word_line`, `line_column`, `translation_line`,
  `translation_document`, `word_lex`, `face_document`.
  The first two form a real mechanical two-step path
  `word -> line -> column`.
- TLHdig-TF 0.4.0 has sign slots and both unvalued and valued non-warp edges,
  including `lexeme`, `analyses`, `witness`, `startsAt`, `endsAt`,
  `joined`, `selected`, and `witness_resolution`.
- BHSA has word slots and explicit linguistic graph edges such as
  `mother` and `functional_parent`; old-version `omap@...` edges are
  version-mapping mechanics and are not structural-semantic examples.

## Current blocking questions

### Membership

Text-Fabric mechanics make exact native node-kind selection unambiguous:
`F.otype.s(node_type)`.

However, the TFont source contract does not currently require
`component_id + node_type` for `execution_shape=membership`, nor does it
forbid unrelated selector fields. Production execution would therefore accept
under-specified reviewed source records unless the source contract is amended
first.

The likely minimal meaning is native node-kind membership only. It must not
mean ontology class membership merely because the native node type has a
similar label.

### Edge path

Text-Fabric direction itself is unambiguous: outgoing is `E.<edge>.f`,
incoming is `E.<edge>.t`.

The TFont `edge-path` contract is not yet executable, because:

1. the schema does not require `component_id`, `steps`, or any start
   selector;
2. a path can be schema-valid with only
   `{"execution_shape": "edge-path"}`;
3. `node_type` is available in the generic binding shape, but no accepted
   source contract says it is the path's start-node selector;
4. each step records only edge + direction, not an expected intermediate/final
   node domain or an edge-value predicate;
5. valued-edge results require an explicit decision to ignore, preserve, or
   filter the edge value.

Therefore I-022 research does not authorize an edge-path executor yet.

### Extent and anchors

The P-002/R-007 modes remain structural interpretation/provenance:

- `textualExtent`;
- `occurrenceSet`;
- `technicalAnchor`;
- `noSlot`.

For the first runtime slice they should not become direct execution operators.

In particular:

- `technicalAnchor` never licenses treating its `oslots` as semantic text
  extent;
- `noSlot` is a valid structural state and must not fabricate slot
  membership;
- `occurrenceSet` is not one contiguous textual span;
- `textualExtent` still does not imply a CRM/CRMtex/POWLA containment
  relation without a reviewed semantic projection.

## Research conclusion

The first production slice should be deliberately narrower than the structural
vocabulary already present in the schema.

### Authorize for the implementation plan: native node-kind membership

Amend the source contract so
`execution_shape="membership"` has one closed meaning:

- required: `component_id`, `node_type`, `execution_shape`;
- `execution_shape` is exactly `membership`;
- feature/value/value-set/edge/direction/steps/interpretation fields are
  forbidden for this shape.

Extent/anchor interpretation remains represented by the existing reviewed
structural dependency contract rather than being overloaded onto node-kind
selection. No current production mapping uses `interpretation` as part of an
executable binding, so allowing it here would widen the first slice without
evidence.

Execution then means exactly:

`loaded_api.F.otype.s(node_type)`

followed by deterministic validation that the returned values are positive,
unique node IDs whose `F.otype.v(node)` is exactly the requested native type.

Do not numerically re-sort this result: Text-Fabric documents
`F.otype.s()` as returning canonical TF node order, and the existing scalar
predicate executor already preserves the loaded selector's order through
`_normalize_result_nodes()`. Membership should reuse that normalization
boundary rather than invent a second ordering rule.

This is **native TF node-kind membership**. A node type named `word`,
`document`, `lex`, `fragment`, etc. does not thereby become an OLiA,
OntoLex, CRM, CRMtex or LRMoo class.

The implementation should reuse the existing I-008 trust sequence:
fresh loaded-context prerequisite evaluation -> fresh resolver plan -> typed
native execution. Public caller-created plans remain non-authoritative.

### Do not authorize yet: edge-path

Keep `edge-path` fail-closed in the I-022 implementation.

The current schema admits under-specified values such as
`{"execution_shape":"edge-path"}`. More importantly, the accepted source
contract does not say what node set starts a path. Treating generic
`node_type` as the start selector would be a new semantic rule, not a runtime
detail.

A later reviewed contract must specify at minimum:

- the start selector/domain;
- a closed non-empty ordered step list;
- exact outgoing/incoming meaning;
- intermediate/final node-domain checks or an explicit statement that they
  are unconstrained native nodes;
- policy for valued-edge return values;
- behavior when an edge is unavailable/not loaded;
- whether one-step `edge + direction` is merely syntax sugar for `steps`;
- how path provenance remains visible in result/fingerprint data.

The real ORACC `word_line -> line_column`, BHSA `mother`, and TLHdig edge
families are sufficient to test those mechanics later, but they do not supply
the missing source-level execution authority.

### Extent/anchor interpretation remains non-executable

`textualExtent`, `occurrenceSet`, `technicalAnchor`, and `noSlot`
remain reviewed structural interpretation/provenance in the first slice.

I-022 must not query `oslots` to manufacture a semantic result merely because
one of these values is present. In particular:

- `technicalAnchor` never becomes textual extent;
- `noSlot` is not an execution failure and receives no synthetic slots;
- `occurrenceSet` is not collapsed into one text span;
- `textualExtent` is not promoted to domain containment.

Warp APIs may still be used internally for native type/domain validation
without removing `otype` or `oslots` from technical coverage exclusions.

### Runtime dependency boundary

Do not add Text-Fabric to ordinary `tfont` dependencies. The current executor
works over already-loaded API objects supplied by the caller. I-022 should do
the same; the pinned Text-Fabric install in research CI exists only to verify
the upstream API contract.

## Plan handoff

If this research is accepted, the I-022 implementation plan should:

1. amend only the `membership` source-shape contract; the current packaged
   mapping inventory proves this is additive for shipped production mappings;
2. add schema/semantic regressions before implementation;
3. preserve all existing semantic digests/fingerprints for existing mappings;
4. add a typed membership executor path shared by exact/approximate/reference
   execution where a fresh resolver plan carries that binding;
5. validate loaded `otype` availability and returned node domains
   fail-closed;
6. preserve empty membership as a successful empty result;
7. leave `edge-path`, `identity-key` and `inspection-only` unsupported by
   the generic structural executor;
8. add no corpus mappings merely to exercise the new runtime path;
9. keep extent/anchor modes provenance-only in this slice;
10. create a separate follow-up for the missing edge-path source/execution
    contract rather than smuggling path semantics into `membership`.

The final implementation still requires plan review, tests-only RED, GREEN,
focused/full exact-head CI, and a fresh code/data-grounded adversarial review.

## Post-implementation reconciliation

I-022 production implementation closes only the reviewed native node-kind
membership slice.

Current state after implementation:

- shape-only `{"execution_shape":"membership"}` is rejected;
- membership requires exactly `component_id + node_type + execution_shape`
  and rejects feature/value/value-set/edge/path/interpretation fields;
- semantic validation requires an exact matching reviewed
  `node-type-present` dependency from the mapping's `native_dependencies`;
- loaded execution supports membership through `F.otype.s(node_type)` plus
  exact `F.otype.v(node)` domain validation;
- exact, approximate, conjunction and I-021 reference executors share that
  membership path;
- packaged production mappings remain 48 scalar/value-set bindings with zero
  shipped membership/edge-path bindings;
- `edge-path` remains source-under-specified and runtime-unsupported, owned by
  I-023 #244;
- TFont still does not declare Text-Fabric as an ordinary runtime dependency.

The earlier plan-handoff sentence saying empty membership should be a
successful empty result is superseded by reviewed plan amendment #246. Fresh
runtime authorization requires `node-type-present`: an absent node type fails
before execution, while a selector that was non-empty during prerequisite
evaluation but becomes empty at execution is treated as runtime drift and
fails closed as `invalid_result_nodes`.

