# Exact execution against already-loaded corpora

ontoTF's first execution surface resolves a reviewed shared semantic request and runs the resulting exact native predicate against corpus APIs that the host has already loaded.

The public entry point is:

```python
from ontotf import execute_exact_semantic

result = execute_exact_semantic(ir, request, contexts)
```

`ir` is the current trusted `CompiledSemanticIR`. `request` is a `SemanticResolveRequest`. Each `LoadedCorpusContext` supplies the current parent-manifest identity plus a tuple of `LoadedComponentContext` objects that bind component identity, observed content identity, and the already-loaded TF/Context-Fabric-compatible API object.

The executor establishes runtime state itself. It builds I-007 observations from those exact component contexts, evaluates the selected compiled release, calls the I-006 exact resolver, and only then reads result nodes through the freshly resolved native binding. Callers do not supply prerequisite attestations or executable plans.

For v0.1 the only executable native binding shape is an explicit string-valued `value-predicate`, for example:

```text
component_id = bhsa-tf
node_type = word
feature = sp
value = subs
execution_shape = value-predicate
```

Execution uses the already-loaded node-feature API directly: `F.<feature>.s(value)` followed by exact node-type filtering with `F.otype.v(node)`. It does not generate a search template or call `S.search()`.

The result keeps the actual node IDs together with the fresh `ExactNativePlan` and `RuntimeEvaluationReport`, so the semantic target, mapping/projection, parent identity, prerequisites, ontology identity, and native predicate remain inspectable.

## Runtime boundary

ontoTF does not load or acquire corpora in this path. The requested feature must already be loaded. Missing or changed runtime state fails closed; there is no feature autoload, network access, ontology dereferencing, source-format ingestion, or MCP-specific transport in the executor.

The Context-Fabric package is not a required ontoTF dependency. ontoTF uses the compatible loaded API structurally, which keeps validator/compiler/resolver use available on Python 3.10-3.12 while current Context-Fabric integration is exercised separately on Python 3.13.

## Current limitations

The v0.1 execution slice intentionally does not implement approximate mappings, multiple same-corpus exact bindings, edge/path execution, identity-key execution, generic boolean query planning, or caller-supplied serialized plan execution. Public plan and report fingerprints are deterministic content identities, not authorization tokens.
