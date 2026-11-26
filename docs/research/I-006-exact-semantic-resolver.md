# I-006 research: exact semantic resolver thin slice

**Issue:** #124  
**Baseline:** `main` `69c295e342b2caf4847ce7f3bc7294d3f6536cdc` after merged I-005/#128  
**Type:** implementation research only; no resolver code in this phase  
**Acceptance slice:** OLiA Noun -> BHSA + ETCBC Syriac + ETCBC ExtraBiblical -> native TF/Context-Fabric plan records + provenance

## 1. Research conclusion

I-006 should be a small protocol-independent resolver over **compiled semantic IR plus separately established runtime prerequisite attestations**.

It must not inspect a live Text-Fabric/Context-Fabric corpus, regenerate compatibility state, reopen mapping/profile/ontology source files, infer semantics from labels or feature names, or execute Context-Fabric queries.

The reviewed I-005 handoff is explicit:

> I-006 receives `CompiledSemanticIR` and separately established runtime prerequisite/compatibility state.

The resolver's job is therefore to validate that supplied runtime state is current and matches one compiled bundle variant, select the exact requested semantic tuple, enforce exact-only/review/dependency gates, and emit immutable native plan records and fingerprints.

Two gaps discovered during this research are separate from the noun resolver itself:

- #130 — production runtime prerequisite/compatibility evaluator and report-vNext;
- #131 / R-018 — reviewed composition semantics when one corpus/variant has multiple exact bindings for the same semantic key.

Neither blocks the first noun contract if I-006 consumes explicit prerequisite attestations and fails closed on multiple exact bindings.

## 2. Current production inputs

Merged I-005 exposes the required immutable runtime facts:

- `CompiledSemanticIR`;
- `BundleVariantKey`;
- `ProfileReleaseKey` and `ProfileReleaseSignature`;
- `BundleVariantIR`;
- `SemanticKey`;
- `TargetBindingIR`;
- `CapabilityKey` / `CapabilityFactsIR`;
- deterministic `semantic_index` and `capability_facts`;
- native execution binding + identity;
- native dependency IDs;
- mapping/projection semantic digests;
- mapping/projection review fingerprints;
- mapping/projection evidence fingerprints;
- expected parent manifest identity;
- ontology bundle identity;
- participating ontology-lock identity;
- optional ontology-bundle requirement/declaration/publication/approximation metadata.

`semantic_index` is already authority-filtered at compile time: provisional/disputed projections, ambiguous candidates, native-only/unsupported rows and authority/identity/identifier/reference families do not become semantic-pivot executable bindings.

I-006 still checks `assessment == exact`; I-005 intentionally indexes reviewed semantic-pivot projections of all positive assessment strengths so later approximate resolution can reuse the same IR.

## 3. Runtime prerequisite boundary

### 3.1 The old compatibility report is not P-003 runtime authority

`src/ontotf/schemas/compatibility-report.schema.json` is still the P-001/v1 shape. It binds:

- `profile_semantic_digest` from the superseded pre-P-003 profile identity model;
- expected/observed parent manifest digests;
- the four P-001 states;
- dependency results;
- evaluator version.

It predates:

- `BundleVariantKey`;
- `ProfileReleaseSignature`;
- mapping-v2/projection semantic identity;
- review authorization state in release coherence;
- active ontology-bundle identity and bridge closure;
- P-003 typed routing.

Therefore I-006 must not accept the v1 compatibility report merely because some field names look useful. #130 owns a versioned evaluator/report migration before production execution trusts dynamically established compatibility.

### 3.2 Resolver-facing prerequisite attestation

I-006 does need a small immutable in-memory contract that tests and future #130 can produce. It should conceptually bind:

```text
variant key
profile-release semantic identity/fingerprint
observed parent manifest digest
parent compatibility state
complete dependency pass set/result identity
active ontology-bundle state/digest
prerequisite evaluator/source contract identifier
prerequisite fingerprint
```

The attestation is **input evidence**, not semantic source authority.

Recommended parent states remain the accepted P-001 vocabulary:

`verified-exact | verified-compatible | unverified | incompatible`.

Only `verified-exact` and `verified-compatible` may authorize a plan.

For `verified-exact`, observed parent manifest digest must equal the selected variant's expected parent manifest digest.

For `verified-compatible`, observed parent manifest digest must differ and the complete release dependency closure must be proven passing. I-006 must not implement how those dependency assertions were measured; #130 owns that evaluator.

### 3.3 Complete dependency closure, not target-local partial activation

`ProfileReleaseSignature.dependency_records` contains the profile release's normalized dependency records. `TargetBindingIR.native_dependencies` identifies the binding-specific dependencies, but P-001/P-003 reject opportunistic partial activation.

For the v1 resolver attestation, executable state should therefore require every dependency ID in the selected release signature to be present in the attested passing dependency set. A target-local subset is insufficient.

This can be relaxed only by a later reviewed architecture change that explicitly introduces partial profile activation.

### 3.4 Active ontology bundle

The selected variant carries `ontology_bundle_digest`.

Resolver prerequisite behavior:

- variant digest `None` -> no active ontology-bundle artifact is required by this variant; the prerequisite state must not fabricate one;
- non-null variant digest -> the attested active bundle digest must match exactly and its runtime state must be verified/active;
- missing, stale or unavailable bundle -> non-executable;
- approximation can never repair this, and I-006 has no approximate mode anyway.

Projection-level `ontology_bundle_requirement`, when present, must agree with the already selected variant/bundle identity. The resolver may validate equality but must not reopen bundle source or bridge artifacts.

## 4. Prevent stale prerequisite reuse

`BundleVariantKey` alone is not a sufficient cache key: it contains corpus/profile/version, expected parent digest and ontology-bundle digest, but not mapping/review/dependency semantic content.

A stale runtime prerequisite keyed only by that tuple could survive a semantically changed build that incorrectly reused the same profile version.

I-006 should therefore bind prerequisite state to the selected `ProfileReleaseSignature` through a versioned deterministic fingerprint. Do **not** revive the old `profile_semantic_digest`.

Recommended identity layers:

- `tfont-profile-release-signature-jcs-sha256-v1` — deterministic projection of the frozen I-005 `ProfileReleaseSignature`;
- `tfont-runtime-prerequisite-jcs-sha256-v1` — selected variant + profile-release signature fingerprint + observed parent + compatibility state + complete dependency result identity + active bundle state/digest + evaluator/source contract identifier;
- `tfont-exact-resolution-jcs-sha256-v1` — exact request + selected binding semantic identities + prerequisite fingerprint + emitted native binding identity.

Volatile timestamps, local paths, MCP/session IDs and display text must not enter these fingerprints.

## 5. Request contract

Reuse the existing exact semantic key instead of inventing a second target tuple type.

Conceptual request:

```text
SemanticResolveRequest
  key: SemanticKey(
    profile_id,
    capability_id,
    target,
    formal_kind,
    semantic_role,
  )
  corpora: explicit non-empty unique tuple/set of corpus IDs
  semantic_mode: exact
```

Rules:

- corpus selection is explicit in I-006; no implicit "all installed corpora" behavior;
- duplicate corpus IDs fail request validation rather than being silently deduplicated;
- result ordering is canonical UTF-16 corpus-ID order, independent of request order;
- only `semantic_mode == exact` is accepted; `approximate` belongs to the later P-003 approximate-resolution ticket;
- request vocabulary must match existing controlled profile/capability/formal-kind/semantic-role vocabularies exactly;
- target string is exact authored/locked identity; no CURIE expansion, label matching, URI normalization or hierarchy traversal occurs at resolution time.

## 6. Exact fail-closed resolution order

For this thin slice use deterministic precedence derived from P-003 §11:

1. validate request shape, controlled vocabulary, mode and corpus selection;
2. for every requested corpus, validate/select exactly one current prerequisite-attested bundle variant;
3. validate release-signature freshness, parent state, complete dependency closure and active bundle identity;
4. derive requested profile/capability operational availability from `CapabilityFactsIR` plus prerequisite state;
5. locate the **exact full `SemanticKey`** in `semantic_index`;
6. restrict rows to the requested corpus + selected variant + `assessment == exact`;
7. require exactly one surviving exact binding for this I-006 slice;
8. validate retained binding/variant/prerequisite fingerprints are internally coherent;
9. emit one native plan record per requested corpus;
10. sort plans deterministically and compute per-plan plus whole-resolution fingerprints.

No requested corpus may be silently dropped. If any requested corpus cannot produce one authorized exact plan, the multi-corpus request fails closed.

A later API may expose structured partial comparison diagnostics, but I-006 must not call a partial result executable.

## 7. Variant selection

Multiple parent variants are a first-class I-005 feature.

For each requested corpus:

- prerequisite state must name/bind one `BundleVariantKey` present in `CompiledSemanticIR.variants`;
- its `ProfileReleaseSignature` fingerprint must match that exact variant's release signature;
- executable parent state must be internally consistent (`verified-exact` equality; `verified-compatible` changed parent + complete passing closure);
- if zero executable attestations match -> fail unavailable/unverified;
- if more than one executable attestation/variant could authorize the same corpus request -> fail ambiguous prerequisite selection rather than choosing one by ordering.

The resolver never chooses the newest profile version, closest parent digest or lexically first variant.

## 8. Capability discovery versus execution authority

R-014 remains authoritative:

- capability operational state is `active | absent | unavailable`;
- reviewed native support may include `native-only` or ambiguous native semantics;
- `unsupported` does not activate a capability;
- active capability never implies every concept is executable.

I-006 can derive a minimal runtime capability view from:

`CapabilityFactsIR + selected prerequisite state`.

Recommended state:

- positive reviewed native support + executable prerequisite -> `active`;
- zero positive reviewed native support -> `absent`;
- positive reviewed native support + non-executable prerequisite -> `unavailable`.

`semantic_capabilities` may expose this compact discovery information and counts, but `semantic_resolve` must independently require the exact requested `SemanticKey` and exact binding. Passing a discovery summary into `semantic_resolve` must never authorize execution.

For scope control, I-006 need only implement the minimal profile/capability discovery surface required to prove this separation for the noun capability; generic filtering/pagination/UI belongs later if needed.

## 9. Semantic index behavior

The authoritative lookup key is exactly:

```text
(profile_id, capability_id, target, formal_kind, semantic_role)
```

A matching target IRI under a different profile, capability, formal kind or semantic role is a different request and must not resolve by target-string coincidence.

`semantic_index` may contain `close`, `broader`, `narrower` and `related` reviewed rows. I-006 filters them out in exact mode. It must not inspect `approximation` to rescue them.

`ambiguous`, `native-only` and `unsupported` never enter this index from I-005. Their absence is authoritative for exact target resolution; I-006 must not reconstruct a target from candidate/native metadata.

## 10. One binding per corpus in the thin slice

I-005 correctly allows multiple `TargetBindingIR` rows for the same semantic key and corpus/variant. There is not yet reviewed authority for how such rows compose into one native query.

Unsafe behaviors include:

- choose first row;
- implicit OR/union;
- implicit AND/intersection;
- choose lexically smallest mapping ID;
- collapse rows because their target is equal.

I-006 OLiA Noun therefore requires **exactly one** exact binding after corpus/variant filtering. More than one is a deterministic non-executable error. #131/R-018 owns broader composition semantics.

## 11. Native plan record

The plan must reuse `TargetBindingIR.native_execution_binding`; it must not emit or parse an ad-hoc query string such as `sp=subs`.

Conceptual frozen plan fields:

```text
corpus_id
semantic_key
semantic_mode = exact
variant key
profile-release signature fingerprint
expected parent manifest digest
observed parent manifest digest
parent compatibility state
prerequisite fingerprint
mapping_id
projection_id
assessment = exact
native_execution_binding_identity
native_execution_binding (NativeBindingIR)
native_dependencies
mapping_semantic_digest
projection_semantic_digest
mapping_review
projection_review
ontology_lock
ontology_bundle_digest
mapping_evidence
projection_evidence
plan_fingerprint
```

Retain the typed binding (`node_type=word`, `feature=sp`, `value=subs`) as data. Context-Fabric string/query generation is the later execution-handoff ticket.

## 12. Resolution result and failure model

Recommended public shapes for the plan gate to freeze:

- `SemanticResolveRequest`;
- `RuntimePrerequisiteState` (resolver-facing attestation, not evaluator implementation);
- `DependencyPrerequisiteResult` or equivalent immutable dependency pass facts;
- `ExactNativePlan`;
- `SemanticResolutionResult`;
- `SemanticResolutionProblem` / `SemanticResolutionError`.

The result should contain canonical plans and a whole-request `resolution_fingerprint` suitable for the later execution handoff.

For the first implementation, any requested-corpus failure raises/fails the complete request with a deterministic machine-oriented problem rather than returning an executable partial plan set.

Diagnostic categories to distinguish in planning include at least:

- `invalid_request`;
- `unsupported_semantic_mode`;
- `unknown_request_vocabulary`;
- `invalid_corpus_selection`;
- `missing_prerequisite`;
- `stale_prerequisite`;
- `ambiguous_prerequisite_variant`;
- `parent_unverified`;
- `parent_incompatible`;
- `dependency_unavailable`;
- `ontology_bundle_unavailable`;
- `capability_absent`;
- `capability_unavailable`;
- `semantic_tuple_absent`;
- `non_exact_mapping`;
- `multiple_exact_bindings`.

The plan phase must freeze exact precedence and whether some categories collapse to a smaller stable public vocabulary.

## 13. Fingerprint boundary

A later Context-Fabric executor should never execute a hand-authored lookalike plan. It should accept only resolver-produced plan records whose fingerprint verifies.

I-006 therefore needs deterministic identity at two levels:

1. **plan fingerprint** — one corpus/binding/prerequisite;
2. **resolution fingerprint** — request identity + canonical ordered plan fingerprints.

Changing any execution-significant input must change identity:

- target tuple;
- selected corpus/variant;
- release signature;
- observed parent/prerequisite state;
- dependency result identity;
- active ontology bundle;
- mapping/projection semantic digest or review authorization;
- ontology lock;
- native execution binding.

Audit-only timestamps/display text must not.

## 14. OLiA Noun acceptance fixture

Reuse the production-valid I-005 contract builder rather than inventing incompatible source semantics.

The positive slice remains:

| corpus | semantic key | native binding |
|---|---|---|
| BHSA | `linguistic / linguistic.part-of-speech / olia:Noun / class / annotation-value` | `word.sp=subs` |
| ETCBC Syriac | same | `word.sp=subs` |
| ETCBC ExtraBiblical | same | `word.sp=subs` |

Each source bundle must still pass structural validation + I-004 + I-005 compilation before resolver tests consume it. I-006 tests may wrap those compiled fixtures with explicit fresh prerequisite attestations for the exact expected parent variants.

These are contract fixtures, not a claim that a broad production corpus mapping package is released.

## 15. Mandatory RED additions from research

In addition to #124's listed RED cases, planning should require:

1. stale prerequisite with matching `BundleVariantKey` but different profile-release signature fails;
2. `verified-exact` with observed-parent digest != expected fails;
3. `verified-compatible` without complete passing release dependency closure fails;
4. target-local dependency subset cannot authorize a plan;
5. stale/mismatched active ontology-bundle digest fails;
6. two executable prerequisite variants for one corpus fail instead of first-match selection;
7. two exact bindings for one corpus/variant fail `multiple_exact_bindings` (until #131 resolves composition);
8. duplicate requested corpus IDs fail rather than dedupe;
9. request corpus order does not change canonical plans/fingerprint;
10. mapping/plan display or audit-only metadata does not alter resolution identity where it is already excluded from semantic fingerprints;
11. changing observed parent, dependency result, release signature, ontology bundle, mapping/projection semantic digest or native binding changes the relevant fingerprint;
12. discovery state `active` with no exact requested tuple still cannot resolve;
13. exact target row for an unrequested corpus is never returned;
14. approximate mode is explicitly rejected, not silently treated as exact.

## 16. CI and boundary

Focused CI should run on Python 3.10 and 3.12 and include:

- I-006 resolver tests;
- I-005 compiler regressions;
- I-004 validation controls.

The repository full suite remains owned by the existing authoritative workflow.

No new runtime dependency is justified by research. Existing dataclasses + JCS/SHA-256 helpers are sufficient.

I-006 production code must not:

- access filesystem/network/live TF/CF corpus state;
- produce compatibility reports;
- evaluate native dependency assertions against corpus data;
- execute Context-Fabric;
- build MCP objects/session state;
- perform RDF/SPARQL reasoning or ontology HTTP lookup;
- infer target/kind/profile/capability from names/labels/URIs;
- resolve authority/identity/identifier families;
- implement approximate execution;
- implement multi-binding OR/AND composition.

## 17. Handoff to later tickets

### #130 runtime prerequisite evaluator

Produces current prerequisite attestations from observed materialized corpus identity and complete TF-native dependency evaluation; replaces the obsolete v1 compatibility-report authority for P-003 runtime use.

### Context-Fabric execution handoff

Consumes only resolver-produced `ExactNativePlan` records and verifies plan/resolution fingerprints before translating typed native bindings into actual Context-Fabric execution.

### #131 multi-binding composition

Defines reviewed composition authority before a corpus may execute multiple same-key bindings as OR/AND/union/etc.

## 18. Research exit condition

The exact-resolver implementation can proceed without reopening semantic-source interpretation:

`CompiledSemanticIR + current prerequisite attestation + exact SemanticKey + explicit corpora`

is sufficient to deterministically return the three OLiA Noun native plan records or fail closed.

The plan phase should freeze the precise dataclass/fingerprint projections and diagnostic precedence, but no additional ontology/corpus research is required for the first noun slice.
