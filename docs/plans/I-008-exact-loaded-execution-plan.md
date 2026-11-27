# I-008 implementation plan — exact execution against already-loaded TF / Context-Fabric

**Issue:** #143  
**Release tracker:** #142  
**Research:** `docs/research/I-008-exact-loaded-execution.md` + review amendment  
**Baseline:** `main` after merged I-008 research (`5479e6da2d3848f48eaedfc54d689fb1531b250b`)

## 1. Public boundary

Add `src/ontotf/semantic_execution.py` and export only the request-oriented execution surface from `ontotf`.

### Public values

```python
@dataclass(frozen=True)
class LoadedComponentContext:
    component_id: str
    content_digest: str
    api: Any  # excluded from repr/equality where practical; never fingerprinted

@dataclass(frozen=True)
class LoadedCorpusContext:
    corpus_id: str
    parent_manifest_digest: str
    components: tuple[LoadedComponentContext, ...]
    active_ontology_bundle_digest: str | None = None

@dataclass(frozen=True)
class ExactCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plan: ExactNativePlan
    runtime_report: RuntimeEvaluationReport

@dataclass(frozen=True)
class ExactExecutionResult:
    execution_contract: str
    resolution: SemanticResolutionResult
    corpora: tuple[ExactCorpusExecution, ...]

@dataclass(frozen=True)
class ExactExecutionProblem:
    category: str
    message: str
    corpus_id: str | None = None
    component_id: str | None = None

class ExactExecutionError(ValueError):
    problem: ExactExecutionProblem
```

Public callable:

```python
def execute_exact_semantic(
    ir: CompiledSemanticIR,
    request: SemanticResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ExactExecutionResult
```

No public `execute_plan()` or public helper accepting `ExactNativePlan` is added.

`LoadedComponentContext.api` is a runtime handle, not semantic data. It is never placed in a digest, equality/authentication rule, serialized result identity, or plan authorization decision.

## 2. Context normalization and same-component trust rule

Materialize `contexts` once. Validate before runtime evaluation:

- exact `LoadedCorpusContext` type;
- non-empty corpus ID and parent digest;
- exact tuple of `LoadedComponentContext` rows;
- at least one component;
- no duplicate component IDs in one corpus;
- every component ID/content digest is a non-empty exact string;
- API handle is non-null;
- no duplicate corpus contexts.

Extra contexts not named in the request are permitted but ignored after structural validation. Every requested corpus must have exactly one context.

For each requested context, build the I-007 `LoadedTFObservation` internally from the exact same normalized component table:

```python
components = {
    row.component_id: (row.content_digest, row.api)
    for row in context.components
}
observation = LoadedTFObservation(
    parent_manifest_digest=context.parent_manifest_digest,
    components=components,
)
```

Execution later looks up the freshly resolved plan's `component_id` in that same normalized table. There is no API parameter beside the observation and no public prerequisite/report input.

## 3. Variant selection for v0.1

For each requested corpus, inspect `ir.variants` and require exactly one `BundleVariantIR` whose `key.corpus_id` matches.

- zero -> `ExactExecutionError(category="missing_runtime_variant")`;
- more than one -> `ExactExecutionError(category="ambiguous_runtime_variant")`.

Do not rank exact vs compatible variants and do not infer a current release from profile version strings. Multi-variant host selection is post-v0.1 work.

Type/IR validity remains I-005/I-006 authority. `semantic_resolve()` will revalidate the complete compiled IR before producing plans.

## 4. Fresh runtime authorization sequence

For each requested corpus in UTF-16 lexical corpus order:

1. normalize context;
2. select the single corpus variant;
3. construct `LoadedTFObservation` from the context's component table;
4. call `evaluate_runtime_prerequisites()` with:
   - selected variant;
   - internally constructed observation;
   - fixed source contract `tfont-exact-execution-runtime-v1`;
   - context active ontology-bundle digest;
5. retain `RuntimeEvaluationReport` and use `.to_prerequisite()`;
6. after all requested corpora have reports, invoke one `semantic_resolve(ir, request, prerequisites)` call;
7. only after that call succeeds may result-node selection begin.

Do not accept a `RuntimePrerequisiteState`, `RuntimeEvaluationReport`, `ExactNativePlan`, plan fingerprint, or resolution fingerprint from the caller as authorization input.

I-007 can read loaded corpus values while evaluating prerequisites. Tests distinguish those prerequisite reads from result execution by instrumenting `NodeFeature.s()`; no result-selector `s()` call is allowed before I-006 succeeds.

## 5. v0.1 executable binding shape

Private helper `_execute_value_predicate(plan, component_api)` is reachable only from the successful `execute_exact_semantic()` path.

Before touching the feature selector, require the plan's `NativeBindingIR` to satisfy exactly:

- `component_id`: non-empty exact string;
- `node_type`: non-empty exact string;
- `feature`: non-empty exact string;
- `value_present is True`;
- `type(value) is str and value != ""`;
- `execution_shape == "value-predicate"`;
- `closed_values is None`;
- `edge is None`;
- `direction is None`;
- `steps is None`;
- `interpretation is None`.

Otherwise raise `ExactExecutionError(category="unsupported_native_binding")` before `feature.s()`.

This deliberately means the old I-005/I-006 fixture with `execution_shape=None` is not directly executable. I-008 RED fixtures will create explicit executable Noun bundles with `execution_shape: value-predicate`, and the production mapping ticket must do the same.

## 6. Loaded API validation and result selection

For the plan's selected component API:

1. call `api.Fall()`; any exception/malformed return -> `loaded_api_unavailable`;
2. require binding feature in the returned loaded feature set; otherwise `feature_not_loaded`;
3. obtain `api.F.<feature>`, `api.F.otype` without any load call;
4. require callable `feature.s` and `otype.v`;
5. call `feature.s(binding.value)` exactly once;
6. materialize returned nodes once;
7. validate every raw node is an exact positive `int` (not `bool`) and there are no duplicates;
8. for every raw node, call `otype.v(node)`; API exception/malformed type result -> `loaded_api_unavailable`;
9. retain only nodes whose exact type string equals `binding.node_type`;
10. preserve the order returned by `feature.s()`.

Context-Fabric 0.5.7 and Text-Fabric-compatible node features document `s(value)` as canonical-order output, so I-008 does not sort node IDs numerically or invent a second ordering rule.

An empty tuple from `feature.s()`, or a non-empty raw set from which no node has the requested node type, is successful `nodes=()`.

No call to `Fabric.load`, `api.load`, `S.search`, filesystem acquisition, downloader, HTTP, ontology lookup, or generic query string generation is present.

## 7. Result assembly

Match each freshly resolved plan to its exact corpus runtime report and context. Reject any plan corpus not present in the authorized request/report set as `plan_context_mismatch`.

Return:

```text
ExactExecutionResult(
  execution_contract="tfont-exact-execution-v1",
  resolution=<fresh SemanticResolutionResult>,
  corpora=(
    ExactCorpusExecution(
      corpus_id=...,
      nodes=(...),
      plan=<fresh ExactNativePlan>,
      runtime_report=<fresh RuntimeEvaluationReport>,
    ),
    ...
  )
)
```

Sort corpus executions by UTF-16 corpus ID exactly as I-006 does. `resolution.request`, `comparison_state`, `losses`, mapping/projection identity, parent/prerequisite identity, native binding, ontology identity, evidence and review data remain inspectable through the existing immutable plan/report objects.

Do not add a new execution hash in v0.1. The existing resolution/plan/runtime-report/prerequisite fingerprints already identify the semantic/runtime inputs; hashing potentially very large result-node arrays adds cost without an accepted consumer.

## 8. Error boundary

### Preserve existing semantic/runtime error types

Do not wrap:

- `RuntimeEvaluationError` for malformed runtime/variant inputs;
- `SemanticResolutionError` for stale/unverified/incompatible/dependency/capability/mapping failures.

This preserves the current semantic diagnostic categories.

### New execution/context categories

Use `ExactExecutionError` only for executor-owned failures:

- `invalid_execution_context`;
- `duplicate_execution_context`;
- `missing_execution_context`;
- `missing_runtime_variant`;
- `ambiguous_runtime_variant`;
- `unsupported_native_binding`;
- `plan_context_mismatch`;
- `missing_execution_component`;
- `loaded_api_unavailable`;
- `feature_not_loaded`;
- `invalid_result_nodes`.

No partial `ExactExecutionResult` is returned if any corpus execution fails.

## 9. TDD RED structure

Create `tests/i008/` and focused workflow `.github/workflows/i008-exact-execution.yml` before `src/ontotf/semantic_execution.py` exists.

### Fixture controls

Add an I-008 fixture builder derived from existing I-006 Noun sources but explicitly setting `native_binding.execution_shape` and projection `native_execution_binding.execution_shape` to `value-predicate`, then refreshing semantic/review digests before structural + semantic validation and compilation.

Control assertions before RED:

- explicit executable bundles validate for BHSA/Syriac/ExtraBiblical;
- compiled semantic key remains `olia:Noun` / linguistic POS;
- each corpus has one exact binding and one variant;
- every plan binding shape intended for I-008 has `execution_shape == value-predicate`;
- old I-006 regression fixtures remain unchanged.

### Initial public-surface RED

Tests import the intended names from `ontotf` and fail because `semantic_execution` / exports do not exist. Existing I-007/I-006/I-005/I-004 controls remain green.

### Behavioral RED matrix

Before production implementation, tests must encode:

1. BHSA exact request returns only `word` nodes with `sp=subs`;
2. Syriac equivalent;
3. ExtraBiblical equivalent;
4. three-corpus request returns deterministic corpus order, exact resolution state, fresh plan/report objects and expected node tuples;
5. empty native matches return `nodes=()` successfully;
6. same-named feature values on a non-`word` node are excluded;
7. feature result order from the API is preserved rather than numeric-sorted;
8. feature not loaded fails without calling any load method;
9. malformed/raising `Fall`, feature `.s`, or `otype.v` becomes deterministic execution failure;
10. malformed/duplicate result node IDs fail rather than being silently cleaned up;
11. unsupported binding shapes (`execution_shape=None`, edge/path, non-string v0.1 value, extra closed-values/interpretation) fail before result `.s()`;
12. missing planned component fails before result `.s()`;
13. zero/multiple compiled variants fail before I-006/native result access;
14. missing/duplicate/malformed execution contexts fail deterministically;
15. unverified/incompatible/stale prerequisite scenarios reach I-006 and prevent result `.s()`;
16. a second lookalike API object cannot be substituted after runtime evaluation because the public context has one component table;
17. public API has no caller-supplied-plan execution parameter/function;
18. no `cfabric`, `tf`, network, MCP, or search-template import/usage in production module.

### Real Context-Fabric RED/integration

Add a Python 3.13 integration test guarded by import availability. The I-008 workflow's integration job installs a reviewed compatible `context-fabric==0.5.7` and creates a tiny local TF fixture. It preloads `sp`, runs the public executor, and verifies result nodes and absence of hidden autoload behavior.

This test may be added in the same tests-only RED commit. Its pre-GREEN expected failure is missing ontoTF executor surface, not a failing Context-Fabric fixture; fixture setup controls must prove Context-Fabric itself loads and exposes the expected feature API.

## 10. GREEN implementation order

1. public immutable types + context normalization;
2. one-variant selection and internal `LoadedTFObservation` construction;
3. fresh I-007 report generation + one I-006 resolution call;
4. exact binding validator;
5. read-only loaded API execution;
6. result assembly and package exports;
7. concise `docs/exact-execution.md` usage/boundary note only after behavioral GREEN; documentation claims must match tests.

No production code should be committed before the tests-only RED has been observed in hosted CI.

## 11. CI gates

Focused workflow:

- Python 3.10: I-008 unit/contract + I-007/I-006 regressions;
- Python 3.12: same;
- Python 3.13: I-008 real Context-Fabric 0.5.7 integration + unit/contract;
- no duplicate full-suite command inside the focused workflow if repository CI policy already owns it.

Final exact-head gates:

- I-008 focused jobs all green;
- existing I-007, I-006, I-005, I-004 workflows green when triggered;
- authoritative full repository suite green;
- exact final head fresh logically independent adversarial review.

## 12. Adversarial final-review targets

The reviewer must specifically attack:

- forged/caller-created plan or prerequisite bypass;
- observation API != execution API substitution;
- multiple variant ambiguity;
- unsupported binding fields leaking into execution;
- `True == 1` / other scalar coercion expansion;
- cross-node-type feature contamination;
- feature autoload or hidden search/network calls;
- duplicate/malformed node outputs;
- partial multi-corpus success leakage;
- incorrect provenance/report-plan pairing;
- dependency creep that makes Context-Fabric mandatory on Python 3.10-3.12;
- accidental implementation of R-018/approximation/generic query semantics.

Any material repair after final review requires fresh exact-head CI and review.

## 13. Exit condition

I-008 is complete when one public request-oriented call can take current trusted IR plus three already-loaded corpus contexts, freshly establish I-007 state, resolve `olia:Noun` through I-006, execute the exact `word.sp=subs` predicates against the same loaded components, and return actual deterministic node results with inspectable plan/runtime provenance — while stale state, forged plan paths, unloaded features and unsupported binding shapes fail closed.