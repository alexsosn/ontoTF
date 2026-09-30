# I-020 plan — productionize approximate semantic resolution and execution

Issue: #224  
Parent: P-004 #202, Workstream B  
Research: `docs/research/I-020-approximate-resolution-execution.md`  
Policy dependency: R-016 #50  
Baseline: main `30c2469cd255fe8231ad34eda59e1c19ac18b814`

## Exit condition

ontoTF exposes a production approximate semantic resolver/executor for the
already-reviewed approximation metadata carried by semantic mappings.

The implementation:

- executes `exact` mappings with no semantic loss when they exist;
- otherwise permits only review-authorized `broader`, `narrower`, or
  `close` mappings;
- requires the caller to explicitly accept every required loss token;
- reports deterministic direction-specific loss records;
- supports single semantic atoms and the existing required-conjunction shape;
- preserves per-corpus comparison state across multi-corpus requests;
- freshly revalidates loaded runtime prerequisites before execution;
- refuses `related`, `native-only`, `unsupported`, ambiguous or
  multiply-authorized substitutions;
- never uses ontology hierarchy traversal as execution authority.

The existing exact resolver/executor API, contract constants, result types and
fingerprints remain unchanged.

No new ontology mappings, source schema, compiled-IR schema, corpus data or
structural edge/path execution is introduced by I-020.

## Compatibility boundary

I-020 is additive.

Do not change the public shape or semantics of:

- `SemanticResolveRequest`;
- `ExactNativePlan`;
- `SemanticResolutionResult`;
- `SemanticConjunctionRequest`;
- `SemanticConjunctionResolutionResult`;
- `semantic_resolve()`;
- `semantic_resolve_conjunction()`;
- `ExactCorpusExecution`;
- `ExactExecutionResult`;
- `ExactConjunctionCorpusExecution`;
- `ExactConjunctionExecutionResult`;
- `execute_exact_semantic()`;
- `execute_exact_conjunction()`;
- any existing exact v1 contract or fingerprint constant.

The exact fingerprints frozen by I-020 research are regression anchors:

- BHSA exact plan:
  `sha256:a7dc2b0d8e234a7df399fed88c2af79aee0653f2233a1b15f68c9022a8f44616`;
- BHSA exact resolution:
  `sha256:90b87e1b4f59c3a53338b8ff952c7a1088905f78d25e46adf0d191a904435cfc`;
- BHSA exact execution resolution:
  `sha256:79b604c59a37759149f3d0836e9209e49ec609cadbcf61fc2a148d6e4c6466fc`;
- three-corpus exact resolution:
  `sha256:024fceafaca2ff36ebb6f52953b32ae5ac36956d70ecb93e66facab67957a5c7`;
- exact Noun+Plural conjunction resolution:
  `sha256:2f4b11335365b24adf8910c28a854dda5b0c99f702b38ad528a5b4c10a7054ca`.

## Public resolver contracts

Add to `src/tfont/semantic_resolver.py` and export from package root:

```python
APPROXIMATE_RESOLVER_CONTRACT = "tfont-approximate-semantic-resolver-v1"
APPROXIMATE_PLAN_FINGERPRINT_ALGORITHM = (
    "tfont-approximate-native-plan-jcs-sha256-v1"
)
APPROXIMATE_RESOLUTION_FINGERPRINT_ALGORITHM = (
    "tfont-approximate-resolution-jcs-sha256-v1"
)
APPROXIMATE_CONJUNCTION_RESOLVER_CONTRACT = (
    "tfont-approximate-semantic-conjunction-resolver-v1"
)
APPROXIMATE_CONJUNCTION_RESOLUTION_FINGERPRINT_ALGORITHM = (
    "tfont-approximate-conjunction-resolution-jcs-sha256-v1"
)
```

### ApproximateSemanticResolveRequest

Add an immutable dataclass:

```python
ApproximateSemanticResolveRequest(
    key: SemanticKey,
    corpora: tuple[str, ...],
    semantic_mode: str = "approximate",
    accept_losses: tuple[str, ...] = (),
)
```

Canonical request rules:

- exact type must be `ApproximateSemanticResolveRequest`;
- `semantic_mode` must be exactly `"approximate"`;
- key vocabulary validation is identical to the exact resolver;
- corpora must be a non-empty exact tuple of unique non-empty strings;
- corpora canonicalize by the existing UTF-16 ordering;
- `accept_losses` must be an exact tuple;
- every accepted loss must be an exact string in `LOSS_TOKENS`;
- duplicate accepted losses fail;
- accepted losses canonicalize by UTF-16 ordering.

Do not accept host-language truthiness, lists, sets, unknown/future loss tokens,
or duplicate loss tokens.

Request-shape validation precedes runtime prerequisite lookup.

### ApproximationLossRecord

Add an immutable dataclass with these fields:

```python
ApproximationLossRecord(
    corpus_id: str,
    semantic_key: SemanticKey,
    mapping_id: str,
    projection_id: str,
    assessment: str,
    native_execution_binding_identity: str,
    losses: tuple[str, ...],
    effects: tuple[str, ...],
    approximation_review_id: str,
    caller_accepted_losses: tuple[str, ...],
    mapping_semantic_digest: str,
    projection_semantic_digest: str,
    prerequisite_fingerprint: str,
    prerequisite_source_contract: str,
)
```

Effects are deterministic runtime vocabulary, not caller text:

- `undercoverage` ->
  `native selector may miss members of the requested semantic target`;
- `overcoverage` ->
  `native selector may include members outside the requested semantic target`.

The order of losses/effects is canonical by loss token.

### ApproximateNativePlan

Add a separate immutable plan type. It carries the same execution/release
provenance needed by `ExactNativePlan`, but uses the approximate contract and
adds:

- `approximation: ApproximationIR | None`;
- `losses: tuple[str, ...]`;
- `loss_record: ApproximationLossRecord | None`.

An exact binding selected through an approximate request has:

- assessment `exact`;
- `approximation=None`;
- `losses=()`;
- `loss_record=None`.

A non-exact binding has a validated reviewed `ApproximationIR`, non-empty
losses, and one loss record.

The approximate plan is the output of the resolver only. There is no public
API that executes a caller-supplied plan.

### ApproximateSemanticResolutionResult

Add:

```python
ApproximateSemanticResolutionResult(
    resolver_contract: str,
    request: ApproximateSemanticResolveRequest,
    plans: tuple[ApproximateNativePlan, ...],
    comparison_state: str,
    losses: tuple[str, ...],
    loss_records: tuple[ApproximationLossRecord, ...],
    resolution_fingerprint: str,
)
```

Plans and loss records canonicalize by corpus ID.

Top-level `losses` is the canonical set union of plan losses.

## Approximation authority validation

The source validator already owns author-time validation. I-020 additionally
defends the runtime boundary because callers can manually construct/replace
public compiled dataclasses.

Add an internal validator for `TargetBindingIR.approximation`.

For assessment `exact` or `related`:

- approximation must be `None`;
- a forged approximation envelope is `invalid_compiled_ir`.

For `close|broader|narrower`:

- `None` is valid but not execution-authorized;
- if present it must be exact `ApproximationIR`;
- status must be exactly `reviewed`;
- eligible must be an exact bool;
- losses must be an exact tuple;
- every loss must be in `LOSS_TOKENS`;
- losses must be unique and canonically ordered;
- rationale and review ID must be non-empty strings;
- evidence must be an exact tuple of `EvidenceFingerprint` values;
- evidence fingerprints must pass the existing evidence projection validation.

When `eligible=True`:

- `broader` losses must be exactly `("undercoverage",)`;
- `narrower` losses must be exactly `("overcoverage",)`;
- `close` losses must be non-empty.

Malformed compiled approximation metadata fails `invalid_compiled_ir`; it is
never downgraded to an ordinary “not authorized” result.

Structural validation alone is insufficient because a caller can replace a
well-formed `ApproximationIR` while leaving the old reviewed
`projection_semantic_digest` on the binding. Before treating approximation
metadata as authority, reconstruct the projection semantic payload from the
selected `TargetBindingIR` fields and require
`projection_semantic_digest_v1(reconstructed_projection)` to equal
`binding.projection_semantic_digest`.

The reconstruction must use the same source semantics as the compiler/digest
contract:

- projection identity, target/routing/formal/semantic/profile/capability fields;
- assessment and ontology-lock ID;
- native execution binding;
- projection evidence;
- optional ontology-bundle requirement/declaration;
- optional publication relation;
- optional approximation envelope;
- audit-only review metadata may be omitted exactly as the semantic digest
  projection omits it.

Optional fields must remain absent when the compiled value is `None`; adding
JSON null would change the reviewed semantic projection.

A structurally valid but digest-incoherent replacement of `eligible`,
`losses`, rationale, review ID or approximation evidence is therefore
`invalid_compiled_ir`.

Do not re-read source JSON or ontology documents at runtime.

## Single-atom selection algorithm

Add:

`semantic_resolve_approximate(ir, request, prerequisites)`.

It reuses the exact resolver's existing internal validation for:

- IR shape;
- prerequisite materialization and variant selection;
- prerequisite coherence/freshness;
- capability state;
- semantic-key routing;
- binding/release/review/digest coherence.

For each requested corpus:

1. Run existing prerequisite and capability checks with the same precedence as
   exact resolution.
2. Require a semantic tuple for the selected variant.
3. Run `_validate_binding_against_release()` for every candidate.
4. Defensively validate approximation coherence for **every** candidate before
   selection. This includes requiring `approximation=None` on `exact` and
   `related` rows. A forged approximation anywhere in the selected semantic
   tuple is `invalid_compiled_ir`, even when a clean exact row would otherwise
   win.
5. Collect exact bindings.
6. If more than one exact binding exists, fail
   `multiple_exact_bindings`.
7. If exactly one exact binding exists, select it immediately with no loss.
   Approximate alternatives are not used to degrade an exact mapping.
8. Otherwise classify non-exact candidates:
   - `related` is non-substitutive;
   - `close|broader|narrower` may be approximation candidates.
9. If there are no `close|broader|narrower` candidates but one or more
   `related` candidates, fail `non_substitutive_mapping`.
10. From `close|broader|narrower`, select mappings whose approximation is
    present, reviewed and `eligible=True`.
11. If none are authorized, fail `approximation_not_authorized`.
12. If more than one is authorized, fail
    `multiple_approximate_bindings`.
    Caller loss acceptance is not a candidate-selection mechanism; R-018 owns
    same-key composition/ambiguity.
13. For the single authorized candidate, require every reviewed loss token to
    occur in canonical `request.accept_losses`.
14. If any required token is absent, fail
    `approximation_loss_not_accepted`.
15. Build the approximate plan and loss record.

No ontology traversal, label matching, fallback target search, candidate scoring
or binding ordering may choose an approximate mapping.

## Error categories and precedence

Reuse all existing exact request/prerequisite/capability/release categories
where the same condition applies.

Add resolver categories:

- `invalid_loss_acceptance` — accepted-loss container is not the exact
  contract or contains duplicates;
- `unknown_loss_token` — an accepted loss is outside the runtime vocabulary;
- `non_substitutive_mapping` — semantic tuple exists only through
  non-substitutive `related` projection(s);
- `approximation_not_authorized` — substitutive-strength candidate exists but
  no candidate has reviewed eligible approximation authority;
- `approximation_loss_not_accepted` — exactly one authorized mapping exists
  but caller did not accept all required losses;
- `multiple_approximate_bindings` — more than one reviewed eligible
  approximate binding exists for the same corpus/key.

Malformed compiled approximation metadata uses existing
`invalid_compiled_ir`.

Precedence:

1. request shape/vocabulary, including accepted-loss validation;
2. IR structural validation;
3. prerequisite/variant checks;
4. capability checks;
5. semantic tuple and binding/release coherence;
6. exact binding multiplicity/selection;
7. non-exact approximation authority;
8. caller loss acceptance.

A stale/blocked runtime prerequisite therefore remains authoritative over a
valid request's mapping-level approximation refusal.

## Comparison state

For each successful corpus plan define its loss shape as its exact
`plan.losses` tuple.

Result comparison state:

- all loss shapes empty -> `exactly-comparable`;
- all non-empty shapes are identical, with any number of exact corpora mixed in
  -> `approximately-comparable`;
- two or more distinct non-empty shapes ->
  `heterogeneous-loss`.

A required corpus failure aborts the resolution. I-020 never returns a silently
partial successful plan set.

## Fingerprints

Approximate fingerprints use canonical JSON and new algorithms.

### Plan fingerprint payload

Include at least:

- algorithm and resolver contract;
- corpus ID and semantic key;
- reference/query routing;
- semantic mode;
- capability/release/parent/prerequisite provenance;
- mapping/projection identity;
- assessment;
- native execution binding identity;
- native dependencies;
- mapping/projection semantic digests;
- review/ontology/evidence provenance;
- approximation projection or null;
- plan losses;
- loss record projection or null.

For a non-exact plan the loss record includes canonical
`caller_accepted_losses`, so authorization state is fingerprint-bound.

For an exact fallback plan, irrelevant accepted losses are not part of the plan
fingerprint because no approximation authorization was consumed.

### Resolution fingerprint payload

Include:

- algorithm and resolver contract;
- canonical request key/corpora/mode;
- canonical full `accept_losses`;
- comparison state;
- top-level losses;
- canonical loss-record projections;
- plan fingerprints.

Thus two approximate requests with different accepted-loss permissions have
different resolution fingerprints even when an exact binding makes their
native plan identical.

## Approximate conjunction resolver

Add immutable:

```python
ApproximateSemanticConjunctionRequest(
    keys: tuple[SemanticKey, ...],
    corpora: tuple[str, ...],
    semantic_mode: str = "approximate",
    accept_losses: tuple[str, ...] = (),
)
```

and:

```python
ApproximateSemanticConjunctionResolutionResult(
    resolver_contract: str,
    request: ApproximateSemanticConjunctionRequest,
    resolutions: tuple[ApproximateSemanticResolutionResult, ...],
    comparison_state: str,
    losses: tuple[str, ...],
    loss_records: tuple[ApproximationLossRecord, ...],
    resolution_fingerprint: str,
)
```

Add:

`semantic_resolve_approximate_conjunction()`.

Contract:

- at least two unique semantic keys;
- canonical key ordering uses existing semantic-key projection ordering;
- corpus/loss request validation matches single-atom approximate resolution;
- every required atom resolves through the approximate resolver;
- no required atom is dropped;
- any atom failure fails the whole conjunction;
- top-level losses are the union of constituent losses;
- loss records preserve every non-exact constituent/corpus record.

For comparison, first union all atom loss tokens per corpus, then apply the
same exact/uniform/heterogeneous multi-corpus rule.

The conjunction fingerprint includes canonical request acceptance and all
constituent resolution fingerprints/loss records.

## Execution contracts

Add to `src/tfont/semantic_execution.py` and export:

```python
APPROXIMATE_EXECUTION_CONTRACT = "tfont-approximate-execution-v1"
APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT = (
    "tfont-approximate-execution-runtime-v1"
)
APPROXIMATE_CONJUNCTION_EXECUTION_CONTRACT = (
    "tfont-approximate-semantic-conjunction-execution-v1"
)
```

Add immutable result types:

- `ApproximateCorpusExecution`;
- `ApproximateExecutionResult`;
- `ApproximateConjunctionCorpusExecution`;
- `ApproximateConjunctionExecutionResult`.

Add a separate public approximate execution error surface:

```python
ApproximateExecutionProblem(
    category: str,
    message: str,
    corpus_id: str | None = None,
    component_id: str | None = None,
)

class ApproximateExecutionError(ValueError):
    problem: ApproximateExecutionProblem
```

Do not expose `ExactExecutionError` from the new approximate public
functions. Private exact execution helpers may be reused, but if they raise an
`ExactExecutionError` inside an approximate call, translate it at the
approximate API boundary while preserving category, message, corpus ID and
component ID exactly. Do not change the existing exact error/result classes or
their behavior.

Corpus execution rows include fresh runtime report plus the fresh approximate
plan(s). Approximate result objects retain the full resolution and therefore
all loss records.

### execute_approximate_semantic()

Input is:

- compiled IR;
- `ApproximateSemanticResolveRequest`;
- loaded corpus contexts.

Algorithm mirrors I-008:

1. validate requested execution contexts;
2. select variants;
3. freshly call `evaluate_runtime_prerequisites()` against loaded contexts
   with `APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT`;
4. convert fresh reports to prerequisite states;
5. call `semantic_resolve_approximate()`;
6. execute only the returned fresh plan;
7. return nodes, fresh runtime report, plan and full loss-bearing resolution.

No function accepts an `ApproximateNativePlan` from the caller.

Native execution in I-020 remains restricted to:

- `value-predicate`;
- `value-set-predicate`.

Reuse/refactor existing private native predicate validation/execution helpers
without changing exact external behavior.

Unsupported structural shapes continue to fail
`unsupported_native_binding`.

### execute_approximate_conjunction()

Mirror I-015:

1. fresh runtime evaluation once per requested corpus;
2. fresh approximate conjunction resolution;
3. require every atom plan for a corpus to share one explicit
   `(component_id, node_type)` domain;
4. execute every plan;
5. intersect node sets within each corpus;
6. require one plan per required atom/corpus;
7. return canonical corpus rows with plans and runtime reports.

The existing node-domain failure category remains
`incompatible_conjunction_node_domain`; error text may be made
exact/approximation-neutral only if exact tests remain unchanged.

## No approximate aggregate API

The current TFont runtime has no aggregate/statistics execution surface.

I-020 does not add one.

A future aggregate layer remains exact-only until it separately implements the
R-016 rule that approximate aggregation requires explicit opt-in and uniform
non-empty loss shape. Heterogeneous-loss aggregation is outside I-020.

## TDD RED

After this plan is independently reviewed and merged, create a dedicated
implementation branch and add `tests/i020/` before any production changes.

The tests-only RED must require the new public constants/types/functions and
cover at least:

### Request and single-atom resolution

1. reviewed eligible `broader` + accepted undercoverage resolves;
2. same broader mapping without accepted undercoverage fails
   `approximation_loss_not_accepted`;
3. reviewed eligible `narrower` + accepted overcoverage resolves;
4. reviewed `close` with undercoverage, overcoverage and both-direction loss
   works only with complete caller acceptance;
5. eligible false and missing approximation both fail
   `approximation_not_authorized`;
6. `related` fails `non_substitutive_mapping`;
7. exact binding wins over approximate alternatives and has no loss record;
8. multiple exact bindings retain `multiple_exact_bindings`;
9. multiple reviewed eligible approximate bindings fail
   `multiple_approximate_bindings`;
10. native-only has no common semantic tuple;
11. unsupported remains capability-absent.

### Request validation precedence

12. non-tuple accepted losses fail `invalid_loss_acceptance`;
13. duplicate accepted losses fail `invalid_loss_acceptance`;
14. unknown accepted loss fails `unknown_loss_token`;
15. those request failures occur even if prerequisites are absent/stale;
16. with a structurally valid request, stale/blocked prerequisite failure occurs
    before mapping-level approximation refusal.

### Defensive IR validation

17. manually replaced wrong approximation type fails
    `invalid_compiled_ir`;
18. forged status/eligibility/loss vocabulary/direction fails
    `invalid_compiled_ir`;
19. a structurally valid replacement of eligible/losses/rationale/review ID or
    approximation evidence that no longer matches the reviewed projection
    semantic digest fails `invalid_compiled_ir`;
20. approximation attached to any exact or related row in the selected semantic
    tuple fails `invalid_compiled_ir` before exact/approximate selection, even
    when another clean exact row exists;
21. malformed approximation evidence fails closed.

### Loss records and comparison

22. broader loss record contains undercoverage and deterministic effect;
23. narrower loss record contains overcoverage and deterministic effect;
24. record binds review ID, caller acceptance, digests and prerequisite
    fingerprint;
25. corpus order and accepted-loss order do not change canonical result;
26. all-exact approximate request -> `exactly-comparable`;
27. exact + same undercoverage across corpora ->
    `approximately-comparable`;
28. undercoverage in one corpus and overcoverage in another ->
    `heterogeneous-loss`.

### Conjunction

29. exact + broader required atoms union to undercoverage;
30. broader + narrower union to both loss tokens;
31. a refused atom fails the whole conjunction;
32. per-corpus intersection preserves I-015 node-domain safety;
33. mixed exact/approximate conjunction execution returns deterministic
    intersections and retains constituent loss records.

### Fresh runtime execution

34. approximate execution re-evaluates runtime prerequisites against loaded
    APIs;
35. stale/mutated loaded state refuses before native query execution;
36. there is no public caller-plan execution path;
37. scalar and finite-set bindings execute; structural shapes remain refused;
38. approximate execution failures use `ApproximateExecutionError`, while
    translated shared-helper failures preserve their exact category/context.

### Exact compatibility

39. all exact fingerprint anchors in
    `docs/research/data/generated/i020/runtime-reconciliation.json` remain
    exact;
40. existing exact resolver/executor/conjunction tests remain green;
41. exact public contract constants remain unchanged.

The RED commit must be observed failing on exact head before GREEN production
changes.

## Implementation scope

Expected production files:

- `src/tfont/semantic_resolver.py`;
- `src/tfont/semantic_execution.py`;
- `src/tfont/__init__.py`;
- `tests/i020/**`;
- `.github/workflows/i020-approximate-execution.yml`.

A small private helper extraction inside the two semantic runtime modules is
allowed when it prevents divergence between exact and approximate execution.

No expected changes to:

- semantic source schemas;
- `semantic_ir.py`;
- semantic digest algorithms;
- semantic validation/policy behavior;
- production mapping resources;
- ontology resources;
- corpus coverage manifests;
- runtime prerequisite contracts;
- production linguistic bundles.

If implementation discovers a need to change any of those, stop and amend this
plan before the production change.

## Focused CI

Add exact-head Python 3.10/3.12 CI that:

1. installs the package;
2. runs `tests/i020`;
3. reruns current I-006 exact resolver contract tests;
4. reruns I-008 exact execution tests;
5. reruns I-015 exact conjunction tests;
6. executes the I-020 research reconciliation script and compares it to the
   committed evidence;
7. builds a wheel and imports the new public approximate API from the isolated
   wheel.

The authoritative Full repository suite must pass on the final exact head.

## Final adversarial review

Fresh logically-independent review of the implementation exact head must
challenge:

- exact API/fingerprint immutability;
- request-validation precedence;
- broader/narrower direction semantics;
- close loss authorization;
- defensive forged-`ApproximationIR` handling;
- runtime reconstruction of the reviewed projection digest so structurally valid
  approximation replacements cannot become authority;
- exact-before-approximate selection;
- multiple-approximate fail-closed behavior pending R-018;
- related/native-only/unsupported/ambiguous boundaries;
- caller loss acceptance binding;
- deterministic loss records and comparison states;
- conjunction loss union and node-domain safety;
- fresh runtime revalidation before execution;
- approximate execution error typing/translation without leaking
  `ExactExecutionError` from the approximate API;
- absence of caller-plan trust;
- absence of ontology reasoning/hierarchy traversal;
- absence of mapping promotion or structural execution scope creep.

Merge only with the reviewed exact head SHA. After merge, run/read back an
authorized broader fixture and an exact compatibility fixture from `main`,
then close #224.
