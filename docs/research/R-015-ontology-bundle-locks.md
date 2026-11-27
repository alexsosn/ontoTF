# R-015: ontology-bundle composition and bridge-lock provenance semantics

**Status:** research/prototype complete; hardened after exact-head adversarial reviews; ready for final logically-independent review  
**Issue:** #49  
**Recorded:** 2026-09-07  
**Depends on:** accepted P-001/R-002/R-006/R-010/R-012, accepted I-002 semantic-digest contract, and merged R-011/R-013/R-014

## Decision

ontoTF semantic composition should be a **content-addressed active bundle of full semantic ontology-lock identities plus explicit term-scoped reviewed bridge artifacts**. It is not one OWL import closure, not a bag of live namespace URLs, and not a composition keyed only by ontology payload hashes.

The active bundle identity is derived from:

```text
unique active profile-contract IDs
+ accepted I-002 semantic ontology-lock identity records
+ reviewed bridge artifacts referenced by active dependency edges
+ active dependency bindings
    ↓ accepted I-002/JCS canonicalization rules
SHA-256 semantic-bundle identity
```

The main invariant is:

> A dependency is executable only when its participating consumer/required locks are present under the expected release/payload identity and the dependency is satisfied either by that exact locked release or by one content-valid, reviewed, explicitly compatible bridge whose endpoint release/digests and term scope match the participating locks and dependency edge.

Inactive optional-profile diagnostics remain outside active execution and active bridge closure. The research prototype is explicitly schema-versioned: only exact integer `schema_version: 1` is interpreted by the v1 validator; unknown, missing, bool-coerced, string or numeric-lookalike versions fail closed.

## 1. Why individual ontology payload hashes are insufficient

P-001 introduced ontology locks, but accepted I-002 review later established an important distinction:

- `content_digest` identifies the pinned ontology payload bytes;
- `{lock_id, content_digest}` does **not** identify all semantic pinning choices of a ontoTF ontology lock.

The normative I-002 ontology-lock semantic identity therefore includes:

Required:

- `lock_id`;
- `ontology_id`;
- `support_tier`;
- `term_namespace`;
- `release`;
- `source_uri`;
- `content_digest`;
- `license`;
- `terms_used`.

Included when present:

- `upstream_release_status`;
- `source_revision`;
- `redistribution_policy`.

Excluded from that semantic identity:

- retrieval timestamps;
- snapshot storage paths/filenames;
- layout/presentation metadata.

R-015 therefore **must not** reduce a participating lock back to `{lock_id, content_digest}`. A release change or a `terms_used` change with identical ontology payload bytes changes the semantic bundle identity.

The research validator directly reuses the accepted I-002 normalization implementation for these semantic lock records. That helper is private today; this is acceptable only because `scripts/research/r015_bundle_id.py` is explicitly non-production. P-003 should expose/share a stable production primitive rather than copying the field/normalization rules.

## 2. Canonical bundle identity

The prototype reuses `ontotf.digests.canonical_json_bytes`, i.e. the accepted RFC 8785/JCS contract, rather than implementing another JSON canonicalizer.

Set-like profile-contract IDs use the same I-002 UTF-16 ordering/duplicate semantics. Ontology-lock records use the same I-002 semantic-lock normalizer, including set-like `terms_used`. Bridge and active-edge collections are ordered by their canonical JCS bytes.

Digest representation is the accepted ontoTF form:

```text
sha256:<64 lowercase hexadecimal digits>
```

The prototype validates this shape for:

- ontology `content_digest` values;
- bridge endpoint payload digests;
- evidence digest;
- bridge content digest;
- reviewed-content digest;
- exact-lock dependency digest.

This avoids a second R-015-only identity dialect.

The bundle contract itself is also version-gated. `schema_version` is not merely another hashed field: v1 code accepts only an exact integer `1`. A future version requires an explicit versioned contract/implementation amendment rather than being interpreted under v1 semantics because its other fields happen to look familiar.

## 3. Three identity layers

### 3.1 Ontology-lock semantic identity

A bundle receives already-assembled I-002 semantic ontology-lock identity records. It does not accept raw P-001 lock files with retrieval/storage fields mixed into that semantic projection.

The distinction matters because `content_digest` identifies the ontology payload while fields such as `release`, `term_namespace`, and `terms_used` are additional semantic/pinning choices.

Changing any I-002 semantic lock field changes bundle identity. Reordering `terms_used` alone does not.

### 3.2 Bridge content identity

A bridge is one explicit cross-release semantic assertion. The prototype content-addresses at least:

- source lock ID;
- source release;
- source ontology payload digest;
- target lock ID;
- target release;
- target ontology payload digest;
- explicit term scope (`source_term`, `target_term`, relation);
- compatibility conclusion;
- evidence ID + immutable evidence digest;
- runtime strength;
- runtime limitations;
- optional assertion-kind field when supplied.

The bridge review wrapper additionally contains:

- `review_status`;
- the exact bridge-content digest reviewed;
- stable review ID;
- stable reviewer ID;
- timezone-aware review timestamp.

Changing endpoint release/digest, term scope, compatibility, evidence, or runtime semantics requires a new bridge content digest and therefore invalidates an old `reviewed_content_digest` binding.

Bridge content is term-scoped. A valid F28 bridge does not upgrade unrelated FRBRoo terms, and no bridge implies ontology-wide release equivalence.

### 3.3 Bundle identity

The bundle combines exact semantic lock identities, reviewed bridge records and active dependency bindings into one deterministic resolution identity.

Review identity/date are operationally identity-bearing because changing which review authorizes a bridge changes the effective reviewed bundle. Reviewer display labels and other presentation-only bridge metadata are excluded.

Audit/storage metadata for ontology locks is not silently ignored *inside* semantic lock records; it belongs outside the semantic lock identity input.

## 4. Bridge term-to-lock binding

A bridge scope is not valid merely because its term strings are non-empty.

When the participating endpoint release and payload digest match the bridge endpoint, the prototype additionally requires:

```text
bridge.scope.source_term ∈ source_lock.terms_used
bridge.scope.target_term ∈ target_lock.terms_used
```

Thus a typo such as `F288` cannot become content-addressed, reviewed and exact-executable merely because it is syntactically a string.

This is a **cross-artifact consistency check**, not ontology truth validation. Accepted I-002 explicitly delegates proof that a declared term really exists in the pinned ontology to later assembly/truth-validation work (I-004/I-006/P-003). R-015 does not claim that `terms_used` membership alone proves an ontology assertion.

If an endpoint lock is absent or differs by release/payload digest, dependency evaluation reports the missing/stale endpoint instead of trying to validate term membership against the wrong release.

## 5. Dependency-edge contract

Dependency activation is security/semantic state, not generic JSON truthiness. If an `active` field is present it must be an **exact JSON boolean**. Values such as `0`, `1`, `null`, `"false"`, `[]` or `{}` are schema-invalid and non-executable. When `active` is omitted, v1 defaults the dependency to active so omission cannot hide an unresolved required dependency.

### Exact locked dependency

Conceptually:

```json
{
  "id": "crmtex-crm",
  "consumer": "crmtex-2.0",
  "requires": "crm-7.1.2",
  "satisfied_by": "lock:crm-7.1.2",
  "required_lock_release": "7.1.2",
  "required_lock_digest": "sha256:...",
  "active": true
}
```

Success requires:

- participating consumer lock;
- `satisfied_by` lock ID equals `requires`;
- explicit required release;
- explicit required payload digest;
- participating required lock matches both.

Missing release or digest is `unbound-exact-lock`; a release/digest mismatch is non-executable.

### Bridge-satisfied dependency

Conceptually:

```json
{
  "id": "crmtex-f28",
  "consumer": "crmtex-2.0",
  "requires": "frbroo-2.4",
  "satisfied_by": "bridge:f28-continuity",
  "required_bridge_scope": {
    "source_term": "frbroo-2.4:F28",
    "target_term": "lrmoo-1.1.1:F28",
    "relation": "reviewed-continuity"
  },
  "active": true
}
```

Success requires:

- participating consumer lock;
- bridge source lock equals `edge.requires`;
- bridge and edge scope match exactly;
- source/target endpoint locks participate;
- bridge source/target release and payload digests match those locks;
- scoped source/target terms are declared in the exact endpoint locks' `terms_used`;
- bridge review is `reviewed` and bound to its current content digest;
- compatibility is explicitly `compatible`;
- the current research exact-mode gate sees `runtime_strength=exact`.

R-016, not R-015, owns any later mode-aware authorization of approximate/related execution.

## 6. Fail-closed outcomes

The reference contract distinguishes outcomes equivalent to:

- `satisfied-exact-lock`;
- `satisfied-reviewed-bridge`;
- `inactive`;
- `missing-consumer-lock`;
- `missing-lock`;
- `dependency-lock-mismatch`;
- `unbound-exact-lock`;
- `missing-bridge`;
- `bridge-requires-mismatch`;
- `bridge-scope-mismatch`;
- `stale-bridge`;
- `unreviewed-bridge`;
- `incompatible-bridge`;
- `unknown-bridge-compatibility`;
- `non-exact-bridge-strength`.

Malformed semantic lock records, malformed/duplicate IDs, invalid digest representation, missing endpoint release/digest, invalid scope, bridge content-digest mismatch, exact-lock/bridge term-membership violations, non-boolean activation markers, and missing/unsupported/wrong-type schema versions are schema/identity errors and therefore non-executable.

## 7. Optional-profile semantics

Mandatory distinction:

```text
optional profile absent/inactive
    !=
profile active but required bridge unresolved
```

Example:

- a corpus with no archaeology capability has no active CRMarchaeo dependency and no bridge error;
- a future corpus activates CRMarchaeo semantics, so those dependency edges enter its active bundle;
- if the required old/current CRM or CRMsci bridge is missing, stale, unreviewed or incompatible, that activated capability becomes unavailable/non-executable with an explicit dependency diagnostic.

Inactive diagnostic edges do not affect active bundle identity. Bridge locks referenced only by inactive edges are not valid active-bundle content. Only an explicit boolean `false` may create the inactive state in v1; false-like values cannot suppress validation.

## 8. Authoritative version-skew cases

### CRMtex 2.0

CRMtex 2.0 declares dependencies on:

- CIDOC CRM 7.1.2;
- CRMinf 0.7(b);
- CRMsci 2.0;
- FRBRoo 2.4.

Primary declaration: <https://cidoc-crm.org/extensions/crmtex/html/CRMtex_v2.0.html>.

R-012 found a concrete bridge surface around CRMtex `TX2 Writing` → FRBRoo 2.4 `F28 Expression Creation`. The official FRBRoo→LRMoo migration table retains F28, supporting a reviewed, release-scoped continuity bridge for that term.

R-012 did **not** find equivalent evidence permitting automatic old-CRMinf `I1` → current-CRMinf `I1` axiom substitution, and it explicitly treats CRMtex `TX14 Reading` → CRMinf `I16 Meaning Comprehension` as composition/sequencing rather than class equivalence.

R-015 therefore preserves exact source/target releases in the bridge artifact instead of assuming a lock ID or shared local code is sufficient.

### Current LRMoo / CRMinf

LRMoo 1.1.1 and CRMinf 1.2.1 use CIDOC CRM 7.1.3 as their current CRM basis. That does not retroactively modernize CRMtex 2.0's historical dependency closure.

Primary declarations:

- <https://cidoc-crm.org/extensions/lrmoo/html/LRMoo_v1.1.1.html>
- <https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html>.

### CRMarchaeo 2.1.1

Stable CRMarchaeo 2.1.1 references CIDOC CRM 7.1.2 and CRMsci 2.0, while the accepted current ontoTF heritage/science stack uses CIDOC CRM 7.1.3 and CRMsci 3.2.

Primary release/declaration source: <https://cidoc-crm.org/extensions/crmarchaeo/html/CRMarchaeo_v2.1.1.html>.

This independently confirms that ontoTF cannot model the CIDOC-family composition as one globally current import closure.

## 9. Composition examples

### OLiA + OntoLex + SKOS

A linguistic+lexical profile can carry separate semantic lock identities for OLiA, OntoLex and SKOS. Multiple locks do not imply a bridge. If the reviewed mappings do not cross a release-skew dependency, the active bundle contains zero bridge locks.

### CIDOC CRM + LRMoo + CRMinf

A current textological composition can use exact semantic locks for CRM 7.1.3, LRMoo 1.1.1 and CRMinf 1.2.1. Bundle identity still captures all lock semantic identities even when no bridge is required.

### CRMtex 2.0 + F28 bridge

A query using only CRMtex TX7 written-text segments needs no F28 bridge merely because TX2 exists elsewhere in CRMtex.

If a query activates an accepted TX2/F28 path, the active bundle includes the exact FRBRoo 2.4 and LRMoo 1.1.1 lock identities, the release/payload-bound F28 bridge, and the scoped dependency edge. No unrelated FRBRoo term becomes executable.

### CRMarchaeo 2.1.1

A corpus with no archaeology capability simply omits the profile. A future active archaeology profile must represent any needed CRM 7.1.2→7.1.3 or CRMsci 2.0→3.2 bridge explicitly; loading a current CRMsci lock does not silently replace the historical dependency.

## 10. Migration behavior

### Ontology payload update

Changing participating `content_digest` changes bundle identity. A bridge pinned to the previous endpoint digest becomes `stale-bridge`.

### Ontology semantic-lock update with identical payload

Changing `release`, `terms_used`, namespace, source pinning or another accepted I-002 semantic identity field changes bundle identity even if ontology payload bytes are unchanged.

If endpoint `release` changes while a bridge remains pinned to the old release, the bridge is stale even when `content_digest` happens to be unchanged.

### Bridge semantic edit

Changing endpoint release/digest, term scope, compatibility, evidence, runtime strength or runtime limitations changes bridge content digest. The prior review no longer authorizes it until `reviewed_content_digest` is refreshed by a new review.

### Bundle-contract version update

Changing the bundle schema version is not treated as an ordinary data mutation. A validator that implements v1 must reject any other version until a versioned amendment defines the new semantics and migration path.

### Inactive/registry-only update

An ontology/profile artifact outside the active selected lock/dependency closure does not change the active bundle identity.

## 11. Agent-facing provenance

### `semantic_capabilities`

Compact output should expose at least:

- profile ID/contract version;
- bundle digest;
- active ontology lock IDs/releases;
- aggregate active bridge state/count;
- profile operational state.

It should not dump every bridge or ontology term by default.

### `semantic_resolve`

Per-corpus plan should expose:

- bundle digest;
- mapping/projection IDs;
- required ontology lock IDs/releases;
- bridge IDs traversed for requested atoms;
- unresolved dependency state/reason;
- execution allowed/denied.

### Full explanation

Add endpoint release/payload digests, bridge scope, bridge content digest, reviewed-content digest, evidence/reviewer/date provenance and dependency path.

Pagination/results must not silently switch bundle identity.

## 12. P-001 / I-002 retained vs P-003 amendments

### Retain

- P-001 individual ontology lock/source provenance;
- accepted I-002 semantic ontology-lock identity fields;
- I-002 RFC 8785/JCS canonicalization;
- `sha256:<64 lowercase hex>` digest representation;
- set-like normalization semantics;
- fail-closed component/parent compatibility discipline.

### P-003 must add or expose

- first-class semantic-bundle identity;
- explicit bundle-schema versioning with unsupported-version fail-closed behavior;
- a stable public/shared helper for I-002 ontology-lock semantic identity normalization (the research prototype currently uses the existing private helper rather than copying it);
- multiple semantic ontology-lock identities per active profile/query bundle;
- explicit bridge artifacts and bridge content digests;
- endpoint lock ID + release + payload-digest binding;
- bridge term membership against exact endpoint `terms_used`;
- term-scoped active dependency edges with exact-boolean activation semantics;
- exact-lock release+digest binding;
- bundle/bridge identity in normalized IR/resolution fingerprints;
- inactive optional-profile separation;
- bridge/evidence/review provenance in explanations;
- fail-closed ontology-term truth validation against pinned ontology snapshots through the assembly/validation layer; `terms_used` membership alone is not sufficient proof.

A single per-mapping ontology payload digest or one live namespace URI is insufficient.

## 13. Executable research/TDD contract

Non-production artifacts:

- `scripts/research/r015_bundle_id.py`;
- `tests/research/test_r015_bundle_id.py`;
- `tests/research/test_r015_bridge_provenance.py`;
- `tests/research/test_r015_jcs_contract.py`;
- `tests/research/test_r015_lock_identity.py`;
- `tests/research/test_r015_active_flag.py`;
- `.github/workflows/r015-bundle-research.yml`.

The suites cover at least:

1. JCS rather than Python-JSON canonicalization;
2. canonical SHA-256 representation;
3. deterministic set/list ordering;
4. full accepted I-002 ontology-lock semantic identity;
5. `terms_used` set normalization;
6. release/semantic-field sensitivity with unchanged ontology payload digest;
7. source/target bridge-term membership;
8. endpoint release and payload-digest binding;
9. bridge evidence/reviewer/date/runtime provenance;
10. stale review after semantic bridge edits;
11. duplicate profile/lock/bridge/edge identities;
12. exact-lock release/digest requirements;
13. scope/edge/source-lock graph binding;
14. missing/stale/unreviewed/incompatible/unknown/non-exact bridge failures;
15. inactive optional dependency separation;
16. exact-boolean activation and missing-activation defaults-to-active behavior;
17. unsupported/malformed/missing schema-version rejection;
18. unreferenced/inactive-only bridge rejection;
19. presentation/audit metadata kept outside semantic lock identity.

The prototype does not perform ontology reasoning and does not prove that declared `terms_used` strings occur in the pinned ontology bytes. It validates an explicit reviewed ontoTF composition contract.

## 14. Non-goals

R-015 does not:

- choose final production JSON/YAML field spelling;
- implement production bundle loading;
- replace P-001 ontology locks;
- authorize approximate execution (R-016);
- define external authority query/reference semantics (R-017);
- require RDF/OWL imports or a triplestore at runtime;
- assert ontology-wide equivalence between releases;
- cryptographically authenticate a reviewer identity;
- prove ontology term existence independently of the later assembly/truth-validation layer.

## 15. Acceptance trace

- [x] deterministic composed bundle identity without a single OWL import closure;
- [x] reconciled bundle ontology identity with the accepted I-002 semantic-lock amendment rather than payload-only `{lock_id,digest}`;
- [x] reuses I-002 JCS/set normalization in the research prototype;
- [x] bridge artifacts are content-addressed, evidence/review bound and release scoped;
- [x] bridge use is exact term scoped and checked against exact endpoint `terms_used`;
- [x] exact-lock dependencies require release + payload digest;
- [x] missing/stale/unreviewed/incompatible/non-exact dependencies fail closed;
- [x] inactive optional profile is distinct from active unresolved bridge dependency;
- [x] dependency activation accepts only exact booleans and omission defaults to active;
- [x] unsupported/missing/wrong-type bundle schema versions fail closed;
- [x] unreferenced bridge locks cannot pollute active identity;
- [x] P-001/I-002 retained invariants and concrete P-003 amendments are identified;
- [x] OLiA/OntoLex/SKOS, CRM/LRMoo/CRMinf, CRMtex/R-012 and CRMarchaeo/R-010 cases are covered;
- [x] compact agent provenance fields are defined;
- [x] executable RED/GREEN research tests cover principal identity and fail-closed invariants.

## 16. Final independent review targets

Fresh exact-head review should challenge especially:

1. whether full I-002 semantic ontology-lock identity is actually used everywhere required;
2. whether R-015 accidentally treats ontology `content_digest` as the whole lock identity;
3. whether endpoint release/digest and scoped terms are sufficiently bound to the reviewed bridge;
4. whether bridge content hashing invalidates stale review after edits;
5. whether evidence/reviewer/date/runtime semantics are complete enough for R-012;
6. whether exact-lock and bridge dependency graph bindings can be bypassed;
7. whether inactive optional profiles and unused artifacts perturb active identity;
8. whether dependency activation or schema-version coercion can create fail-open execution;
9. whether canonical ordering really follows accepted I-002/JCS semantics, including non-BMP strings;
10. whether CRMtex/CRMarchaeo version-skew claims still match authoritative release declarations;
11. whether the research-only use of private I-002 normalizers is clearly delegated to a stable shared P-003 implementation rather than becoming accidental public API;
12. whether `terms_used` membership is correctly presented as consistency validation rather than proof of ontology truth;
13. whether any unknown/uncontrolled bridge field can silently upgrade execution semantics.

## References

Internal normative/review inputs:

- `docs/plans/I-002-ontology-lock-semantic-identity-amendment.md`;
- `docs/plans/I-002-canonicalization-digest-plan.md`;
- `docs/research/R-012-crmtex-modern-bridge.md`;
- `docs/research/R-010-archaeology-material-profile.md`;
- `docs/research/R-011-ontology-mapped-pilots.md`;
- `docs/research/R-014-semantic-profile-capabilities.md`.

Primary external release declarations:

- CRMtex 2.0: <https://cidoc-crm.org/extensions/crmtex/html/CRMtex_v2.0.html>;
- LRMoo 1.1.1: <https://cidoc-crm.org/extensions/lrmoo/html/LRMoo_v1.1.1.html>;
- CRMinf 1.2.1: <https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html>;
- CRMarchaeo 2.1.1: <https://cidoc-crm.org/extensions/crmarchaeo/html/CRMarchaeo_v2.1.1.html>;
- CRMsci 3.2: <https://cidoc-crm.org/extensions/crmsci/html/CRMsci_v3.2.html>.
