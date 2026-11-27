# I-008 research — exact execution against already-loaded TF / Context-Fabric

**Issue:** #143  
**Release tracker:** #142  
**Baseline:** `main` after merged I-007 (`4b331cd19ff461a15763894db5ae7f8765a8d4b4`)  
**Type:** production-runtime research gate; no implementation in this document

## Decision

The v0.1.0 executor should be deliberately narrow. It should accept a semantic request plus current trusted `CompiledSemanticIR` and current already-loaded corpus contexts, establish I-007 runtime state itself, call I-006 `semantic_resolve()` in the same process, and execute only the freshly returned exact plans.

The first executable native binding is the one already demonstrated by the R-011 and I-005/I-006 Noun slice:

```text
OLiA Noun
  -> linguistic / linguistic.part-of-speech
  -> exact semantic-pivot projection
  -> word.sp = "subs"
```

for BHSA, ETCBC Syriac, and ETCBC ExtraBiblical.

The v0.1 executor does not accept an `ExactNativePlan` as execution authority. A serialized or hand-constructed plan is outside the public execution entry point. This directly implements the merged R-019 decision that public fingerprints are deterministic identities rather than authentication tokens.

## Evidence inspected

### ontoTF runtime chain

Current `main` now has the whole pre-execution chain:

1. I-004 validates reviewed semantic source bundles.
2. I-005 compiles them into deterministic `CompiledSemanticIR` and reverse indexes.
3. I-006 resolves an exact `SemanticResolveRequest` into `ExactNativePlan` rows after checking current runtime prerequisites.
4. I-007 derives those prerequisites from the observed materialized corpus and selected compiled release.

I-006 selects exactly one fresh prerequisite variant per requested corpus and fails closed on missing, stale, ambiguous, unverified, incompatible, dependency-unavailable, or ontology-bundle-unavailable state. It also fails closed when more than one exact binding survives for a corpus. This is sufficient for the v0.1 single-binding execution slice and deliberately leaves R-018 composition out of scope.

### Exact Noun mappings

R-011 pins the relevant empirical corpus evidence and records the same exact native predicate for all three release corpora:

| corpus | pinned R-011 revision | TF version | reviewed Noun native predicate |
|---|---|---|---|
| BHSA | `4db00e2157915495e1a4d3d57e41223df24775da` | 2021 | `word.sp=subs` |
| ETCBC Syriac | `bb0eaa7e21b020a26b7566d2e495da9b1f84a919` | 0.9 | `word.sp=subs` |
| ETCBC ExtraBiblical | `9a56288e6777bad6328856acf055c780e65dd5d9` | 0.2 | `word.sp=subs` |

R-011 classifies all three as exact `olia:Noun` mappings. The I-005/I-006 fixtures encode the same shape in mapping-v2 as `component_id + node_type=word + feature=sp + value=subs`. Those fixtures use synthetic parent digests and example evidence/ontology resources, so they are test evidence only and must not be promoted verbatim to release data.

### Mapping-v2 execution shape

`mapping.schema.json` permits a `native_execution_binding` to contain `component_id`, `node_type`, `feature`, `value`, and optional `execution_shape`. The current Noun fixture leaves `execution_shape` unset even though P-003 defines `value-predicate` as the intended semantic shape.

For production v0.1 mapping artifacts, set `execution_shape: value-predicate` explicitly. The executor should require that value and the exact minimal field family needed by the release slice rather than infer a generic execution language from arbitrary combinations of optional binding fields.

The first executor therefore accepts only a binding equivalent to:

```text
component_id: non-empty
node_type: non-empty
feature: non-empty
value_present: true
value: non-empty string for the v0.1 slice
execution_shape: value-predicate
closed_values: null
edge/direction/steps/interpretation: null
```

Supporting additional JSON scalar types or other binding shapes can be added by later reviewed tickets when a real released mapping needs them. Restricting v0.1 to the demonstrated string-valued predicate avoids silently inheriting Python equality corner cases such as `True == 1`.

## Context-Fabric / Text-Fabric execution surface

The current Context-Fabric repository was inspected at commit `3a38ca80e617d872ce1664e0f0740486d0e7e8ac`; core package metadata reports Context-Fabric `0.5.7`.

Its loaded API deliberately mirrors Text-Fabric's feature model:

- `api.F.<feature>.v(node)` returns the feature value or `None`;
- `api.F.<feature>.s(value)` returns matching nodes in canonical order;
- `api.F.otype.v(node)` returns the node type;
- `api.F.otype.s(type)` returns nodes of a type in canonical order.

For a v0.1 `value-predicate` plan, `api.F.sp.s("subs")` plus an `api.F.otype.v(node) == "word"` filter is sufficient. This is preferable to generating a Context-Fabric search template: it executes the exact reviewed native predicate directly, avoids a second query compiler, preserves canonical result order, and cannot widen the request through query-language translation.

The executor must first verify that the planned node feature is already loaded. It must never call `Fabric.load()`, API `load()`, a corpus acquisition path, or a network path. Missing/unreadable loaded capabilities produce an explicit execution problem.

## Dependency decision

Do **not** add Context-Fabric as a required ontoTF dependency for I-008.

Current ontoTF supports Python `>=3.10`, while Context-Fabric 0.5.7 declares Python `>=3.13`. Making Context-Fabric a required dependency would unnecessarily drop ontoTF's supported Python 3.10-3.12 validator/compiler/resolver use cases.

I-008 should use a small structural/duck-typed loaded-API protocol and no import from `cfabric` or `tf`. A real Context-Fabric integration smoke can run separately on Python 3.13. Release packaging may later add an optional execution extra if that improves installation UX, but the executor contract does not require one.

## Trusted execution entry point

The public v0.1 API should be request-oriented, not plan-oriented. Conceptually:

```text
execute_exact(
    ir=current trusted CompiledSemanticIR,
    request=SemanticResolveRequest,
    corpora=current already-loaded runtime contexts,
) -> ExactExecutionResult
```

Each per-corpus runtime context should bind together:

- corpus ID;
- the I-007 `RuntimeObservation` over the currently selected materialized corpus;
- the already-loaded API object used for execution;
- active ontology-bundle digest when required.

The same context is used for prerequisite evaluation and native execution. This avoids evaluating one corpus/API and executing against a different one by accident.

The implementation should normalize the contexts into immutable/private runtime records before evaluation. Local API object identity, path, session, host, user, and timestamps are not part of semantic/result fingerprints.

## Variant policy for v0.1

Do not invent a general variant resolver in I-008.

The release mapping set will publish exactly one current compiled variant for each of the three v0.1 corpora. For each requested corpus, the executor should require exactly one `BundleVariantIR` in the supplied trusted IR:

- zero variants -> explicit missing-runtime-variant problem;
- more than one -> explicit ambiguous-runtime-variant problem;
- exactly one -> run I-007 against that variant.

This is intentionally stricter than a future multi-version host. It prevents the executor from guessing among historical/current variants or treating `verified-compatible` as a selection ranking. A later release can add explicit host-selected variant semantics when there is a real multi-version deployment case.

## Execution sequence

For each requested corpus, in deterministic corpus order:

1. validate one runtime context exists and no duplicate corpus contexts are present;
2. select the only compiled variant for that corpus; fail on zero/multiple;
3. call I-007 `evaluate_runtime_prerequisites()` against that context's observation and active ontology bundle;
4. retain the resulting `RuntimeEvaluationReport` and convert it to `RuntimePrerequisiteState`;
5. after all requested corpora are evaluated, call I-006 `semantic_resolve()` once with the current trusted IR, canonical request, and the freshly produced prerequisites;
6. execute only the plans returned by that invocation;
7. for each plan, locate the exact context/corpus and exact `component_id`, verify the already-loaded feature API is available, require the v0.1 `value-predicate` binding shape, obtain `feature.s(value)`, filter by `F.otype.v(node) == node_type`, and preserve canonical order;
8. return immutable per-corpus results plus explanation/provenance.

No native API call used to collect result nodes occurs before steps 3-5 authorize the request. I-007 may inspect loaded corpus features as prerequisite evidence; that is prerequisite evaluation, not semantic result execution.

## Result contract

The first result should keep result payload and explanation together without copying the whole plan graph. Minimum per-corpus execution record:

- corpus ID;
- result node tuple;
- plan fingerprint;
- resolution fingerprint;
- I-007 report fingerprint;
- prerequisite fingerprint;
- variant / expected and observed parent identities;
- mapping ID and projection ID;
- mapping/projection semantic digests;
- native binding identity and a compact native binding projection;
- ontology lock/bundle identity;
- exact assessment and semantic target.

The top-level result retains the canonical semantic request, comparison state (`exactly-comparable` for this slice), losses (empty), and deterministic corpus ordering.

A result fingerprint may be useful for reproducible explanation/caching, but it must not include local API object identity or volatile host/session data and must never be described as execution authorization.

## Failure model

Keep semantic authorization failures from I-006/I-007 distinct from native execution failures.

Fail before result-node access for:

- missing/duplicate runtime context;
- zero or multiple compiled variants for a requested corpus;
- I-007 invalid/stale/unverified/incompatible/dependency/bundle state;
- I-006 capability/mapping/semantic-resolution failure;
- plan/context corpus mismatch;
- unsupported or malformed native execution binding;
- component absent from the selected context;
- planned feature not already loaded or API methods unavailable.

An empty set of matching nodes is a successful execution with `nodes=()`. Runtime compatibility says that the reviewed predicate can be executed; it does not promise the current corpus contains at least one result unless the dependency contract itself asserts that value.

Native API exceptions should be contained as deterministic execution problems rather than leaking arbitrary exceptions as successful partial output.

## Forged-plan adversarial case

I-008 should not expose `execute_plan(plan, api)` as its primary production surface. Its public request execution path never accepts a caller-supplied plan, so a forged `ExactNativePlan` has no path to native execution.

A test should construct a syntactically valid lookalike plan with a recomputable public fingerprint and demonstrate that the production executor has no plan-authority input path. If an internal helper executes one plan, it must be private and called only with plans freshly returned inside `execute_exact()` after I-007 + I-006.

This is simpler and stronger than duplicating all I-006 plan-equivalence validation in a second public API.

## Real Context-Fabric integration gate

Unit tests should use a minimal loaded-API double to drive RED/GREEN deterministically on Python 3.10 and 3.12 without adding Context-Fabric as a core dependency.

Before final I-008 merge, add a focused integration smoke on Python 3.13 against Context-Fabric 0.5.7 (or the then-current reviewed compatible 0.5.x release) that proves the exact loaded feature API used by the executor:

- build/load a tiny local TF fixture through Context-Fabric;
- pre-load `otype` and the test feature;
- execute one `value-predicate` plan through the public request-oriented executor;
- assert canonical result nodes and no hidden feature load/network behavior.

The release-candidate gate later repeats the same path against the three actual v0.1 corpora.

## Production mapping handoff

I-008 does not turn `tests/i005/_fixtures.py` into release mappings. #142 separately requires production artifacts using the R-011 pinned corpus revisions and reviewed evidence.

Those production mappings should make the executable shape explicit (`execution_shape: value-predicate`) and must replace fixture-only parent hashes, example ontology/evidence URIs, reviewer metadata, and placeholder provenance with release-grade values. I-008 should be developed so those artifacts plug into validation -> compile -> runtime evaluation -> resolution -> execution without another executor redesign.

## Rejected alternatives

### Execute caller-supplied `ExactNativePlan`

Rejected for v0.1. It recreates the R-019 authentication problem and forces a second implementation of I-006 authorization equivalence.

### Use `api.S.search()` / generate Context-Fabric templates

Rejected for the Noun slice. The reviewed plan is one exact node-feature value predicate; translating it into another query language adds semantics and failure modes without value.

### Add `context-fabric` as a required dependency

Rejected because Context-Fabric 0.5.7 currently requires Python >=3.13 while ontoTF intentionally supports >=3.10, and the needed loaded API can be expressed structurally without importing the package.

### Implement all mapping-v2 native binding shapes now

Rejected. Only `value-predicate` is needed for the v0.1 released semantic slice. Edge paths, membership, identity keys, closed-domain predicates, and inspection-only semantics should arrive with concrete production mappings and their own TDD evidence.

### General compatible-variant ranking

Rejected for v0.1. One release variant per corpus is enough; guessing among multiple compatible variants would be new package-manager/runtime policy.

## Plan inputs

The I-008 plan should freeze:

- request-oriented public API and immutable result/problem types;
- one-variant-per-corpus v0.1 rule;
- one context object binding observation + loaded API + active bundle;
- I-007-before-I-006-before-native-access ordering;
- exact `value-predicate` binding validator;
- canonical matching algorithm and empty-result semantics;
- deterministic explanation/result fingerprints;
- Python 3.10/3.12 unit RED matrix and Python 3.13 real Context-Fabric integration smoke;
- explicit exclusion of caller-supplied plan execution, autoload, network access, generic query language, R-018 composition, approximation, and non-semantic resolver families.

## Research conclusion

I-008 can complete the first real ontoTF product slice without adding a query engine or coupling ontoTF core to Context-Fabric. The narrow safe implementation is:

```text
current trusted IR
+ exact semantic request
+ already-loaded per-corpus runtime contexts
        ↓
fresh I-007 evaluation
        ↓
I-006 exact resolution
        ↓
private value-predicate execution via loaded F/otype APIs
        ↓
deterministic nodes + semantic/runtime provenance
```

That is sufficient for `olia:Noun` across the three release corpora and leaves broader execution semantics for post-v0.1 work.