# R-004: documentation architecture and generated reference design

**Status:** research complete; R-005 accepted; R-001 accepted; R-002 accepted; R-003 accepted; pending exact-head independent review  
**Issue:** #4  
**Recorded:** 2026-09-05

## Decision

ontoTF should use a **source-first, generated-reference documentation architecture**.

Canonical machine-readable profile/mapping data, approved normative ontoTF rules, parent-corpus evidence, and external ontology definitions have different authority domains. They must be validated together; none is a universal precedence layer that can silently redefine the others.

The POC should expose three documentation surfaces from one repository:

1. **normative project documentation** — approved architecture, mapping/governance, compatibility, and versioning rules;
2. **scholarly/user documentation** — methodology, rationale, tutorials, contribution and review guidance;
3. **generated semantic reference** — deterministic per-profile, per-native-selector, per-mapping, per-concept, compatibility, coverage, ontology-lock, and compact agent-facing reference derived from validated sources.

Plain repository Markdown remains reviewable and usable offline. A static site may add navigation/search. Generated JSON is the machine-facing reference. None is maintained as an independent semantic database.

## 1. Accepted foundation contracts

R-005 accepted empirical corpus evidence at reviewed head `48c8bd78d0c3a0501b2fdec6946db5df90517bdb`, merged as `a9c4d74d4de2f9a15eb1464dce341ecd2f92f898`.

R-001 accepted distribution and compatibility semantics at reviewed head `68b88a820f5519ad65d46b732679a6278e9ca3c9`, merged as `a22a95084a1518882d1e3e87d10e9757121f106d`.

R-002 accepted ontology governance and mapping-assessment semantics at reviewed head `d82e6ef2726f149f903eb43ddbfb615faf399cd5`, merged as `a554d4fdc36c8854519064f3a7611b80efa29622`.

R-003 accepted agent/human ergonomics and protocol-portability semantics at reviewed head `6747379a4aa68c17c156344f3ed3b0c2cb29d423`, merged as `02abd89b5b7d4c83027e1e8503a02eef23cab91e`.

R-004 treats those contracts as fixed dependencies unless a later reviewed change explicitly reopens them.

## 2. Research basis

### 2.1 OLiA

OLiA separates native annotation models, a reference model, and linking models. That pattern supports ontoTF's need to keep three distinct objects visible: native corpus semantics, external terminology, and the reviewed mapping between them.

Useful documentation patterns:

- architecture is described separately from model instances;
- machine-readable ontology/linking artifacts remain primary data;
- human pages provide navigation and explanation rather than becoming another editable mapping store.

Inspected sources:

- <https://acoli-repo.github.io/olia/>
- <https://acoli-repo.github.io/olia/models.html>
- <https://acoli-repo.github.io/olia/overview.html>

### 2.2 CIDOC CRM

CIDOC CRM publishes explicit version/status pages that distinguish official, stable, and draft releases. ontoTF should likewise display the exact ontology release/status against which a mapping/profile was reviewed. A convenient “latest” link must never replace immutable provenance.

R-002 remains authoritative for supported ontology releases; R-004 only defines how their status and locks are rendered.

### 2.3 OntoLex

OntoLex documents a core plus optional modules. ontoTF should mirror this ergonomically: each profile page lists the semantic modules/locks it actually uses rather than presenting every ontology supported globally.

### 2.4 Text-Fabric corpora

BHSA and other TF corpora demonstrate the value of feature-specific native pages: feature description, applicable node types, value codes, and corpus-specific cautions. Those pages remain native evidence. ontoTF links to them and renders the ontoTF projection beside the pinned native selector/path rather than copying upstream prose as a new authority.

### 2.5 Context-Fabric MCP and R-003

R-003 retains Context-Fabric's progressive-disclosure principle: compact capability discovery first, detailed mapping/native evidence on demand.

The **current host implementation** inspected by R-003 is Context-Fabric `cfabric-mcp 0.1.7`, whose package metadata declares `mcp>=1.0,<2`. The **current protocol target** is MCP `2026-07-28`. These are distinct operational facts.

Documentation must therefore distinguish:

- host implementation/version;
- current protocol target;
- actually negotiated protocol for a running integration when reported diagnostically;
- immutable semantic profile/mapping identity.

Negotiated protocol and transport/session state **must not become part of semantic identity**. Semantic provenance is based on profile/mapping source, parent component identity/evidence, ontology locks, and reviewed mapping semantics. Host/protocol metadata may explain an integration environment but must not cause two semantically identical resolutions to receive different semantic meaning merely because one host is handshake-era and another is stateless.

### 2.6 Agora

Agora owns discovery/install/integration metadata. It should link to ontoTF profiles and reference pages but not host a fork of semantic mapping documentation. ontoTF owns mapping semantics; Context-Fabric owns native query/MCP host behavior; parent corpora own native semantics.

## 3. Information objects documentation must not collapse

### 3.1 Native corpus semantics

Examples include BHSA `sp=subs`, CUC `emen`, TLHdig `analysis -> lex`, and Pseudepigrapha reading→manuscript witness attestation.

Authority: exact parent corpus artifact plus authoritative native documentation/source evidence.

### 3.2 Research candidate evidence

R-005 `S/C/B/N/R/U/L` classifications are **research candidate** evidence only. They can be linked from research/review pages but **cannot appear as an approved released mapping** unless an independently reviewed canonical mapping assertion exists.

### 3.3 Approved ontoTF mapping assertions

An **approved mapping** contains stable mapping ID, native selector/path, external target where applicable, ontoTF mapping assessment, applicability, review status, rationale/evidence, profile binding, and ontology lock.

Authority: canonical mapping source, provided it validates against normative ontoTF rules and external/native evidence.

### 3.4 Publication relations

A **publication relation** is an optional RDF/OWL/SKOS formalization. It is independent of the ontoTF mapping assessment. An approved `exact` assessment to an OWL class does not automatically create `owl:equivalentClass`, `owl:sameAs`, or a SKOS mapping predicate.

### 3.5 Profile identity and compatibility

R-001 compatibility is represented with:

- `verified-exact`;
- `verified-compatible`;
- `unverified`;
- `incompatible`.

Authority: profile manifest plus the parent component manifest, component identities, and complete dependency closure/evidence used to establish the state.

### 3.6 Normative interpretation rules

Approved ontoTF architecture/specifications define what mapping assessments mean, which states execute, how compatibility is proven, how dense empties are interpreted, and which publication formalizations are legal.

A canonical mapping file is not allowed to override those rules.

### 3.7 Explanatory prose

Research, tutorials, release narratives, and long scholarly notes explain decisions and evidence. They do not activate mappings or redefine normative rules.

## 4. Scoped authority domains

ontoTF should use **scoped authority domains**, not a numeric precedence hierarchy.

| authority domain | authoritative artifact | responsibility |
|---|---|---|
| **native corpus semantics** | pinned parent corpus artifact + authoritative native docs/source | native node/edge/feature/value/path meaning |
| **external ontology semantics** | pinned ontology release/specification | external term meaning and formal vocabulary |
| **ontoTF mapping assertions** | canonical reviewed mapping source | native→external projection, assessment, applicability, rationale |
| **profile identity and compatibility** | profile manifest + R-001 compatibility evidence | profile release identity, parent component manifest, component identities, complete dependency closure |
| **ontology lock identity** | ontology lock | exact tested ontology versions/snapshots/digests/status |
| **normative interpretation rules** | approved ontoTF architecture/specification | legality and interpretation of mappings, compatibility, execution, provenance and publication |
| **generated derivatives** | deterministic build from validated sources | runtime index, RDF/JSON, generated Markdown/HTML/reference JSON |
| **explanation/history** | guides, research, notes, release prose | rationale, pedagogy, historical context |

The domains constrain one another through validation rather than precedence.

### 4.1 Conflict rules

- **mapping source vs generated derivative** → generation/drift defect; CI fails;
- **mapping source vs runtime index** → compiler/cache defect; released bundle invalid;
- **mapping source vs native corpus evidence** → substantive mapping defect; mapping must be revised/reviewed;
- **mapping source vs external ontology definition/lock** → mapping or lock defect; review/activation fails;
- **mapping/profile data vs approved normative ontoTF rule** → **invalid mapping/profile**; **CI and profile activation fail**. The normative rule constrains the data rather than being overridden by it;
- **profile manifest vs observed parent components** → recompute R-001 state from component identity/dependency evidence; no schema-name shortcut;
- **guide/tutorial factual claim vs canonical validated mapping** → explanatory prose defect; fix the guide;
- **generated reference vs canonical validated source** → generated output is stale/incorrect; never hand-edit the generated page to hide the conflict.

This preserves both machine-readable source-of-truth and the authority of normative interpretation rules.

## 5. POC repository documentation layout

```text
ontoTF/
├── AGENTS.md
├── CONTRIBUTING.md
├── profiles/
│   ├── bhsa/
│   │   ├── manifest.yaml
│   │   ├── mappings/
│   │   ├── notes/
│   │   └── tests/
│   ├── cuc/
│   ├── syriac/
│   ├── peshitta/
│   ├── syrnt/
│   ├── extrabiblical/
│   ├── tlhdig-tf/
│   └── pseudepigrapha-tf/
├── ontology/
│   ├── lock.yaml
│   └── local/
├── schemas/
├── docs/
│   ├── research/
│   ├── plans/
│   ├── architecture/
│   ├── guides/
│   │   ├── querying.md
│   │   ├── mapping-review.md
│   │   └── versioning-and-provenance.md
│   ├── reference/                      # GENERATED; do not edit
│   │   ├── index.json
│   │   ├── profiles/<profile-id>/
│   │   │   ├── index.md
│   │   │   ├── compatibility.md
│   │   │   ├── coverage.md
│   │   │   └── native/
│   │   ├── concepts/<stable-concept-key>.md
│   │   ├── mappings/<stable-mapping-id>.md
│   │   └── ontologies/<ontology-id>.md
│   └── releases/<profile-id>/
├── scripts/
└── tests/
```

Exact future schema filenames remain a design decision. The source/derived boundary and reference navigation layout are the research contract.

## 6. Authored versus generated material

### Hand-authored

- research reports and rejected alternatives;
- approved normative architecture/specification prose;
- tutorials/cookbooks;
- contribution/review guidance;
- scholarly rationale notes linked by stable mapping IDs;
- release narrative and migration explanation.

Hand-authored notes may explain but cannot change machine semantics.

### Generated

- profile and compatibility references;
- native selector → semantic mapping tables;
- semantic concept → corpus/native realization tables;
- mapping-detail pages;
- coverage/gap reports;
- mapping-assessment distributions;
- ontology term/version/status pages for terms actually used;
- license/provenance summaries already encoded in locks/manifests;
- compact `reference/index.json` and detail JSON;
- semantic diff sections;
- RDF/Turtle/JSON publication exports;
- runtime/index documentation;
- optional generated TF-module documentation.

### Hybrid release notes

Release notes may combine hand-written motivation with a visibly delimited generated semantic diff. The generated section is reproducible and must not be hand-edited independently.

## 7. Bidirectional navigation

### 7.1 Native → semantic

A generated native entry links:

```text
profile + immutable release
  -> native selector/path
    -> stable mapping ID
      -> approved external target (if any)
      -> Mapping assessment
      -> Publication relation (if any)
      -> applicability/review/evidence
      -> compatibility/provenance
```

The page shows:

- parent component manifest and compatibility state;
- native node/edge kind and direction/path;
- authoritative upstream documentation link;
- approved mappings only in released semantic reference;
- mapping assessment and review state;
- publication relation independently;
- native-only/unsupported state where appropriate;
- stable mapping/profile IDs.

Research candidates may be linked under evidence but are visually and structurally distinct from approved mappings.

### 7.2 Semantic → corpora

A concept page lists each evaluated profile independently, for example:

```text
external concept X
  -> BHSA: <approved assessment> -> native selector
  -> ExtraBiblical: <independently approved assessment> -> native selector
  -> Syriac: <approved assessment or unsupported>
  -> Peshitta: unsupported in inspected profile
```

Each row exposes compatibility separately from mapping assessment.

Explicit states include:

- `exact`, `close`, `broader`, `narrower`, `related` assessment;
- `ambiguous`;
- `native-only`;
- `unsupported`;
- `verified-exact`, `verified-compatible`, `unverified`, `incompatible` profile compatibility where relevant.

An **empty cell is forbidden** for an evaluated profile: a negative/unknown state must be named explicitly.

### 7.3 Mapping-detail page

One stable mapping ID gets one generated page containing:

- profile/release;
- native selector/path;
- external target URI/CURIE when one exists;
- **Mapping assessment**;
- **Publication relation** or explicit `none`;
- applicability;
- evidence/rationale;
- review status;
- ontology lock;
- parent compatibility evidence;
- tests/fixtures;
- first-introduced / last-changed release;
- links to native and semantic indexes.

## 8. Stable identifiers and URLs

Labels and page titles are not semantic identifiers.

Rules:

1. mapping assertions have stable mapping IDs;
2. profiles have stable logical IDs independent of GitHub paths;
3. external concepts are keyed internally by full URI;
4. page anchors derive from stable IDs rather than heading text;
5. `/latest/` may exist for navigation, but provenance links identify immutable profile releases;
6. redirects may preserve renamed site paths, while historical release reference remains immutable.

Conceptual URLs:

```text
/reference/<profile-id>/<profile-version>/...
/reference/concepts/<stable-concept-key>/
/reference/mappings/<stable-mapping-id>/
```

Deployment hostname is not semantic identity.

## 9. Mapping assessment, approximation and uncertainty

Generated pages use the R-002/R-003 vocabulary exactly:

- `exact`;
- `close`;
- `broader`;
- `narrower`;
- `related`;
- `ambiguous`;
- `native-only`;
- `unsupported`.

Assessment direction is native/source → external target.

For an external-concept query:

- **`broader` can under-cover** because the native/source concept is narrower than the external target;
- **`narrower` can over-cover** because the native/source concept is broader than the external target;
- `close` may differ extensionally in either direction;
- `related` is informational and not an automatic substitute.

Generated pages must show that consequence and exact-mode executability separately. They must not describe approximation with an unqualified generic “relation” label.

Evidence uncertainty is separate again: a mapping may have an approved assessment while upstream/native documentation contains a scholarly caveat. The mapping page displays both.

## 10. Compatibility and provenance

Generated compatibility and mapping pages use R-001 evidence rather than a repository/version/schema shorthand.

Minimum profile provenance:

```text
ontoTF profile:            <profile ID + immutable version>
Compatibility:            verified-exact | verified-compatible | unverified | incompatible
Parent component manifest:<manifest algorithm + digest>
Component identities:     <identities for semantically addressed native components>
Dependency evidence:      <closure/report/fingerprint sufficient to justify state>
Mapping source:           <source digest/revision>
Ontology lock:            <lock ID/digest>
Generated by:             <generator version>
```

For `verified-compatible`, the page links or embeds evidence that the **complete dependency closure** validated against the changed component set. For `unverified`, it says which evidence is missing. For `incompatible`, it identifies the failed required dependency.

If licensing applies, the profile/ontology page also records mapping artifact license, parent-corpus license link, ontology licensing/reference policy, and any redistribution constraint relevant to generated/materialized data.

## 11. Research candidates, semantic values and empirical domains

### 11.1 Candidate versus released mapping

R-005 candidate cells can appear in research/review evidence but cannot enter released reference/index data as mappings without stable canonical mapping IDs and review state.

### 11.2 Dense storage empties

Generated inventory/reference data distinguish:

- `node_records_seen` — raw records encountered;
- `nodes_with_value` — records carrying actual non-empty semantic values;
- `empty_observation_count` — storage/API empty observations;
- `observed_values` — non-empty values only.

`""` and `None` are **storage-level empty** observations, not semantic values unless the parent corpus explicitly defines the literal as meaningful. Empty records do not establish feature applicability to a node type and do not become explicit absence/unknown/omission/non-attestation semantics.

### 11.3 Observed versus bounded domains

Documentation distinguishes:

- **observed small domain** — finite non-empty values seen in the pinned artifact;
- **documented bounded/categorical vocabulary** — authoritative source documentation establishes a bounded inventory;
- **open/large domain**;
- **unknown closure**.

An observed finite release is not automatically a **closed vocabulary**.

Concrete regression: pinned CUC 0.2.8 non-empty `emen` observations include `excised`, `missing`, `redundant`, `remark`, `restored`. This is an observed release domain, not a promise that future releases cannot add a value.

## 12. Agent-facing documentation

`docs/reference/index.json` is a bounded navigation/capability index, not a whole ontology/mapping dump.

Conceptual profile entry:

```json
{
  "profile": "tfont-bhsa@0.1.0",
  "compatibility": "verified-exact",
  "parent_component_manifest": "sha256:...",
  "ontology_locks": ["olia:<lock>"],
  "semantic_domains": ["morphology", "syntax", "lexical"],
  "coverage_url": "...",
  "concept_index_url": "..."
}
```

Detailed mapping/evidence resources are fetched selectively by stable ID.

Operational integration metadata is documented separately from semantic identity. Agent/runtime diagnostics may report:

```text
Current host implementation: cfabric-mcp 0.1.7
Host SDK constraint: mcp>=1.0,<2
Current protocol target: 2026-07-28
Negotiated protocol: <runtime value when known>
```

The negotiated protocol, transport, and MCP session state must not become part of semantic identity or alter mapping/profile provenance. Documentation for protocol-specific behavior links to Context-Fabric/MCP rather than copying their manuals.

## 13. Human-facing documentation

### Corpus scholar landing page

Answers:

- Which immutable profile and parent component set were evaluated?
- Is compatibility exact, compatible, unverified, or incompatible?
- Which kinds of semantic questions are supported?
- Which native distinctions remain local?
- Which mappings are approximate/ambiguous?
- What native constraints/path does a semantic query use?

### Ontology/linked-data user concept page

Answers:

- Which profiles map to this concept?
- With which mapping assessment?
- Is there a separate publication relation?
- What native selector realizes it?
- Which ontology lock/profile/parent evidence was tested?
- What review/evidence supports the assertion?

### Contributor guide

Explains:

1. locate native evidence;
2. verify external ontology definition/lock;
3. change canonical mapping/profile source;
4. add positive and negative fixtures;
5. run validation/generation;
6. inspect semantic diff and generated reference;
7. obtain exact-head independent skeptical review.

## 14. Concrete documentation prototypes

These are shapes, not new mapping approvals.

### 14.1 BHSA `sp`, `gn`, `nu`

A native page for `word / sp=subs` should show native BHSA meaning, upstream feature-doc link, applicability from the pinned native contract, reviewed mapping target/assessment if one is eventually approved, and the exact native query selector.

A guide may show a reviewed high-level `Noun + Feminine + Plural` semantic request compiling to native constraints such as:

```text
word sp=subs gn=f nu=pl
```

The generated reference remains one reviewed semantic assertion per stable mapping ID.

### 14.2 BHSA `vt` / `vs`

BHSA stem/verbal-form labels do not automatically become universal tense/stem categories. If no reviewed external projection exists, the released page says `native-only` or `unsupported` as appropriate rather than fabricating equivalence.

### 14.3 Syriac

ETCBC Syriac and SyrNT may share high-level concepts while using different native structures/vocabularies. Semantic concept pages show each realization independently rather than presenting schema aliases.

### 14.4 CUC

`cert`, `emen`, and `alt` remain separate native/editorial assertions. Generated pages use actual non-empty values and distinguish observed domains from documented bounded vocabularies.

### 14.5 TLHdig-TF lexical path

Generated edge page:

```text
Native edge: lexeme
Direction: analysis -> lex
Occurrence semantics: follow analysis/lexeme relation and documented occurrence path
Caution: lex.oslots is a technical anchor, not full lexical occurrence extent
```

### 14.6 TLHdig-TF cluster/surface/witness

Cluster range semantics, surface/document structure, and line→fragment witness links are documented natively. A witness label alone never turns that relation into Pseudepigrapha reading attestation.

### 14.7 ExtraBiblical versus BHSA

Shared ETCBC spelling/family motivates reuse research but not automatic reuse. A concept page shows separate approved assertions and separate compatibility bindings.

### 14.8 Local-only example

A conversion/alignment-specific value such as TLHdig-TF `cu_aligned` remains visible as `native-only` if no reviewed external projection exists.

## 15. Markdown, static site and JSON

Use all three from one build graph.

### Repository Markdown

Required for code review, versioning, offline use and release bundles.

### Static site

Recommended for cross-links/search. A conventional generator such as MkDocs is sufficient; HTML is a build product, not semantic source.

### Generated JSON

Required for agents/tooling so they do not scrape HTML. JSON and Markdown derive from the same deterministic normalized semantic intermediate representation.

## 16. Documentation ownership boundaries

| information | authority/owner | ontoTF behavior |
|---|---|---|
| native feature/node/edge meaning | parent corpus | link exact selector/evidence; do not fork native authority |
| external term definition | ontology project | link/pin lock metadata; do not copy as normative redefinition |
| ontoTF native→external mapping | ontoTF canonical mapping | generated reference renders assessment/evidence/review |
| ontoTF normative mapping/compatibility rules | ontoTF approved specs | constrain canonical data and generated output |
| semantic resolver/query contract | ontoTF R-003/design/runtime | normative ontoTF docs + generated API/capability reference |
| native query/MCP host implementation | Context-Fabric | link host/query docs; do not fork implementation manual |
| MCP protocol specification | MCP project | link exact protocol revision; do not imply host support from protocol recency |
| discovery/install coordinates | Agora/ontoTF distribution metadata | publish/link coordinates, not semantic mapping rules |

R-004 may state compatibility assumptions needed by ontoTF, but mutable host/protocol implementation details remain owned upstream.

## 17. Canonical CI drift and release contract

A documentation build is semantic validation. The following is the **single canonical CI contract** for later implementation:

1. validate **canonical mapping source against schema**;
2. validate profile manifest and ontology lock;
3. validate **parent component manifest**, required **component identities**, and **complete dependency closure**, producing one of the four R-001 compatibility states;
4. validate canonical mapping/profile data against approved normative ontoTF rules; any conflict fails CI/profile activation;
5. enforce **research candidate** vs approved mapping separation so R-005 candidate evidence cannot leak into released mapping reference;
6. validate **mapping assessment and publication relation** as independent fields and validate any formal publication relation against R-002 rules;
7. exclude **storage-level empty** observations from semantic values/applicability unless explicitly defined meaningful by native source;
8. distinguish **observed small domain** from **documented bounded** vocabulary and closed/unknown-closure status;
9. ensure compatibility references use the **four R-001 compatibility states** and expose component/dependency evidence;
10. ensure evaluated **negative states** (`native-only`, `unsupported`, `ambiguous`, `unverified`, `incompatible`) are rendered explicitly rather than as blank cells;
11. compile one **deterministic normalized semantic intermediate representation** from validated sources;
12. generate runtime sidecar/index, RDF/JSON publication, reference Markdown/JSON, and static-site inputs from that IR;
13. run generation twice or compare canonical digests to prove deterministic output;
14. fail `git diff --exit-code` or equivalent when committed generated reference is stale;
15. build static documentation in strict mode and fail broken internal links, duplicate/stale stable anchors, or unresolved generated references;
16. verify generated profile/mapping pages carry profile/mapping source, ontology lock, parent component manifest/component identities, compatibility/dependency evidence, and generator identity;
17. verify current-host/protocol documentation separates the pinned host implementation, **negotiated protocol**, and protocol target; protocol/transport/session metadata must not enter semantic identity;
18. run representative documentation regressions for BHSA, Syriac, CUC, TLHdig-TF, ExtraBiblical, local-only semantics, and negative capability states;
19. produce a **semantic diff** that independently classifies mapping assessment, publication relation, native selector/path, target/lock, compatibility evidence, review status, and prose-only changes;
20. require release-note/reviewer attention for semantic API changes even when generated prose still builds;
21. ensure every generated file carries a clear **generated/do-not-edit marker** where the format permits;
22. verify release reference and compact agent index identify the same immutable profile/mapping/ontology/parent semantic inputs as runtime artifacts.

The design/implementation phase should convert these observable checks into TDD fixtures; this research PR does not implement the generator.

## 18. Semantic diff as documentation

A generated semantic diff classifies at least:

- mapping added/removed;
- **mapping assessment changed** (`close`→`exact`, `exact`→`close`, etc.);
- **publication relation changed** independently;
- **native selector/path changed**;
- external target or **ontology lock/release changed**;
- **parent compatibility evidence changed**;
- review state changed;
- rationale/prose-only change.

Assessment changes are public semantic behavior changes even when no Python code changes. Publication-formalization changes are separately visible so RDF changes are not confused with runtime query semantics.

## 19. Unsupported and negative semantics

For every evaluated concept/domain, generated references explicitly distinguish:

- `not-evaluated` — research has not decided;
- `unsupported` — active profile has no supported projection/capability;
- `native-only` — relevant native distinction intentionally has no external target;
- `ambiguous` — evidence does not support one unambiguous projection;
- `unverified` — parent/profile evidence incomplete; inspection allowed, semantic execution not;
- `incompatible` — required parent dependency failed;
- approximation-required assessments (`close`, `broader`, `narrower`, etc.) with exact-mode consequence.

An **empty cell** is **forbidden** once a profile/concept combination has been evaluated; blank output is documentation failure, not a semantic state.

## 20. Documentation versioning

Generated semantic reference is versioned with the ontoTF profile release, not only the parent corpus release.

Each immutable profile reference identifies:

```text
ontoTF profile/mapping source -> semantic assertions
Parent component manifest     -> native evidence target
Compatibility/dependency evidence -> executable state
Ontology lock                 -> external terminology target
```

A current/latest site view may exist for navigation. Query provenance and released references point to immutable profile/mapping identity.

Historical reference pages are never rewritten merely because an ontology later deprecates a term; new releases add migration/deprecation notices.

## 21. Independent documentation-review checklist

A final reviewer should be able to answer:

1. Can every displayed approved mapping be reconstructed from canonical validated source?
2. Does each native selector link to exact pinned native evidence?
3. Can research candidates be mistaken for released mappings?
4. Are mapping assessment and publication relation rendered independently?
5. Are all four compatibility states and their component/dependency evidence visible?
6. Are storage empties excluded from semantic domains/applicability?
7. Are observed release domains distinguished from documented closed/bounded vocabularies?
8. Are `native-only`, `unsupported`, `ambiguous`, `unverified`, and `incompatible` visible rather than blank?
9. Can a corpus scholar and ontology user navigate to the same stable mapping assertion from opposite directions?
10. Does semantic diff expose every semantic dimension changed by a PR?
11. Are host/protocol operational details separated from semantic identity/provenance?
12. Can the reference be used offline from a released profile bundle?
13. Do generated/runtime artifacts identify the same canonical semantic inputs?

## 22. Rejected alternatives

### Numeric source-of-truth precedence

Rejected. Authority is scoped. Canonical mapping data cannot override normative interpretation rules, native source semantics, or external ontology definitions.

### Hand-maintained mapping tables in Markdown

Rejected. They become a second semantic database and drift from runtime source.

### RDF/Turtle as sole documentation/authoring source

Rejected. RDF remains a generated publication surface; R-003 selected schema-validated YAML as the human review source for the POC.

### Generate tutorials/research rationale from mapping data

Rejected. Semantic facts can be generated; scholarly argument and pedagogy remain authored prose.

### Put mapping documentation in parent corpora or Agora

Rejected. ontoTF profiles release independently and Agora is a thin discovery/install layer. Link upstream native evidence rather than fork it.

### One giant JSON reference

Rejected. Agent ergonomics require compact index + selectively fetched detail resources.

### Version documentation only by parent corpus release

Rejected. Mapping semantics and ontology locks can change independently.

### Protocol/session identity as semantic identity

Rejected. R-003 requires equivalent semantic resolution across handshake-era and stateless hosts for identical semantic inputs.

## 23. Unresolved implementation choices

Design work still needs to choose:

1. exact canonical mapping/profile JSON Schemas and file granularity;
2. whether generated reference Markdown is committed or release-built only;
3. exact static-site generator/theme configuration;
4. stable URI namespace for ontoTF-local mapping/concept identifiers;
5. how much upstream feature metadata to cache versus link;
6. exact `reference/index.json` / detail schemas;
7. semantic-diff presentation in GitHub checks/release notes;
8. forge-independent reviewer provenance representation;
9. central-site versus profile-bundle hosting/retention policy;
10. exact runtime diagnostics schema for host implementation / negotiated protocol metadata.

These choices do not reopen scoped authority, generated-reference derivation, component-aware compatibility, assessment/publication separation, explicit negative states, or protocol-independent semantic identity.

## 24. Acceptance trace

- Source-of-truth hierarchy: scoped authority domains and explicit conflicts in §4.
- Exact repository layout: §5.
- Generated versus authored material: §6.
- Bidirectional navigation: §7.
- Mapping assessment, uncertainty, negative states: §§9, 19.
- Compatibility/provenance/licenses: §§10, 20.
- Agent and scholar documentation: §§12–13.
- ontoTF / parent / Context-Fabric / MCP / Agora ownership: §16.
- Update/release/CI drift: one canonical 22-step contract in §17 plus semantic diff §18.
- Required concrete examples: §14.
- Stable URLs/anchors/versioning: §§8, 20.
- Current-host versus protocol target/negotiation portability: §§2.5, 12, 16–17.

## 25. Sources

Primary sources/evidence used by this research:

- OLiA documentation architecture: <https://acoli-repo.github.io/olia/>, <https://acoli-repo.github.io/olia/models.html>, <https://acoli-repo.github.io/olia/overview.html>;
- CIDOC CRM release/status documentation: <https://cidoc-crm.org/versions-of-the-cidoc-crm>;
- OntoLex core and Lexicog documentation: <https://ontolex.github.io/ontolex/specification.html>, <https://ontolex.github.io/lexicog/>;
- Text-Fabric/BHSA native feature documentation and metadata API;
- Context-Fabric MCP at `Context-Fabric/context-fabric@3a38ca80e617d872ce1664e0f0740486d0e7e8ac`;
- MCP `2026-07-28` specification/release evidence as accepted by R-003;
- Agora plugin-boundary architecture;
- accepted ontoTF R-001 / PR #8;
- accepted ontoTF R-002 / PR #9;
- accepted ontoTF R-003 / PR #10;
- accepted ontoTF R-005 / PR #7.

Any future material change to those accepted contracts requires R-004 reconciliation and fresh exact-head review before release-documentation behavior changes.
