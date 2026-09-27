# P-004 — seven-model production coverage roadmap

**Issue:** #202  
**Status:** roadmap/design  
**Baseline:** `main` after I-015, `a7fd42b020a7784cdbc739dc7e20b657c0f0e0b8`

## 1. Objective

Complete the common semantic basis originally accepted by R-002/R-006:

1. SKOS
2. OLiA
3. OntoLex-Lemon
4. CIDOC CRM
5. CRMtex
6. LRMoo
7. CRMinf

This roadmap does not redefine PROV-O/SHACL/Web Annotation as members of the seven-model semantic pivot. Optional domain extensions remain evidence-gated.

The target is a production semantic adapter over the original seven-corpus acceptance family:

- BHSA
- ETCBC Syriac
- ETCBC ExtraBiblical
- CUC
- Pseudepigrapha-TF
- ORACC-TF
- TLHdig-TF

## 2. What “full coverage” means

Full coverage is **not** “every native item maps to a shared ontology term”.

For each immutable production profile release, every in-scope native semantic item must have one reviewed disposition:

- exact;
- close;
- broader;
- narrower;
- related;
- ambiguous;
- native-only;
- unsupported;
- or explicitly technical/non-semantic and excluded from the semantic denominator.

The primary completion metric is therefore:

> **100% reviewed/accounted semantic coverage inside the declared production denominator.**

Common-target coverage is reported separately and may legitimately remain below 100%.

This preserves the fail-closed architecture and avoids ontology mappings created merely to improve a percentage.

### R-011 baseline

The historical seven-pilot research baseline had:

- 685 raw denominator items;
- 99 reviewed items = 14.5%;
- 26 items with common targets = 3.8%;
- 52 reviewed pilot mapping rows;
- 62.0% weighted common-target coverage in a separate agent-useful denominator.

Those figures answer different questions. P-004 uses reviewed denominator completion, not the weighted pilot score, as the final completion criterion.

## 3. Production denominator

### 3.1 Included

The semantic census includes, where meaningful:

- node/entity kinds;
- node features;
- explicitly bounded semantic feature values;
- semantic edge features and reviewed paths;
- extent/anchor semantics when they carry meaning rather than storage mechanics;
- authority/identity/identifier references;
- explicit source assertion shapes.

### 3.2 Excluded from semantic coverage

Storage mechanics are still documented but do not inflate the semantic denominator:

- warp features;
- synthetic/empty slots used only as technical anchors;
- implementation-only IDs;
- converter bookkeeping with no source semantics;
- generic slot coverage and ordinary TF mechanics unless a profile explicitly assigns them semantic meaning.

Observed values are not treated as a closed semantic enum merely because they happen to be finite in one snapshot.

### 3.3 Exhaustiveness

BHSA/Syriac/ExtraBiblical/CUC/TLH should use machine-exhaustive inventories where feasible.

Pseudepigrapha and ORACC must move beyond the old curated R-011 denominator where their current converter/model can expose a machine-exhaustive semantic inventory. If a true exhaustive denominator cannot be generated, the production profile must state the exact bounded limitation and cannot claim corpus-wide 100% coverage.

## 4. Coverage matrix

The seven recurring TFont profiles and seven core models are related but not one-to-one:

| TFont profile | primary core model(s) |
| --- | --- |
| structural | native TF/Context-Fabric semantics; no forced core ontology |
| linguistic | OLiA |
| lexical | OntoLex-Lemon + SKOS |
| written-text | CRMtex + CIDOC CRM |
| textology | LRMoo + CIDOC CRM/CRMtex as needed |
| heritage | CIDOC CRM |
| scholarly-inference | CRMinf |

SKOS is cross-cutting for concept schemes and reviewed concept mappings.

## 5. Workstream A — census and coverage accounting

Before broad mapping promotion:

1. regenerate current semantic inventories for all seven corpora;
2. pin exact corpus/component revisions for the next production profile release;
3. classify every denominator item under a controlled profile/capability;
4. record current reviewed disposition or mark it explicitly unreviewed;
5. emit machine-readable coverage reports per corpus/profile/ontology;
6. freeze denominator digests so later “100%” claims are reproducible.

### Exit

- no invisible/unaccounted denominator items;
- coverage calculator reproducible from repository artifacts;
- later workstreams can reduce `unreviewed` monotonically to zero.

## 6. Workstream B — runtime prerequisites for full semantic coverage

I-015 proves exact scalar/value-set atoms and conjunction. The remaining common pivot requires productionizing previously researched runtime contracts.

### B1. Approximate semantics — R-016

Implement reviewed approximate resolution/execution for eligible:

- close;
- broader;
- narrower.

Each executable approximation must carry explicit loss/coverage semantics. `related` and `ambiguous` are never substitution authority.

Approximate conjunction must preserve every atom and aggregate losses fail-closed.

### B2. Authority/identity/identifier — R-017

The compiler already emits authority/identity/identifier indexes. Add agent/runtime resolution over those indexes without leaking authority values into the common semantic index.

Required for SKOS-backed concept schemes, catalogue IDs and external lexical identities.

### B3. Multi-binding composition — R-018

Implement explicit composition for multiple exact bindings under one SemanticKey only when the reviewed composition contract authorizes it.

Do not reinterpret ordinary ambiguity as composition.

### B4. TF-native graph execution

Extend execution beyond the current scalar/value-set feature predicates to the typed native shapes already allowed by the architecture:

- node-kind;
- valued/unvalued edge traversal;
- direction;
- bounded path traversal;
- reviewed extent/anchor interpretation.

This is necessary for written-text, textology and heritage mappings.

### B5. Ontology bundle and bridge runtime

Enforce R-012/R-015 version-aware bridge requirements, especially CRMtex 2.0’s historical CRM/FRBRoo/CRMinf dependency family.

Matching class codes or labels never create a bridge.

### Exit

Every execution shape required by accepted seven-model mappings is either implemented with tests or explicitly non-executable and represented as such.

## 7. Workstream C — OLiA production linguistic coverage

I-015 is the first slice.

### C1. BHSA / Syriac / ExtraBiblical

Complete review of:

- POS;
- gender;
- number;
- person;
- tense/aspect/mood;
- verbal voice/derivational stem categories;
- nominal state/case where source semantics permit;
- syntax;
- discourse.

Traditional category names do not prove equivalence. For example, Semitic verbal stems should be decomposed and mapped only to defensible OLiA semantics rather than hard-coded `Hiphil = Aphel` style equivalence.

### C2. ORACC / TLH

Review native linguistic analysis and promote OLiA mappings where source semantics justify them. Preserve language-specific or analysis-specific categories as native-only/ambiguous where necessary.

### C3. Cross-corpus acceptance

Required queries include representative combinations of POS + morphology + syntax, with exact and authorized approximate cases.

### Exit

All in-scope linguistic denominator items in eligible corpora have reviewed dispositions; zero `unreviewed` remains in released linguistic profiles.

## 8. Workstream D — OntoLex-Lemon + SKOS lexical coverage

### D1. Identity layers

Keep distinct:

- lexical entry;
- canonical/citation form;
- other lexical forms;
- lexical sense;
- lexical concept;
- root/morphological abstraction;
- gloss/definition strings.

### D2. Corpus coverage

Productionize lexical records in at least:

- BHSA;
- Syriac;
- ExtraBiblical;
- ORACC;
- TLH.

CUC/Pseudepigrapha participate only where actual lexical identity semantics exist.

### D3. SKOS

Use SKOS for:

- controlled concept schemes;
- broader/narrower/related relationships where reviewed;
- cross-scheme mappings with correct strength.

Do not create concept identity from gloss-string equality.

### D4. External lexical authorities

Use R-017 authority/identity paths where a corpus has exact external IDs. Source senses remain source senses unless a reviewed shared concept mapping exists.

### Exit

Every lexical denominator item has a reviewed disposition; entry/form/sense/concept distinctions are queryable and provenance-preserving.

## 9. Workstream E — CIDOC CRM + CRMtex coverage

Primary corpora: CUC, ORACC, TLH, plus any other corpus with actual carrier semantics.

### E1. CIDOC CRM / heritage

Review and productionize where present:

- physical object;
- physical part;
- identifier;
- material/support;
- place/provenance;
- production/modification events;
- custody/current location;
- actors and times tied to those events.

Generic ORACC `document` remains non-E22 until a reviewed selector proves physical-carrier identity.

### E2. CRMtex / written text

Review and productionize:

- written text;
- written-text segment;
- segment relations;
- line/column/word/sign where the native semantics fit TX7-style segmentation;
- grapheme vs glyph only where the source distinguishes abstract sign identity from concrete written occurrence;
- writing systems;
- transcription/recognition/reading activities only when the source models the activity itself.

Storage shape alone never authorizes CRMtex.

### Exit

Heritage and written-text denominators for eligible corpora are fully reviewed, and executable mappings use typed graph plans rather than label inference.

## 10. Workstream F — LRMoo textology/transmission coverage

Productionize only source-supported distinctions among:

- Work;
- Expression;
- Manifestation;
- Item;
- textual version/realization;
- derivation/revision/translation;
- symbolic fragment;
- transmission/witness relationships.

Physical fragments and symbolic expression fragments remain distinct.

### Pseudepigrapha

Use it as the strongest first production textology case while preserving its apparatus graph exactly.

Residual apparatus concepts without a defensible seven-model target remain native/profile-local. Do not mint a large TFont apparatus ontology merely to force common-target coverage.

### Exit

All in-scope textology denominator items are reviewed, including explicit native-only apparatus roles where no core target exists.

## 11. Workstream G — CRMinf scholarly-inference coverage

Audit all seven corpora for explicit source-recorded:

- propositions/claims;
- belief states;
- inference/reconstruction activity;
- meaning comprehension;
- provenance statements/assessments.

Do not map ordinary catalogue/source facts, damage flags or editor/display codes to CRMinf.

A profile with no positive scholarly-inference evidence is complete when that absence is explicitly reviewed and represented.

### Exit

Zero unreviewed scholarly-inference candidates remain. Positive mappings exist only where source semantics actually record claims/inference.

## 12. Workstream H — cross-model composition and completion release

The final acceptance suite must prove complementary projections without collapsing semantic layers.

Required composition families:

1. OLiA grammatical categories on OntoLex lexical entities;
2. CRM physical carriers bearing CRMtex written text;
3. LRMoo intellectual/textual entities related to carriers only through reviewed relations;
4. CRMinf claims/inference about entities from the other profiles;
5. SKOS concept mappings/authority filters without using SKOS as generic OWL equivalence.

Required negative controls:

- native-only;
- unsupported;
- ambiguous;
- related used as substitute constraint;
- stale ontology bridge;
- incompatible corpus parent;
- unsafe identity conflation;
- technical anchor treated as source semantics;
- cross-component node-ID intersection without a reviewed shared identity domain.

## 13. Dependency order

```text
A  census / denominator
        ↓
B  runtime prerequisites
        ↓
   ┌────┴────┐
   C         D
 OLiA   OntoLex+SKOS
   └────┬────┘
        ↓
E  CIDOC CRM + CRMtex
        ↓
F  LRMoo
        ↓
G  CRMinf
        ↓
H  seven-model composition + completion release
```

C and D may proceed in parallel after B.

E follows B because R-011 already shows many non-linguistic mappings are `close` and graph-shaped.

F follows E so physical carrier / physical writing / intellectual text are not conflated.

G follows F so inference targets already-distinguished source/text/carrier entities.

## 14. Release strategy

Do not mutate historical profile releases.

Each corpus gets immutable semantic profile releases with:

- exact parent/component identities;
- denominator digest;
- mapping/evidence/review digests;
- ontology/bundle locks;
- coverage report.

A corpus revision creates a new profile release and coverage delta report.

Suggested milestones:

- **M1:** coverage accounting + missing runtime primitives;
- **M2:** full linguistic + lexical production coverage;
- **M3:** full written-text + heritage production coverage;
- **M4:** full textology + scholarly-inference coverage;
- **M5:** seven-model completion release.

## 15. Completion criteria

The seven-model core is complete when:

- all seven pilot corpora have versioned production coverage manifests;
- every declared semantic denominator is 100% reviewed/accounted;
- no `unreviewed` item remains inside supported scope;
- all seven core models have locked production artifacts and are used positively where corpus evidence supports them;
- absence/native-only/unsupported states are explicit where evidence does not support positive mappings;
- exact and authorized approximate semantic queries execute with deterministic provenance;
- cross-model queries preserve identity/layer boundaries;
- all negative controls fail closed;
- coverage reports are reproducible from repository artifacts;
- full exact-head and post-merge suites pass;
- a final independent adversarial review finds no ontology-coverage inflation or semantic-layer collapse.

## 16. Child-ticket process

Each implementation child follows:

```text
research/reconciliation
→ reviewed plan
→ TDD RED
→ minimal GREEN
→ focused + full exact-head CI
→ fresh logically-independent adversarial review
→ expected-head merge
```

R-011 mappings are research leads, not automatic production mappings. Every promoted row is rechecked against the exact corpus pin and exact ontology lock used by its production profile.
