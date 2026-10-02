# I-023 research — closed TF edge-path execution

Issue: #244  
Parent: P-004 #202, Workstream B  
Predecessor: I-022 #242 / implementation PR #247  
Baseline: main `c8b38cfb5656b161acbf1b9afcde3655770ee69f`

## Research status

Complete; research-only. This branch does not change production schemas,
validation, IR, resolver, or execution behavior.

The reproducible probe is
`scripts/research/i023_edge_path_execution_reconciliation.py`; frozen evidence
is written to
`docs/research/data/generated/i023/edge-path-reconciliation.json`.

The current source contract still accepts under-specified and ambiguous
`edge-path` bindings. In particular, all of the following are schema-valid
today:

- `{"execution_shape":"edge-path"}`;
- steps without a component or start node kind;
- `component_id + node_type + steps`;
- the legacy-looking one-step `edge + direction` surface;
- a typed-start path polluted by unrelated `feature` or `interpretation`
  fields.

At the same time, `edgeStep` is closed to only `edge + direction`, so it
cannot currently express an expected result node type.

## Mechanical grounding

Pinned Text-Fabric revision
`0c45c386916cb52be84098796ec27ce97e5bf9fc` provides the mechanics already
identified in I-022:

- `E.<edge>.f(node)` traverses outgoing edges;
- `E.<edge>.t(node)` traverses incoming edges;
- both return TF-canonical node order;
- valued edges return `(node, value)` pairs;
- `EdgeFeature` retains explicit `doValues` state.

The current TFont `LoadedTFObservation.path()` checks only that every
`edge + direction` step is loaded. It does not attest start-node semantics,
endpoint domains, connectivity, or valued/unvalued edge behavior.

Committed corpus evidence provides three useful controls:

- ORACC `word_line` is `word -> line`, unvalued;
- ORACC `line_column` is `line -> column`, unvalued;
- therefore `word_line -> line_column` is a concrete two-step unvalued path
  from native `word` nodes to native `column` nodes;
- BHSA `mother` is an unvalued graph edge with multiple native source and
  target types;
- TLHdig includes valued edges `joined`, `selected`, and
  `witness_resolution`, which are a mandatory negative control.

These facts authorize mechanical tests only. No edge name is promoted to
CRM/CRMtex/POWLA/linguistic semantics by this research.

## Start selector

The smallest closed meaning for an executable path is:

```json
{
  "component_id": "...",
  "node_type": "...",
  "execution_shape": "edge-path",
  "steps": [
    {"edge": "...", "direction": "outgoing"}
  ]
}
```

For this shape, `node_type` means the native **start-node selector**:

`F.otype.s(node_type)`

It is not the result node domain and it is not an ontology class.

The mapping must carry both:

1. an exact matching `node-type-present` dependency for
   `component_id + node_type`;
2. an exact matching `path-present` dependency for the same component and
   ordered `steps`.

A generic `component-present` or unrelated edge dependency is insufficient.

## Canonical path syntax

Only `steps` should be executable syntax for `edge-path`.

The generic top-level `edge + direction` fields should be rejected for this
shape rather than retained as one-step sugar. Keeping two equivalent source
representations would complicate review authority, semantic digests, and
provenance without adding capability.

The closed first-slice source rule should therefore require:

- `component_id`;
- `node_type`;
- `execution_shape="edge-path"`;
- non-empty ordered `steps`;

and forbid:

- `feature`;
- `value`;
- `closed_values`;
- `values`;
- top-level `edge`;
- top-level `direction`;
- `interpretation`.

## Intermediate and final node domains

The first slice should not invent target-node-type semantics that the current
source contract cannot state.

Policy:

- the reviewed `node_type` constrains only start nodes;
- every traversed node must be a positive unique TF node ID;
- every traversed node must have a readable, non-empty `F.otype.v(node)`;
- intermediate and final node types are otherwise unconstrained native node
  types;
- parent/profile identity and reviewed path authority remain the semantic
  boundary.

A later contract may add explicit endpoint/result domains if a production
mapping needs them. That must be versioned rather than inferred from edge
labels or corpus observations.

## Valued edges

The first production slice should reject valued edges fail-closed.

Current execution results are node sets plus reviewed plan/runtime provenance;
they have no lossless place to carry edge values or path traces. Silently
dropping a TLHdig edge value would therefore change native semantics.

At each step the executor should require a loaded edge API with explicit
`doValues is False`. A missing/malformed flag or `True` must fail closed.
A future valued-edge ticket can define whether values are filters, returned
provenance, semantic payload, or all three.

## Traversal and ordering

Execution should use only already-loaded APIs:

1. fresh prerequisite evaluation;
2. fresh resolver plan;
3. `F.otype.s(start_node_type)`;
4. for each ordered step, `E.<edge>.f` or `.t`;
5. validate every returned node through `F.otype.v`;
6. de-duplicate by first discovery.

Because the start selector and each Text-Fabric edge call are already
canonically ordered, first-discovery de-duplication is deterministic without
touching undocumented `C.rank` internals.

An empty start selector after a fresh `node-type-present` pass is runtime
drift and should fail closed, matching I-022 membership behavior.

An empty frontier **after traversal** is a legitimate path result: path
presence says the edges are loaded, not that every start node has a reachable
target.

The existing execution result already contains the reviewed plan and runtime
report, so the exact ordered path and prerequisite authority remain visible.
This is sufficient for unvalued paths; it would not be sufficient for valued
edges, which is why they remain unsupported.

## Conjunction boundary

I-015 conjunction safety currently treats
`(binding.component_id, binding.node_type)` as the result node domain.

That assumption is valid for value predicates and membership, where
`node_type` is the result domain. It is false for the proposed edge-path
contract, where `node_type` is the **start** domain.

Therefore the first edge-path implementation must remain unsupported in exact
and approximate conjunction execution. Allowing it through the current
conjunction helper would create a false domain-equivalence proof.

A separate follow-up should define an explicit result-domain contract before
edge-path participates in conjunction/intersection execution.

## Recommended first production slice

Authorize the implementation plan to:

- close the `edge-path` source shape to
  `component_id + node_type + steps + execution_shape`;
- define `node_type` as start selector;
- require exact matching `node-type-present` and `path-present`
  dependency authority;
- support only unvalued edges;
- traverse outgoing/incoming steps in order;
- validate all traversed node IDs and native node existence;
- use stable first-discovery ordering;
- permit empty post-traversal results;
- expose the same path execution through exact semantic, approximate semantic,
  authority, identity, and identifier surfaces where their reviewed plans
  carry the binding;
- explicitly keep edge-path unsupported in exact/approximate conjunction;
- preserve `interpretation` / `oslots` as non-executable;
- add no Text-Fabric runtime dependency and no corpus autoload;
- add no production ontology mappings merely to exercise the executor.

## Non-goals

- no valued-edge execution;
- no path-value filter language;
- no generic graph query language;
- no inferred endpoint type from an edge name;
- no CRM/CRMtex/POWLA promotion from native structure;
- no `oslots` extent semantics;
- no caller-created trusted plan;
- no corpus acquisition or network dereference;
- no conjunction support until result-domain semantics are explicit.

## Plan handoff

If independently accepted, the next PR should be a plan-only gate specifying
the exact schema/validation/runtime changes and a tests-only RED commit before
any production implementation.

The implementation PR must prove at minimum:

- ORACC `word -> line -> column` outgoing mechanics;
- incoming traversal;
- BHSA-style multi-domain edge mechanics without inferred domain meaning;
- TLHdig valued-edge rejection;
- missing/unloaded/malformed edge fail-closed behavior;
- duplicate and invalid node rejection;
- valid empty post-traversal result;
- stale prerequisite/runtime drift handling;
- unchanged production mapping fingerprints for existing resources;
- exact/approximate/reference execution reuse;
- explicit conjunction rejection;
- no `oslots`, autoload, network, or Text-Fabric package dependency.
