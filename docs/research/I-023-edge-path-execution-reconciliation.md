# I-023 research — closed TF edge-path execution

Issue: #244  
Parent: P-004 #202, Workstream B  
Predecessor: I-022 #242 / implementation PR #247  
Valued-edge follow-up: I-024 #252  
Baseline: main `c8b38cfb5656b161acbf1b9afcde3655770ee69f`

## Research status

Complete; research-only. This branch does not change production schemas,
validation, IR, resolver, or execution behavior.

The reproducible probe is
`scripts/research/i023_edge_path_execution_reconciliation.py`; frozen evidence
is written to
`docs/research/data/generated/i023/edge-path-reconciliation.json`.

Adversarial reconciliation against accepted R-007 changed the initial
recommendation materially. The first research draft proposed using
`node_type` as a start selector while leaving intermediate/final node domains
unconstrained and rejecting valued edges only at runtime. That is too weak.

R-007 §2.8 already requires the canonical mapping/IR mechanics for a directed
TF edge to preserve at least:

- source selector/type;
- edge feature name;
- target selector/type;
- native direction;
- valued versus unvalued state;
- value semantics when the edge is valued.

R-007 §10 additionally requires first-class directed edge selector/path
semantics and an explicit valued/unvalued distinction. I-023 therefore cannot
authorize production edge-path execution until the mapping/IR step shape
preserves the result node domain and explicit unvalued state.

## Current contract gap

The current source contract still accepts under-specified and ambiguous
`edge-path` bindings:

- `{"execution_shape":"edge-path"}`;
- steps without a component or start node kind;
- `component_id + node_type + steps`;
- the duplicate one-step `edge + direction` surface;
- a typed-start path polluted by unrelated `feature` or `interpretation`
  fields.

At the same time, current `edgeStep` and `EdgeStepIR` contain only
`edge + direction`. The source schema rejects a step carrying either a result
node type or explicit valued/unvalued state.

So I-023 requires a source/IR amendment before runtime code.

## Mechanical grounding

Pinned Text-Fabric revision
`0c45c386916cb52be84098796ec27ce97e5bf9fc` provides the required mechanics:

- `E.<edge>.f(node)` traverses outgoing edges;
- `E.<edge>.t(node)` traverses incoming edges;
- both order results by TF canonical rank;
- valued edges return `(node, value)` pairs;
- `EdgeFeature` retains explicit `doValues` state.

The current TFont `LoadedTFObservation.path()` checks only that every
`edge + direction` step is loaded. It does not attest start-node semantics,
result-node domains, connectivity, or valued/unvalued state.

Committed corpus evidence supplies controls:

- ORACC `word_line` is unvalued `word -> line`;
- ORACC `line_column` is unvalued `line -> column`;
- therefore `word_line -> line_column` is a concrete typed two-step path
  `word -> line -> column`;
- BHSA `mother` is an unvalued graph edge with multiple source and target
  native types;
- TLHdig includes valued edges `joined`, `selected`, and
  `witness_resolution`.

These are mechanical fixtures only. Native edge names do not acquire
CRM/CRMtex/POWLA/linguistic meaning from their storage shape.

## Closed first-slice source contract

The smallest R-007-compatible **unvalued** executable binding is:

```json
{
  "component_id": "...",
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

For this shape:

- top-level `node_type` is the native start-node selector;
- each step's `result_node_type` is the required native domain after that
  traversal step;
- `valued` is explicit and must be exactly `false` in the I-023 production
  slice;
- ordered `steps` is the only path syntax.

Top-level `edge + direction` must be rejected for `edge-path`; retaining two
equivalent serializations would create duplicate review/digest identities.

The edge-path shape must also forbid `feature`, `value`,
`closed_values`, `values`, top-level `edge`, top-level `direction`, and
`interpretation`.

## Why valued=true is not included in I-023

R-007 requires value semantics when an edge is valued. Current execution
results expose node sets plus plan/runtime provenance; they cannot carry a TF
edge value or path-value trace losslessly.

Allowing `valued:true` without a reviewed value-semantics/result contract
would preserve only a storage flag while discarding the information R-007 says
must survive.

Therefore I-023 closes its executable step to `valued:false`. I-024 #252
owns research and productionization of valued-edge source semantics, IR,
results/provenance, filters and composition.

The I-023 executor must additionally verify loaded
`edge_api.doValues is False`; missing, malformed, or true state fails closed.
This protects against source/runtime drift.

## Dependency authority

An executable path must be authorized by the mapping's reviewed
`native_dependencies`.

The first slice requires:

1. exact matching `node-type-present` authority for the top-level start
   `node_type`;
2. exact matching `node-type-present` authority for every
   `result_node_type` in the path;
3. one exact matching `path-present` dependency for the same component and
   ordered `edge + direction` sequence.

The existing P-002 `path-present` dependency contract remains unchanged. It
attests that the ordered directed edge APIs are present; it does not carry
semantic domain or valuedness authority. Those are preserved in the mapping
binding and checked independently.

This avoids silently changing dependency-contract v1.

## Runtime traversal and domain validation

Execution remains over already-loaded APIs only:

1. fresh prerequisite evaluation;
2. fresh resolver plan;
3. `F.otype.s(start_node_type)`;
4. validate start nodes against `F.otype.v`;
5. for each ordered step:
   - obtain the loaded edge API;
   - require `doValues is False`;
   - traverse with `.f` or `.t`;
   - validate every returned node ID;
   - require `F.otype.v(node) == result_node_type`;
   - de-duplicate by first discovery;
6. return the final frontier.

The start selector and Text-Fabric edge calls are canonically ordered, so
first-discovery de-duplication is deterministic without reading undocumented
rank internals directly.

An empty start selector after fresh `node-type-present` authorization is
runtime drift and fails closed, matching I-022 membership.

An empty frontier after one or more traversals is valid: loaded path existence
does not imply reachability for every selected start node.

## Conjunction boundary

I-015 conjunction safety currently uses
`(binding.component_id, binding.node_type)` as the result domain. That is
correct for value predicates and membership but would use the **start** domain
for edge-path.

Once the I-023 step contract carries `result_node_type`, edge-path has an
explicit result domain: the final step's `result_node_type`.

The implementation plan must therefore add one central result-domain helper:

- predicate/membership → `binding.node_type`;
- edge-path → `binding.steps[-1].result_node_type`.

Exact and approximate conjunction may support edge-path only through this
helper. A mixed conjunction whose final result domains differ still fails
closed exactly as I-015 requires.

No endpoint type may be inferred from a real corpus edge inventory at runtime;
the reviewed binding is authoritative.

## Recommended production slice

The implementation plan may authorize:

- extend mapping `edgeStep` and `EdgeStepIR` with required
  `result_node_type` and explicit unvalued state;
- close `edge-path` to
  `component_id + node_type + steps + execution_shape`;
- require all start/intermediate/final node-type dependency authority plus
  matching `path-present` authority;
- support outgoing and incoming unvalued traversal;
- validate every step's loaded `doValues` state and result node domain;
- use stable first-discovery ordering;
- allow empty post-traversal results;
- reuse the executor through exact/approximate semantic and
  authority/identity/identifier surfaces;
- preserve conjunction safety through the explicit final result-domain helper;
- keep `interpretation` / `oslots` non-executable;
- add no Text-Fabric runtime dependency, corpus autoload, network access, or
  production semantic mapping merely for tests.

## Digest/version boundary

Current packaged production mappings contain 48 executable bindings and only
`value-predicate | value-set-predicate`; there are zero packaged structural
bindings. Adding fields to the edge-path-only step shape therefore does not
change any current production native binding identity or mapping/projection
semantic digest.

The implementation plan must nevertheless pin regression tests over all
packaged mapping/projection digests before changing the schema/IR.

## Non-goals

- valued-edge execution: #252;
- path-value filters or path-value result payloads;
- generic graph query language;
- inferred result type from edge names or corpus statistics;
- CRM/CRMtex/POWLA promotion from native structure;
- `oslots` extent semantics;
- caller-created trusted plans;
- corpus acquisition or network dereference.

## Plan handoff

The next PR is plan-only. It must specify exact schema/IR/validation/runtime
changes and the tests-only RED boundary before production implementation.

The implementation PR must prove at minimum:

- schema rejection of shape-only/mixed/one-step-alias paths;
- required `result_node_type` and `valued:false` on every step;
- ORACC `word -> line -> column` outgoing mechanics;
- incoming traversal with explicit result domains;
- BHSA-style multi-domain edge mechanics without inferred semantic meaning;
- TLHdig valued-edge source/runtime rejection;
- matching start/intermediate/final node-type and path dependency authority;
- missing/unloaded/malformed edge fail-closed behavior;
- duplicate/invalid/wrong-domain node handling;
- valid empty post-traversal result;
- stale prerequisite/runtime drift handling;
- unchanged packaged production mapping/projection fingerprints;
- exact/approximate/reference execution reuse;
- conjunction result-domain safety using the final typed step;
- no `oslots`, autoload, network, or Text-Fabric package dependency.
