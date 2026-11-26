# I-006 research adversarial-review amendment

**Issue:** #124  
**Amends:** `docs/research/I-006-exact-semantic-resolver.md`  
**Reviewed head before amendment:** `75c3687c21c3ad359c1edc7f6d7e62c888dced67`

This amendment is normative where it is more specific than the original research artifact.

## 1. Finding: resolved-plan routing was under-specified

P-003 §10/§11 requires a resolved target atom to expose the requested target **and routing**, formal kind, semantic role, profile and capability. The original I-006 research plan-record sketch preserved `SemanticKey`, which contains profile/capability/target/formal-kind/semantic-role, but it omitted the routing pair.

For `semantic_resolve` v1 the only legal routing pair is fixed and explicit:

```text
reference_kind = semantic-pivot
query_role = semantic-constraint
```

`ExactNativePlan` must retain both fields even though the API family implies them. They participate in plan fingerprint identity. A later authority resolver must not be able to reuse an exact semantic plan merely because target/kind/role text happens to coincide.

The plan gate must add RED coverage proving the emitted plan has exactly this routing pair and that authority-value rows can never satisfy `semantic_resolve`.

## 2. Finding: comparison state is part of the P-003 resolver result

P-003 resolver step 9 requires a comparison/loss state. The original research artifact described whole-request failure but did not make the successful exact comparison state explicit.

I-006 is exact-only. Therefore a successful result over one or more requested corpora has:

```text
comparison_state = exactly-comparable
losses = ()
```

If any requested corpus cannot produce an authorized exact plan, the complete request remains non-executable/fails closed; I-006 does not return a successful `partial/non-executable` result with some runnable plans.

`SemanticResolutionResult` must retain `comparison_state`, and the whole-resolution fingerprint must bind it.

## 3. Finding: resolver contract identity must be explicit

A versioned hash algorithm name is not sufficient if the fingerprint projection can silently change while keeping the same callable/API behavior. The plan phase must freeze an explicit resolver/fingerprint contract identifier and include it in plan/result identity.

Recommended v1 constants/identities are conceptually:

```text
EXACT_RESOLVER_CONTRACT = tfont-exact-semantic-resolver-v1
PROFILE_RELEASE_FINGERPRINT_ALGORITHM = tfont-profile-release-signature-jcs-sha256-v1
RUNTIME_PREREQUISITE_FINGERPRINT_ALGORITHM = tfont-runtime-prerequisite-jcs-sha256-v1
EXACT_PLAN_FINGERPRINT_ALGORITHM = tfont-exact-native-plan-jcs-sha256-v1
EXACT_RESOLUTION_FINGERPRINT_ALGORITHM = tfont-exact-resolution-jcs-sha256-v1
```

The exact spellings remain a plan-gate decision, but the semantic rule is fixed: changing resolver interpretation/projection requires a new versioned identity, never silent reuse.

Both per-plan and whole-resolution projections must include the resolver contract identifier.

## 4. Revised minimum `ExactNativePlan` evidence surface

The plan phase must freeze at least these execution/provenance fields:

```text
resolver_contract
corpus_id
semantic_key
reference_kind = semantic-pivot
query_role = semantic-constraint
semantic_mode = exact
capability_state = active
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
native_execution_binding
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

This is still a native-plan **record**, not a Context-Fabric query string. No protocol/MCP/session fields belong here.

The plan may retain additional already-compiled projection metadata (for example bundle requirement/declaration evidence) for explanation, but such additions must not reopen source interpretation and must use existing immutable I-005 records.

## 5. Revised successful result surface

`SemanticResolutionResult` must contain at least:

```text
resolver_contract
request
plans  # canonical UTF-16 corpus order
comparison_state = exactly-comparable
losses = ()
resolution_fingerprint
```

A successful result never contains an unavailable/partial requested corpus in I-006.

## 6. Additional RED cases

Add to the I-006 plan matrix:

1. every exact semantic plan exposes `semantic-pivot + semantic-constraint` routing;
2. same target/kind/role in `authority_index` cannot satisfy `semantic_resolve`;
3. successful one-corpus and three-corpus exact results report `exactly-comparable` and empty losses;
4. changing resolver-contract identity changes plan/result fingerprints;
5. changing routing identity changes fingerprint projection or is rejected before plan creation;
6. no successful result is emitted with a partial requested corpus set.

## 7. Review closure

With these amendments the research boundary satisfies the P-003 resolved-atom and comparison-state requirements while remaining inside #124 scope:

- exact semantic-pivot resolution only;
- separately established runtime prerequisite state;
- no live corpus compatibility evaluation (#130);
- no multi-binding composition inference (#131);
- no Context-Fabric execution;
- no approximate/authority/identity/identifier resolution.
