# I-005 plan amendment: profile-release coherence across parent variants

**Issue:** #123  
**Status:** normative amendment to `I-005-semantic-ir-compiler-plan.md`  
**Reason:** adversarial self-check before independent plan review

Where this amendment conflicts with the parent plan, this amendment is authoritative.

## 1. Problem

The parent plan correctly allows one semantic profile release to coexist across several exact parent variants, keyed by `expected_parent_manifest_digest`. But allowing arbitrary semantic differences between those variants would weaken the accepted R-001 version-binding contract.

R-001 explicitly permits **the same ontoTF profile release** to support more than one exact parent revision only after each parent has been validated. P-003 additionally makes mapping semantic identity, profile/catalog/dependency contract versions and active ontology-bundle identity part of compiled/runtime provenance.

Therefore two inputs with the same:

```text
(corpus_id, authored_profile_id, profile_version)
```

may differ in parent identity, but they must not silently carry different semantic profile content under the same release version.

## 2. Profile release key

Freeze:

```python
@dataclass(frozen=True, order=True)
class ProfileReleaseKey:
    corpus_id: str
    authored_profile_id: str
    profile_version: str
```

`BundleVariantKey` remains as specified in the parent plan and adds parent-specific identity:

```text
ProfileReleaseKey
+ expected_parent_manifest_digest
+ ontology_bundle_digest
```

The ontology-bundle field remains on the variant for direct resolver provenance, but §3 below constrains it to be coherent across one profile release.

## 3. Semantic release signature

For every compiled bundle, derive an immutable `ProfileReleaseSignature` from already validated semantic facts, excluding the expected-parent manifest digest.

It must contain at least:

```text
profile schema version
profile catalog version
dependency contract version
mapping document schema version
minimum ontoTF runtime
sorted controlled profile declarations
sorted controlled capability declarations
normalized dependency semantic records
sorted (mapping_id, mapping_semantic_digest) pairs
ontology_bundle_digest (nullable)
sorted ontology lock fingerprints used by the bundle
mapping semantic algorithm id
projection semantic algorithm id
```

### Dependency records

Dependencies are semantic/execution prerequisites and must participate in release coherence. Retain their validated closed record semantics, not only dependency IDs. Canonicalize the exact dependency objects with existing JCS semantics after normalizing fields already defined as set-like by their source contract.

Do **not** include:

- expected parent component content digests;
- transport/source filenames;
- audit-only review timestamps/reviewer prose;
- arbitrary source serialization ordering.

The signature may be represented as a frozen record plus a versioned JCS/SHA-256 digest, e.g.:

```text
ontotf-profile-release-signature-jcs-sha256-v1
```

If the implementation exposes an overall digest, export the algorithm constant. The inspectable component record remains authoritative for debugging.

## 4. Coherence rule

When compiling multiple bundles:

1. group by `ProfileReleaseKey`;
2. compute `ProfileReleaseSignature` for each member;
3. all signatures in the group must be exactly equal;
4. only `expected_parent_manifest_digest` may differ between legal exact-parent variants;
5. differing semantic release signatures under the same release key fail deterministically:

```text
SemanticIRError(category="profile_release_conflict")
```

This means an ontology-bundle change, mapping semantic edit, controlled capability/profile change, dependency semantic change or semantic contract-version change requires a profile version change rather than masquerading as another parent variant.

## 5. Consequence for ontology bundle variants

The parent plan allowed `ontology_bundle_digest` to distinguish bundle variants. That field remains required in `BundleVariantKey`, but within one `ProfileReleaseKey` it must be identical because it is also part of `ProfileReleaseSignature`.

Thus:

- same semantic profile release + parent A -> legal;
- same semantic profile release + parent B -> legal;
- same release label + different ontology bundle -> `profile_release_conflict`;
- same release label + different mapping digest -> `profile_release_conflict`;
- new profile version + new ontology/mapping semantics -> legal separate release.

This preserves both exact-parent multiplicity and semantic release versioning.

## 6. Public IR additions

Add to the parent plan's public types:

```python
@dataclass(frozen=True, order=True)
class ProfileReleaseKey: ...

@dataclass(frozen=True)
class ProfileReleaseSignature: ...
```

`BundleVariantIR` must retain both its `ProfileReleaseKey`/signature and its parent-specific `BundleVariantKey`.

`CompiledSemanticIR` should expose release signatures either through each `BundleVariantIR` or a deterministic `profile_releases` tuple. Prefer no duplicated top-level index unless I-006 needs direct lookup; RED may pin the smallest shape before GREEN.

## 7. Additional RED requirements

Add to the parent plan matrix:

1. same corpus/profile/version + identical semantic signature + different expected-parent digests -> both variants compile;
2. same release key + different mapping semantic digest -> `profile_release_conflict`;
3. same release key + different ontology bundle digest -> `profile_release_conflict`;
4. same release key + different dependency semantic record -> `profile_release_conflict`;
5. same semantic differences under a bumped `profile_version` -> legal separate profile release;
6. authored list/object ordering changes that are non-semantic under current contracts do not create a false release conflict.

## 8. I-006 handoff

I-006 can now treat a `ProfileReleaseKey` as one coherent semantic release with one or more exact parent variants. Runtime compatibility selects the variant matching the loaded parent; semantic target/index content is stable across those variants by compiler construction.

This prevents I-006 from having to decide which conflicting mapping semantics to trust under one release label.