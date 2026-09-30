# I-020 research — reconcile approximate resolution/execution with current runtime

Issue: #224  
Parent: P-004 #202, Workstream B  
Research dependency: R-016 #50  
Baseline: main `6efdb106aaf81f349c1b238344b3a195c2c9bd5f`  
Status: research complete; ready for independently reviewed plan

## Question

What is the smallest production change that can implement the reviewed R-016
approximate execution policy without weakening the exact resolver/executor
contracts shipped by I-006, I-008 and I-015?

The current runtime already carries and validates the mapping-level
approximation contract all the way into compiled IR. Production work is missing
only the request/selection/fingerprint/result/execution surface for using that
contract.

No semantic source schema migration and no compiled-IR schema migration are
required.

## Executable reconciliation evidence

The exact-head probe is:

`scripts/research/i020_runtime_reconciliation.py`

and its committed output is:

`docs/research/data/generated/i020/runtime-reconciliation.json`.

The research workflow runs the probe on Python 3.10 and 3.12 and reruns the
current exact resolver, exact executor and exact conjunction guardrails.

At the I-020 baseline the probe demonstrates:

- exact single-corpus resolver contract:
  `tfont-exact-semantic-resolver-v1`;
- exact execution contract:
  `tfont-exact-execution-v1`;
- exact conjunction resolver/execution contracts remain v1;
- the exact BHSA noun control resolves with zero losses and executes nodes
  `[1, 3]`;
- the exact three-corpus noun control canonicalizes plans as
  `bhsa, extrabiblical, syriac`, remains `exactly-comparable`, and reports
  zero losses;
- the exact control fingerprints are frozen in the generated evidence;
- a validated reviewed/eligible `broader` projection reaches
  `TargetBindingIR.approximation` intact;
- exact resolution of that projection fails as `non_exact_mapping`;
- asking the current resolver for `semantic_mode="approximate"` fails as
  `unsupported_semantic_mode`.

This is the intended pre-I-020 state.

## What is already productionized

### Mapping/source validation

`semantic_policy_validation.py` already validates the R-016 envelope.

An approximation may exist only on:

- `close`;
- `broader`;
- `narrower`.

The envelope already requires:

- `status == "reviewed"`;
- exact boolean `eligible`;
- closed loss vocabulary;
- non-empty rationale;
- non-empty review ID;
- no duplicate loss tokens.

Eligible direction rules are already enforced:

- `broader` -> exactly `undercoverage`;
- `narrower` -> exactly `overcoverage`;
- eligible `close` -> at least one reviewed loss token.

The current closed loss vocabulary is exactly:

- `undercoverage`;
- `overcoverage`.

The approximation object is part of the projection semantic payload rather
than audit-only metadata. Therefore mapping/projection digest and review
binding already cover approximation authorization and loss direction.

### Compiled IR

`semantic_ir.py` already compiles the envelope to immutable
`ApproximationIR`:

- status;
- eligible;
- losses;
- rationale;
- review_id;
- evidence.

`TargetBindingIR` already carries that value. The I-020 probe confirms it is
preserved at runtime.

No new mapping format, semantic digest version or IR field is needed.

### Exact resolver

The current `semantic_resolve()` has a deliberately strict exact contract.

It:

1. validates the selected runtime prerequisite state;
2. verifies capability availability;
3. validates candidate bindings against the selected release;
4. selects only assessment `exact`;
5. fails `non_exact_mapping` when no exact binding exists;
6. fails `multiple_exact_bindings` rather than composing same-key bindings;
7. fingerprints an exact plan/result with exact v1 algorithms.

It also rejects every request whose mode is not exactly `exact`.

These semantics should remain unchanged.

### Exact executor

`execute_exact_semantic()` does not accept a caller-created plan.

It:

1. normalizes loaded corpus contexts;
2. freshly evaluates runtime prerequisites against the loaded APIs;
3. converts the fresh reports to prerequisite states;
4. invokes the resolver again;
5. validates the selected native binding;
6. executes only supported scalar/value-set predicate shapes.

This is the trust boundary I-020 must preserve. Approximate execution must also
resolve from fresh runtime state rather than accept a caller-supplied
pre-authorized plan.

### Exact conjunction

I-015 resolves every atom through the exact resolver and intersects the
resulting native node sets per corpus.

Required conjunction behavior is all-or-nothing: a failed required atom fails
the conjunction. No atom is silently dropped.

I-020 should preserve that shape and change only atom resolution policy for the
new approximate surface.

## Current negative-control representation

The compiler/runtime already gives useful fail-closed boundaries.

- `related` is a semantic-index projection but exact resolution refuses it as
  non-exact.
- `native-only` can produce an active capability without a common semantic
  binding; the current exact resolver reports no semantic tuple.
- `unsupported` produces an absent capability and cannot resolve.
- ambiguous native state is not authority for choosing a common semantic
  target.
- authority/identity/identifier indexes are separate from the semantic-pivot
  index and cannot satisfy semantic resolution.

I-020 must not blur any of these boundaries. R-017 and R-018 remain separate
work.

## Smallest safe public API change

The safest additive design is a separate approximate surface rather than
changing the exact public dataclasses/functions in place.

This avoids changing:

- `SemanticResolveRequest`;
- `ExactNativePlan`;
- `SemanticResolutionResult`;
- exact resolver contract strings;
- exact plan/result fingerprint algorithms;
- `ExactExecutionResult`;
- exact conjunction request/result types.

The implementation plan should introduce approximate-specific public types and
functions, conceptually:

- `ApproximateSemanticResolveRequest`;
- `ApproximationLossRecord`;
- `ApproximateNativePlan`;
- `ApproximateSemanticResolutionResult`;
- `semantic_resolve_approximate()`;
- approximate conjunction request/result types;
- `semantic_resolve_approximate_conjunction()`;
- `execute_approximate_semantic()`;
- `execute_approximate_semantic_conjunction()`;
- approximate execution result/corpus result types.

Names may be tightened by the reviewed implementation plan, but exact public
types should not be repurposed.

The approximate request should explicitly carry:

- semantic key(s);
- corpus selection;
- a fixed/validated approximate mode marker;
- `accept_losses`, an exact tuple/set-like collection from the closed loss
  vocabulary.

The caller acceptance value is authorization input and must participate in the
approximate resolution fingerprint.

## Approximate candidate-selection policy

For each corpus and requested semantic key, prerequisite/capability validation
retains the current exact precedence.

After that:

1. If exactly one exact binding exists, use it with no loss.
2. If multiple exact bindings exist, retain the existing
   `multiple_exact_bindings` refusal; I-020 does not perform R-018
   composition.
3. If no exact binding exists, inspect non-exact semantic-pivot bindings.
4. `related` is never substitutive.
5. A `close|broader|narrower` binding is executable only when its compiled
   approximation envelope is structurally valid, reviewed, `eligible=True`,
   and carries a loss set legal for its assessment.
6. The caller must accept every required loss token for that binding.
7. If more than one approximate binding remains executable for the same
   semantic key/corpus, fail closed rather than choose one by ordering.
8. If no binding is executable, return a deterministic refusal category that
   distinguishes unavailable approximation authorization from unaccepted loss
   when possible.

The exact resolver must not be modified to perform this selection.

## Defensive IR revalidation

Bundle validation normally guarantees a coherent `ApproximationIR`, but
`CompiledSemanticIR` is a public Python value and can be manually constructed
or mutated with dataclass replacement in a caller/test.

The approximate resolver therefore must defensively revalidate the compiled
approximation envelope before treating it as execution authority.

At minimum it must reject:

- wrong approximation type;
- non-reviewed status;
- non-boolean eligibility;
- unknown/duplicate loss tokens;
- eligible `broader` without exactly undercoverage;
- eligible `narrower` without exactly overcoverage;
- eligible `close` with no loss;
- approximation on `exact` or `related`;
- stale/incoherent mapping/projection release identity already covered by the
  existing binding/release validation.

It must not infer authority from ontology hierarchy or labels.

## Approximate plan and loss record

Approximate execution needs more provenance than the current
`tuple[str, ...]` top-level loss summary.

Each non-exact executable corpus plan should carry a deterministic loss record
including at least:

- corpus ID;
- semantic key/target;
- mapping ID;
- projection ID;
- assessment;
- native execution binding identity;
- exact reviewed losses;
- human-readable effect derived from the loss vocabulary;
- approximation review ID;
- caller-accepted losses;
- mapping/projection semantic digests;
- prerequisite fingerprint/source contract.

The plan already carries most of the mapping/release provenance used by the
exact plan. The loss record should not duplicate mutable source objects.

Suggested deterministic effects:

- undercoverage:
  `native selector may miss members of the requested semantic target`;
- overcoverage:
  `native selector may include members outside the requested semantic target`.

A reviewed close mapping with both tokens exposes both effects.

The loss record and caller acceptance must participate in the approximate plan
and resolution fingerprints.

## Exact bindings inside approximate requests

Approximate mode is permission to use reviewed approximation when necessary,
not an instruction to degrade an exact binding.

Therefore an exact mapping wins before approximate candidates and contributes:

- the same native execution binding;
- no semantic loss record;
- no loss token.

The approximate plan/result contract may have a distinct fingerprint from the
exact API because it is a different request/contract. It must not change the
underlying exact native binding or pretend that an exact row incurred loss.

## Multi-corpus comparison

Successful per-corpus plans retain independent loss sets.

The approximate result computes comparison state from the non-empty corpus
loss shapes:

- all empty -> `exactly-comparable`;
- one uniform non-empty loss shape, possibly mixed with exact corpora ->
  `approximately-comparable`;
- two or more different non-empty loss shapes -> `heterogeneous-loss`.

If any required corpus cannot produce an executable plan, resolution fails
rather than returning a silently partial plan set.

This preserves the current all-requested-corpora contract.

The current TFont runtime has no aggregate/statistics API. I-020 therefore does
not invent the R-016 optional approximate-aggregate surface. Any later
aggregation API should remain exact-only until it separately implements the
R-016 uniform-loss rule.

## Conjunctions

Approximate conjunction resolution should mirror I-015 composition:

1. canonicalize required semantic keys;
2. resolve every atom through the approximate resolver under the same caller
   loss acceptance;
3. fail the whole conjunction if any required atom fails;
4. union atom loss tokens conservatively;
5. preserve every atom loss record;
6. execute native plans and intersect node sets per corpus.

Loss union follows R-016:

- exact + exact -> empty;
- exact + under -> under;
- exact + over -> over;
- under + under -> under;
- over + over -> over;
- under + over -> both.

No quantitative bound is implied.

For cross-corpus comparison, the conjunction's corpus loss shape is the union
of that corpus's required atom losses, then the same exact/uniform/heterogeneous
comparison rule is applied.

## Fresh execution authorization

Approximate executors must use the same trust pattern as I-008/I-015:

- caller supplies semantic request plus loaded contexts;
- runtime evaluates fresh parent/component/dependency/ontology-bundle state;
- fresh prerequisite states are passed to the approximate resolver;
- resolver creates fresh approximate plans;
- only those plans are executed.

No public API should execute a caller-supplied `ApproximateNativePlan`.

Native execution remains limited to the currently supported scalar and finite
value-set predicates in I-020. Structural edge/path execution belongs to the
later P-004 Workstream B structural ticket.

## Error/refusal precedence

Preserve existing prerequisite/capability fail-closed precedence.

Approximation-specific refusal should happen only after the same checks that an
exact request currently performs for:

- variant selection;
- stale/invalid prerequisite;
- parent compatibility;
- dependency availability;
- ontology-bundle state;
- capability absence/unavailability;
- semantic tuple existence;
- compiled binding/release coherence.

This prevents approximate mode from becoming a route around runtime safety.

Then use approximation-specific errors for:

- no substitutive reviewed mapping;
- approximation not reviewed/eligible;
- required loss not accepted;
- multiple executable approximate bindings;
- malformed compiled approximation metadata.

Exact APIs retain their existing categories unchanged.

## Fingerprint/version boundary

Approximate contracts need new versioned constants/algorithms.

They must not reuse exact algorithm names because the payload adds:

- approximate request mode;
- accepted losses;
- approximation review authorization;
- loss records;
- different comparison states.

Exact v1 fingerprints in the committed research evidence are regression
anchors and must remain byte-for-byte unchanged after I-020.

## No ontology reasoning authority

I-020 executes only explicit compiled mappings.

It must not:

- traverse subclass/subproperty hierarchies to find a substitute;
- follow SKOS broader/narrower links to manufacture a mapping;
- infer assessment from labels;
- use ontology graph structure to convert `related` into executable
  approximation;
- bypass bridge/bundle/version prerequisites.

Ontology structure remains mapping-research evidence, not runtime execution
authority.

## Plan handoff

The implementation plan should:

1. keep all exact public types/functions/fingerprints unchanged;
2. add a separate approximate request/plan/result surface;
3. reuse existing prerequisite selection, capability checks, release
   validation and native binding execution internally;
4. defensively validate compiled approximation authority;
5. require exact closed-vocabulary caller loss acceptance;
6. choose exact bindings before approximate bindings;
7. refuse multiple approximate candidates pending R-018;
8. add deterministic direction-specific loss records and fingerprints;
9. implement single-atom and conjunction resolution/execution;
10. preserve fresh runtime revalidation before execution;
11. add multi-corpus exact/uniform/heterogeneous comparison tests;
12. add negative controls for related, native-only, unsupported, ambiguous,
    malformed approximation, missing acceptance and stale prerequisites;
13. prove exact single/conjunction fingerprints from the I-020 evidence remain
    unchanged;
14. add no new mapping, ontology, hierarchy traversal or aggregate execution.

A separate plan review is required before any production changes.
