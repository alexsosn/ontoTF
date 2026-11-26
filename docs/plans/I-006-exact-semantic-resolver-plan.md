# I-006 plan: exact semantic resolver thin slice

**Issue:** #124  
**Baseline:** `main` `4bf840e574e29dbc6997bd8fbe7bc95d444cab1a` after reviewed I-006 research  
**Depends on:** merged I-005/#128, P-003, P-002, R-014, reviewed I-006 research + adversarial amendment  
**Scope:** exact semantic-pivot resolution to native TF/Context-Fabric plan records; no live corpus evaluation or query execution

## 1. Implementation boundary

Implement one new module:

`src/ontotf/semantic_resolver.py`

It consumes only:

- `CompiledSemanticIR` produced by I-005;
- immutable caller-supplied `RuntimePrerequisiteState` records representing separately established runtime compatibility/prerequisite evidence;
- one exact `SemanticResolveRequest`.

It does **not** read mapping/profile/ontology source files, inspect a live TF/Context-Fabric corpus, produce compatibility reports, evaluate TF-native dependency assertions against corpus data, or execute Context-Fabric.

#130 owns production prerequisite evaluation/report-vNext. #131 owns same-corpus multi-binding composition. The later P-003 execution-handoff ticket owns conversion of typed plans to actual Context-Fabric execution.

## 2. Public constants

Freeze these v1 identities:

```python
EXACT_RESOLVER_CONTRACT = "ontotf-exact-semantic-resolver-v1"
PROFILE_RELEASE_FINGERPRINT_ALGORITHM = "ontotf-profile-release-signature-jcs-sha256-v1"
RUNTIME_PREREQUISITE_FINGERPRINT_ALGORITHM = "ontotf-runtime-prerequisite-jcs-sha256-v1"
EXACT_PLAN_FINGERPRINT_ALGORITHM = "ontotf-exact-native-plan-jcs-sha256-v1"
EXACT_RESOLUTION_FINGERPRINT_ALGORITHM = "ontotf-exact-resolution-jcs-sha256-v1"
```

Digest values themselves use the repository convention:

`sha256:<64 lowercase hex>`.

Changing any projection semantics requires a new algorithm/contract identifier.

## 3. Public immutable types

All public dataclasses are `@dataclass(frozen=True)` and deliberately **not** `order=True`. Canonical ordering is explicit UTF-16 code-unit ordering.

### 3.1 `DependencyPrerequisiteResult`

```python
class DependencyPrerequisiteResult:
    dependency_id: str
    result: str                 # pass | fail | unknown
    observed_evidence_digest: str | None
    evaluator_rule_version: str
```

Rules:

- dependency IDs non-empty;
- result closed to `pass|fail|unknown`;
- evaluator rule version non-empty;
- optional evidence digest is opaque content identity; no network/file lookup.

### 3.2 `RuntimePrerequisiteState`

```python
class RuntimePrerequisiteState:
    variant: BundleVariantKey
    profile_release_fingerprint: str
    observed_parent_manifest_digest: str
    parent_state: str           # verified-exact | verified-compatible | unverified | incompatible
    dependency_results: tuple[DependencyPrerequisiteResult, ...]
    active_ontology_bundle_digest: str | None
    ontology_bundle_state: str  # not-required | verified | unavailable
    source_contract: str
```

The dataclass does not carry a caller-authored self-hash. `runtime_prerequisite_fingerprint()` deterministically derives the fingerprint from the fields above. This avoids recursive/self-declared identity while still allowing stale-release detection through `profile_release_fingerprint`.

The prerequisite is trusted **input evidence**, not a substitute for #130's production evaluator. I-006 validates its internal coherence against the compiled release before producing a plan.

### 3.3 `SemanticResolveRequest`

```python
class SemanticResolveRequest:
    key: SemanticKey
    corpora: tuple[str, ...]
    semantic_mode: str = "exact"
```

`corpora` is explicit, non-empty and duplicate-free. Resolver output normalizes it to UTF-16 corpus order; input order never affects result equality/fingerprint.

Only `exact` is implemented.

### 3.4 `SemanticCapabilityView`

Minimal R-014 discovery record:

```python
class SemanticCapabilityView:
    corpus_id: str
    variant: BundleVariantKey
    profile_id: str
    capability_id: str
    state: str                  # active | absent | unavailable
    facts: CapabilityFactsIR
    executable_exact: bool
    prerequisite_fingerprint: str
```

This is discovery only. `SemanticResolveRequest` never accepts a `SemanticCapabilityView` as authority.

### 3.5 `ExactNativePlan`

```python
class ExactNativePlan:
    resolver_contract: str
    corpus_id: str
    semantic_key: SemanticKey
    reference_kind: str         # exactly semantic-pivot
    query_role: str             # exactly semantic-constraint
    semantic_mode: str          # exactly exact
    capability_state: str       # exactly active
    variant: BundleVariantKey
    profile_release_fingerprint: str
    expected_parent_manifest_digest: str
    observed_parent_manifest_digest: str
    parent_state: str
    prerequisite_fingerprint: str
    mapping_id: str
    projection_id: str
    assessment: str             # exactly exact
    native_execution_binding_identity: str
    native_execution_binding: NativeBindingIR
    native_dependencies: tuple[str, ...]
    mapping_semantic_digest: str
    projection_semantic_digest: str
    mapping_review: ReviewFingerprint
    projection_review: ReviewFingerprint
    ontology_lock: OntologyLockFingerprint
    ontology_bundle_digest: str | None
    mapping_evidence: tuple[EvidenceFingerprint, ...]
    projection_evidence: tuple[EvidenceFingerprint, ...]
    plan_fingerprint: str
```

No query string or Context-Fabric object is emitted.

### 3.6 `SemanticResolutionResult`

```python
class SemanticResolutionResult:
    resolver_contract: str
    request: SemanticResolveRequest   # canonicalized corpus order
    plans: tuple[ExactNativePlan, ...]
    comparison_state: str             # exactly-comparable in I-006 success
    losses: tuple[str, ...]           # () in I-006
    resolution_fingerprint: str
```

Any requested-corpus failure prevents a successful result. There is no executable partial success in I-006.

### 3.7 Problems/errors

```python
class SemanticResolutionProblem:
    category: str
    message: str
    corpus_id: str | None = None
    related_id: str | None = None

class SemanticResolutionError(Exception):
    problem: SemanticResolutionProblem
```

Wrong top-level Python object types may use `TypeError`; semantic/runtime contract failures use `SemanticResolutionError`.

## 4. Public callables

Export from `ontotf.__init__`:

```python
profile_release_fingerprint(signature: ProfileReleaseSignature) -> str
runtime_prerequisite_fingerprint(state: RuntimePrerequisiteState) -> str
semantic_capabilities(
    ir: CompiledSemanticIR,
    prerequisites: Iterable[RuntimePrerequisiteState],
    *,
    corpora: Iterable[str] | None = None,
) -> tuple[SemanticCapabilityView, ...]
semantic_resolve(
    ir: CompiledSemanticIR,
    request: SemanticResolveRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> SemanticResolutionResult
```

`semantic_capabilities` is deliberately small: it provides runtime R-014 state for selected/current prerequisite variants. No pagination/UI/filter language beyond optional corpus selection.

`semantic_resolve` is the only execution-authority-producing API in I-006, and only for the semantic-pivot exact family.

## 5. Explicit fingerprint projections

Do **not** use `dataclasses.asdict()` as the versioned identity definition. Define explicit JSON-compatible projections so adding a dataclass field later cannot silently change identity.

All projections use existing `canonical_json_bytes()` + SHA-256.

### 5.1 Profile-release fingerprint

`profile_release_fingerprint()` projects every field of current `ProfileReleaseSignature` with explicit field names:

```text
profile_schema_version
profile_catalog_version
dependency_contract_version
mapping_schema_version
minimum_ontotf_runtime
profiles
capabilities
dependency_records
mapping_digests
ontology_bundle_digest
ontology_locks
mapping_semantic_algorithm
projection_semantic_algorithm
mapping_reviews
projection_reviews
```

Nested lock/review records use their semantic I-005 fields only. Preserve the deterministic tuple ordering already produced by I-005; this fingerprint identifies that compiled release signature rather than inventing new source normalization.

### 5.2 Runtime-prerequisite fingerprint

Projection:

```json
{
  "algorithm": "ontotf-runtime-prerequisite-jcs-sha256-v1",
  "variant": {"...": "all BundleVariantKey fields"},
  "profile_release_fingerprint": "sha256:...",
  "observed_parent_manifest_digest": "...",
  "parent_state": "...",
  "dependency_results": [
    {
      "dependency_id": "...",
      "result": "...",
      "observed_evidence_digest": null,
      "evaluator_rule_version": "..."
    }
  ],
  "active_ontology_bundle_digest": null,
  "ontology_bundle_state": "...",
  "source_contract": "..."
}
```

Dependency results are canonical UTF-16 `dependency_id` order. Duplicate dependency IDs fail before hashing; no last-one-wins behavior.

### 5.3 Exact plan fingerprint

Projection binds at least:

```text
algorithm
resolver_contract
corpus_id
semantic key fields
reference_kind
query_role
semantic_mode
variant key
profile_release_fingerprint
expected parent digest
observed parent digest
parent_state
prerequisite_fingerprint
mapping_id
projection_id
assessment
native_execution_binding_identity
native_dependencies
mapping_semantic_digest
projection_semantic_digest
mapping/projection ReviewFingerprint semantic fields
ontology-lock fingerprint
ontology_bundle_digest
mapping/projection evidence fingerprints
```

The native binding payload itself need not be rehashed separately because `native_execution_binding_identity` already uses I-005's JCS/SHA-256 identity and the plan also stores the typed binding. Before emitting, verify the stored binding identity matches a deterministic projection of that binding; a mismatch in a manually malformed IR fails `invalid_compiled_ir`.

### 5.4 Whole-resolution fingerprint

Projection:

```text
algorithm
resolver_contract
canonical request (full SemanticKey + UTF-16-sorted corpora + exact mode)
comparison_state = exactly-comparable
losses = []
UTF-16-corpus-ordered plan_fingerprints
```

Input request order does not affect this fingerprint or result equality.

## 6. Request validation

Validate before prerequisite/index work:

1. exact `CompiledSemanticIR` / `SemanticResolveRequest` types;
2. `semantic_mode == "exact"`, otherwise `unsupported_semantic_mode`;
3. non-empty tuple/list of non-empty corpus strings;
4. duplicate corpus ID -> `invalid_corpus_selection`;
5. profile ID in `PROFILE_IDS`;
6. capability ID in `CAPABILITY_IDS` and capability prefix scopes to the requested profile;
7. formal kind in `FORMAL_KINDS`;
8. semantic role in `SEMANTIC_ROLES`;
9. non-empty target string.

There is no label/CURIE/namespace/hierarchy normalization.

## 7. Prerequisite indexing and selection

Materialize prerequisite iterable once. Type-check every item.

Build by corpus/variant using explicit UTF-16 sorting.

For every requested corpus:

- zero prerequisite records -> `missing_prerequisite`;
- prerequisite whose variant is absent from `ir.variants` -> `stale_prerequisite`;
- profile-release fingerprint mismatch -> `stale_prerequisite`;
- more than one prerequisite capable of selecting different current variants for the corpus -> `ambiguous_prerequisite_variant`;
- do not choose newest/lexical-first/closest variant.

For the resolver, exactly one current prerequisite record per requested corpus must survive freshness checks.

For `semantic_capabilities`, the same freshness/uniqueness rule selects the current variant even when its operational state is non-executable; discovery can then report `unavailable` rather than turning an incompatible parent into an executable plan.

## 8. Executable prerequisite validation

Precedence after fresh variant selection:

### Parent

- `unverified` -> `parent_unverified`;
- `incompatible` -> `parent_incompatible`;
- unknown state -> `invalid_prerequisite`;
- `verified-exact` requires `observed_parent_manifest_digest == variant.expected_parent_manifest_digest`, otherwise `stale_prerequisite`;
- `verified-compatible` requires observed != expected, otherwise `invalid_prerequisite`.

### Complete dependencies

Expected dependency IDs are exactly the first elements of `BundleVariantIR.release_signature.dependency_records`.

For executable state:

- prerequisite dependency ID set must exactly equal expected ID set; missing or extra IDs -> `stale_prerequisite`;
- every result must be `pass`; `fail|unknown` -> `dependency_unavailable`;
- duplicate dependency IDs -> `invalid_prerequisite`.

This deliberately enforces complete release closure, not target-local `TargetBindingIR.native_dependencies` only.

### Active ontology bundle

If selected variant's `ontology_bundle_digest is None`:

- require `ontology_bundle_state == "not-required"`;
- require `active_ontology_bundle_digest is None`.

If non-null:

- `unavailable` -> `ontology_bundle_unavailable`;
- require state exactly `verified`;
- require attested digest exactly equal variant digest;
- mismatch -> `stale_prerequisite`.

Projection `ontology_bundle_requirement`, if present, must agree with the selected variant's bundle digest; mismatch in compiled IR -> `invalid_compiled_ir`.

## 9. Capability-state overlay

For a selected variant and requested `(profile, capability)` find exact `CapabilityKey` in `ir.capability_facts`.

State:

- no fact or `reviewed_native_support == 0` -> `absent`;
- positive support + fresh but non-executable parent/dependency/bundle prerequisite -> `unavailable`;
- positive support + executable prerequisite -> `active`.

`executable_exact` is `state == active and facts.exact > 0`.

`semantic_capabilities` returns these views only; no target tuple is implied.

`semantic_resolve` requires `active` before target lookup. Passing a capability view is not accepted as an input.

## 10. Exact semantic lookup

Use only `CompiledSemanticIR.semantic_index` and exact `SemanticKey` equality.

For each requested corpus after prerequisite + active-capability gates:

1. locate the one index row whose key equals the complete request key;
2. if no row -> `semantic_tuple_absent`;
3. restrict bindings to selected corpus and exact selected `BundleVariantKey`;
4. if none -> `semantic_tuple_absent`;
5. validate each candidate binding's own profile/capability/target/formal-kind/semantic-role equals the index/request key and routing is exactly `semantic-pivot + semantic-constraint`; mismatch -> `invalid_compiled_ir`;
6. partition by assessment;
7. zero exact rows but one or more non-exact rows -> `non_exact_mapping`;
8. exactly one exact row -> continue;
9. more than one exact row -> `multiple_exact_bindings` (no implicit OR/AND/first-row selection; #131 owns composition).

Defensive checks before plan emission:

- mapping and projection review status are still `reviewed`;
- projection's `ontology_bundle_digest` equals selected variant bundle digest;
- native binding identity recomputes to the stored identity;
- binding variant/corpus matches selection.

These checks validate compiled IR coherence only; they do not reopen I-004 source semantics.

## 11. Deterministic diagnostic precedence

Global/request errors precede corpus-specific errors.

For requested corpora, process canonical UTF-16 corpus order and fail on the first problem in this precedence:

1. missing/stale/ambiguous prerequisite selection;
2. invalid/inconsistent parent state;
3. dependency closure failure;
4. ontology-bundle prerequisite failure;
5. capability absent/unavailable;
6. semantic tuple absent;
7. non-exact-only mapping;
8. multiple exact bindings;
9. invalid compiled-IR coherence discovered during plan emission.

Known failure must not be downgraded to a later generic absence.

Public categories frozen for RED:

```text
invalid_request
unsupported_semantic_mode
unknown_request_vocabulary
invalid_corpus_selection
invalid_prerequisite
missing_prerequisite
stale_prerequisite
ambiguous_prerequisite_variant
parent_unverified
parent_incompatible
dependency_unavailable
ontology_bundle_unavailable
capability_absent
capability_unavailable
semantic_tuple_absent
non_exact_mapping
multiple_exact_bindings
invalid_compiled_ir
```

## 12. Successful exact plan/result

One plan per requested corpus, canonical UTF-16 corpus order.

For the accepted three-corpus noun request, plans must contain:

- BHSA -> `word.sp=subs`;
- ETCBC Syriac -> `word.sp=subs`;
- ETCBC ExtraBiblical -> `word.sp=subs`.

All have:

- `assessment=exact`;
- `reference_kind=semantic-pivot`;
- `query_role=semantic-constraint`;
- `capability_state=active`;
- current variant/prerequisite provenance;
- mapping/projection/lock/review/evidence provenance;
- deterministic plan fingerprints.

The successful result has:

- canonical request corpora;
- all requested plans;
- `comparison_state=exactly-comparable`;
- `losses=()`;
- deterministic whole-resolution fingerprint.

## 13. TDD fixture/control strategy

Add `tests/i006/`.

### `tests/i006/_fixtures.py`

Reuse `tests/i005/_fixtures.py` to build production-valid BHSA/Syriac/ExtraBiblical noun bundles, then:

1. structurally validate source fixtures;
2. pass I-004 `validate_semantic_bundle()`;
3. compile through public `compile_semantic_ir()`;
4. construct explicit runtime prerequisite records for each current variant from the compiled release signature;
5. dependency results are generated from the selected release signature's dependency IDs, all `pass` for positive controls;
6. exact-parent attestation uses observed digest == expected;
7. bundle state is `not-required` for the current noun fixtures unless an explicit bundle test installs one.

Fixture controls must run without importing the new resolver module.

### Clean RED attribution

Commit tests/workflow before `src/ontotf/semantic_resolver.py` or new `ontotf.__init__` exports.

RED workflow has two steps:

1. fixture/I-005 controls — **green**;
2. I-006 resolver contract — **red solely because the public resolver API/module is absent**.

No production change before this RED is observed on Python 3.10 and 3.12.

## 14. Mandatory RED matrix

### Public/exact happy path

1. intended public imports are absent on RED head;
2. BHSA noun -> one exact plan with typed `word/sp/subs` binding;
3. Syriac noun -> same;
4. ExtraBiblical noun -> same;
5. explicit three-corpus request returns all three in UTF-16 corpus order;
6. reversing request corpus order produces equal result/fingerprint;
7. plans expose full required mapping/projection/parent/bundle/lock/review/evidence provenance;
8. plan routing is exactly semantic-pivot + semantic-constraint;
9. result is exactly-comparable with empty losses;
10. no query string/CF execution object is present.

### Request fail-closed

11. empty corpora -> `invalid_corpus_selection`;
12. duplicate corpus -> `invalid_corpus_selection`;
13. approximate mode -> `unsupported_semantic_mode`;
14. unknown profile/capability/kind/role -> `unknown_request_vocabulary`;
15. matching target with wrong profile/capability/kind/role -> `semantic_tuple_absent` or capability failure according to frozen precedence;
16. unrequested corpus row never leaks into plans.

### Prerequisite/variant

17. missing prerequisite -> `missing_prerequisite`;
18. unknown variant -> `stale_prerequisite`;
19. matching variant with wrong profile-release fingerprint -> `stale_prerequisite`;
20. two fresh candidate prerequisite variants for one corpus -> `ambiguous_prerequisite_variant`;
21. verified-exact + observed parent mismatch -> `stale_prerequisite`;
22. unverified -> `parent_unverified`;
23. incompatible -> `parent_incompatible`;
24. verified-compatible with observed==expected -> `invalid_prerequisite`;
25. missing one release dependency -> `stale_prerequisite`;
26. extra dependency -> `stale_prerequisite`;
27. duplicate dependency ID -> `invalid_prerequisite`;
28. fail/unknown dependency -> `dependency_unavailable`;
29. non-null variant bundle + unavailable state -> `ontology_bundle_unavailable`;
30. stale bundle digest -> `stale_prerequisite`;
31. null-bundle variant with fabricated active digest/state -> `invalid_prerequisite` or `stale_prerequisite` per implementation branch fixed above.

### Capability vs execution

32. reviewed native-only support can yield capability `active` but cannot resolve absent requested semantic tuple;
33. unsupported-only facts -> capability `absent`;
34. positive facts + unverified/incompatible prerequisite -> capability `unavailable` in `semantic_capabilities`;
35. an `active` discovery view cannot be passed to or substitute for exact semantic index authority.

### Assessment/routing/index isolation

36. non-exact close/broader/narrower/related semantic row never resolves in exact mode;
37. ambiguous/native-only/unsupported do not become semantic target plans;
38. same target in authority index does not satisfy `semantic_resolve`;
39. hand-crafted mismatched semantic-index binding routing/key fails `invalid_compiled_ir`.

### Multi-binding

40. two exact bindings in one selected corpus/variant -> `multiple_exact_bindings`;
41. exact + non-exact rows selects the single exact row only;
42. two bindings are never silently ORed/ANDed or first-selected.

### Fingerprints

43. profile-release fingerprint stable on repeat;
44. prerequisite dependency input order does not change prerequisite fingerprint;
45. observed parent change changes prerequisite/plan/resolution fingerprint;
46. dependency result change changes prerequisite/plan/resolution fingerprint;
47. profile-release fingerprint change is stale and cannot produce a plan;
48. ontology-bundle identity change changes prerequisite/plan identity;
49. native binding/mapping/projection semantic identity change changes plan identity or fails stale coherence;
50. resolver contract participates in plan/result fingerprint fixed projection;
51. audit-only data not represented in I-005 semantic fingerprints cannot alter plan identity;
52. whole resolution fingerprint changes if requested corpus set changes.

## 15. GREEN implementation order

1. frozen constants/problem/input/output dataclasses;
2. UTF-16 helpers and explicit semantic/profile/prerequisite fingerprint projections;
3. request validation/canonicalization;
4. prerequisite indexing/freshness checks;
5. executable parent/dependency/bundle gate;
6. capability overlay + minimal `semantic_capabilities`;
7. exact semantic-index lookup and single-binding gate;
8. compiled-IR coherence checks;
9. immutable plan builder + plan fingerprint;
10. canonical result + comparison state + resolution fingerprint;
11. public exports.

Do not refactor I-005/I-004 unless a RED proves a required shared public helper. Reuse `canonical_json_bytes()` and `native_binding_identity()` rather than implementing another JSON/hash stack.

## 16. CI

Add `.github/workflows/i006-semantic-resolver.yml`:

- push on `impl/i006-exact-semantic-resolver`;
- pull_request path filters for resolver source, `tests/i006/**`, relevant I-005/I-004 source/tests, research/plan and workflow;
- exact-head `actions/checkout@v5`;
- `actions/setup-python@v6`;
- Python 3.10 + 3.12;
- editable install;
- fixture/control step;
- I-006 focused contract;
- I-005 regressions;
- I-004 regressions.

Do not duplicate generic full-suite ownership. `.github/workflows/full-suite.yml` is authoritative.

Final implementation merge requires:

- exact-head I-006 green on 3.10/3.12;
- I-005 + I-004 regressions green;
- authoritative full suite green;
- current-main integration check;
- fresh logically-independent adversarial review of the exact final head;
- any material repair after review triggers a new review.

## 17. Explicit non-goals

I-006 does not:

- inspect live TF/CF data;
- compute observed parent manifests;
- evaluate dependency assertions against corpus data;
- produce/migrate compatibility reports (#130);
- execute Context-Fabric;
- produce CF query strings;
- resolve approximate mappings;
- resolve authority/identity/identifier families;
- infer labels/features/hierarchy/CURIEs/namespaces;
- use network/RDF/SPARQL/MCP state;
- compose multiple exact bindings (#131);
- introduce generic source/data adapters.

## 18. Exit condition

Given compiled I-005 IR, fresh explicit prerequisite attestations, the exact OLiA Noun `SemanticKey`, and explicit BHSA/Syriac/ExtraBiblical corpus selection, `semantic_resolve()` returns three deterministic immutable native plan records carrying `word.sp=subs`, full required provenance, `exactly-comparable` state and verifiable plan/resolution fingerprints without source reinterpretation or query execution.
