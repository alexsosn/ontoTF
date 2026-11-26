# I-007 research — derive runtime prerequisite attestations for compiled semantic IR

**Issue:** #130  
**Baseline:** `main` `a05a9ba1a32a26cdcdf28f0a44656d63c3b35da8`  
**Type:** runtime prerequisite / compatibility evaluation

## Question

How should ontoTF derive the `RuntimePrerequisiteState` consumed by I-006 from an actually observed materialized TF/Context-Fabric corpus, while preserving the P-001 compatibility states, P-002 dependency semantics, P-003 prerequisite ordering, I-003 parent identity, I-005 release identity, and the R-019 rule that deterministic fingerprints do not authenticate their producer?

## Current state

The current `compatibility-report.schema.json` is a P-001/v1 artifact. It binds a `profile_semantic_digest` and a profile id/version, but it predates the I-005 `BundleVariantKey` / `ProfileReleaseSignature`, mapping-v2 and projection review authority, active ontology-bundle identity and the P-003 execution boundary. It remains useful historical/schema compatibility material but is not sufficient execution authority for the current architecture.

I-006 deliberately accepts immutable prerequisite state supplied by another trusted layer. Its resolver validates parent state, complete dependency closure, active ontology-bundle identity, release fingerprint and source contract. The missing production boundary is therefore observation/evaluation, not another resolver.

## Text-Fabric observation surface

Text-Fabric models a dataset as an annotated directed graph. Every dataset has `otype` node-type and `oslots` extent features; other node and edge features are wefts. The core API exposes node features (`F`), edge features (`E`), locality (`L`), text (`T`) and search (`S`). This is enough to evaluate the P-002 TF-native dependency shapes without compiling query strings or doing semantic lookup.

Primary TF documentation consulted:

- data model: https://annotation.github.io/text-fabric/tf/about/datamodel.html
- core API: https://annotation.github.io/text-fabric/tf/core/index.html
- Fabric API / feature data: https://annotation.github.io/text-fabric/tf/core/fabric.html

The evaluator should not depend on notebook/app display helpers. It should depend on a narrow observation interface that can be backed by an already loaded TF/Context-Fabric API. This keeps the evaluator deterministic and testable without importing a corpus in unit tests.

## Architectural split

I-007 should have two layers with one authority direction.

### A. Pure release/prerequisite evaluator

Inputs:

1. one I-005 `BundleVariantIR` / `ProfileReleaseSignature`;
2. observed parent-manifest identity and observed component identities from I-003-compatible observation;
3. deterministic observed TF facts needed by the release's dependency records;
4. active ontology-bundle identity/availability supplied by the host's selected installed ontology bundle, not fetched from the network;
5. a versioned evaluator/source contract.

Output:

- one immutable evaluation report containing the four compatibility-state semantics and full per-dependency results;
- a resolver-facing `RuntimePrerequisiteState` projection whose shape is exactly what I-006 consumes;
- a deterministic report/prerequisite fingerprint over stable semantic/runtime facts only.

This layer performs no Context-Fabric query execution and no semantic target resolution.

### B. TF observation adapter

A small adapter reads the already loaded materialized corpus and projects only the facts requested by dependency records. It does not decide semantic compatibility; it only produces deterministic observations.

Keeping observation separate from evaluation prevents TF API details from becoming the authority model and makes it possible to test all eight dependency kinds with synthetic observation fixtures.

The adapter is still in I-007 scope because #130 requires a real production path from materialized TF state, but its interface should remain private/narrow rather than becoming a generic corpus-ingestion framework.

## Authority and freshness identity

A runtime report must be bound to exactly one compiled variant/release. The stable authority tuple is:

- `BundleVariantKey` including corpus id, authored profile id/version, expected parent manifest digest and required ontology-bundle digest;
- `profile_release_fingerprint(ProfileReleaseSignature)` using the same I-006 versioned projection;
- observed parent manifest digest;
- complete evaluated dependency results keyed by the release's exact dependency IDs;
- active ontology-bundle digest/state;
- evaluator/source contract version.

A cached result is reusable only when that tuple still matches current trusted state. A changed release signature with the same human-readable profile version must invalidate reuse. A changed parent must invalidate an old `verified-exact` result even if individual target mappings appear unchanged.

Volatile fields such as generated timestamp, local filesystem root, notebook path, host name, PID or user/session id must be excluded from deterministic report identity.

## Parent compatibility state

P-001's four states remain useful, but the state must be derived rather than caller-authored.

### `verified-exact`

Require all of:

- observed parent manifest digest equals the variant's `expected_parent_manifest_digest`;
- every release dependency has one deterministic `pass` result;
- no required observation is unknown/unavailable;
- required ontology-bundle closure is satisfied exactly;
- release/variant identity is current.

### `verified-compatible`

May be emitted only when:

- observed parent digest differs from expected;
- every release dependency still has a deterministic `pass` result against the observed parent;
- required components needed by the dependency closure can be identified/evaluated in the observed parent;
- ontology-bundle closure remains exact;
- no dependency result depends on unverified inference.

This is compatibility by the reviewed dependency contract, not by digest similarity. Merely changing the parent digest is not enough to claim compatible.

### `unverified`

Use when compatibility cannot be established because at least one required dependency/observation is `unknown`, unavailable, unsupported by the observation adapter, or otherwise incomplete, provided there is no known failed requirement that makes the release incompatible.

This state is non-executable for I-006.

### `incompatible`

Use when at least one required dependency deterministically fails, a required component is absent, or another evaluated release prerequisite is known not to hold for the observed parent.

A stale/mismatched report object itself should not be reclassified as an observed corpus incompatibility. Stale variant/release/report reuse is an input-validation error; compatibility state describes the evaluated observed parent.

## Complete dependency closure

I-005 stores every dependency as `(dependency_id, canonical_dependency_json)` in `ProfileReleaseSignature.dependency_records`. I-007 must parse/evaluate **all** of these records for a release. No target-local subset may authorize execution in v1.

The report must contain exactly one result for every dependency ID and no extras. Duplicate dependency IDs or malformed canonical records are invalid compiled/release input, not runtime `unknown`.

This matches I-006's current fail-closed closure check and avoids a semantic query accidentally bypassing a profile-level prerequisite that is not locally referenced by one mapping.

## Evaluation semantics for the eight P-002 kinds

The profile schema defines eight closed TF-native kinds. The evaluator should dispatch on the canonical dependency record and return `pass | fail | unknown` plus stable evidence identity where appropriate.

### `component-present`

Authority comes from the observed parent component manifest. `pass` iff the required `component_id` exists as a current observed component. A missing component is `fail`; inability to establish the parent/component manifest is `unknown`.

No independent `required` flag exists; presence of the dependency makes it required.

### `node-type-present`

`pass` iff the loaded TF dataset exposes at least one node of the required `otype` value within the dependency's component scope. If the relevant component is absent, the dependency fails. If the adapter cannot inspect the component/dataset, result is unknown.

The observation should be derived from the loaded `otype` feature/API, not by parsing application display output.

### `feature-present`

`pass` iff the required node feature exists for the declared node type/component under the loaded dataset contract. The check is about feature availability on that type, not merely a same-named metadata key somewhere in the corpus.

A declared feature object that cannot be loaded/read deterministically is unknown rather than silently treated as present.

### `edge-present`

`pass` iff the required edge feature/direction is available in the component's TF graph contract. Direction is part of the dependency semantics. An edge feature present only under a different interpretation/direction does not satisfy the dependency.

### `path-present`

Evaluate every ordered edge/direction step. `pass` requires the complete path shape to be representable from the loaded feature graph; a missing required step is fail. If the adapter cannot establish a step's availability, result is unknown. Do not run an unbounded corpus search merely to prove that a specific path has at least one incidental instance unless the reviewed assertion semantics explicitly require occurrence rather than schema/feature availability.

Research decision: v1 treats `path-present` as **execution-shape availability**, consistent with dependency use as a prerequisite for a native binding. It does not promise an extensional proof that at least one result row exists for an arbitrary semantic query.

### `native-value-present`

`pass` requires the exact JSON-scalar value (including authored null) to be observed for the declared node type/feature under semantic value equality. Absence of the value from an otherwise inspectable feature is fail; inability to enumerate/read the feature is unknown.

Value identity must preserve null vs absence and must not coerce strings/numbers/booleans.

### `value-domain`

Two modes remain distinct.

- `observed`: the declared values are required observed support facts. `pass` when each required value can be observed under exact JSON-scalar identity; additional values do not invalidate compatibility.
- `closed-reviewed`: the declared set is a reviewed **allowed closed domain**, as established by the P-002 source contract. Runtime compatibility requires every completely observed non-missing feature value to belong to that reviewed set: **observed domain ⊆ reviewed closed domain**. Any observed out-of-domain value is `fail`; inability to enumerate the complete observed domain is `unknown`. A reviewed allowed value need not occur in every materialized corpus release, so absence of an allowed value is not itself a compatibility failure.

This asymmetry is intentional. P-002 says `closed-reviewed` means the reviewed source contract explicitly claims a closed domain and requires evidence so a finite observed release sample cannot silently become that closure. It does not say every allowed member must occur in every release. Therefore set equality would over-constrain valid corpora.

The closed-reviewed source evidence remains compile-time review authority; I-007 does not re-review or fetch it.

### `extent-interpretation`

The assertion is about the reviewed native interpretation token (`textualExtent | occurrenceSet | technicalAnchor | noSlot`) for a node type/component. This cannot be safely inferred from node counts alone. The observation adapter needs an explicit deterministic interpretation fact supplied by the corpus/native-adapter contract or another reviewed local metadata source.

If that interpretation fact is absent, result is `unknown`; do not guess from `oslots` topology. This is the main dependency kind that requires corpus adapter metadata rather than generic TF feature introspection.

## Evidence digests in runtime results

`observed_evidence_digest` should identify the deterministic observation projection used to decide a dependency, not a local path or arbitrary human summary. Recommended projection inputs are dependency-kind-specific stable facts, for example:

- component identity/digest;
- node-type/feature/edge existence facts;
- exact value or canonical value-domain set;
- explicit extent-interpretation metadata.

Use the existing canonical JSON + SHA-256 family with a new versioned I-007 observation-fingerprint algorithm. Do not hash Python reprs or TF object addresses.

A dependency can have `observed_evidence_digest=None` only when there is no positive deterministic observation to bind, especially `unknown`; exact policy should be frozen in the implementation plan.

## Ontology bundle and bridges

I-007 must not dereference ontology URLs at runtime. I-004/I-005 already bind participating ontology locks and an optional validated ontology-bundle digest into release identity.

Runtime observation therefore asks the host for the identity of the **installed/selected active bundle**. If the release requires no bundle, active state must be `not-required` with no digest. If it requires a bundle, executable compatibility requires the exact required digest to be locally available/selected.

A different active digest is stale/mismatched runtime state, not “close enough”. Missing required bundle availability makes the prerequisite non-executable. The implementation plan should preserve I-006's categories for unavailable versus stale/malformed states.

Bridge semantics themselves are not re-evaluated by I-007: they were structurally/semantically validated in I-004 and bound into the required bundle/release. I-007 proves that the reviewed bundle identity required by that release is the one active at runtime.

## Old compatibility report

The current v1 schema cannot be upgraded by field-name coincidence. In particular, `profile_semantic_digest` is not the I-005 profile release fingerprint and must never be accepted as one.

Recommended compatibility strategy:

- keep the v1 schema/loader valid for historical/API compatibility unless a separate deprecation ticket changes it;
- define a distinct I-007 runtime report contract/version and Python type;
- do not make `semantic_resolve` accept the v1 report object/dict directly;
- if a future migration converter is needed, it may produce only `unverified`/informational output unless it can re-establish all current release, dependency, parent and bundle facts.

This prevents an old report generated under weaker semantics from authorizing P-003 execution.

## API boundary

Recommended production API shape:

- `evaluate_runtime_prerequisites(variant, observation, *, source_contract=...) -> RuntimeEvaluationReport`
- `RuntimeEvaluationReport.prerequisite_state` or a pure projection helper returning the I-006 `RuntimePrerequisiteState` once I-006 is merged;
- a narrow TF observation protocol/type and a concrete adapter for an already loaded TF/Context-Fabric API.

The pure evaluator should not import notebook/app APIs, execute semantic queries, load remote corpora or decide which corpus version to install.

If I-006 is not yet merged when I-007 implementation begins, production must wait rather than duplicating the prerequisite dataclasses on a competing branch. Research/plan can proceed independently; code should build on the merged I-006 public contract.

## Deterministic report identity

A versioned report fingerprint should include at least:

- evaluator report contract/algorithm id;
- full variant key;
- I-006-compatible profile release fingerprint;
- observed parent manifest digest;
- compatibility state;
- canonically sorted dependency results including rule version and observation digest;
- active ontology bundle digest/state;
- resolver-facing prerequisite source contract.

It should exclude:

- generated timestamps;
- local path/root;
- process/host/user/session IDs;
- display summaries or logging text;
- Python/TF object identities.

Changing any execution-relevant observation, release signature or evaluator rule contract must change the report identity.

## R-019 trust boundary

R-019 establishes that public deterministic fingerprints identify content but do not authenticate producer origin. I-007 follows the same rule.

A hand-constructed report that recomputes its public digest is not trusted merely because the hash matches. In the same trusted execution host, trust comes from invoking the I-007 evaluator over the selected live/materialized corpus and passing its result directly to I-006/execution. Across an untrusted serialization/process boundary, runtime state must be re-established locally or carried over a separately authenticated channel.

No MAC/signature/key management belongs in I-007 unless a later remote-principal architecture requires it.

## Error/state precedence

Keep input validity separate from observed compatibility:

1. malformed/wrong-type variant/release/observation input -> typed evaluator error;
2. release/variant self-incoherence -> typed invalid-release/compiled-IR error;
3. inability to establish required observation -> dependency `unknown` and overall `unverified`;
4. deterministic failed requirement -> dependency `fail` and overall `incompatible`;
5. changed parent with all requirements passing -> `verified-compatible`;
6. exact parent with all requirements passing -> `verified-exact`.

Known failure should dominate unknown for the overall state: if one required dependency deterministically fails and another is unknown, the release is already known incompatible. This avoids reporting merely unverified when execution is definitely unsafe.

The plan should pin deterministic first-error behavior for malformed inputs separately from the aggregate compatibility state.

## Cache model

Cache by stable authority/observation identity, not by corpus path or profile version alone. A practical cache key can be based on:

- variant key / profile release fingerprint;
- observed parent manifest digest;
- evaluator/source contract version;
- active ontology-bundle identity.

However, dependency observations are themselves derived from the observed parent. If a loaded mutable runtime can change without changing the parent identity, cache reuse is unsafe. The host must treat I-003 parent identity as identifying an immutable/quiescent materialization for the evaluation window, consistent with prior filesystem research: ontoTF does not promise a hostile concurrent-writer snapshot.

## Test architecture required by research

The implementation RED should use a synthetic observation adapter/protocol so each dependency kind can be proved without a network corpus. Add a small real TF fixture only if necessary to prove the concrete adapter speaks the actual public TF API; avoid making the core contract tests download BHSA or another large corpus.

Minimum RED matrix:

1. exact parent + complete pass closure -> verified-exact;
2. changed parent + complete pass closure -> verified-compatible;
3. one fail -> incompatible;
4. one unknown -> unverified;
5. fail + unknown -> incompatible;
6. missing/extra dependency result cannot appear in resolver-facing projection;
7. stale/mismatched variant/release invalidates reuse;
8. required bundle exact/missing/wrong/no-bundle states;
9. report fingerprint changes under parent/dependency/rule/source-contract/bundle/release changes;
10. timestamps/local paths do not enter identity;
11. all eight dependency kinds have pass/fail/unknown boundary tests where meaningful;
12. JSON scalar identity preserves null, false, zero and strings without coercion;
13. closed-reviewed value domain rejects observed values outside the reviewed closure but permits reviewed values that simply do not occur in the current release;
14. extent interpretation without explicit adapter fact is unknown, never guessed;
15. old v1 compatibility-report-shaped data cannot become executable prerequisite state;
16. no semantic lookup/query execution/network fetch occurs in evaluation;
17. resolver integration consumes only the reviewed I-006 prerequisite type after I-006 merges;
18. a serialized hand-constructed report is not documented or exposed as authenticated execution authority.

## Potential follow-up discovered

The exact concrete Text-Fabric observation adapter deserves its own implementation sub-boundary inside I-007, but not a separate semantic feature ID unless planning shows it can land independently. In particular, `extent-interpretation` requires explicit corpus/native-adapter metadata not derivable safely from generic TF graph topology. If current corpus packages do not expose that metadata consistently, implementation should return `unknown` for that dependency rather than invent heuristics, and a later corpus-adapter metadata ticket can improve coverage.

## Exit decision

I-007 should replace the obsolete v1 compatibility-report execution role with a new deterministic runtime evaluation report bound to one current I-005 variant/release and projected into I-006 `RuntimePrerequisiteState`.

The architecture is:

`loaded TF/Context-Fabric + observed parent identity -> narrow deterministic observation adapter -> pure eight-kind dependency evaluator + bundle closure -> four-state runtime report -> I-006 prerequisite projection`

Key constraints:

- all release dependencies participate; no target-local partial activation in v1;
- `verified-exact` requires expected parent + complete pass closure;
- `verified-compatible` requires changed parent + complete pass closure, not digest similarity;
- deterministic fail dominates unknown; otherwise incomplete evidence is unverified;
- active ontology bundle is matched locally by exact reviewed digest, never fetched live;
- old `profile_semantic_digest` reports cannot authorize current execution;
- report identities exclude volatile deployment data;
- deterministic hashes are content identity, not producer authentication;
- no resolver/query execution, ontology dereferencing, generic ingestion or MCP/session identity enters I-007.
