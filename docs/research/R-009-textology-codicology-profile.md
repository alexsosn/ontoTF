# R-009: textology, codicology, and critical-apparatus semantic profile

**Status:** research complete; pending fresh logically-independent review  
**Issue:** #41  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-002/R-003/R-005, merged R-006/R-007/R-008, merged R-012 #54, and merged roadmap guardrail #45

## Decision

ontoTF should represent textological and codicological semantics as a **layered composition**, not as one manuscript ontology and not as one universal `Witness` type.

The first profile has five distinct layers:

1. **physical carrier / codicology** — CIDOC CRM for physical objects, parts, identifiers, production, materials, places, custody and provenance; CRMtex for physical writing and written-text segments actually borne by those carriers;
2. **intellectual/textual realization** — LRMoo for works, expressions, manifestations/items where justified, expression derivation, and symbolic/textual fragments;
3. **witness / apparatus assertions** — native variation-locus, reading, explicit omission, witness-attestation and unattested states preserved as reviewed profile-local semantic roles when no supported common target is defensible;
4. **scholarly/editorial epistemic layer** — CRMinf for attributed propositions, beliefs, inference/provenance assessment and meaning-comprehension activity only when the source actually records such claims or processes;
5. **publication / targeting** — Web Annotation as optional publication/targeting infrastructure, never as the canonical runtime representation of TF slot sets or apparatus graphs.

The governing invariant is:

> **Physical carrier, physical writing, intellectual text, textual witness, apparatus reading, source assertion, and scholarly inference are separate semantic objects/roles. A source may connect them, but ontoTF must not collapse them because one corpus node or label happens to serve several purposes.**

The evidence still does **not** justify minting a normative ontoTF critical-apparatus ontology. Pseudepigrapha-TF provides a robust full reading/witness graph; the other inspected corpora expose related witness, fragment, damage, qere, edition, or editorial assertions, but not a second independent full reading-at-locus apparatus model. That preserves R-002's rule that ontoTF-local ontology terms should be introduced only for recurring cross-corpus gaps.

Canonical IR still must preserve profile-local apparatus **roles and assertion shapes** so native execution and cross-corpus comparison remain possible without inventing a common target. R-013 owns the final controlled role vocabulary. R-011 must measure whether these gaps recur strongly enough to justify a small later vocabulary or whether an external apparatus ontology becomes acceptable after governance/version review.

## 1. Layer model

```text
PHYSICAL / CODICOLOGICAL
  CIDOC CRM physical object / part / material / identifier / place / event
             │
             ├── bears reviewed physical writing
             ▼
WRITTEN TEXT ON THE CARRIER
  CRMtex TX1 Written Text
      └── TX7 Written Text Segment
            ├── line / column / written segment where justified
            └── glyph / grapheme only where native semantics support the distinction

INTELLECTUAL / TEXTUAL
  LRMoo F1 Work
      └── F2 Expression / derivation / symbolic fragment relations
             │
             └── embodied/preserved by carriers only when source semantics justify it

WITNESS / APPARATUS
  native/profile-local variation locus
      ├── reading A ── attested by ── textual witness X
      ├── reading B ── attested by ── textual witness Y
      └── explicit omission ── attested by ── witness Z

  unattested = derived state relative to a closed native witness/locus inventory,
               not a fabricated omission or source assertion

EPISTEMIC / EDITORIAL
  CRMinf proposition / belief / inference / provenance assessment
      └── only when the source records an attributed scholarly assertion or process
```

This is not an RDF import graph. Each projection activates only when native corpus semantics support that layer.

## 2. Standards and prior art

### 2.1 CIDOC CRM

CIDOC CRM remains the physical heritage backbone selected by R-002. It is the default layer for:

- a manuscript, tablet, codex, fragment, sherd, or other physical human-made object when the source denotes a physical carrier;
- physical part-whole relations;
- identifiers and inventory/catalogue identity;
- production, modification, ownership/custody and provenance events;
- material/support facts;
- actors, places and times connected to those events.

A physical object does not become an intellectual/bibliographic object merely because it carries text. A physical fragment is ordinarily a CRM physical object or physical part. It is **not automatically** an LRMoo textual fragment.

### 2.2 CRMtex 2.0

Primary sources:

- <https://cidoc-crm.org/crmtex/ModelVersion/version-2.0>
- <https://cidoc-crm.org/extensions/crmtex/html/CRMtex_v2.0.html>

CRMtex is the selected layer for physical writing itself:

- `TX1 Written Text` — visible/tactile writing on a physical support;
- `TX7 Written Text Segment` — a significant portion of written text, including column/line/word/sign-like segmentations where source semantics fit;
- `TXP4 has segment` — written-text segmentation;
- `TX8 Grapheme` / `TX9 Glyph` — abstract/concrete written-sign distinctions only where native semantics support them;
- recognition and reading activities only when the corpus records the relevant activity semantics.

R-007 controls the structural boundary: a TF `line`, `column`, `sign`, slot set, or `oslots` relation does not become a CRMtex segment/glyph relation from storage shape alone.

R-012 controls the version boundary: CRMtex 2.0 keeps its declared dependency closure. The current first pilots do not require `TX2 Writing` or `TX14 Reading` merely to model textual structure. Pseudepigrapha's apparatus node called `reading` is not CRMtex `TX14 Reading`.

### 2.3 LRMoo 1.1.1

Primary sources:

- <https://cidoc-crm.org/lrmoo/ModelVersion/version-1.1.1>
- <https://cidoc-crm.org/extensions/lrmoo/html/LRMoo_v1.1.1.html>
- <https://cidoc-crm.org/sites/default/files/LRMoo_V1.1.1.pdf>

LRMoo supplies the intellectual/textual layer:

- `F1 Work` for identifiable intellectual creation at work level;
- `F2 Expression` for a particular realization of a work;
- derivation/revision/translation relations where the source states them;
- `F5 Item` where a physical object is genuinely an item/holding in the bibliographic sense, not merely any ancient object;
- `R15 has fragment` for **symbolic/expression fragments**, not automatically physical manuscript pieces.

`R15 has fragment` relates an `F2 Expression` to an `E90 Symbolic Object` fragment. A TLHdig physical fragment may carry a textual fragment, but those are distinct entities unless the source/converter explicitly identifies both layers.

### 2.4 CRMinf 1.2.1

Primary sources:

- <https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html>
- <https://cidoc-crm.org/sites/default/files/CRMinf_v1.2.1%28stable%29.pdf>

Relevant current classes include `I1 Argumentation`, `I2 Belief`, `I4 Proposition Set`, `I5 Inference Making`, `I10 Provenance Statement`, `I14 Provenance Belief`, `I15 Provenance Assessment`, and `I16 Meaning Comprehension`.

CRMinf is not a generic wrapper for every corpus fact. A flat catalogue statement such as `provenience = Nineveh` remains a provenance-bearing native/source assertion unless the dataset separately models a scholar's assessed belief or inference. CRMinf is appropriate when the source records who asserted, inferred, assessed, reconstructed, or adopted a proposition and with what evidence/provenance.

R-012's TX14/I16 conclusion remains in force: current CRMinf treats CRMtex reading/deciphering and I16 meaning comprehension as distinct composable activities, not a broader/narrower class substitution.

### 2.5 SAWS

The Sharing Ancient Wisdoms ontology is valuable prior art for ancient-text transmission. Its current documented ontology is version 2.1 at permanent URI:

<http://purl.org/saws/ontology>

It reuses and extends FRBRoo through the Erlangen OWL implementation and models relationships among manuscripts, textual units and transmitted/reused content.

It should remain reference/prior art rather than a new normative ontoTF dependency because:

- its architecture is tied to the older FRBRoo/Erlangen family rather than current LRMoo 1.1.1;
- the original SAWS project states that its work is under a Creative Commons Attribution-NonCommercial-ShareAlike licence, which conflicts with R-002's requirement for commercial-use-compatible normative dependencies;
- its project/version context is historical rather than a current ontoTF interoperability target.

A later separately licensed redistribution of SAWS data does not silently relicense or modernize the 2.1 ontology model for ontoTF's normative dependency purposes.

Decision: **reference/prior art only**, consistent with R-002.

### 2.6 Critical Apparatus Ontology (CAO) 0.9

The Critical Apparatus Ontology declares:

- IRI: <https://w3id.org/cao>
- version: 0.9
- release date: 2019-07-08

Its published documentation remains an ontology specification draft and imports older FRBR and ontology-design-pattern components plus Web Annotation. The ontology documentation does not expose a clear licence value sufficient to promote the artifact to a normative redistributable ontoTF snapshot under R-002 governance.

Decision: **reference/prior art only**.

CAO must not be confused with SPAR C4O; `http://purl.org/spar/c4o/` is a different ontology and is not the Critical Apparatus Ontology.

### 2.7 Critical Edition Ontology (CEO) 1.0

Critical Edition Ontology (CEO) 1.0 was published in 2023 and described in 2024 literature. Its ontology IRI is:

<http://purl.org/critical-edition-ontology>

CEO explicitly models:

- apparatus / critical apparatus;
- apparatus entry / critical apparatus entry;
- reading / reading in apparatus;
- gap;
- witness;
- witness carrier;
- siglum / siglum reference;
- textual tradition;
- critical intervention and critical text/passage;
- Web Annotation-based targeting/selectors.

Its separation between textual `Witness` and physical `WitnessCarrier` is useful prior art for ontoTF. The generated documentation defines `Witness` as an `F2 Expression`, `WitnessCarrier` as an `F3 Manifestation`, and `preserves` as a specialization of the model's `R4 embodies`. Its apparatus reading/siglum-reference model is much closer to Pseudepigrapha-TF than generic CRM/LRMoo alone.

CEO is nevertheless **not promoted to a supported profile in R-009**:

1. R-002 did not review/accept it as a normative dependency;
2. its generated ontology embeds/redeclares an older F1/F2/F3/R3/R4/R15/R76 family rather than simply depending on the accepted current LRMoo 1.1.1 contract, so local names cannot be assumed semantically/version compatible;
3. the 2024 article is CC BY 4.0, but R-009 did not establish a sufficiently explicit licence for redistribution of the ontology artifact itself as a pinned normative ontoTF dependency;
4. adopting it therefore requires explicit governance, licensing, and current-LRMoo bridge research.

Decision: **strongest current apparatus prior art / candidate future alignment profile**, reference-only for the first P-003 design.

### 2.8 MeMO and MMDIO manuscript/codicology prior art

The Medieval Manuscript Ontology (MeMO) declares:

- IRI: <https://w3id.org/irnerio/ontology/memo>
- version IRI: <https://w3id.org/irnerio/ontology/memo/2020-03-06>
- CC BY 4.0 licensing.

It models codex, folio, recto/verso, binding, physical medium, manuscript, text, gloss, columns and related manuscript metadata. It is useful codicological prior art, but is built around FRBR/FaBiO modeling rather than the current LRMoo basis.

A newer related model, the **Medieval Manuscript Data Integration Ontology (MMDIO)**, version 1.1.0 (2024), declares IRI:

<https://w3id.org/irnerio-mosaico/ontology/mmdio/>

and is also CC BY 4.0. MMDIO extends the MeMO/FaBiO approach for heterogeneous manuscript data integration. Its existence makes the manuscript-vocabulary survey current, but it does not change the first-profile decision: the ontoTF pilot corpora do not yet show recurring quire/folio/hand/binding semantics that require adding a second normative manuscript ontology, and the FRBR/FaBiO modeling boundary would still need reconciliation with current LRMoo.

The Mapping Manuscript Migrations project likewise demonstrates that CRM + FRBR-family models can support large manuscript provenance graphs while source-specific vocabulary fills local gaps.

Decision: **MeMO/MMDIO/MMM are prior art; open a normative codicology-profile research gate only when actual corpus recurrence demonstrates a gap that CRM/CRMtex/LRMoo cannot cover cleanly.**

## 3. Responsibility matrix

| semantic question | primary ontoTF layer | unsafe shortcut |
|---|---|---|
| What physical object is this? | CIDOC CRM | `manuscript` label ⇒ LRMoo Expression |
| What physical part is this fragment/folio/surface? | CIDOC CRM physical object/part | physical fragment ⇒ LRMoo R15 fragment |
| What writing exists on the carrier? | CRMtex TX1/TX7 where warranted | TF slot/line ⇒ CRMtex segment automatically |
| What intellectual work is represented? | LRMoo F1 | physical object identity ⇒ Work |
| What textual realization/version is represented? | LRMoo F2 where warranted | every `version` string ⇒ F2 |
| What is a symbolic fragment of an expression? | LRMoo R15 where source defines it | physical sherd/manuscript piece ⇒ R15 |
| Which witness attests which reading at which locus? | native/profile-local apparatus assertion; future reviewed target | generic witness metadata ⇒ reading attestation |
| Is this an explicit omission? | explicit native reading/absence assertion | no edge/value ⇒ omission |
| Is this witness unattested at a locus? | derived closed-world state with provenance | unattested ⇒ explicit omission |
| Is this a scholarly reconstruction/interpretation? | CRMinf when source records claim/inference | editorial display state ⇒ inference |
| Where/how is an annotation published? | optional Web Annotation | selector ⇒ canonical TF extent |

## 4. Witness identity contract

`Witness` is too overloaded for one automatic mapping. ontoTF must distinguish at least:

1. **physical witness carrier** — manuscript, tablet, fragment, printed item, or other physical object;
2. **textual witness identity** — a textual realization/tradition-level witness that may be preserved by one or more carriers;
3. **witness attestation assertion** — the native/source assertion that a witness supports a particular reading at a particular locus;
4. **witness metadata label** — a feature saying an object/book belongs to witness A/B without asserting reading-at-locus semantics.

R-013 owns final controlled role names. R-009 requires only that canonical mapping/IR preserve the distinction.

One native node may legitimately support several reviewed roles. ontoTF should preserve one native identity plus complementary roles/projections rather than duplicate or silently retype the source entity.

## 5. Apparatus gap analysis

### 5.1 What the seven-model core covers

The accepted stack already covers most surrounding semantics:

- physical carrier/item/material/provenance → CIDOC CRM / LRMoo where appropriate;
- physical writing and segments → CRMtex;
- work/expression/derivation → LRMoo;
- attributed inference/reconstruction → CRMinf;
- publication targets → Web Annotation optionally.

### 5.2 Residual apparatus assertion shape

The seven-model core does not directly provide the whole execution contract:

```text
variation locus
  -> one or more readings
  -> each reading attested by zero or more identified textual witnesses
  -> explicit omission represented as positive source evidence
  -> non-attestation distinct from explicit omission
  -> orphan/malformed readings preserved without fabricating a locus
```

CEO provides strong prior art for many of these concepts, but it is not yet an accepted supported dependency.

### 5.3 Should ontoTF mint a local apparatus ontology now?

**No.** The R-002 recurrence threshold is still not met.

Pseudepigrapha-TF supplies a robust full apparatus graph. Peshitta A/B metadata, TLHdig line/fragment witness relations, BHSA qere information, and ORACC edition structures concern related witness/text phenomena but do not independently instantiate the same complete reading-at-locus assertion model.

R-009 therefore requires:

- exact preservation of the Pseudepigrapha apparatus graph in native/profile-local IR;
- controlled semantic roles/assertion shapes sufficient for agents and R-011 measurements;
- profile-local roles must not enter the common semantic→native index as though they had an accepted ontology target;
- CEO/CAO/SAWS may guide mapping research/documentation only;
- R-011 must test whether another independent corpus demonstrates the same gap strongly enough to justify a tiny ontoTF vocabulary;
- if CEO later passes licensing/governance/current-LRMoo review, prefer reuse/alignment over inventing overlapping local ontology terms.

This is a deliberate `native-only`/profile-local result, not a failure of the mapping framework.

## 6. Pseudepigrapha-TF mapping pattern

### 6.1 Native graph

Current Pseudepigrapha-TF exposes:

- textual version / stable TF version ID;
- `unit` — apparatus locus;
- `reading` — ordinary reading at a unit;
- `orphan_reading` — preserved malformed/source-anomaly reading without fabricated unit;
- `variant_word` — token inside a non-primary reading;
- `manuscript` — source witness identity;
- `resource` and metadata-only version identities.

Relevant edges:

- `reading_of`: reading → unit;
- `witness`: reading/orphan reading → manuscript;
- `variant_word_of`: variant word → reading;
- `manuscript_of`: manuscript → exact textual-version owner;
- `resource_of`: resource → exact version owner.

### 6.2 Explicit omission vs unattested

The apparatus API distinguishes:

- `reading` — witness explicitly assigned to a non-empty reading;
- `omission` — witness explicitly assigned to an empty source reading;
- `unattested` — no reading at that unit cites the witness.

An explicit empty reading is **positive source evidence** for omission. Absence of an edge is not.

`unattested` is a derived state valid only relative to the known version, witness inventory, and locus. It must retain that closure/provenance context and must never be serialized as if the source asserted omission or lacuna.

### 6.3 Manuscript node semantics

The native `manuscript` node is a textual witness identity in the converter contract. Some records may correspond to physical manuscript carriers, but ontoTF must not map every such node directly to a CRM physical object or LRMoo F5 Item unless the source identity denotes that carrier.

A future mapping may separate:

```text
native textual witness identity
  -> textual witness / LRMoo expression candidate when justified

separate physical carrier identity
  -> CIDOC CRM physical object / LRMoo F5 Item when justified

carrier preserves/embodies witness
  -> reviewed relation
```

CEO's `Witness` vs `WitnessCarrier` distinction is useful prior art for this decomposition without being a normative target yet.

### 6.4 Versions and passages

Pseudepigrapha-TF preserves multiple textual versions under a work and reports `available`, `not_present`, and `metadata_only`. A normalized chapter/verse address is applied independently per version and is **not** evidence of exact cross-version alignment.

Therefore:

- version identity is a candidate textual-realization/LRMoo F2 projection only after source-level review;
- metadata-only versions remain valid identities, not fake empty text;
- source references remain authoritative for exact loci;
- common section labels do not manufacture alignment.

### 6.5 First-profile apparatus projection

| native assertion | ontoTF treatment |
|---|---|
| `unit` | profile-local variation-locus role; `native-only` common-target state |
| `reading` | profile-local reading role; `native-only` common-target state |
| `reading_of` | profile-local reading-at-locus relation |
| `witness` edge | profile-local reading-attestation relation |
| empty reading + cited witnesses | explicit-omission source assertion |
| no reading cites witness at locus | derived unattested state, not source assertion |
| `orphan_reading` | preserve reading; locus unsupported/unknown rather than invented |
| manuscript metadata | textual-witness metadata; carrier projection only with independent evidence |

R-011 may execute corpus-specific apparatus queries through these native/profile-local roles, while reporting that no common semantic pivot target exists yet.

## 7. TLHdig-TF mapping pattern

TLHdig-TF stresses physical/documentary and editorial semantics rather than a full apparatus graph.

### 7.1 Physical/document hierarchy

The current model includes `document`, `surface`, `column`, `line`, `fragment`, sign-level text, and witness/join relations where source evidence provides them.

| native object | candidate layer | guardrail |
|---|---|---|
| document/tablet/manuscript physical object | CIDOC CRM physical object | only if native identity denotes carrier |
| physical fragment | CIDOC CRM physical object/part | not LRMoo R15 by label |
| surface | CRM physical part/support context as reviewed | not inferred from generic TF containment |
| column/line written portion | CRMtex TX7 candidate | native written-text semantics required |
| sign | CRMtex glyph/grapheme candidate | abstract/concrete distinction source-evidenced |

### 7.2 Damage and editorial clusters

TLHdig `cluster` nodes and induced sign flags encode damage/editorial ranges, including point and range cases. These are native/source states.

A damage/restoration marker does not automatically imply:

- a known ancient physical event;
- a modern scholarly inference;
- a CRMinf belief;
- a CRMtex recognition activity.

Preserve cluster type/range/evidence first. CRM condition concepts may be candidates where native semantics genuinely describe object condition; CRMinf activates only when explicit attributed interpretation/reconstruction is represented.

### 7.3 `edit` nodes

An `edit` node is an editorial activity/event in the corpus model. It is not CRMtex `TX2 Writing` merely because encoded text changes. It may project to a generic activity and, when it makes an attributed proposition/reconstruction with evidence, participate in CRMinf.

### 7.4 Witness/fragment relations

TLHdig witness relations concerning fragments/lines can support broad witness discovery but are not equivalent to Pseudepigrapha reading→manuscript attestation at a variation locus. A common `witness has reading at locus` query must fail closed for TLHdig unless an actual native assertion supports it.

## 8. ORACC-TF mapping pattern

ORACC-TF remains a stress/conversion target rather than a finalized released ontoTF profile. Its source/target schema separates physical/catalogue data, text structure, lexical layers and editorial/damage information.

Textological mapping should remain layered:

- tablet/document/object identity → CIDOC CRM physical object where warranted;
- surface/line/written sign structure → CRMtex candidates after review;
- lexical semantics → R-008, not textology;
- damage/missing/editorial states → native facts, with CRM/CRMinf projection only when semantics fit;
- period/provenience/catalogue authority semantics → primarily R-010/R-017;
- no reading-at-locus apparatus capability merely because ORACC has readings, normalizations or edition structures.

A source field named `reading` is not Pseudepigrapha apparatus Reading and is not CRMtex TX14 by label similarity.

## 9. Negative/control corpus

BHSA or ETCBC Syriac is a control case. The inspected TF versions expose textual sections and linguistic annotation but no physical manuscript carrier graph or full critical apparatus.

Expected capability behavior:

- linguistic/lexical profiles active as appropriate;
- textual section/navigation remains native/structural unless mapped;
- physical codicology capability absent;
- reading-at-locus apparatus capability absent;
- archaeology/material capability absent;
- manuscript-fragment or witness-omission requests report unsupported/non-resolvable rather than an empty result that implies the corpus was searched for such assertions.

## 10. Codicological-detail policy

Support/material, folio, recto/verso, quire, binding, hand/script, ruling and similar features should not force a manuscript ontology into every profile.

Policy:

1. map broadly supported physical facts to CIDOC CRM where appropriate;
2. map physical writing/script facts through CRMtex where appropriate;
3. preserve source-local codicological values when no accepted target fits;
4. use MeMO/MMDIO and other manuscript ontologies as mapping/design prior art;
5. open a normative profile decision only after independent corpus recurrence demonstrates semantics that CRM/CRMtex/LRMoo cannot represent without repeated local constructs.

Sparse corpora advertise absence rather than empty placeholder profiles.

## 11. Provenance, uncertainty, and assertion status

### 11.1 Source facts vs scholarly beliefs

Every mapped assertion must retain whether it is:

- direct native/source assertion;
- deterministic converter derivation with explicit rule/closure assumptions;
- reviewed semantic projection;
- attributed scholarly claim/inference;
- ontoTF runtime/query derivation.

Only appropriate source claims/processes project to CRMinf belief/inference classes.

### 11.2 Explicit absence vs missing evidence

Required distinction:

```text
explicit source omission
    != source did not attest witness at this locus
    != source/corpus lacks apparatus capability
    != selector/data was not loaded
    != source anomaly/malformed reading
```

These states remain distinct in normalized IR and resolver explanations.

### 11.3 Damage/restoration/uncertainty

Preserve at least:

- native damage/restoration state;
- source certainty/uncertainty value where present;
- responsible source/editor/record when available;
- whether reconstruction is a transcription convention or attributed scholarly proposition;
- exact evidence/reference for any semantic projection.

Do not infer confidence from typography or absence unless the source contract defines that rule.

### 11.4 Dating/provenance

A catalogue date/provenience is a source assertion. If the source separately records scholar, method/evidence, confidence or competing proposals, those richer claims may activate CRMinf provenance/belief/assessment semantics.

Do not manufacture an inference graph from a flat date or place string.

## 12. Canonical mapping/IR requirements for P-003

### 12.1 Layer and role separation

Canonical mapping/IR must distinguish reviewed roles for:

- physical carrier;
- physical part;
- written text / written segment;
- intellectual work;
- expression/textual realization;
- textual witness;
- variation locus;
- apparatus reading;
- witness attestation;
- explicit omission;
- scholarly claim/inference.

R-013 owns exact identifiers/enums.

### 12.2 Multi-entity decomposition

One source record may require several semantic entities/projections rather than one `external_target`:

```text
source manuscript record
  ├── physical carrier projection -> CIDOC CRM
  ├── textual witness projection -> LRMoo/profile-local role
  └── provenance/assertion layer -> native/PROV/CRMinf as evidence warrants
```

The schema must not force these into one URI or one assessment.

### 12.3 Assertion shape

A canonical assertion may need:

```text
subject native selector/identity
semantic role/relation
object native selector/identity or literal
source direction/cardinality
assessment/projection(s)
profile membership
source assertion vs derived state
closure assumptions for negative/absence derivations
evidence/review identity
parent component identity
```

This is required for apparatus edges and physical/textual relations, not only feature-value mappings.

### 12.4 Native-only profile roles

Profile-local apparatus roles without a supported target remain valid `native-only` records. They may support native query planning/capability reporting but must not enter common semantic→native indexes under a fabricated target.

### 12.5 Capability granularity

Agent discovery must distinguish at least:

- physical carrier/codicology;
- written-text segmentation;
- textual work/version;
- textual witness discovery;
- reading-at-locus apparatus;
- explicit omission;
- scholarly inference/reconstruction.

A corpus may support witness discovery without reading attestation. R-014 owns exact capability IDs.

### 12.6 Explanation/provenance

A textological resolution should expose:

- requested common/profile-local semantic role;
- native selector/path/edge used;
- mapping assessment/common target if any;
- source assertion vs derived state;
- closure/witness-inventory context for `unattested`;
- ontology/profile/bridge bundle identities;
- parent corpus/component version;
- evidence/review provenance.

## 13. Representative agent queries

### 13.1 Physical carrier navigation

> Find physical tablets/manuscripts/fragments and navigate their surfaces/columns/lines where supported.

CUC/TLHdig/ORACC participate only through reviewed physical/written-text mappings. Pseudepigrapha participates in physical-carrier semantics only where source witness metadata truly denotes a carrier. BHSA/Syriac report unsupported codicology capability.

### 13.2 Textual versions of a work

> Show textual realizations/versions of a work and indicate which are metadata-only or lack this passage.

Pseudepigrapha exposes native version identities/status without manufacturing alignment. LRMoo projection requires reviewed expression semantics. `not_present` and `metadata_only` remain distinct from empty text.

### 13.3 Witness reading at locus

> At this locus, which witnesses attest each reading?

Pseudepigrapha executes through `unit` + `reading_of` + `witness`. TLHdig/Peshitta-style witness metadata does not satisfy that assertion shape unless native semantics independently provide it. Explanation reports profile-local/native-only apparatus roles until a supported common target exists.

### 13.4 Explicit omissions

> Which witnesses explicitly omit this locus?

Only positive empty-reading evidence counts. `unattested`, missing edge, absent capability and unloaded data do not.

### 13.5 Fragment query

> Find symbolic fragments of this textual expression and physical fragments carrying it.

LRMoo R15 may answer symbolic fragments; CIDOC CRM answers physical fragments/parts. The result sets are not collapsed; a reviewed relation may connect them.

### 13.6 Scholarly reconstruction

> Which restored/reconstructed readings are editorial claims, who made them, and what evidence supports them?

Source-only damage/restoration conventions remain native. CRMinf is used only where attributed propositions/inference/evidence are represented. Converter normalization is not a scholar's inference.

## 14. Adversarial/negative cases

P-003/R-011 should include at least:

1. **physical/textual fragment collapse:** TLH physical `fragment` → LRMoo R15 solely by label → reject;
2. **witness overload:** Peshitta `witness=A` metadata → reading-at-locus attestation → reject;
3. **apparatus/CRMtex reading collision:** Pseudepigrapha `reading` → CRMtex TX14 → reject;
4. **absence→omission:** no witness edge → explicit omission → reject;
5. **metadata-only→empty text:** metadata-only version treated as zero-length textual evidence → reject;
6. **section-label alignment:** identical chapter/verse address across versions → exact alignment → reject;
7. **TF containment→codicological part:** `oslots` inclusion → physical part-of → reject without reviewed semantics;
8. **edit→ancient writing:** TLH `edit` → CRMtex TX2 Writing → reject;
9. **damage→inference:** native damage/restoration → CRMinf belief without attributed claim → reject;
10. **CEO direct import:** CEO's embedded older F-model merged into current LRMoo bundle without bridge/governance → fail closed;
11. **SAWS normative activation:** SAWS 2.1 used as normative dependency despite older-model and licensing conflict → reject;
12. **unattested decontextualization:** derived `unattested` emitted without witness/locus closure context → reject;
13. **CAO/C4O identity collision:** SPAR C4O URI accepted as Critical Apparatus Ontology → reject;
14. **MeMO identity drift:** obsolete/incorrect URI accepted instead of the pinned MeMO ontology/version IRI → reject.

## 15. Inputs to R-011

The ontology-mapped pilot should test:

- CRM physical carrier vs CRMtex written-text segmentation on CUC/TLHdig/ORACC;
- LRMoo work/expression/version semantics on Pseudepigrapha where warranted;
- physical vs symbolic fragment separation;
- Pseudepigrapha variation-locus/reading/witness/omission roles as profile-local/native-only unless an accepted apparatus target emerges;
- witness-discovery vs reading-attestation capability;
- CRMinf only for real attributed reconstruction/provenance claims;
- unsupported textology/codicology capability on BHSA/Syriac control;
- residual gap measurement: whether apparatus roles recur independently enough to justify a later local vocabulary.

Coverage metrics must not penalize legitimate profile-local/native-only semantics by fabricating mappings.

## 16. Inputs to P-003

P-003 should preserve these conclusions unless later reviewed evidence supersedes them:

1. physical carrier, physical writing, intellectual text, textual witness, apparatus assertion and scholarly inference are separate mapping layers;
2. CIDOC CRM + CRMtex + LRMoo + CRMinf form the supported foundation for surrounding textology/codicology semantics;
3. LRMoo R15 symbolic fragments must not stand in for physical fragments;
4. Pseudepigrapha's full apparatus graph remains executable as native/profile-local semantics without a common target;
5. explicit omission and derived unattested are first-class distinct states with different provenance/closure requirements;
6. textual witness identity and physical witness carrier must be separable;
7. SAWS and CAO remain prior art; CEO 1.0 is the strongest modern apparatus candidate but requires governance/licensing/current-LRMoo review before normative use;
8. MeMO and MMDIO are current manuscript/codicology prior art but do not justify another first-profile dependency absent corpus recurrence and LRMoo reconciliation;
9. no ontoTF apparatus ontology is minted yet because independent full-apparatus recurrence is not demonstrated;
10. R-013/R-014 must provide role/capability identifiers without pretending profile-local roles are ontology targets;
11. R-011 must empirically test common projections and residual native-only apparatus gaps.

## 17. Rejected alternatives

### A. One `Manuscript` class for carrier + witness + expression

Rejected: physical object, textual witness, and expression can have different identities/cardinalities.

### B. Use LRMoo for every physical/textual layer

Rejected: LRMoo complements rather than replaces CRM physical objects or CRMtex physical writing.

### C. Use CRMtex TX14 for critical-apparatus readings

Rejected: TX14 is an intellectual reading/comprehension activity; Pseudepigrapha `reading` is a textual alternative at a locus.

### D. Treat every restoration as CRMinf inference

Rejected: source transcription/editorial state can be asserted directly without explicit inference/belief semantics.

### E. Adopt CAO/SAWS normatively now

Rejected due support-tier, old-model and licensing/governance constraints.

### F. Adopt CEO 1.0 immediately

Rejected for the first profile: CEO is strong apparatus prior art, but current-LRMoo compatibility and ontology-artifact redistribution licensing are not yet reviewed to R-002 standards.

### G. Adopt MeMO/MMDIO immediately

Rejected: both are useful open manuscript models, but their FRBR/FaBiO basis requires reconciliation and current pilot recurrence does not justify another normative profile.

### H. Mint a ontoTF apparatus ontology now

Rejected: only one inspected corpus exposes a robust full apparatus graph. Profile-local roles preserve functionality without creating a premature vocabulary authority.

## 18. Acceptance-criteria trace

- [x] Keeps physical object, physical writing, intellectual text/version, witness attestation and scholarly inference distinct.
- [x] Covers Pseudepigrapha-TF's actual unit/reading/witness/omission/unattested model, including orphan readings and metadata-only versions.
- [x] Covers TLHdig-TF physical fragments, surfaces/columns/lines, damage/editorial clusters, edit nodes and witness distinctions.
- [x] Distinguishes ORACC physical/textual/catalogue semantics without inventing apparatus capability.
- [x] Evaluates CIDOC CRM, CRMtex, LRMoo and CRMinf responsibilities and preserves R-012 version/composition constraints.
- [x] Evaluates SAWS/CAO as prior art and CEO 1.0 as stronger modern apparatus prior art without premature promotion.
- [x] Evaluates current MeMO/MMDIO codicology prior art and records exact ontology identities/licensing.
- [x] Determines that a local ontoTF apparatus ontology is not yet justified; profile-local roles/native-only mappings suffice for current evidence.
- [x] Defines explicit omission vs unattested/missing/unsupported semantics and scholarly attribution rules.
- [x] Produces implementable R-011/P-003 mapping, IR, capability and adversarial-test requirements.

## 19. References

### Accepted ontoTF research

- [R-002 ontology governance](R-002-ontology-governance.md)
- [R-005 corpus semantic census](R-005-corpus-semantic-census.md)
- [R-006 common ontology pivot](R-006-common-ontology-pivot.md)
- [R-007 TF structural semantics](R-007-tf-structural-semantics.md)
- [R-008 lexical-semantic profile](R-008-lexical-semantic-profile.md)
- [R-012 CRMtex modern bridge](R-012-crmtex-modern-bridge.md)

### Standards / ontology sources

- CIDOC CRM: <https://cidoc-crm.org/>
- CRMtex 2.0: <https://cidoc-crm.org/crmtex/ModelVersion/version-2.0>
- CRMtex declarations: <https://cidoc-crm.org/extensions/crmtex/html/CRMtex_v2.0.html>
- LRMoo 1.1.1: <https://cidoc-crm.org/lrmoo/ModelVersion/version-1.1.1>
- LRMoo declarations: <https://cidoc-crm.org/extensions/lrmoo/html/LRMoo_v1.1.1.html>
- CRMinf 1.2.1: <https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html>
- Web Annotation: <https://www.w3.org/TR/annotation-model/>
- SAWS 2.1: <http://purl.org/saws/ontology>
- Critical Apparatus Ontology 0.9: <https://w3id.org/cao>
- Critical Edition Ontology 1.0: <http://purl.org/critical-edition-ontology>
- Medieval Manuscript Ontology: <https://w3id.org/irnerio/ontology/memo>
- MMDIO 1.1.0: <https://w3id.org/irnerio-mosaico/ontology/mmdio/>

### Corpus evidence

Pseudepigrapha-TF and TLHdig-TF source/converter behavior is pinned by R-005. R-009 additionally checked current public repository documentation to ensure that interpretation still matches executable apparatus/document contracts. Released R-011 mappings must remain pinned to exact corpus/profile revisions rather than silently following repository heads.