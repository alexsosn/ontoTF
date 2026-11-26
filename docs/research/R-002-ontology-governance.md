# R-002: ontology governance and supported semantic profiles

**Status:** research complete; R-005 and R-001 accepted; pending exact-head independent review  
**Issue:** #2  
**Recorded:** 2026-09-05

## Decision

ontoTF should use a **tiered, open-ended ontology policy** rather than one imported universal ontology.

The POC should distinguish four support tiers:

1. **core infrastructure vocabularies** — stable, open standards used by ontoTF itself to express mapping relations, provenance and annotation targets;
2. **supported semantic profiles** — maintained external ontologies that ontoTF validates and uses for a defined semantic domain;
3. **external controlled vocabularies** — authoritative evolving datasets that ontoTF links to term-by-term but does not import as normative runtime dependencies;
4. **reference/prior-art vocabularies** — useful models that are draft, stale, non-commercially licensed, superseded, or otherwise unsuitable as normative dependencies.

The initial recommendation is:

| tier | vocabularies / ontologies |
|---|---|
| **supported foundation models** | SKOS, OLiA, OntoLex-Lemon core, CIDOC CRM 7.1.3, CRMtex 2.0, LRMoo 1.1.1, CRMinf 1.2.1; PROV-O for provenance; SHACL 1.0 for RDF validation tooling |
| **supported linguistic/lexical profiles** | OLiA, OntoLex-Lemon 2016 core + VarTrans, LexInfo 3.0, OntoLex Lexicog 2019 |
| **supported heritage/text profiles** | CIDOC CRM 7.1.3, CRMtex 2.0, LRMoo 1.1.1, CRMinf 1.2.1 |
| **optional supported domain/publication profiles** | CRMarchaeo 2.1.1, CRMsci 3.2, LexInfo 3.0, OntoLex Lexicog 2019, OntoLex VarTrans, Web Annotation |
| **external controlled vocabularies** | Getty AAT, PeriodO |
| **reference/prior art** | POWLA, SAWS, Critical Apparatus Ontology 0.9, OntoLex Morph until final publication, OntoLex FrAC until final publication |

ontoTF must not infer semantic identity from similar labels. Formal equivalence is exceptional. Every mapping carries a formalism-neutral **mapping assessment** (`exact | close | broader | narrower | related | ambiguous | native-only | unsupported`) for query planning and UX, while an independent **publication relation** records an RDF/OWL/SKOS formalization only when the target model justifies one. The corpus-native assertion remains authoritative.

The directional assessment values are always interpreted from the native/source concept toward the external target: **`broader` means the target is broader than the native/source concept**, while **`narrower` means the target is narrower than the native/source concept**. This runtime direction is part of the ontoTF assessment contract and does not imply any particular RDF predicate.

### Mapping-assessment semantics

The ontoTF assessment vocabulary has the following governance meanings, independent of any RDF publication predicate:

- **`exact` — the external target and native/source concept are judged semantically coextensive** for the reviewed ontoTF projection. This is a mapping-level assessment, not RDF identity or OWL equivalence.
- **`close` — the external target and native/source concept are substantially overlapping or near-equivalent**, but the evidence does not justify coextensiveness/interchangeability.
- **`broader` — the external target is broader than the native/source concept**.
- **`narrower` — the external target is narrower than the native/source concept**.
- **`related` — the external target is semantically related but neither coextensive nor ordered as broader/narrower**.
- **`ambiguous` — available evidence does not justify one unambiguous external-target assessment**; multiple plausible targets or relations remain unresolved.
- **`native-only` — the native/source concept is intentionally supported without an external ontology target** because preserving the native semantics is the reviewed outcome.
- **`unsupported` — the active ontoTF profile does not provide a supported semantic projection for the native/source concept** under the current ontology/profile policy.

Mapping-level **`exact` is distinct from R-001 `verified-exact`**: the former describes a reviewed semantic relation between a native/source concept and a target concept, while the latter proves exact identity of the loaded parent component set. **`native-only` and `unsupported` have no external target** and therefore cannot acquire a publication mapping relation. `ambiguous` likewise does not authorize an automatic cross-ontology projection; R-003 may refine runtime presentation and query-planning behavior without changing these governance meanings.

A mapping records both a **stable term URI** and the **tested ontology release/snapshot**. Versionless namespaces alone are not enough for reproducibility. Existing mapping releases never change meaning merely because an upstream ontology publishes a new release or deprecates a term.

When no external term fits, ontoTF should prefer, in order:

1. preserve the native corpus concept without a semantic projection;
2. map it approximately to an external concept where that relation is defensible;
3. define a corpus-local concept if the value is specific to one annotation tradition;
4. define a small ontoTF concept only when the same semantic gap recurs across independent corpora and is needed for interoperability.

R-005 demonstrates full variation-unit/reading/witness-attestation/explicit-absence apparatus semantics robustly in Pseudepigrapha-TF, but not in a second independent corpus. Peshitta A/B witness metadata and TLHdig line→fragment witness links are related assertions, not equivalent reading-at-locus apparatus graphs. Therefore the foundation POC should **not mint** apparatus-specific ontoTF domain vocabulary yet; keep those semantics native/profile-local and retain CAO/SAWS as prior art until recurrence or mapping-infrastructure necessity is established.

R-001 accepted the distribution/version-binding dependency at exact reviewed head `68b88a820f5519ad65d46b732679a6278e9ca3c9`, merged as `a22a95084a1518882d1e3e87d10e9757121f106d`. R-002 therefore assumes the accepted component-aware parent identity contract: every semantically addressable native component is identity-bound for `verified-exact`, and any non-exact component set must pass the complete dependency-closure validation before semantic execution.

## 1. Evaluation method

Candidates were assessed on:

- authoritative specification and current release/status;
- stable namespace and term-URI policy;
- license and redistribution conditions;
- governance and recent maintenance;
- release/deprecation behavior;
- fit to the node, feature and edge semantics measured in R-005;
- overlap with other selected vocabularies;
- ability to resolve or validate offline from a pinned snapshot;
- suitability as a normative dependency versus an alignment/publication target.

The evaluation deliberately separates the age of a standard from the age of its latest document. A stable Recommendation such as SKOS does not need recent specification churn to remain useful. Conversely, a newer draft is not selected merely because its date is later than the last stable release.

Where an ontology has a stable term namespace but no strong semantic-version contract, ontoTF should store an immutable content digest and, when available, the exact source-repository commit used for validation.

## 2. Openness policy

### 2.1 Normative and supported dependencies

A vocabulary may be a core or supported ontoTF dependency only when ontoTF can lawfully:

- use its term URIs in mappings;
- redistribute the mapping files that refer to those terms;
- keep the ontology subset or full machine-readable snapshot required for reproducible offline validation;
- use it in commercial as well as non-commercial environments;
- publish derived alignment assertions.

Acceptable examples include CC0/public-domain dedication, CC BY, Apache-2.0, W3C specifications under the applicable W3C document/software terms, and attribution-licensed open datasets such as ODC-By when their attribution conditions are preserved.

A non-commercial restriction is incompatible with a normative dependency because it would make the semantic layer unusable in otherwise lawful commercial research tooling. Ambiguous rights also block normative support until clarified.

### 2.2 External vocabularies

An evolving controlled vocabulary may remain external even when its license is open. ontoTF then stores the external URI and the exact snapshot/revision used for validation, but does not make installing the complete vocabulary a prerequisite for ordinary runtime use.

This is the preferred treatment for Getty AAT and PeriodO.

### 2.3 Reference-only models

A model can remain useful as scholarly prior art even when ontoTF does not depend on it. Reference status permits documentation links and explicit alignments where legally permitted, but ontoTF must not imply that the model is maintained, stable or part of the supported runtime contract.

## 3. Version and URI governance

Every external term used by a released ontoTF profile should be represented in the ontology lock with at least:

```yaml
ontology: olia
term: http://purl.org/olia/olia.owl#Masculine
term_uri_policy: stable
release: null
source_revision: d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6
content_digest: sha256:...
retrieved_at: 2026-09-05
support_tier: supported-profile
```

For an ontology with an explicit release:

```yaml
ontology: cidoc-crm
term: http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object
release: 7.1.3
release_status: official-iso-correspondence
content_digest: sha256:...
```

The later design ticket may revise field names, but not these invariants:

- stable term URI and tested release/snapshot are separate facts;
- the lock is immutable for a published mapping release;
- updating an ontology lock creates a new mapping release;
- a replacement/deprecation must be reviewed rather than silently followed;
- offline CI resolves against the pinned local snapshot, not whatever a namespace URL serves that day.

### 3.1 Deprecation

If an upstream term is deprecated or replaced:

1. existing ontoTF releases keep the old lock and old mapping;
2. the next mapping revision records the upstream deprecation/replacement evidence;
3. maintainers decide whether the new term is semantically equivalent, broader/narrower, or merely a successor in maintenance history;
4. regression queries compare the old and new projections;
5. migration is documented in generated mapping reference material.

A changed URI is not automatically a changed concept, and an upstream `replacedBy` assertion is not automatically sufficient evidence for OWL equivalence.

## 4. Mapping-strength policy

ontoTF separates a reified **mapping assessment** from any RDF **publication relation**. The assessment controls runtime/query behavior; it does not automatically select an RDF predicate. Formalization follows the native formalism of the target ontology or remains an explicit ontoTF mapping assertion when no safe RDF/OWL/SKOS relation exists.

### 4.1 Identity and OWL equivalence

`owl:sameAs` is reserved for two identifiers denoting the same individual/resource.

`owl:equivalentClass` or `owl:equivalentProperty` is allowed only when the two class/property meanings have been demonstrated to have the same extension under the relevant modelling assumptions. Matching labels, shared glosses or broadly similar corpus use are insufficient.

The ordinary corpus-mapping workflow should therefore almost never emit OWL equivalence automatically.

### 4.2 SKOS mappings

SKOS mapping predicates are used only when the mapped resources are genuinely SKOS concepts in concept schemes. They are not a generic encoding for mappings to OWL/RDFS classes or properties such as OLiA or CIDOC CRM. For genuine SKOS concepts:

- `skos:exactMatch` — high-confidence interchangeability between concepts in different concept schemes; still not an OWL identity claim;
- `skos:closeMatch` — materially similar but not guaranteed interchangeable;
- `skos:broadMatch` / `skos:narrowMatch` — directional abstraction/specialization;
- `skos:relatedMatch` — semantic relation without hierarchical or near-equivalence claim.

`skos:closeMatch` is intentionally not transitive. ontoTF must not infer A≈C merely because A close-matches B and B close-matches C.

The compact R-005 candidate words are research evidence only. Approved mappings receive a reviewed ontoTF assessment; that assessment remains separate from RDF formalization. For OWL/RDFS class/property targets, use `rdfs:subClassOf` / `rdfs:subPropertyOf` or OWL equivalence only when logically justified, otherwise publish the reified ontoTF assertion without manufacturing a SKOS predicate.

### 4.3 Native assertions remain authoritative

A projection does not overwrite the corpus value. A result record can, for example, keep a corpus-native grammatical-gender value next to a same-domain external candidate:

```text
native: BHSA word.gn = m
target: olia:Masculine
assessment: close
publication_relation: none
confidence: illustrative
```

This example is intentionally like-for-like: both sides concern grammatical gender rather than crossing from a verbal-stem value to a part-of-speech category. It illustrates the record shape and the separation between ontoTF assessment and RDF publication formalism; it does **not** itself approve `close` (or `exact`) for a released mapping. A production mapping must review the pinned BHSA definition and pinned OLiA class definition before choosing the final assessment. Because the target is an OLiA OWL class and this example asserts no independently justified OWL/RDFS relation, `publication_relation` remains `none`; ontoTF must not manufacture a SKOS mapping predicate.

If no defensible external concept exists, the projection is absent rather than fabricated.

## 5. Cross-linguistic categories

Language-independent categories should be mapped only at the abstraction level actually supported by the corpus analysis.

Examples:

- masculine/feminine, singular/plural/dual and person categories often have good OLiA/LexInfo targets;
- a broad `Verb` or `Noun` category may have a useful cross-linguistic projection even when corpus-specific POS systems differ at finer levels;
- BHSA `qal`, Syriac `peal`, Hittite stem classes and Akkadian/ORACC morphological analyses remain language- or annotation-specific concepts unless a maintained ontology explicitly models the exact category;
- BHSA `wayq` and other corpus-specific verbal categories should not be collapsed into a generic tense/aspect term that loses the source analysis;
- a value may have both a broad external projection and a local narrower concept.

This rule avoids building a covert comparative grammar into the ontology layer.

## 6. Candidate matrix

Scores are qualitative: `5` strong, `1` poor. `maintenance` reflects governance/current maintenance appropriate to the candidate's role, not raw commit frequency.

| candidate | status at 2026-09-05 | openness | maintenance | target-corpus fit | offline/reproducible | decision |
|---|---|---:|---:|---:|---:|---|
| SKOS | W3C Recommendation, 2009 | 5 | 5 | 5 | 5 | core |
| PROV-O | W3C Recommendation, 2013 | 5 | 5 | 5 | 5 | core |
| Web Annotation | W3C Recommendation, 2017 | 5 | 5 | 5 | 5 | optional publication/targeting profile |
| SHACL 1.0 | W3C Recommendation, 2017 | 5 | 5 | 4 | 5 | validation standard |
| OLiA | maintained ontology ecosystem; checked 2026 repo head | 5 | 4 | 5 | 5 | supported linguistic profile |
| OntoLex-Lemon core | W3C CG Final Report, 2016 | 4 | 4 | 5 | 5 | supported lexical profile |
| OntoLex VarTrans | part of published 2016 model | 4 | 4 | 4 | 5 | supported lexical profile |
| OntoLex Lexicog | W3C CG Final Report, 2019 | 4 | 4 | 3 | 5 | supported optional lexical profile |
| LexInfo 3.0 | published ontology, Apache-2.0 | 5 | 4 | 5 | 5 | supported linguistic profile |
| OntoLex Morph | public-review draft in 2026 | 4 | 5 | 5 | 5 | reference until final |
| OntoLex FrAC | public-review draft in 2026 | 4 | 5 | 3 | 5 | reference until final |
| CIDOC CRM | 7.1.3 last official ISO-corresponding release; later 7.x drafts | 5 | 5 | 5 | 5 | supported heritage core |
| CRMtex | 2.0 stable | 5 | 5 | 5 | 5 | supported textual/epigraphic profile |
| LRMoo | 1.1.1 official IFLA | 5 | 5 | 5 | 5 | supported bibliographic profile |
| CRMinf | 1.2.1 stable | 5 | 5 | 4 | 5 | supported inference profile |
| CRMarchaeo | 2.1.1 stable | 5 | 5 | 3 | 5 | optional supported profile |
| CRMsci | 3.2 stable | 5 | 5 | 2 | 5 | optional supported profile |
| Getty AAT | actively maintained open vocabulary, ODC-By 1.0 | 4 | 5 | 4 | 4 | external vocabulary |
| PeriodO | active linked-data period gazetteer, public-domain dedication | 5 | 5 | 4 | 5 | external vocabulary |
| POWLA | older draft/project model | 3 | 2 | 3 | 4 | reference only |
| SAWS | v2.1 model; reusable ontology license not established from authoritative distribution inspected | 2 | 2 | 4 | 4 | reference only |
| CAO | 0.9 draft, 2019 ontology, repository last changed 2021 | 5 | 2 | 5 | 5 | reference/alignment only |

## 7. Core infrastructure vocabularies

### 7.1 SKOS

**Authoritative specification:** W3C Recommendation, *SKOS Simple Knowledge Organization System Reference*, 18 August 2009.  
**Namespace:** `http://www.w3.org/2004/02/skos/core#`.  
**Governance:** W3C Recommendation process.  
**Role in ontoTF:** concept schemes and publication mapping relations.

SKOS supplies exact/close/broad/narrow/related publication relations for genuine concept-scheme mappings. The **ontoTF mapping assessment** remains the formalism-neutral runtime/query contract and does not require every target ontology term to be represented as a SKOS concept.

ontoTF should not make every ontology class into a SKOS concept. SKOS is used for ontoTF's own concept schemes and for mappings where the external resource is appropriately treated as a concept scheme. OWL class/property relations remain OWL relations.

### 7.2 PROV-O

**Authoritative specification:** W3C Recommendation, 30 April 2013.  
**Namespace:** `http://www.w3.org/ns/prov#`.  
**Role:** mapping provenance, derivation, agent/activity attribution and generated artifact provenance.

PROV-O covers a recurrent need that should not become custom ontoTF vocabulary: which mapping artifact was generated from which corpus revision, by which activity/software/reviewer, and which prior mapping it revised.

Runtime need not perform OWL reasoning over PROV-O. The source/publication artifact can use it while the compiled sidecar stores equivalent indexed metadata.

### 7.3 Web Annotation

**Authoritative specifications:** W3C Web Annotation Data Model and Vocabulary Recommendations, 23 February 2017.  
**Namespace:** `http://www.w3.org/ns/oa#`.  
**Role:** supported **optional publication/targeting** profile for portable annotations targeting corpus entities or source spans. It is not required by every ontoTF profile or runtime mapping.

This is a better maintained publication/targeting choice than using POWLA as the generic RDF annotation layer where portable annotation exchange is actually needed. It is especially useful when a semantic assertion targets:

- a native TF node identifier;
- a byte/source span retained by a converter;
- a passage selector;
- a non-containment region that should not be confused with `oslots` extent.

ontoTF does not need to rewrite every TF feature as an OA annotation. OA is a publication/alignment mechanism for assertions that benefit from a portable target/body model.

### 7.4 SHACL

ontoTF should use **SHACL 1.0**, the W3C Recommendation, for RDF-publication validation where appropriate. The 2026 SHACL 1.2 work is still draft and should not be the POC's normative validation baseline.

SHACL belongs to the validation/tooling contract, not the semantic profile hierarchy.

## 8. Linguistic and lexical profiles

### 8.1 OLiA

**Project:** Ontologies of Linguistic Annotation.  
**Stable namespace pattern:** `http://purl.org/olia/...`.  
**Machine-readable data license:** CC BY 3.0 unless a component says otherwise; project code is separately Apache-licensed.  
**Checked source revision:** `acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6` (2026-02-04).

OLiA remains the strongest broad linguistic alignment candidate because it was designed to mediate heterogeneous annotation schemes rather than require all corpora to share one tagset. Its domain spans morphology, morphosyntax, syntactic structures and relations, semantics/discourse and other annotation categories.

ontoTF should support OLiA as a linguistic profile while keeping two layers distinct:

- the corpus's native annotation model/value;
- the OLiA reference category to which ontoTF maps it.

Because OLiA's stable PURLs are not a complete release-lock mechanism, ontoTF CI should validate against a pinned repository snapshot/content digest.

### 8.2 OntoLex-Lemon

**Published baseline:** W3C Community Group Final Report, 10 May 2016.  
**Core namespace:** `http://www.w3.org/ns/lemon/ontolex#`; published modules include SynSem, Decomp, VarTrans and LIME namespaces.  
**Governance:** W3C Ontology-Lexica Community Group.

OntoLex is suitable for lexical entries, forms, senses/concepts, decomposition and lexical relations. It is particularly relevant to BHSA lexemes, Syriac/SyrNT lexical structures, TLHdig lexical analysis and the ORACC lexical stress case.

Community Group reports are not W3C Recommendations. ontoTF documentation must say this explicitly and pin the tested final report/snapshot. Current work on OntoLex 1.1 must not silently alter the interpretation of a mapping released against the 2016 model.

### 8.3 LexInfo 3.0

**Project/repository:** `ontolex/lexinfo`.  
**Version:** 3.0.  
**Checked source revision:** `4182300b1f550cd45f4d8f586898ac267003bc3d` (2023-09-15 deployment update).  
**License:** Apache-2.0.  
**Namespace:** `http://www.lexinfo.net/ontology/3.0/lexinfo#`.

LexInfo supplies reusable linguistic categories around OntoLex, including parts of speech, morphosyntactic categories and lexical frames. It should be a supported profile alongside OLiA, not a mandatory replacement for OLiA.

Where both offer a candidate term, mapping authors should select the ontology whose definition best matches the native corpus assertion. ontoTF should not emit two "equivalent" targets merely to maximize apparent coverage.

### 8.4 OntoLex Lexicog

**Status:** W3C Community Group Final Report, 2019.  
**Namespace:** `http://www.w3.org/ns/lemon/lexicog#`.

Lexicog is useful when a corpus/profile needs dictionary-entry structure rather than only lexical entry/form/sense semantics. It is a supported optional lexical profile, not part of every corpus mapping.

### 8.5 OntoLex VarTrans

VarTrans is included in the published 2016 OntoLex family and is useful for lexical variation and translation relations. It can be supported where the source actually asserts those relations.

A bilingual gloss is not by itself a `vartrans:Translation` assertion. Corpus gloss fields stay native lexical metadata unless the source semantics support a stronger relation.

### 8.6 OntoLex Morph

The Morph module remains under active development and public review in 2026. The checked repository `ontolex/morph` had head `743d461f99b266d8db8b507db177f031aa452afa` on 2026-07-23, with public-review work in progress.

Morph is technically relevant to ontoTF's ancient-language corpora, but the POC should not make a draft module normative. ontoTF may:

- cite its model as prior art;
- experiment with alignments on non-release branches;
- promote it to a supported profile after a final CG publication and a dedicated compatibility review.

### 8.7 OntoLex FrAC

The Frequency, Attestation and Corpus Information work remains in public-review development in 2026. The checked repository `ontolex/frequency-attestation-corpus-information` had head `25f1d09786876bd4910d20914a3d62fa279b296e` on 2026-07-28.

Its attestation model is relevant to corpus lexical evidence, but ontoTF does not need a draft module to answer the initial interoperability queries. Keep it reference-only until final publication.

## 9. Heritage, text and material profiles

### 9.1 CIDOC CRM

**Normative POC release:** CIDOC CRM **7.1.3**, February 2024, listed as the last official release with ISO correspondence.  
**Namespace:** `http://www.cidoc-crm.org/cidoc-crm/`.  
**License:** CC BY 4.0 for the official documentation/model materials.  
**Governance:** CIDOC CRM Special Interest Group under ICOM/CIDOC, with ISO correspondence.

The newer 7.4 release dated August 2026 is explicitly a **Draft**. ontoTF should not replace 7.1.3 with it merely because 7.4 is newer.

CIDOC CRM supplies durable concepts for physical objects, identifiers, production, actors, places, times and information objects. It is the general heritage base for CUC/TLHdig/ORACC physical and catalogue metadata.

### 9.2 CRMtex

**Version:** 2.0, June 2023, stable.  
**Namespace:** `http://www.cidoc-crm.org/extensions/crmtex/`.  
**Governance:** CIDOC CRM extension process.

CRMtex is directly relevant to written/inscribed textual entities and is the preferred supported text/epigraphy extension for sign/tablet corpora where its definitions fit.

It does not replace the TF token/sign graph. A `sign` slot is mapped to a CRMtex concept only when the corpus-native entity satisfies that concept's definition.

### 9.3 LRMoo

**Version:** 1.1.1, approved official IFLA release in 2025.  
**Namespace:** `http://iflastandards.info/ns/lrm/lrmoo/`.  
**License:** CC BY 4.0.  
**Governance:** joint IFLA LRMoo Working Group and CIDOC CRM SIG.

LRMoo is preferred over old FRBRoo for new ontoTF mappings. It is useful for works, expressions, manifestations/items and bibliographic relationships around corpora, witnesses and editions.

ontoTF may align legacy models that use FRBRoo, but should not introduce a new normative dependency on superseded FRBRoo solely because CAO or SAWS used it.

### 9.4 CRMinf

**Version:** 1.2.1, April 2026, stable.  
**Role:** argumentation/inference and belief/evidence modelling.

CRMinf is useful for claims that an analyst inferred a semantic identification from evidence. It should be a supported optional profile rather than a requirement for simple deterministic mappings.

A mapping-confidence field in ontoTF does not automatically become a CRMinf inference graph. Use CRMinf where the project actually wants to publish the argument/evidence structure.

### 9.5 CRMarchaeo

**Version:** 2.1.1, April 2024, stable.  
**Namespace:** `http://www.cidoc-crm.org/extensions/crmarchaeo/`.

CRMarchaeo is appropriate when a corpus carries excavation/stratigraphic observations. Current ORACC/TLHdig stress cases chiefly need object, material, provenance and text modelling, so CRMarchaeo should be optional rather than imported for every cuneiform profile.

### 9.6 CRMsci

**Version:** 3.2, April 2026, stable.

CRMsci is useful for scientific observation/measurement workflows. It is retained as an optional supported profile for future material-analysis or measurement modules, but R-005 does not justify making it part of the core corpus ontology stack.

## 10. External controlled vocabularies

### 10.1 Getty AAT

The Getty Art & Architecture Thesaurus is actively maintained. Getty's downloadable linked-open-data vocabularies are licensed under **Open Data Commons Attribution 1.0 (ODC-By)**. AAT concept URIs use the Getty vocabulary infrastructure, e.g. `http://vocab.getty.edu/aat/...`.

AAT offers strong coverage for:

- materials;
- object/work types;
- techniques;
- roles;
- cultures and other heritage terminology.

ontoTF should link to selected AAT terms but avoid vendoring the whole vocabulary as a runtime dependency. The ontology lock should record the URI and snapshot/date used for validation; attribution requirements must be retained in redistributed subsets or generated documentation.

### 10.2 PeriodO

PeriodO provides stable identifiers for scholarly period definitions and linked-data exports, including ARK-based permalinks. Its dataset is dedicated to the public domain.

PeriodO is a good target for corpus period metadata when the source period label corresponds to a specific published PeriodO definition. The mapping must preserve the corpus label and source provenance because period definitions are scholarly claims with spatial/source context, not universal date buckets.

## 11. Reference/prior-art models

### 11.1 POWLA

POWLA demonstrated how linguistic annotation graphs could be represented in RDF/OWL and remains relevant background for standoff linguistic annotation. Its public project history is old/draft compared with the selected alternatives.

ontoTF already has TF/Context-Fabric as its native graph model, Web Annotation for portable targeting, and OLiA for annotation semantics. Making POWLA normative would add another structural abstraction without solving an uncovered POC requirement.

Decision: reference only.

### 11.2 SAWS

SAWS models relationships among ancient wisdom texts and witnesses and remains valuable prior art for intertextual/textual relationships. The authoritative ontology distribution inspected for R-002 establishes the model/version/PURL but does **not establish a reusable ontology license**. ontoTF therefore records the license as unknown/not established rather than inferring either permissive or non-commercial terms.

Its historical dependence on FRBRoo and the unresolved reuse rights are reasons not to adopt it as a normative POC dependency now that LRMoo is available.

Decision: reference/alignment only unless authoritative licensing and current-model evidence are later established and pinned.

### 11.3 Critical Apparatus Ontology (CAO)

The CAO ontology explicitly declares:

- base IRI `https://w3id.org/cao/`;
- version `0.9`;
- ontology date `08.07.2019`;
- CC BY 3.0 license;
- imports including Web Annotation and HiCO;
- concepts such as `VariationUnit`, `Reading` and `BaseReading`.

The checked repository `fgiovannetti/cao` is at `7a96094092123d5f53358cd3311c583495d9cd8e` (2021-01-07), while the ontology remains labelled 0.9/draft and incorporates legacy FRBRoo modelling.

CAO is one of the closest conceptual precedents for Pseudepigrapha-TF's apparatus, but its maturity/maintenance make it a poor normative dependency for a new POC.

Decision: use CAO as explicit prior art and publish alignments where justified. Keep apparatus domain concepts native/profile-local in the foundation POC until a second independent corpus establishes the same semantic gap or the design proves a term is required for ontoTF mapping infrastructure itself.

## 12. Minimal ontoTF vocabulary

ontoTF should not create a broad competing ontology. The initial local vocabulary should be restricted to gaps established by at least two corpus/stress cases or necessary to express the mapping contract itself.

### 12.1 Text-critical concepts

Do **not mint** ontoTF-local apparatus domain terms in the foundation POC. R-005 establishes full variation-unit/reading/witness-attestation/explicit-absence semantics in Pseudepigrapha-TF only; Peshitta witness designations and TLHdig fragment links do not constitute a second independent corpus with the same apparatus relation. Preserve the Pseudepigrapha-TF concepts natively/profile-locally and document the external ontology gap.

A later governance/design change may mint an apparatus term only after a **second independent corpus** requires the same semantic gap, or after the term is shown to be necessary for ontoTF's mapping-contract infrastructure rather than one corpus domain. `Witness` should likewise map to an established bibliographic/heritage entity when the native semantics justify it rather than being universalized from a shared label.

### 12.2 What should not enter the ontoTF vocabulary

Do not mint local replacements for:

- generic provenance — use PROV-O;
- mapping strength — use the ontoTF mapping-assessment contract; publish SKOS/OWL/RDFS relations only where the target formalism justifies them;
- annotation targets/selectors — use Web Annotation where publication needs them;
- lexical entry/form/sense — use OntoLex where applicable;
- generic museum/material entities — use CIDOC CRM/AAT where applicable;
- generic linguistic categories already covered by OLiA/LexInfo;
- source-specific values such as BHSA `qal` or SyrNT `peal` unless a recurring interoperability requirement emerges.

### 12.3 Technical anchors

R-005 found TF nodes whose `oslots` are technical anchors rather than semantic extents. This distinction belongs to the **mapping/runtime metadata contract**, not the domain ontology. The profile should be able to declare an extent interpretation such as `semantic`, `anchor-only`, `source-span`, or `sidecar-zero-span`, but those labels should not be presented as universal humanities ontology classes.

## 13. Coverage against target corpora

### 13.1 BHSA

Primary useful profiles:

- OLiA/LexInfo for POS, gender, number, person and selected morphological categories;
- OntoLex for `lex` entities and lexical identity;
- SKOS for ontoTF/local concept schemes and publication mappings only when both resources are genuine SKOS concepts;
- PROV-O for mapping provenance.

Approximate cross-ontology projection remains a **ontoTF mapping assessment** unless the target formalism independently justifies a publication relation; merely being approximate does not make the mapping a SKOS mapping.

Native BHSA syntax (`mother`, `functional_parent`, `distributional_parent`) must remain distinct predicates. OLiA can provide semantic categories where definitions match, but the edges are not automatically replaced by generic `dependsOn`/`parent` relations.

### 13.2 ETCBC ExtraBiblical

The structural similarity to older ETCBC/BHSA layers permits reuse of many reviewed mappings, but absence of BHSA's exact lexical-node design means compatibility must still be validated per corpus.

Use OLiA/LexInfo/OntoLex selectively; do not inherit the entire BHSA profile by repository family alone.

### 13.3 ETCBC Syriac, Peshitta and SyrNT

- ETCBC Syriac 0.9: OLiA/LexInfo for morphology; OntoLex for lexical projections where the native structure supports them.
- SyrNT: OntoLex is especially useful because the corpus has explicit lexeme nodes and SEDRA-derived lexical structure.
- Peshitta 0.2: the A/B `witness` string is not a critical-reading attestation graph. Map only the semantics actually documented.

Hebrew and Syriac stem systems remain language-specific concepts with optional broad/related alignments.

### 13.4 CUC

CUC needs:

- CRM/CRMtex for tablet/physical textual entities where definitions fit;
- Web Annotation for portable targeting of sign-level editorial assertions if exported;
- SKOS/local concepts for editorial state inventories that lack exact maintained targets;
- AAT as an external vocabulary for material/object terminology if such metadata is mapped.

`emen`, `cert` and `alt` stay separate assertions. ontoTF must not collapse all three to one generic uncertainty concept.

### 13.5 TLHdig-TF

Useful profiles include:

- CIDOC CRM + CRMtex for documents, surfaces, fragments and textual/material entities;
- OntoLex for lexical analyses/lexeme relations;
- PROV-O for source/repair/build provenance;
- Web Annotation for source-span/editorial targeting;
- LRMoo where edition/witness bibliographic semantics fit;
- AAT for controlled material/object terms where exact matches exist.

The line → fragment `witness` edge is not equivalent to Pseudepigrapha reading → manuscript attestation. `cluster` damage ranges and boundary edges need their native representation preserved.

### 13.6 Pseudepigrapha-TF

This is the strongest apparatus stress case, but R-005 did not establish recurrence in a second independent corpus, so apparatus domain concepts remain native/profile-local in the foundation POC.

Use:

- LRMoo/CIDOC CRM/CRMtex for bibliographic, witness and textual entities where definitions fit;
- PROV-O for source/conversion/editorial provenance;
- Web Annotation for target/locus publication;
- native/profile-local apparatus concepts for variation units, readings, attestation and explicit absence;
- CAO/SAWS only as documented alignments/prior art.

The existence of an external `Reading` class is not enough to import CAO wholesale when its remaining model/release constraints are unsuitable.

### 13.7 ORACC-TF

ORACC stresses several domains simultaneously:

- OntoLex + LexInfo for lexical entries/forms/analyses where source semantics support them;
- CIDOC CRM/CRMtex for inscribed objects, documents and physical/textual hierarchy;
- AAT for material/object-type terminology;
- PeriodO for scholarly period labels with a defensible source-period match;
- CRMarchaeo only where excavation/stratigraphic facts actually appear;
- PROV-O for corpus/source/catalogue derivation.

An ORACC `c type=sentence` implicit chunk does not become an OLiA/BHSA sentence because an ontology contains a class named Sentence.

Zero-span source entities remain representable in the ontoTF sidecar without inventing TF slots merely to satisfy ontology structure.

## 14. Profile composition rules

A corpus profile declares only the ontology families it uses. There is no mandatory import closure such as "all corpora import CIDOC + OLiA + OntoLex".

Example conceptual manifest fragment:

```yaml
profiles:
  linguistic:
    - {id: olia, lock: olia-2026-02-04}
    - {id: lexinfo, lock: lexinfo-3.0-4182300}
  lexical:
    - {id: ontolex, lock: ontolex-2016-final}
  heritage:
    - {id: cidoc-crm, lock: cidoc-crm-7.1.3}
    - {id: crmtex, lock: crmtex-2.0}
external_vocabularies:
  - {id: aat, snapshot: 2026-06}
```

The exact syntax is deferred to the design phase.

### 14.1 Imports versus links

Prefer **linking** over `owl:imports` unless import closure is genuinely required for validation/reasoning.

Reasons:

- remote imports weaken offline reproducibility;
- an upstream import can change transitively;
- importing a large ontology does not improve a mapping that uses only three terms;
- some external vocabularies are datasets rather than ontologies intended for import.

Build tooling should resolve all selected terms against locally pinned snapshots and may produce a self-contained validation bundle.

## 15. Failure behavior

A mapping/profile must fail validation when:

- a supported ontology term is missing from its pinned snapshot;
- the mapping uses a draft ontology while declaring it supported/stable;
- an ontology lock differs from the tested content digest;
- an unsupported license is promoted to normative dependency;
- a deprecated term is silently replaced without a mapping version change;
- an OWL equivalence assertion lacks explicit reviewed justification;
- a generated RDF publication cannot resolve its declared prefixes/terms from the lock;
- a profile requires an external vocabulary snapshot that is not available offline for CI.

Runtime may still expose the native corpus when a semantic profile cannot load. It must report the semantic profile as unavailable/stale rather than silently falling back to guessed mappings.

## 16. Rejected alternatives

### One universal imported ontology

Rejected. R-005 demonstrates linguistic, lexical, physical, apparatus and editorial structures whose useful external models come from different ontology families. One import closure would increase coupling without creating semantic identity.

### OLiA alone

Rejected as a complete stack. OLiA is strong for linguistic annotation but does not replace lexical, bibliographic, material, provenance or apparatus modelling.

### CIDOC CRM alone

Rejected as a complete stack. CRM is a strong heritage backbone but is too general to replace OLiA/LexInfo/OntoLex for grammatical and lexical semantics.

### OntoLex as the universal corpus ontology

Rejected. OntoLex models lexica well; it does not define the full syntax, physical-object, witness or editorial apparatus semantics needed by the target corpora.

### POWLA as runtime RDF graph model

Rejected. ontoTF already has native TF/Context-Fabric graphs, and R-001 recommends a compiled semantic sidecar. Web Annotation and the selected domain ontologies cover the publication needs with stronger current governance.

### SAWS or CAO as the normative apparatus ontology

Rejected for the POC. SAWS reusable ontology licensing was not established from the authoritative distribution inspected, and its model is tied to older FRBRoo. CAO is open and semantically close to the problem, but remains a 0.9/draft model with limited recent maintenance and legacy dependencies. Both remain explicit prior art.

### Draft OntoLex Morph/FrAC as supported dependencies

Rejected until final publication. Active maintenance is positive evidence, but draft public-review status means their semantics can still change.

### Always follow the latest ontology release

Rejected. It destroys reproducibility and can silently change mappings. ontoTF binds to a tested ontology lock and upgrades deliberately.

## 17. Unresolved design questions

The later design work must still decide:

1. exact ontology-lock file syntax and digest canonicalization;
2. whether supported ontology snapshots are vendored, release-attached, or fetched into a verified cache;
3. canonical ontoTF namespace/URI shape for the minimal local vocabulary;
4. whether local concepts are authored directly as SKOS, OWL, or a simpler declarative source compiled to both;
5. the exact machine-readable field for reviewed mapping justification/confidence;
6. whether Web Annotation selectors target stable corpus node URIs, source spans, or both in the first POC;
7. which SHACL shapes are normative for published RDF versus internal sidecar validation;
8. criteria and migration procedure for promoting OntoLex Morph or FrAC after final publication.

These questions refine implementation. They do not reopen the support-tier, openness, version-lock or exact/approximate mapping decisions in this report.

## 18. Acceptance-criteria trace

- **Current status/version/governance/license checked:** all proposed supported candidates and all required candidates are classified above; draft/stale/licensing-uncertain cases are explicitly downgraded.
- **Support policy:** four tiers — core, supported, external, reference — with optional domain profiles.
- **Exact versus approximate mappings:** runtime mapping assessment is formalism-neutral and directionally defined from native/source to target; all eight assessment values are defined independently of publication predicates; SKOS exact/close/broad/narrow/related publication relations are used only for genuine SKOS concepts/concept schemes, while OWL/RDFS relations require their own logical justification.
- **Local concepts:** native-only first; corpus-local for source-specific categories; ontoTF-local only for recurrent interoperability gaps.
- **Version/deprecation:** stable URI plus tested release/snapshot/content digest; no silent migration.
- **Runtime versus publication:** runtime uses the compiled sidecar from accepted R-001; RDF vocabularies are validated source/publication semantics and need not imply a triplestore.
- **Corpus coverage:** BHSA, CUC, all three Syriac profiles, ExtraBiblical, TLHdig-TF, Pseudepigrapha-TF and ORACC-TF are exercised explicitly.
- **Domain coverage:** linguistic, lexical-semantic, textological/codicological, physical/material and archaeological/scientific optional domains are covered.
- **Apparatus gap:** recurrence is not yet established across a second independent corpus, so apparatus domain terms remain native/profile-local; mapping strength/provenance/targeting use existing standards/contracts.

## 19. Authoritative sources and inspected snapshots

Primary sources used for the decision include:

- SKOS Reference: `https://www.w3.org/TR/skos-reference/`
- PROV-O: `https://www.w3.org/TR/prov-o/`
- Web Annotation Vocabulary: `https://www.w3.org/TR/annotation-vocab/`
- SHACL: `https://www.w3.org/TR/shacl/`
- OLiA project: `https://acoli-repo.github.io/olia/`; checked `acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6`
- OntoLex-Lemon 2016 Final Report: `https://www.w3.org/2016/05/ontolex/`
- OntoLex Lexicog: `https://www.w3.org/2019/09/lexicog/`
- LexInfo: `https://github.com/ontolex/lexinfo`; checked `4182300b1f550cd45f4d8f586898ac267003bc3d`
- OntoLex Morph: `https://github.com/ontolex/morph`; checked `743d461f99b266d8db8b507db177f031aa452afa`
- OntoLex FrAC: `https://github.com/ontolex/frequency-attestation-corpus-information`; checked `25f1d09786876bd4910d20914a3d62fa279b296e`
- CIDOC CRM versions: `https://cidoc-crm.org/versions-of-the-cidoc-crm`
- CRMtex versions: `https://cidoc-crm.org/crmtex/versions`
- CRMinf versions: `https://cidoc-crm.org/crminf/versions`
- CRMarchaeo versions: `https://cidoc-crm.org/crmarchaeo/versions`
- CRMsci versions: `https://cidoc-crm.org/crmsci/versions`
- LRMoo: `https://cidoc-crm.org/lrmoo/`
- Getty vocabulary downloads/licensing: `https://www.getty.edu/research/tools/vocabularies/obtain/download.html`
- PeriodO: `https://perio.do/`
- SAWS ontology: `http://purl.org/saws/ontology`
- Critical Apparatus Ontology: `https://github.com/fgiovannetti/cao`; checked repo head `7a96094092123d5f53358cd3311c583495d9cd8e`, ontology IRI `https://w3id.org/cao/`, version 0.9.

R-005 / PR #7 was accepted at exact reviewed head `48c8bd78d0c3a0501b2fdec6946db5df90517bdb` and merged as `a9c4d74d4de2f9a15eb1464dce341ecd2f92f898`. This report has been reconciled against that empirical dependency; any future material census revision requires a new R-002 reconciliation.

R-001 / PR #8 was accepted at exact reviewed head `68b88a820f5519ad65d46b732679a6278e9ca3c9` and merged as `a22a95084a1518882d1e3e87d10e9757121f106d`. This report is reconciled against its component-aware distribution/version-binding contract; any future material R-001 change requires a new R-002 reconciliation.
