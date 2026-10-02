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

The first research pass proposed a start-typed path with unconstrained
intermediate/final node types. Independent adversarial reconciliation rejected
that proposal: accepted R-007 explicitly requires native edge source/target
types and valued/unvalued distinction to survive canonical mapping/IR.
The contract below corrects that gap.

## Current gap

The current mapping schema still accepts under-specified and mixed
`edge-path` bindings:

- `{"execution_shape":"edge-path"}`;
- steps without component/start domain;
- `component_id + node_type + steps`;
- top-level one-step `edge + direction`;
- unrelated `feature` or `interpretation` fields.

Current `edgeStep` is closed to only `edge + direction`. It therefore cannot
state the traversal-result node domain or whether an edge is valued.

That is insufficient for R-007 and also conflicts with I-015 conjunction
safety, which needs a known result domain.

## Mechanical grounding

Pinned Text-Fabric revision
`0c45c386916cb52be84098796ec27ce97e5bf9fc` provides:

- `E.<edge>.f(node)`: outgoing traversal;
- `E.<edge>.t(node)`: incoming traversal;
- TF-canonical ordering for both;
- `(node, value)` pairs for valued edges;
- explicit `EdgeFeature.doValues` implementation state.

Current `LoadedTFObservation.path()` proves only that the requested
`edge + direction` steps are loaded. It does not prove endpoint types,
connectivity, or valuedness.

Committed corpus controls remain:

- ORACC `word_line`: `word -> line`, unvalued;
- ORACC `line_column`: `line -> column`, unvalued;
- BHSA `mother`: unvalued, with multiple native endpoint types;
- TLHdig valued controls: `joined`, `selected`,
  `witness_resolution`.

## Closed source contract

The executable binding should be:

```json
{
  "component_id": "oracc-tf",
  "node_type": "word",
  "execution_shape": "edge-path",
  "steps": [
    {
      "edge": "word_line",
      "direction": "outgoing",
      "result_node_type": "line",
      "valued": false
    },
    {
      "edge": "line_column",
      "direction": "outgoing",
      "result_node_type": "column",
      "valued": false
    }
  ]
}
```

Binding-level `node_type` is the **start traversal domain** and therefore
selects `F.otype.s(node_type)`.

Each step must require exactly:

- `edge`;
- `direction`;
- `result_node_type`;
- `valued`.

For the first production slice, `valued` is required and must be exactly
`false`.

`result_node_type` means the expected type of nodes **returned by that
traversal step**. For outgoing traversal it is the native edge target type; for
incoming traversal it is the native edge source type. Therefore the current
domain + direction + result domain preserve both native endpoint types without
directional ambiguity.

The `edge-path` binding must reject:

- `feature`;
- `value`;
- `closed_values`;
- `values`;
- top-level `edge`;
- top-level `direction`;
- `interpretation`.

Top-level `edge + direction` should not survive as one-step sugar. One
canonical representation keeps review authority, digests and provenance
unambiguous.

## Dependency authority

A reviewed edge-path owner must have dependencies that authorize:

1. the start `component_id + node_type` with exact
   `node-type-present`;
2. every distinct step `result_node_type` with exact
   `node-type-present` on the same component;
3. the exact ordered `edge + direction` sequence with matching
   `path-present`.

`path-present` remains a mechanical loaded-edge prerequisite. The typed
domains and explicit `valued=false` remain part of the reviewed mapping
identity and are revalidated during execution.

This avoids expanding the dependency contract merely to duplicate binding
semantics while still preventing an unreviewed start/result domain from
becoming executable.

## Runtime traversal

Execution should use only already-loaded APIs:

1. fresh prerequisite evaluation;
2. fresh resolver plan;
3. `F.otype.s(start_node_type)`;
4. validate each start node is exactly the start type;
5. for each ordered step:
   - require the edge is still listed by `Eall()`;
   - get `E.<edge>.f` or `.t`;
   - require explicit `doValues is False`;
   - traverse the current frontier;
   - normalize positive unique node IDs;
   - require `F.otype.v(node) == step.result_node_type`;
   - de-duplicate by first discovery;
6. return the final frontier.

The start selector and each Text-Fabric edge call are canonically ordered, so
first-discovery de-duplication is deterministic without reading undocumented
`C.rank` internals.

An empty start selector after a fresh `node-type-present` pass is runtime
drift and fails closed, matching I-022 membership.

An empty frontier after one or more traversal steps is valid: loaded path
availability does not assert graph connectivity for every start node.

## Valued-edge boundary

R-007 requires valued/unvalued distinction to survive mapping and IR. The first
slice satisfies that requirement by making `valued=false` explicit rather
than silently assuming it.

`valued=true` remains unsupported until a separate contract defines how edge
values survive execution: filter predicate, returned path provenance, semantic
payload, or some combination. Accepting valued edges while returning only node
IDs would discard native semantics.

The runtime must therefore fail closed if `doValues` is missing, malformed,
or true for a step whose reviewed contract says `valued=false`.

## Conjunction domain

The initial research pass found that current conjunction safety treats
`binding.node_type` as the result domain. With typed steps, the production
fix can preserve conjunction support instead of banning edge-path:

- scalar predicate / value-set / membership result domain:
  `binding.node_type`;
- edge-path result domain:
  `binding.steps[-1].result_node_type`.

A shared private result-domain helper should feed I-015 exact and approximate
conjunction checks. This keeps intersection fail-closed while allowing typed
edge-path plans to participate when all constituents resolve to the same
component and final node type.

A forged/malformed edge-path with no valid final result domain remains
unsupported.

## Recommended first production slice

Authorize a plan-only gate to:

- extend `edgeStep` with required `result_node_type` and
  `valued=false`;
- close `edge-path` to
  `component_id + node_type + steps + execution_shape`;
- extend `EdgeStepIR` accordingly;
- require matching `node-type-present` dependencies for start and every
  result domain plus exact `path-present`;
- execute only unvalued paths;
- validate every start/intermediate/final node against the reviewed domain;
- use stable first-discovery ordering;
- permit empty post-traversal results;
- share execution across exact/approximate semantic, conjunction, authority,
  identity and identifier surfaces;
- update conjunction result-domain validation to use the final typed step;
- preserve `interpretation` / `oslots` as non-executable;
- add no Text-Fabric runtime dependency, autoload or network access;
- add no production semantic mappings solely to exercise the runtime.

## Non-goals

- no `valued=true` execution yet;
- no edge-value filter language;
- no path-trace result object in this slice;
- no generic graph query language;
- no endpoint types inferred from edge names;
- no CRM/CRMtex/POWLA promotion from native structure;
- no `oslots` extent semantics;
- no caller-created trusted plan;
- no corpus acquisition or URI dereference.

## Plan handoff

The next PR must be plan-only and specify the exact schema, IR, validation,
runtime, conjunction and TDD changes before production code.

Implementation acceptance must include:

- ORACC typed `word -> line -> column` outgoing path;
- incoming path with correctly reversed native endpoint orientation;
- BHSA-style multi-domain edge control without inferred semantics;
- TLHdig `valued=true` rejection;
- schema rejection of shape-only/mixed/legacy alias paths;
- dependency-authority rejection for missing/wrong start or result node types
  and wrong path sequence;
- missing/unloaded/malformed edge fail-closed behavior;
- duplicate/invalid/wrong-type traversed node rejection;
- valid empty post-traversal result;
- stale prerequisite/runtime drift handling;
- unchanged existing production mapping fingerprints;
- exact/approximate/reference/conjunction reuse;
- no `oslots`, autoload, network, or Text-Fabric package dependency.
