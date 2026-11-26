# I-005 research amendment: review authority and parent variants

**Issue:** #123  
**Status:** normative amendment after logically-independent adversarial review  
**Amends:** `I-005-semantic-ir-compiler.md`  
**Current-main integration:** `7cdad03cbbd49794322f516e444cb68861f0e152` (F-024/#122 merged)  
**Review finding head superseded:** `780f2dfe4e1e3ee210bfd597ae9ba4f82feb2e62`

Where this amendment conflicts with the parent research document, this amendment is authoritative.

## 1. Review binding is not review authorization

Fresh review of the actual I-004 implementation found a distinction the parent research did not pin strongly enough.

`validate_projection_reviews()` verifies the current projection semantic digest and `reviewed_mapping_digest` binding when a review is present. Mapping-level validation similarly verifies current mapping-v2 digest/review binding. Neither path requires:

```text
review.status == reviewed
```

The structural schema intentionally permits:

```text
reviewed | provisional | disputed
```

Therefore a `ValidatedSemanticBundle` proves that review metadata is structurally/semantically coherent and fresh; it does **not** mean every contained mapping/projection is approved for authoritative reverse-index use.

I-005 must apply an explicit authority gate during compilation.

### 1.1 Mapping-level authority

A mapping contributes authoritative runtime semantics only when:

```text
mapping.review.status == reviewed
```

Consequences:

- a reviewed `native-only` mapping may contribute positive native capability-support facts but no target reverse index;
- a reviewed `ambiguous` mapping may contribute positive native capability-support facts and preserve candidates for inspection, but no candidate target reverse index;
- `unsupported` remains negative knowledge and never contributes positive capability support;
- a `provisional` or `disputed` mapping contributes no authoritative reverse-index row and no positive capability-support fact, regardless of whether its semantic digest is current.

The plan may preserve provisional/disputed records in non-authoritative inspection IR if doing so remains simple, but their review status must remain explicit and they must never be mistaken for resolver authority.

### 1.2 Projection-level authority

A semantic-pivot or authority-value projection enters its target-bearing reverse index only when **both** are true:

```text
mapping.review.status == reviewed
projection.review.status == reviewed
```

The projection must also satisfy the already validated routing/state contract.

A reviewed mapping with a provisional/disputed child projection can still establish reviewed native capability support at mapping level; that child projection does not count as shared/exact target coverage and does not enter `semantic_index` or `authority_index`.

### 1.3 External-reference authority

The current external-reference schema has no child review object. Mapping-v2 semantic identity includes query-relevant external references, and I-004 binds the current mapping digest to its mapping review.

Therefore:

- `entity-identity` and `catalogue-identifier` reverse-index rows require `mapping.review.status == reviewed`;
- their evidence bindings remain preserved as source provenance;
- no nonexistent child-review status is inferred;
- provenance/locator references remain non-target references regardless of mapping review state.

### 1.4 Capability summary counts

Capability facts must use the same review authority boundary:

- reviewed mapping-level native semantics can count toward native support;
- shared/exact/non-exact projection counts include only child projections whose projection review status is `reviewed` under a reviewed mapping;
- provisional/disputed mappings and projections are visible only as explicit non-authoritative inspection metadata if retained, not as active support counts.

This closes the path where a fresh-but-provisional review could silently become resolver authority.

## 2. One semantic profile release may have multiple parent variants

The parent research proposed rejecting duplicate `(corpus_id, profile source id, profile_version)` inputs. That conflicts with accepted R-001, which explicitly permits one ontoTF profile release to support multiple exact parent revisions after each parent target is validated.

I-005 must represent **compiled bundle variants** rather than assume one parent fingerprint per profile release.

### 2.1 Bundle variant identity

Freeze a variant key equivalent to:

```text
BundleVariantKey(
    corpus_id,
    authored_profile_id,
    profile_version,
    expected_parent_manifest_digest,
    ontology_bundle_digest,
)
```

`ontology_bundle_digest` is nullable when the validated source has no active ontology bundle.

Including the ontology bundle prevents two semantically different active ontology compositions from being collapsed merely because corpus/profile/parent strings match. The variant key uses I-004-verified identities only; it does not compute runtime compatibility.

The plan may give this key a versioned overall fingerprint derived with existing JCS/SHA-256, but the component tuple remains inspectable in the IR.

### 2.2 Duplicate rule

V1 rule: **reject exact duplicate variant keys rather than deduplicate them**.

Rationale:

- duplicate installation/input is usually an integration error;
- silent deduplication hides which package/source instance won;
- permitting two semantically different payloads under one exact variant key would make runtime provenance ambiguous.

Error category should be deterministic, e.g. `duplicate_bundle_variant` or the plan's equivalent.

If the same corpus/profile release supports two parent revisions, the expected-parent digests differ and the variants coexist legally.

### 2.3 Reverse-index values retain variant identity

P-003 reverse-index **keys** remain unchanged:

```text
semantic_index(profile, capability, target, formal_kind, semantic_role)
authority_index(authority_system, authority_resource, formal_kind, semantic_role)
identity_index(authority_system, external_entity_id, identity_strength)
identifier_index(issuer_or_namespace, literal_id)
native_index(corpus_id, native_binding_identity)
```

Their **values** must carry `BundleVariantKey` (or its frozen record) in addition to corpus/mapping/projection/reference provenance.

This allows one semantic target to have:

- several corpora;
- and, within one corpus, several validated parent variants of the same profile release.

I-006 can then select the variant matching the currently loaded/compatible parent rather than collapsing by corpus ID.

### 2.4 Capability facts are variant-scoped

The parent research grouped capability facts only by `(corpus_id, profile_id, capability_id)`. That would conflate parent variants before runtime compatibility is known.

I-005 must first compile capability facts at:

```text
(bundle_variant, controlled_profile_id, capability_id)
```

I-006 may aggregate them to a corpus-level `semantic_capabilities` view **after** selecting/establishing the operational variant for the current parent.

This also keeps a stale/unavailable parent variant from contaminating the summary of the selected current variant.

## 3. Current-main integration result

F-024/#122 merged onto `main` after the initial I-005 research commit. It changes repository ownership namespace scanning and diagnostics only. It does not modify:

- `src/ontotf/semantic_validation.py`;
- `src/ontotf/semantic_child_validation.py`;
- `src/ontotf/semantic_vocabulary.py`;
- mapping/profile/ontology schemas;
- P-003/R-001/R-013/R-014/R-017 semantic contracts.

The research branch integrated current `main` before this amendment. No semantic conclusion changed because of F-024.

## 4. Revised plan requirements

The implementation plan must now explicitly pin:

1. cross-bundle `BundleVariantKey` including expected-parent and ontology-bundle fingerprints;
2. exact duplicate-variant rejection;
3. mapping-level `reviewed` gate for authoritative native support and external-reference indexes;
4. additional projection-level `reviewed` gate for semantic/authority reverse indexes and shared/exact coverage counts;
5. variant identity on every reverse-index binding value;
6. variant-scoped capability facts;
7. tests where one profile release legally has two parent variants;
8. tests where a provisional/disputed mapping or projection is digest-fresh but excluded from authoritative indexes;
9. tests proving identity/catalogue references inherit mapping-level review authority and do not invent child review state.

## 5. Revised RED requirements

Add at least these regressions to the parent research RED matrix:

1. two validated bundles for the same corpus/profile/version with different expected-parent digests compile as two legal variants;
2. two bundles with the same exact variant key fail deterministically;
3. both parent variants appear under the same semantic target key with distinct variant provenance;
4. digest-fresh `mapping.review.status=provisional` produces no authoritative reverse-index row or positive capability-support fact;
5. reviewed mapping + digest-fresh provisional projection produces native capability support but no semantic/authority target row for that projection;
6. reviewed ambiguous/native-only mapping can contribute reviewed native capability support while remaining absent from target reverse indexes;
7. reviewed entity-identity/catalogue reference can enter only its dedicated index using mapping-level review authority;
8. provisional/disputed mapping-level identity/catalogue reference cannot enter those indexes.

## Exit judgment

The two adversarial blockers are resolved at research-contract level. The I-005 direction remains **GO**, with bundle variants and explicit review-status authority gates now mandatory plan inputs.