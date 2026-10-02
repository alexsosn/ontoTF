# I-022 research — typed TF-native structural execution reconciliation

Issue: #242  
Parent: P-004 #202, Workstream B  
Source-contract dependencies: P-002 #37, R-007 #39  
Execution trust dependency: R-019 #134 / I-008 #143  
Baseline: main `d1da009cc49b3dc812a395e0813c51500c28fa08`

## Research status

In progress. This branch contains only reconciliation/probe material; it does
not change production source schemas or runtime behavior.

The current evidence already establishes one blocking contract gap: the
mapping schema names `membership` and `edge-path` as execution shapes, but
does not define a closed required/forbidden field shape for either one.
Consequently shape-only objects are currently schema-valid.

The research probe records that fact against the actual schema and also pins:

- the current `NativeBindingIR` field set;
- the current executor's only supported shapes
  (`value-predicate`, `value-set-predicate`);
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

## Provisional recommendation

The likely implementation boundary is:

1. amend the mapping source contract to close `membership` exactly;
2. implement only exact native node-kind membership first, reusing the
   existing fresh-runtime trust path;
3. preserve extent interpretation as plan/provenance/guard metadata only;
4. keep `edge-path` fail-closed until the source contract explicitly states
   its start selector, path shape, node-domain rules and valued-edge policy;
5. do not add Text-Fabric as a TFont runtime dependency merely for this work:
   the executor continues to operate on already-loaded API objects.

This recommendation remains provisional until generated evidence is frozen and
the research PR receives a fresh independent adversarial review.
