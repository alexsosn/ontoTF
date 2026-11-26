# R-001 review reconciliation: content identity and compatibility

**Status:** normative amendment to `R-001-distribution-architecture.md` for this research PR  
**Recorded:** 2026-09-05  
**Reason:** resolves blocking independent-review findings on PR #8

Where this amendment conflicts with the earlier R-001 draft, **this amendment supersedes it**. The final design ticket should consume the reconciled rules below, not the superseded shorthand in the original draft.

## 1. Two different identities are required

R-001 originally overloaded a schema fingerprint with too much responsibility. ontoTF needs two independent verification objects:

1. **parent artifact identity** — proves that the loaded parent TF bytes are the exact artifact ontoTF tested;
2. **profile dependency fingerprint** — proves that a different parent artifact still satisfies every native semantic dependency used by a profile.

They answer different questions and must never be substituted for one another.

### 1.1 Parent artifact identity

For every exact tested target, a profile release records a deterministic content identity independent of download transport.

For a normal TF directory the POC should use a canonical digest over the exact native `*.tf` feature files:

```text
for each regular *.tf file sorted by relative path:
    hash(path)
    hash(separator)
    hash(file bytes)
    hash(separator)
```

R-005 already implements this kind of value as `tf_files_sha256`. The POC design may refine the canonical manifest/digest algorithm, but it must preserve these invariants:

- directories such as BHSA `.tf/` are not mistaken for feature files;
- ordering and path encoding are deterministic;
- the digest covers the **actual parent semantic data**, not Git metadata;
- the same TF bytes acquired from GitHub, Hugging Face, Agora, an archive, or a local directory resolve to the same artifact identity;
- a trusted immutable release-asset digest may additionally be recorded, but transport-specific digest alone cannot replace semantic-content identity.

Git repository revision remains provenance and acquisition evidence. It is not, by itself, proof of loaded bytes once the corpus has been copied or repackaged.

### 1.2 Exact-target verification

A loaded corpus is `verified-exact` only when ontoTF recomputes or otherwise cryptographically verifies its parent artifact identity against an exact tested target in the profile manifest.

Conceptual exact target:

```yaml
parent:
  corpus_id: ETCBC/bhsa
  tf_version: "2021"
  upstream_revision: 4db00e...
  artifact_identity:
    algorithm: ontotf-tf-files-sha256-v1
    digest: ...
```

`upstream_revision` is still required because researchers need to know the authoritative source state, but exact verification is based on the loaded artifact identity.

## 2. Schema fingerprint becomes a dependency fingerprint

A profile must not auto-enable merely because generic TF schema metadata are unchanged.

A mapping can depend on:

- slot type and node types;
- particular node/edge feature existence;
- feature metadata that affects interpretation;
- bounded categorical values;
- a specific value in an otherwise open domain;
- a lexical/sense/entity identifier;
- edge valued/unvalued status and source/target type constraints;
- section/text-format structure;
- a structural invariant such as `analysis -> lex` rather than `lex.oslots` extent;
- an external sidecar/native adapter contract;
- absence of a collision or reserved feature;
- other native assertions explicitly referenced by the mapping.

Therefore compatibility for a non-exact parent revision must validate the **exact dependency closure of that profile**.

### 2.1 Dependency declaration

Every mapping/profile source must compile to a dependency declaration sufficient to validate every native selector it uses.

Conceptually:

```yaml
depends_on:
  slot_type: word
  node_types: [word, lex]
  node_features:
    sp:
      applies_to: [word]
      required_values: [subs]
    lex:
      applies_to: [word]
      open_values_used: []
  edge_features:
    mother:
      valued: false
      source_types: [clause, phrase]
      target_types: [clause, phrase]
  invariants:
    - id: bhsa-mother-native-semantics-v1
```

If a profile maps one particular lexical entity from an open domain, that value/identifier is part of `open_values_used` or an equivalent explicit dependency. Merely knowing that a `lex` feature exists is insufficient.

### 2.2 Compatibility states

The POC should use states with unambiguous evidence:

- **`verified-exact`** — loaded parent artifact identity equals an exact tested target;
- **`verified-compatible`** — artifact is not an exact target, but the current profile's complete declared dependency closure has been validated against it under the profile's compatibility rules;
- **`incompatible`** — at least one required dependency differs, is absent, or cannot be validated;
- **`unverified`** — ontoTF cannot prove exact identity or complete dependency compatibility.

Do not call the second state `verified-schema`; the relevant object is broader than schema.

### 2.3 Unverified means non-executable

An `unverified` profile may be inspected for diagnostics, migration planning, or a human review report, but **semantic execution is disabled**.

This reconciles R-001 with R-003's fail-closed ergonomic policy. There is no agent-controlled `allow_unverified=true` escape hatch in the normal semantic search API. A developer/debug command may produce a prospective resolution plan only if it is visibly marked non-executable and cannot be passed directly to semantic execution without successful verification.

This rule prevents an LLM from converting an “explicit opt-in” knob into a silent safety bypass.

## 3. Verification across acquisition routes

Distribution and identity stay separate.

### Git checkout

1. acquire pinned/tagged data;
2. record Git revision for provenance;
3. compute canonical parent artifact identity over the actual TF files;
4. compare with the profile target/dependency rules.

### Context-Fabric / Hugging Face artifact

1. acquire the selected revision/artifact;
2. verify provider/release digest when available;
3. resolve the native TF semantic payload or its trusted content manifest;
4. verify the same ontoTF parent artifact identity/dependency closure.

Precompiled `.cfm` bytes alone are not automatically equivalent evidence unless the Context-Fabric build supplies a trustworthy manifest binding them to the exact TF source identity ontoTF expects.

### Agora materialization

Agora may select/download the declared ontoTF profile and parent resource, but ontoTF verifies semantic compatibility itself. Agora registry metadata is useful acquisition evidence; it is not the semantic verifier.

### Local directory / archive

No Git repository is required. ontoTF computes the native artifact identity directly from the loaded TF files and either reaches `verified-exact`, validates full dependencies for `verified-compatible`, or fails closed.

## 4. Canonical source versus runtime sidecar terminology

The original draft used “sidecar” once for both semantic source and runtime contract. Use these terms consistently:

- **profile source** — canonical human-reviewable declarative mapping + manifest/dependencies/tests;
- **compiled runtime sidecar** — deterministic generated lookup/index consumed by ontoTF;
- **RDF/publication export** — deterministic generated standards-oriented representation;
- **materialized TF module** — optional deterministic generated compatibility product.

Only the **profile source** is editable semantic source. Generated artifacts are disposable/rebuildable and carry source/profile/ontology/parent fingerprints.

## 5. Optional materialized TF modules have a reserved boundary

A generated ontoTF TF compatibility module must be semantics-preserving and collision-safe.

Default forbidden outputs:

- `otype.tf`;
- `oslots.tf`;
- replacement native `otext` configuration;
- any existing native node/edge feature name;
- any feature whose meaning depends on silently changing Text-Fabric traversal/rendering behavior.

Ordinary generated convenience features must use a ontoTF namespace/prefix chosen by design and CI must fail on collisions.

If a future product intentionally transforms the TF warp or text formats, it is **not** an ordinary ontoTF semantic module. It requires a separate architecture decision, explicit new corpus/artifact identity, and its own provenance.

## 6. Profile-release manifest consequences

The reconciled release manifest needs, conceptually:

```yaml
profile:
  id: ontotf-bhsa
  version: 0.1.0

parent:
  corpus_id: ETCBC/bhsa
  exact_targets:
    - tf_version: "2021"
      upstream_revision: 4db00e...
      artifact_identity:
        algorithm: ontotf-tf-files-sha256-v1
        digest: ...

compatibility:
  dependency_contract_version: 1
  dependency_fingerprint: ...
  dependency_manifest: dependencies.json

artifacts:
  profile_source_digest: ...
  runtime_sidecar_digest: ...
  rdf_export_digest: ...
  tf_module_digest: null
```

The design ticket chooses serialization and exact field names. R-001 fixes the information boundary.

## 7. CI consequences

A profile CI gate must test both exact identity and reusable compatibility.

For every exact target:

1. acquire the exact parent corpus/release;
2. compute canonical artifact identity;
3. assert it equals the manifest target;
4. load/inspect every declared dependency;
5. validate node/edge kinds and semantics required by the profile;
6. validate every mapped bounded value;
7. validate every mapped **open-domain value/entity identifier** actually referenced;
8. validate structural invariants and native edge direction/value status;
9. compile the runtime sidecar and publication artifacts;
10. run positive and negative semantic fixtures.

For a claimed compatible non-exact target:

1. compute its artifact identity (for audit, even though it differs);
2. validate the complete dependency closure;
3. fail on any undeclared/unvalidated dependency;
4. record a compatibility evidence digest/report;
5. run the same semantic fixtures relevant to that mapping profile.

A generic “feature names still exist” smoke check is insufficient.

## 8. Effects on the architecture decision

The overall R-001 decision does **not** change:

- central ontoTF source repository during the POC;
- independently releasable per-corpus profile bundles;
- profile source as the editable authority;
- compiled sidecar for fast native Context-Fabric execution;
- RDF as publication/interchange rather than mandatory query runtime;
- optional TF materialization only where faithful;
- Agora as thin discovery/acquisition/compatibility metadata, not semantic owner.

The amendment makes the version-binding part strong enough for those distribution choices to be safe across transports and open-domain mappings.

## 9. Rejected weaker rules

### Git commit alone proves exact parent data

Rejected. Copies, archives, generated distributions and local directories can lose or spoof repository context while retaining metadata strings.

### Generic schema digest proves mapping compatibility

Rejected. A mapped open-domain value/entity may change while feature metadata remain byte-for-byte identical.

### `allow_unverified` execution for advanced users/agents

Rejected for the normal resolver/search contract. Unverified mappings can be inspected, not executed as semantic truth.

### Generated TF modules may override native/reserved features if namespaced metadata explains it

Rejected. The collision itself changes native semantics/behavior; explanation does not make it semantics-preserving.

## 10. Acceptance trace for review findings

- transport-independent exact identity: §§1, 3;
- full profile dependency closure including open-domain values/entities: §2, §7;
- canonical source versus runtime sidecar terminology: §4;
- fail-closed unverified behavior reconciled with R-003: §2.3;
- reserved/warp/config collision policy for optional TF modules: §5;
- CI verification changes: §7.

A final independent reviewer should verify this amendment against the accepted R-005 generated inventories and the final R-003 compatibility/error contract before R-001 merges.