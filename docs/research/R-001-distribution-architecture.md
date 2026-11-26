# R-001: distribution and version-binding architecture

**Status:** research complete; R-005 accepted; pending exact-head independent review  
**Issue:** #1  
**Recorded:** 2026-09-05

## Decision

For the POC, ontoTF should use a **central source repository with independently versioned per-corpus semantic sidecar bundles**.

Each corpus profile is authored and validated in the ontoTF repository, but is publishable as its own immutable release artifact. The **ontoTF profile source** is the canonical human-reviewable semantic source. A **compiled runtime sidecar** is a deterministic generated lookup/index derived from that source. Exact compatibility binds to a transport-independent parent component manifest covering every **semantically addressable native component** of the tested parent — the TF payload plus any declared external sidecar, catalogue, zero-span entity store, or native-adapter artifact. Reusable compatibility validates the profile dependency closure against a different parent component set. ontoTF may optionally generate a Text-Fabric feature module when the mapped semantics can be represented faithfully as TF node/edge features, but generated TF features are never the canonical mapping source.

Agora should discover and install ontoTF profiles and select compatible profiles for a parent corpus. Agora should not contain mappings, ontology reasoning, term equivalence rules, or corpus-specific semantic transformations. Context-Fabric/Text-Fabric remain corpus loaders and query engines; ontoTF owns semantic resolution over the loaded corpus plus its sidecar.

The POC therefore has four distinct artifact roles:

1. **parent corpus artifact** — authoritative native TF data plus any semantically addressable native sidecars/catalogue/adapter data and corpus metadata;
2. **ontoTF profile source** — version-controlled declarative semantic mappings, compatibility manifest, tests and documentation;
3. **ontoTF runtime sidecar** — deterministic compiled/indexed representation consumed by ontoTF without requiring an RDF store;
4. **optional materialized TF module** — derived node/edge features for tools that only understand TF features, produced only where semantic fidelity is preserved.

RDF/Turtle should be a standards-oriented publication/interchange representation of the semantic graph, not a requirement that runtime queries use RDF or a triplestore. The later ontology-governance ticket may refine the exact RDF vocabulary and authoring serialization, but it should not reopen the distribution decision above.

## 1. Research basis and pins

The distribution decision was checked against current upstream behavior at these revisions:

| system | revision / version inspected | evidence |
|---|---|---|
| Text-Fabric | `annotation/text-fabric@1079c68e051947efd955b61ad499e3a9beb03b09`, TF `13.1.0` | `tf/docs/about/datasharing.md`, `tf/docs/about/usefunc.md`, `tf/parameters.py` |
| Context-Fabric | `Context-Fabric/context-fabric@3a38ca80e617d872ce1664e0f0740486d0e7e8ac`, core `0.5.7` | `Fabric`, downloader, TF compatibility docs, corpus distribution implementation/plan |
| Agora | `alexsosn/Agora@848c18afa83946b368da01866226f93c516739d5` | marketplace architecture, registry, `feature-modules.yaml`, registry validator |
| target corpus semantics | R-005 / PR #7, accepted reviewed head `48c8bd78d0c3a0501b2fdec6946db5df90517bdb` (merged as `a9c4d74d4de2f9a15eb1464dce341ecd2f92f898`) | empirical census of BHSA, CUC, Syriac variants, ExtraBiblical, TLHdig-TF, Pseudepigrapha-TF and ORACC-TF |

R-005 accepted the empirical corpus-semantics dependency at exact reviewed head `48c8bd78d0c3a0501b2fdec6946db5df90517bdb`. This report has been reconciled against that accepted evidence; any future material R-005 revision requires a new R-001 reconciliation.

## 2. Observed Text-Fabric constraints

### 2.1 TF already supports third-party feature modules

Text-Fabric's data-sharing contract explicitly treats modules as independently distributed sets of TF features. A module can live in another GitHub/GitLab repository, and `use(..., mod=...)` loads its features together with the main corpus. The module directory is versioned using the **main corpus version**. TF documentation states that a properly designed module must correspond to a specific version of the main source.

TF checkout syntax also supports reproducibility controls:

- `latest` — latest release;
- `hot` — latest commit;
- explicit release tag;
- explicit commit hash;
- `clone` — local checkout;
- `local` — local TF data directory.

TF records loaded modules in provenance output. Official releases can distribute zipped TF data; a module may be kept in a separate repository and released independently from the parent corpus.

These are useful compatibility mechanisms, but they solve **feature distribution**, not semantic ontology distribution.

### 2.2 Main-data version and module release are separate dimensions

The TF module path contains a parent-data version directory, while the module repository itself can have independent releases/commits. That distinction is essential for ontoTF:

- BHSA `2021` identifies a corpus schema/data generation;
- a ontoTF BHSA mapping can evolve through `0.1.0`, `0.1.1`, etc. without changing BHSA;
- the same ontoTF profile release may support more than one exact parent revision only after each target has been validated.

A string such as `tf/2021` is therefore insufficient as the full compatibility contract. It identifies a version directory but not the exact parent data revision whose feature inventory/value domain was tested.

### 2.3 TF modules are feature-shaped

A normal TF module merges feature files into the feature namespace. That works well for an annotation such as `valence`, `strongs`, or an additional edge relation over existing nodes.

R-005 found semantics that do not fit a feature-only canonical representation:

- an ontology term may apply to a native feature/value without needing a new feature;
- the same abstract concept may be a feature in one corpus and a node+edge structure in another;
- TLHdig-TF contains non-textual entities whose `oslots` are technical anchors rather than semantic extents;
- ORACC-TF has genuine zero-span source entities that are kept outside the TF warp;
- Pseudepigrapha-TF witness/readings require a graph of locus, reading, manuscript and explicit absence states;
- mapping strength and uncertainty are assertions about the mapping itself, not annotations that should be written onto every corpus node.

A TF module can be generated for a subset of these use cases, but cannot safely be the universal source representation.

## 3. Observed Context-Fabric constraints

### 3.1 Context-Fabric consumes the same `.tf` model but not TF Advanced

Context-Fabric preserves the Text-Fabric core graph APIs and reads the same `.tf` feature files, compiling them to memory-mapped `.cfm` data. Current Context-Fabric documentation explicitly says it implements the TF core module, not TF's `advanced` layer that provides the `use('corpus')` auto-download/application workflow.

At the inspected revision, Context-Fabric `Fabric` accepts multiple `locations` and `modules`. It scans `.tf` files in each selected `location/module`; module order is significant because a later module can override an earlier feature with the same name.

Consequences for ontoTF:

- a materialized ontoTF TF module can be loaded alongside the corpus in Context-Fabric;
- ontoTF must avoid accidental feature-name collision/override, preferably by namespacing generated compatibility features and failing CI on undeclared collisions;
- Context-Fabric itself should not be required to understand ontoTF ontology manifests in order to load raw corpus data;
- the semantic sidecar/resolver can sit above Context-Fabric's corpus API and use native feature/edge access without modifying `.cfm` internals.

### 3.2 Context-Fabric distribution is independently revision-pinnable

Current Context-Fabric includes a Hugging Face Hub downloader whose `revision` can be a tag, branch or commit. This is another useful acquisition mechanism, especially for large precompiled `.cfm` artifacts, but it is not a reason to make Hugging Face the identity authority for ontoTF profiles.

A corpus can be obtained from TF-native GitHub/GitLab data, Context-Fabric/HF distribution, Agora materialization, or a local checkout. ontoTF compatibility must resolve all of those to the **same logical parent corpus identity plus the same declared component identities**, rather than bind semantic correctness to one download transport.

### 3.3 Runtime performance favors a sidecar index

Context-Fabric gains its performance by compiling once and memory-mapping indexed data. ontoTF should follow the same separation of concerns: preserve a reviewable semantic source, then compile a deterministic runtime index. Re-parsing a whole RDF graph or executing SPARQL for every agent request is not required by the problem and would couple semantic interoperability to an unnecessary infrastructure choice.

The runtime sidecar can be opened offline next to the corpus. A later implementation benchmark should decide the exact index encoding after query shapes from R-003 are known.

## 4. Observed Agora constraints

### 4.1 Agora is an integration/discovery layer

Agora's architecture distinguishes marketplace, plugin, provider/backend and corpus/resource. It explicitly states that data quality, corpus semantics and upstream limitations remain owned by the source corpus rather than being reinterpreted by Agora.

Current Agora already supports a generic `feature-module` resource kind with:

- parent corpus ID;
- compatible parent versions;
- upstream repository/module path;
- lazy acquisition;
- module status/coverage;
- source dependencies/provenance;
- licensing and verification status.

Its registry validator checks that a feature module refers to an existing corpus parent on the same provider/plugin and validates controlled vocabularies. This proves that Agora can carry **compatibility and acquisition metadata** without owning the scholarly semantics.

### 4.2 ontoTF sidecars should not be mislabeled as ordinary feature modules

A ontoTF profile is broader than a TF feature bundle. The recommended later Agora integration is a resource type such as `semantic-module` (name to be finalized in the design ticket) with the same thin fields Agora already understands conceptually:

- parent resource ID;
- compatible/tested parent revisions;
- ontoTF profile ID/version;
- immutable release location and digest;
- optional materialized TF-module artifact;
- ontology/profile identifiers;
- acquisition and verification status.

If Agora does not add a new resource kind immediately, the POC can be installed directly from ontoTF and Agora integration can wait. It is preferable to temporary non-registration than to describe a semantic sidecar falsely as a `feature-module`.

Agora may resolve/download/select an artifact. The ontoTF library must interpret it.

## 5. Corpus-census constraints from R-005

The distribution architecture must survive the actual target family rather than only BHSA.

### BHSA and ExtraBiblical

These are the easiest cases for an optional generated TF module because they use word slots and related ETCBC linguistic structures. Even here, mappings such as native `mother` versus structural containment are ontology assertions; materialized convenience features cannot replace the mapping source.

### CUC

CUC uses sign slots and physical `tablet -> column -> line` structure. Editorial certainty/emendation/alternative-reading semantics live on signs. A sidecar can map those values to ontology terms without copying a new ontology feature onto 146k signs.

### Syriac / Peshitta / SyrNT

The three repositories have materially different schemas. Distribution must bind a profile to `ETCBC/syriac 0.9`, `ETCBC/peshitta 0.2`, or `ETCBC/syrnt 0.1` separately. A generic `syriac` compatibility declaration is not sufficient.

### TLHdig-TF

TLHdig-TF combines sign slots, physical structure, alternative morphological-analysis nodes, lexical entities, editorial ranges, fragments, edit events and valued selection edges. Some non-textual nodes use technical TF anchors. A sidecar can say which native relation carries semantic extent/attestation without rewriting the corpus.

### Pseudepigrapha-TF

Witness semantics require explicit reading/unit/manuscript relations and distinguish explicit omission from unattested/unknown. A generated one-feature-per-word representation would lose essential graph semantics. Sidecar-first is mandatory for faithful cross-corpus witness concepts.

### ORACC-TF

The current target includes sign slots, source GDL structures, physical object/catalogue metadata and zero-span sidecar entities. ontoTF cannot require every mapped entity to be a materialized TF node. The distribution format must allow a profile to describe corpus-native sidecar/entity sources alongside TF nodes/features. If an ORACC profile semantically addresses those native sidecar/catalogue entities, their bytes are part of the tested parent component manifest; a TF-only digest cannot establish exact identity for that profile.

## 6. Architecture alternatives

Scores: 1 = poor, 3 = workable with material costs, 5 = strong. `Maintenance` includes contribution ergonomics and release independence. `Stale behavior` scores the ability to fail clearly when a corpus drifts.

| alternative | fidelity | independent releases | human install | agent discovery | version resolution | independent publication | Agora fit | CI validation | maintenance | optional profiles | stale behavior | total / 55 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A. Central ontoTF source + independently released semantic sidecars + optional generated TF modules** | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **54** |
| B. One repository/package per corpus from day one | 5 | 5 | 3 | 4 | 5 | 5 | 5 | 5 | 2 | 5 | 5 | 49 |
| C. Put mappings in each parent corpus repository | 4 | 1 | 5 | 3 | 4 | 1 | 3 | 4 | 2 | 3 | 4 | 34 |
| D. Make TF feature modules the canonical ontoTF artifact | 2 | 5 | 5 | 4 | 4 | 5 | 5 | 5 | 4 | 3 | 4 | 46 |
| E. Store mapping logic/metadata centrally in Agora | 3 | 4 | 5 | 5 | 4 | 3 | 1 | 4 | 2 | 4 | 4 | 39 |
| F. RDF/triplestore-only runtime package per corpus | 5 | 5 | 2 | 3 | 5 | 5 | 3 | 5 | 3 | 5 | 5 | 46 |

### A. Central source + independent sidecars — recommended

Strengths:

- one place to evolve core mapping vocabulary/schema during the POC;
- cross-corpus CI can detect inconsistent use of ontology terms;
- each profile can have its own release/tag/version and parent compatibility matrix;
- sidecar representation covers TF nodes, features, technical anchors and zero-span entities;
- optional TF modules retain excellent compatibility with existing TF/CF workflows;
- the same manifest can later move unchanged to a separate repository.

Main risk: a central repository can become a contribution bottleneck. Independent profile release tags and a future split path mitigate that without paying multi-repo coordination costs before the schema stabilizes.

### B. One repository per corpus immediately

Semantically sound, but premature during the POC. Core manifest/schema changes would require synchronized changes across many repositories; cross-corpus mapping review becomes harder; contribution scaffolding and release automation are duplicated.

This becomes attractive after the profile schema and governance rules stabilize or when an external corpus maintainer wants independent ownership.

### C. Mappings live with the parent corpus

Rejected as the default because mapping releases would be coupled to unrelated parent corpus governance and release cadence. It would also require upstream maintainers to accept every ontology dependency/profile ontoTF wants to support. Parent repositories should be able to opt in, but ontoTF cannot depend on that.

### D. TF feature module as canonical source

Rejected as canonical because R-005 demonstrates graph and zero-span semantics that do not fit feature materialization faithfully. Retain it as a derived compatibility product.

### E. Agora owns mappings

Rejected. It violates Agora's thin marketplace boundary and would duplicate mutable corpus/ontology semantics in an integration registry. Agora should know enough to select the correct ontoTF artifact, no more.

### F. RDF/triplestore-only runtime

RDF is useful for publication and ontology interoperability, but requiring a triplestore would add installation, indexing and query-engine complexity to every TF workflow. The POC needs deterministic corpus lookup first. Keep RDF as a publication/interchange representation; compile a direct lookup index for runtime.

## 7. POC repository layout

Conceptual layout; the design ticket may refine filenames but should preserve the boundaries.

```text
ontoTF/
├── schemas/
│   ├── profile-manifest.schema.*
│   └── mapping.schema.*
├── ontology/
│   ├── lock.*                 # exact external ontology/version pins
│   └── local/                 # ontoTF-local concepts allowed by governance
├── profiles/
│   ├── bhsa/
│   │   ├── manifest.*
│   │   ├── mapping.*          # authoritative declarative source
│   │   ├── docs/
│   │   ├── fixtures/
│   │   └── tests/
│   ├── cuc/
│   ├── syriac/
│   ├── peshitta/
│   ├── syrnt/
│   ├── extrabiblical/
│   ├── tlhdig-tf/
│   ├── pseudepigrapha-tf/
│   └── oracc-tf/
├── build/
│   └── ...                    # generated; not semantic source
└── docs/
```

A published **profile bundle** should contain at least:

```text
<ontotf-profile-id>-<mapping-version>/
├── manifest.json              # normalized release manifest
├── mapping.<rdf-or-source-export>
├── runtime/index.json|...     # deterministic compiled lookup representation
├── docs/reference.*           # generated mapping reference
├── checksums.txt
└── optional-tf/
    └── <parent-tf-version>/
        ├── *.tf
```

The exact runtime index encoding should be benchmarked in implementation; its **logical contract** is fixed here: deterministic, offline, read-only, generated from the profile source, no semantic information present only in the compiled form.

## 8. Version-binding manifest proposal

The POC should bind compatibility through exact tested targets, not only a loose version range.

Conceptual manifest:

```yaml
schema_version: 1
profile:
  id: ontotf-bhsa
  version: 0.1.0
  mapping_revision: <ontoTF Git commit>

parent:
  resource_id: bhsa
  upstream_repository: ETCBC/bhsa
  data_path: tf/2021
  slot_type: word

compatibility:
  policy: exact-tested-targets
  targets:
    - tf_version: "2021"
      upstream_revision: 4db00e2157915495e1a4d3d57e41223df24775da
      artifact_identity:
        algorithm: ontotf-parent-components-sha256-v1
        components:
          tf:
            kind: tf-payload
            algorithm: ontotf-tf-files-sha256-v1
            digest: sha256:<digest>
          # Additional native components are declared when the profile
          # semantically addresses sidecar/catalogue/adapter data.
      dependency_manifest: dependencies.json
      tested: true

ontologies:
  lock: ontology/lock.*
  profiles: [core, linguistic]

artifacts:
  runtime:
    digest: sha256:<digest>
  rdf:
    digest: sha256:<digest>
  tf_module:
    available: true
    parent_tf_version: "2021"

provenance:
  generated_from: <ontoTF Git commit>
```

### Required identity fields

A verified compatibility target should include:

1. **logical corpus resource ID** — e.g. `bhsa`, `cuc`, `tlhdig-tf`;
2. **canonical upstream repository/data location**;
3. **parent TF/schema version**;
4. **exact immutable upstream revision** used in CI as provenance/acquisition evidence;
5. **transport-independent parent component manifest** with exact **component identities** for every semantically addressable native component — the TF payload plus any external sidecar, catalogue, zero-span entity store, or native-adapter artifact used by the profile;
6. **complete profile dependency closure**, including every native selector/value/entity/invariant used by the mapping;
7. **expected slot type**;
8. **ontoTF profile version and source revision**;
9. **locked ontology/profile versions**.

The design ticket should define canonical component-identity and dependency-manifest construction. The TF payload identity hashes the parent semantic TF bytes, including storage-level dense records, but that digest is only one component identity when the profile addresses native semantics outside `*.tf`. Exact identity requires every declared semantically addressable component to match the tested target. Dependency compatibility is semantic: an empty-string or `None` dense record carries **no semantic value** unless the parent corpus explicitly defines otherwise, so it cannot satisfy a required mapped value or establish feature applicability. Likewise, an **observed small** release domain is not automatically a **closed vocabulary**: compatibility validates the particular values and invariants the profile depends on rather than assuming every finite observed domain is permanently closed.

### Compatibility states

Runtime discovery should distinguish:

- `verified-exact` — every declared semantically addressable parent component identity equals the exact tested target and no required component is missing or unverifiable;
- `verified-compatible` — one or more component identities differ, but the current profile's complete declared dependency closure has been validated against the changed parent component set;
- `incompatible` — at least one required dependency differs, is absent, or cannot be validated;
- `unverified` — ontoTF cannot prove exact component identity or complete dependency compatibility.

Semantic execution is enabled only for `verified-exact` and `verified-compatible`. `unverified` is diagnostic and **non-executable**: it may support migration inspection or a prospective resolution report, but there is no normal agent/user opt-in that converts it into executable semantic truth. `incompatible` fails closed.

Negative regression case: if **TF bytes stay identical** but a required **external sidecar** or other semantically addressable native component changes, the profile **must not remain `verified-exact`**. It may become `verified-compatible` only after the full dependency closure validates against the changed component; otherwise it is `incompatible` or `unverified`.

A semver/version range may be a **discovery hint**, but must not by itself authorize a mapping. Many TF corpora use non-semver versions such as `2021`, `c`, or corpus-specific tags, and a repository can change data inside a nominally same version directory.

## 9. Parent updates and stale mappings

When a parent corpus changes:

1. acquisition resolves the new corpus revision and complete semantically addressable native component set used by the profile;
2. ontoTF computes/verifies the transport-independent component identities;
3. if any declared component identity is not an exact tested target, ontoTF validates the complete profile dependency closure across the changed component set;
4. semantic queries are enabled only after reaching `verified-exact` or `verified-compatible`; otherwise the profile is `unverified` or `incompatible` and remains non-executable;
5. CI for the ontoTF profile is run against the new exact parent revision/component set;
6. any changed dependency — including mapped open-domain values/entity IDs, edge semantics, external sidecar/native-adapter entities, structural invariants, or required bounded values — requires mapping review;
7. a new ontoTF profile release records the added exact component manifest or explicit compatibility evidence.

Do not silently fall back to a nearest earlier mapping. A reproducible semantic request receives verified execution or a diagnostic failure; an unverified profile never produces plausible but unvalidated semantic results.

## 10. Release and integrity model

### Immutable source identity

All verified targets and build provenance use exact Git commit SHAs. Human-readable tags/releases remain useful labels but are not the final identity check.

### Profile releases

The central ontoTF repository can publish profiles independently with namespaced tags, for example:

```text
profile/bhsa/v0.1.0
profile/cuc/v0.1.0
profile/tlhdig-tf/v0.2.0
```

A profile release contains only that profile's normalized manifest, semantic source/export, runtime bundle, generated reference and optional TF module. A change to BHSA mapping does not require a new CUC artifact.

### Integrity

Release artifacts should carry SHA-256 digests in the manifest. When available, GitHub immutable releases and artifact/release attestations should be used so consumers can verify that a bundle corresponds to the recorded repository revision and build workflow. GitHub currently supports cryptographically verifiable artifact attestations and immutable releases whose tag/assets are locked after publication; verification can also be done offline for attestations.

This is a distribution integrity guarantee, not a scholarly correctness guarantee. Independent semantic review and corpus-version CI remain separate requirements.

### Archival publication

A stable profile release may additionally be archived to Zenodo for DOI/citation. Zenodo should be a preservation/publication mirror, not the runtime resolver's only source. Offline users can install a verified release bundle once and keep corpus + profile bundle entirely local.

## 11. RDF/Turtle boundary

The project should support an RDF representation because ontology terms and mapping relations benefit from stable URIs and standard semantic-web interchange. It should not require RDF infrastructure to execute a corpus query.

Recommended boundary:

- **authoritative semantics:** declarative ontoTF profile source plus ontology lock and validation rules;
- **publication/interchange:** deterministic RDF export, with Turtle as the human-readable default and JSON-LD as an optional machine-oriented serialization;
- **runtime:** deterministic lookup/index sidecar compiled from the same source;
- **TF compatibility:** optional generated `.tf` node/edge features for the safe representable subset.

No information may exist only in a generated TF module or runtime cache. Round-trip equality of serialization syntax is unnecessary; semantic equivalence to the source mapping is required and should be tested.

R-002 should decide the exact ontology/mapping predicates and URI governance. R-003 should decide the runtime query shapes. Those decisions can change the internal source/index serialization without changing the distribution architecture.

## 12. Ownership boundaries

| component | owns | must not own |
|---|---|---|
| parent corpus repository | native nodes/features/edges and native sidecar/catalogue data, corpus versioning, native semantics, source provenance, corpus licence | ontoTF cross-corpus equivalence claims unless it explicitly chooses to contribute them |
| ontoTF | ontology/profile locks, corpus mapping assertions, mapping strength, semantic sidecars, mapping validation, generated semantic reference, optional TF materialization | parent corpus data truth; download-marketplace policy; MCP transport |
| Text-Fabric | TF data model, module loading/distribution conventions, core/advanced APIs | ontoTF ontology policy |
| Context-Fabric core | efficient `.tf`/`.cfm` loading and core graph/query APIs | ontoTF mapping governance or marketplace discovery |
| Context-Fabric MCP | agent transport, corpus selection, native corpus query tools, optional invocation of ontoTF semantic resolver | canonical mapping definitions |
| Agora | discovery, parent/resource compatibility metadata, installation/acquisition, selection, integration verification | substantive mappings, ontology reasoning, duplicated corpus quality judgments |

The runtime integration can therefore look like:

```text
Agent
  -> Context-Fabric MCP / ontoTF-aware tool
       -> loaded native corpus API
       -> selected ontoTF sidecar resolver
            -> native feature/edge lookup
            -> semantic projection + provenance
```

Agora participates before runtime by resolving the appropriate corpus/profile artifacts; it need not be on every query path.

## 13. Concrete deployment examples

### BHSA

- parent: `ETCBC/bhsa`, TF version `2021`, exact tested commit;
- ontoTF profile: `ontotf-bhsa`;
- runtime: sidecar mapping native POS/morphology/syntax/lexical structures to ontology terms;
- optional TF product: safe projected categories with ontoTF-namespaced feature names;
- CI: verify `word` slot, required `lex`/syntactic nodes/features/edges and bounded mapped values before release.

### CUC

- parent: `DT-UCPH/cuc`, TF `0.2.8`, sign slot;
- profile maps sign/text/physical/editorial features;
- sidecar is primary; generated TF module should be limited because existing sign features already carry the native assertions and copying them adds cost without semantic benefit.

### ETCBC Syriac

- `syriac`, `peshitta`, and `syrnt` receive separate profile IDs/manifests;
- shared internal mapping fragments may be reused only through explicit composition;
- compatibility is never declared against a generic "Syriac corpus" identifier.

### ExtraBiblical

- profile can share tested BHSA-family mapping fragments for common ETCBC concepts;
- separate parent target is still required because node inventory differs (for example no separate `lex` node in the inspected version).

### TLHdig-TF

- sign-slot profile maps physical structure, morphology-analysis alternatives, lexical attestations, damage/editorial ranges, witnesses and edit provenance;
- semantic edge definitions such as `analysis -> lex` remain in the sidecar; technical `oslots` anchors are explicitly marked non-extensional;
- a flat TF-module-only product would be insufficient.

### Pseudepigrapha-TF

- sidecar maps reading/locus/manuscript/version/omission semantics and source provenance;
- generated TF features may expose convenience categories, but cannot replace witness graph relations or explicit unknown/unattested states;
- compatibility binds to converter schema + pinned upstream source revision.

### ORACC-TF

- profile is not released until ORACC-TF has a stable schema release;
- sidecar can cover TF warp entities plus zero-span sidecar/catalogue entities;
- any native sidecar/catalogue component that the profile addresses is explicitly included in the parent component identity manifest;
- ontoTF runtime entity addressing must allow non-TF entities qualified by source identity and profile adapter, rather than requiring every semantic object to have a TF node number.

## 14. Offline and caching behavior

A reproducible offline workspace should be representable as:

```text
workspace/
├── corpus/             # exact parent corpus revision/component set or exported data
├── ontotf-profile/      # exact immutable ontoTF bundle
└── lock.json           # resolved component/profile/ontology identities and digests
```

After acquisition, no network is required for semantic querying. The lock records the resolved corpus component/profile/ontology revisions and digests.

Caches may accelerate acquisition or compilation but are disposable. Semantic identity must never be inferred from the cache path alone. A corrupted or mismatched runtime cache is rejected by digest/version metadata and can be regenerated from the profile source/bundle.

For Context-Fabric `.cfm` caches, ontoTF should treat the native corpus feature set exposed by the API as authoritative; ontoTF does not need to embed its semantic sidecar into the `.cfm` cache format.

## 15. Agent discovery behavior

An agent should be able to ask discovery questions before executing a semantic query:

- Which ontoTF profiles are installed for this corpus?
- Which profile release is compatible with the exact loaded corpus component set?
- Which ontology profiles are active?
- Is a requested concept native, projected with a `same/close/broader/...` mapping, or unsupported?
- Which native feature/node/edge/sidecar entity produces the answer?
- Is this mapping `verified-exact`, `verified-compatible`, `unverified`, or `incompatible`, and what component/dependency evidence supports that state?

Agora can help discover/install the profile. ontoTF supplies the semantic capability metadata. Context-Fabric supplies native corpus schema and values. These layers should not synthesize one another's claims.

## 16. CI contract for a profile release

A profile cannot be released as verified merely because its manifest validates. CI should acquire each exact declared parent target and check at least:

1. transport-independent parent component manifest, exact component identities for every semantically addressable native component, upstream revision provenance, and TF/schema version;
2. expected slot type;
3. every dependency in the compiled profile dependency closure exists with the expected node/edge/sidecar kind, datatype, applicability, and structural invariants;
4. every mapped bounded value and every referenced open-domain value/entity identifier is validated explicitly; unrelated new values in an open domain do not invalidate a profile unless the dependency contract says they matter;
5. edge direction/value semantics and external sidecar/native-adapter contracts match the adapter declaration;
6. no generated TF compatibility feature collides with native or selected optional-module features unless the override is explicit and tested;
7. semantic sidecar source compiles deterministically;
8. generated RDF/runtime/TF artifacts all record the same profile/parent-component/ontology locks;
9. representative cross-corpus queries from R-005 produce expected supported/unsupported behavior;
10. release bundle digests/attestations are emitted from the reviewed commit.

Implementation must follow TDD once the research/design gate opens; these checks are acceptance requirements, not implementation in this research PR.

## 17. Migration from central POC to per-corpus repositories

The profile bundle is designed as the unit of migration.

If BHSA later moves to `ontoTF/ontotf-bhsa` or an ETCBC-owned repository:

1. copy the `profiles/bhsa` source subtree and its tests into the new repository;
2. preserve the profile ID and manifest schema;
3. continue versioning the profile independently;
4. update artifact/discovery coordinates in the central ontoTF catalog and Agora;
5. retain old release coordinates as immutable historical provenance;
6. keep logical mapping/entity identifiers independent of the hosting repository URL;
7. run the same exact-parent CI contract in the new repository.

No corpus consumer should have to change semantic query syntax solely because the profile's Git repository changed. Hosting location is acquisition metadata, not semantic identity.

The central ontoTF repository can then evolve into a core schema/governance/catalog repository while independently maintained profile packages own their release cycles.

## 18. Failure policy

Fail closed where a wrong semantic result would look plausible.

| condition | behavior |
|---|---|
| profile missing | report semantic capability unavailable; native corpus remains queryable |
| every declared semantically addressable parent component identity equals the exact tested target | `verified-exact`; enable profile normally |
| one or more component identities differ but complete profile dependency closure validates | `verified-compatible`; enable with compatibility evidence |
| TF payload matches but a required external sidecar/catalogue/native component differs | must not remain `verified-exact`; validate full dependency closure before any execution |
| exact component identity or complete dependency compatibility cannot be proved | `unverified`; diagnostic/non-executable |
| required feature/node/edge/sidecar entity absent | mark profile stale/incompatible |
| new unmapped categorical value appears | return native value + unmapped status; never coerce to nearest known term |
| ontology dependency unavailable offline | use locked local copy if bundled; otherwise profile unavailable rather than silently changing vocabulary |
| optional materialized TF module unavailable | sidecar semantic queries continue; feature-only clients lose only the compatibility projection |
| mapping sidecar digest mismatch | refuse to load |
| Agora metadata stale | ontoTF manifest remains authoritative for semantic compatibility; discovery can report registry mismatch |

## 19. Rejected assumptions

1. **Corpus version directory is enough compatibility information.** Rejected: exact revisions and relevant schema/value inventories may change independently.
2. **One ontoTF repository implies one release cadence.** Rejected: per-profile release artifacts/tags provide independent cadence inside a monorepo.
3. **TF feature modules can express the whole ontology layer.** Rejected by sign-slot, witness-graph, technical-anchor and zero-span cases.
4. **RDF requires a triplestore runtime.** Rejected: RDF can be an interchange/publication representation while runtime uses a compiled index.
5. **Context-Fabric should absorb ontoTF mappings into `.cfm`.** Rejected: this would couple independent semantic releases to corpus-cache internals and make invalidation harder.
6. **Agora should duplicate mapping manifests.** Rejected: Agora should carry only the metadata needed for discovery/acquisition/compatibility selection and point at the authoritative ontoTF release.
7. **A semver range can authorize auto-loading.** Rejected: several TF corpora use non-semver data versions, and compatible-looking versions can still change schema semantics.
8. **Generated projected features should overwrite native features.** Rejected: native corpus semantics remain authoritative; collision is a validation failure unless a deliberately named override artifact is requested.
9. **Matching TF bytes prove exact parent semantics when the profile also addresses native sidecars.** Rejected: exact identity is component-aware and must cover every semantically addressable native component.

## 20. Unresolved questions delegated to later tickets/design

These do not reopen the distribution decision:

- R-002: exact ontology set, local-term governance, mapping predicates, URI policy and RDF source/export syntax;
- R-003: exact semantic query API, discovery schema, provenance payload and runtime index access patterns;
- R-004: which reference tables are generated from manifests versus maintained prose;
- design ticket: exact manifest serialization, canonical parent-component identity and profile-dependency-manifest algorithms, runtime index encoding, artifact naming and signing workflow;
- implementation benchmark: whether JSON, SQLite, memory-mapped arrays or another deterministic index best serves R-003 query shapes;
- Agora follow-up: final name/schema for `semantic-module`, and whether it is added before or after the first ontoTF POC release.

## 21. Acceptance-criteria trace

- [x] Recommends one exact POC distribution architecture.
- [x] Binds parent identity through logical resource ID, canonical source, TF/schema version, exact tested revision provenance and a transport-independent component manifest covering every semantically addressable native component.
- [x] Defines reusable compatibility through the complete profile dependency closure, including mapped open-domain values/entities, external sidecar/native-adapter contracts and structural invariants.
- [x] Defines the profile source as canonical semantic source; the runtime sidecar and TF feature module are deterministic generated artifacts.
- [x] Defines `unverified` as diagnostic/non-executable and separates storage-empty records from semantic values/feature applicability.
- [x] Keeps Agora limited to discovery, compatibility metadata, acquisition and integration verification.
- [x] Separates source, publication/interchange, runtime and TF compatibility artifacts.
- [x] Covers BHSA, CUC, Syriac, ExtraBiblical and TLHdig-TF deployment behavior.
- [x] Covers Pseudepigrapha-TF and ORACC-TF stress cases, including native zero-span sidecar identity.
- [x] Scores central, per-corpus, parent-owned, TF-module-only, Agora-owned and RDF-runtime alternatives.
- [x] Addresses independent release cycles, offline use, caching, integrity/attestations, stale mappings and parent schema drift.
- [x] Defines an explicit migration path from central POC to per-corpus repositories.
- [x] Leaves ontology governance/query/documentation details to R-002/R-003/R-004 without leaving distribution undecided.

## 22. Gate result

R-001's distribution question is resolved for design purposes: **central source repository, independently releasable exact-version-bound semantic sidecars, optional generated TF modules, thin Agora registration, and a non-RDF-specific runtime index**.

R-005 accepted the empirical dependency at exact reviewed head `48c8bd78d0c3a0501b2fdec6946db5df90517bdb` (merged as `a9c4d74d4de2f9a15eb1464dce341ecd2f92f898`). R-001 is therefore no longer dependency-blocked; merge now requires exact-head validation and fresh independent review of this R-001 head.

## Sources

Primary implementation/documentation pins:

- Text-Fabric data sharing: `annotation/text-fabric@1079c68e.../tf/docs/about/datasharing.md`
- Text-Fabric `use()`/module/version semantics: `annotation/text-fabric@1079c68e.../tf/docs/about/usefunc.md`
- Context-Fabric `Fabric`: `Context-Fabric/context-fabric@3a38ca80.../libs/core/cfabric/core/fabric.py`
- Context-Fabric downloader: `Context-Fabric/context-fabric@3a38ca80.../libs/core/cfabric/downloader/download.py`
- Context-Fabric TF compatibility: `Context-Fabric/context-fabric@3a38ca80.../site/src/app/docs/concepts/text-fabric-compat/page.mdx`
- Agora marketplace architecture: `alexsosn/Agora@848c18af.../wiki/architecture/ref-marketplace-architecture.md`
- Agora feature modules: `alexsosn/Agora@848c18af.../registry/feature-modules.yaml`
- Agora registry validator: `alexsosn/Agora@848c18af.../scripts/validate_registry.py`
- GitHub artifact attestations: https://docs.github.com/en/actions/concepts/security/artifact-attestations
- GitHub immutable releases: https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases
