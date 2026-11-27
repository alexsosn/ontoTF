# R-010: archaeology, material-culture, provenance, and period profile

**Status:** research complete; pending fresh logically-independent review  
**Issue:** #42  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-002/R-003/R-005, merged R-006/R-007/R-008/R-009, merged R-012 #54, and merged roadmap guardrail #45

## Decision

ontoTF should use a **capability-gated heritage profile**, not an “ancient object = archaeology” rule.

The first contract is:

1. **CIDOC CRM is the default material-culture backbone** for physical objects, parts, identifiers, materials, production/modification, actors, places, current/former location, ownership/custody and source provenance where native semantics warrant those assertions.
2. **CRMarchaeo activates only for explicit excavation/stratigraphic evidence**: excavation processing, stratigraphic units/interfaces, embeddings/find contexts, archaeological encounter/find events and stratigraphic relations. A tablet, manuscript, fragment, museum number, provenience string or ancient date does not activate CRMarchaeo by itself.
3. **CRMsci activates only for explicit observation, measurement, sampling, position determination or scientific-analysis processes/results.** A catalogue material label or editor's qualitative description does not become a scientific measurement.
4. **Getty AAT is an external controlled-value authority**, especially for material/object/technique terminology, not a semantic replacement for CRM classes/properties. ontoTF binds the exact AAT record and reviewed Getty data snapshot/provenance.
5. **PeriodO is an external scholarly-period authority**, not a universal fixed chronology. A PeriodO URI identifies one published definition of a period with source-specific temporal/spatial scope.
6. **PROV-O remains optional publication/provenance infrastructure.** The canonical ontoTF evidence/review/parent-component provenance contract remains authoritative at runtime; PROV-O is used only where it adds an interoperable publication representation.
7. **The first R-011 pilot should not advertise CRMarchaeo or CRMsci capability for ORACC-TF, TLHdig-TF, CUC, or linguistic controls unless pinned native evidence actually supplies the required excavation/scientific assertion shape.** Current inspected evidence does not.

The governing invariant is:

> **Object identity, material/type classification, find/provenience assertion, current custody/location, excavation context, scientific observation, and scholarly periodization are different semantics. Similar place/date/material strings do not collapse them.**

## 1. Responsibility model

```text
PHYSICAL / HERITAGE OBJECT
  CIDOC CRM
    object / physical part
    identifier / inventory number
    material / production / modification
    actor / place / custody / location
              │
              ├── optional authority value --> Getty AAT / place authority
              │
              ├── source provenance assertion
              │
              ├── only if excavation evidence exists
              ▼
ARCHAEOLOGICAL CONTEXT
  CRMarchaeo
    excavation process
    stratigraphic unit/interface
    embedding / find context
    stratigraphic relation
              │
              └── depends on pinned old CRM/CRMsci releases; bridge required before
                  composition with ontoTF's current CRM/CRMsci stack

SCIENTIFIC OBSERVATION
  CRMsci
    observation / measurement / sample / position determination
              │
              └── result and method remain source/provenance bound

SCHOLARLY PERIODIZATION
  source period label
      └── reviewed authority link --> one PeriodO period definition
                                  (source + temporal approximation + geography)

ontoTF evidence/review provenance
  └── optional PROV-O publication view
```

## 2. CIDOC CRM baseline

CIDOC CRM is sufficient for the majority of material-culture semantics currently evidenced in the target corpus family.

Use it, where native semantics warrant, for:

- physical tablet/manuscript/object identity;
- physical fragment/part identity;
- inventory/catalogue identifiers;
- material/support classifications;
- production or modification events when represented;
- actors and organizations;
- places;
- ownership/custody/current location versus historical location/provenance assertions;
- source records describing object history.

ontoTF must preserve the distinction between **identifier** and **type/value**. A museum accession number is not an ontology class. A CDLI/Pleiades/Getty/PeriodO URI is not automatically a common semantic target merely because it is external and dereferenceable; R-017 owns the final authority-reference contract.

## 3. CRMarchaeo 2.1.1

Primary sources:

- stable release: <https://cidoc-crm.org/crmarchaeo/ModelVersion/version-2.1.1>
- declarations: <https://cidoc-crm.org/extensions/crmarchaeo/html/CRMarchaeo_v2.1.1.html>

CRMarchaeo 2.1.1 is explicitly an extension for the **archaeological excavation process**. Its classes include:

- `A1 Excavation Processing Unit`;
- `A2 Stratigraphic Volume Unit`;
- `A3 Stratigraphic Interface`;
- `A4 Stratigraphic Genesis`;
- `A5 Stratigraphic Modification`;
- `A6 Group Declaration Event`;
- `A7 Embedding`;
- `A8 Stratigraphic Unit`;
- `A9 Archaeological Excavation`;
- `A10 Excavation Interface`.

Its properties include excavation, embedding, stratigraphic and find relationships such as `AP13 has stratigraphic relation to`, `AP17 is found by`, `AP18 is embedding of`, `AP19 is embedding in`, and `AP21 contains`.

This is a strong reason **not** to activate it merely because a corpus contains archaeological objects. A catalogue field `provenience=Ur` does not provide an excavation processing unit, stratigraphic volume, embedding, or encounter event.

### 3.1 Version-composition constraint

CRMarchaeo 2.1.1 explicitly references:

- CIDOC CRM **7.1.2**;
- CRMsci **2.0**.

ontoTF's accepted current basis otherwise uses:

- CIDOC CRM **7.1.3**;
- CRMsci **3.2**.

This is structurally the same kind of version-composition problem R-012 identified for CRMtex. R-010 does not rewrite CRMarchaeo 2.1.1 against current namespaces and does not assume a coherent import closure.

Consequences:

1. a CRMarchaeo profile lock must preserve its declared dependency releases;
2. any composition with current CRM/CRMsci requires explicit reviewed bridge/bundle semantics;
3. R-015 must include this dependency edge in ontology-bundle identity/fail-closed bridge rules;
4. because no first-pilot corpus currently needs CRMarchaeo semantics, no ad hoc bridge should be invented simply to claim archaeology support.

### 3.2 Source assertion vs interpretation

CRMarchaeo itself carefully distinguishes excavation observations from subsequent interpretation. Its `A1 Excavation Processing Unit` scope notes that excavation documentation should describe material state at excavation time and should be distinguished from later interpretation of causes.

That matches ontoTF's provenance rule directly:

```text
recorded excavation/find state
    != later archaeological interpretation
    != ontoTF semantic projection
```

Where interpretation is explicitly modeled, CIDOC/CRMarchaeo attribute-assignment semantics and/or CRMinf may participate, but a flat excavation record must not be upgraded to a scholarly inference graph automatically.

## 4. CRMsci 3.2

Primary source:

- <https://cidoc-crm.org/crmsci/ModelVersion/crmsci-v3.2>
- <https://cidoc-crm.org/extensions/crmsci/html/CRMsci_v3.2.html>

CRMsci 3.2 is stable in 2026 and references CIDOC CRM 7.1.3. Relevant classes include:

- `S2 Sample Taking`;
- `S3 Measurement by Sampling`;
- `S4 Single Observation`;
- `S21 Measurement`;
- `S23 Position Determination`;
- `S24 Sample Splitting`;
- `S27 Observation`;
- `S28 Observable Situation`.

This profile activates only when the source supplies actual observation/measurement semantics: what was observed/measured/sampled, by what activity/method, and what value/result/location was determined.

Unsafe promotions include:

- `material=clay` → scientific measurement;
- `damage=1` → observation activity;
- a catalogue coordinate → position-determination event, unless the source records that event/process;
- a converter-derived Unicode/sign property → scientific observation.

A source may state the **result** of a prior scientific analysis without exposing its process. ontoTF should preserve that source result and provenance; it must not fabricate a missing CRMsci activity graph merely to normalize the value.

## 5. Getty AAT policy

Getty currently publishes AAT and related vocabularies openly under **ODC-By 1.0**, with individual linked-data records and regularly refreshed downloads.

ontoTF should use AAT as an **external controlled vocabulary/authority**, consistent with R-002 and R-017.

Good candidates include reviewed source values for:

- material (`clay`, `stone`, `parchment`, etc. where the exact Getty concept fits);
- object type (`tablet`, object categories, etc.);
- technique or production terminology where native semantics warrant it.

AAT mappings must preserve:

```text
native source value
AAT record URI
reviewed mapping assessment
Getty dataset/snapshot identity or retrieval provenance
source corpus release
mapping evidence/review
```

Do not use an AAT URI as a substitute for a CIDOC CRM type/relation assertion. For example, a source object can be a CRM physical object **and** carry an AAT type/material authority value as complementary semantics.

Do not infer exactness from English label equality.

## 6. PeriodO policy

Primary sources:

- technical model: <https://perio.do/technical-overview/>
- license: <https://perio.do/license/>

PeriodO is CC0/public-domain dedicated and models each historical-period entry as a **published definition**, represented as a SKOS concept. A PeriodO authority is a SKOS concept scheme sharing one bibliographic source.

Each period definition has:

- a source-given name;
- some temporal bounds;
- an implicit or explicit geographic association;
- a citable published source;
- a structured temporal approximation plus source wording;
- stable resolvable ARK identity.

This is exactly the right model for ontoTF's period problem: period labels are **scholarly definitions**, not universal date constants.

Therefore:

```text
ORACC period = "Old Babylonian"
```

must not become one unqualified numeric interval.

A reviewed mapping may instead say:

```text
native period label
  -> PeriodO definition X
       source: authority/publication X
       spatial scope: X
       temporal approximation: X
       mapping assessment: reviewed
```

Two corpora using the same English period label may map to different PeriodO definitions. Conversely, two differently named source periods may overlap temporally without being semantically equivalent.

Exact date-range filtering and period-concept filtering are different query operations.

## 7. PROV-O role

R-002 already accepts PROV-O as provenance infrastructure. R-010 does not replace ontoTF's native evidence/review/parent-component provenance contract with PROV-O.

Use PROV-O only where it provides an interoperable publication view of:

- an assertion derived from a source record;
- mapping review/evidence provenance;
- generated artifacts;
- agent/result provenance where publication requires RDF.

Do not duplicate every CIDOC CRM object-history event as generic PROV activity/entity edges merely because PROV-O is available.

Runtime truth remains the canonical ontoTF provenance/evidence contract; RDF/PROV export is derived.

## 8. Place and provenance distinctions

ontoTF must distinguish at least:

1. **findspot / excavation location** — where the object was archaeologically encountered, with CRMarchaeo only if the excavation/find process is actually represented;
2. **source provenience** — catalogue/source claim about origin/find provenance, which may be imprecise, historical, inferred, or conventional;
3. **production/origin place** — place associated with production, not necessarily findspot;
4. **current location** — where the object is currently held/displayed;
5. **current/former keeper or owner** — actor/custody relation, not a place;
6. **authority place identifier** — Pleiades/TGN/etc. resource identifying a place, not itself a provenance relation.

A single source string such as `Nineveh` cannot determine which relation applies without field/source semantics.

A museum name is not automatically the current physical location: it can be a keeper/collection/catalogue authority while the object is elsewhere.

## 9. Corpus stress cases

### 9.1 ORACC-TF

R-005's pinned ORACC-TF stress census records rich catalogue/object metadata including material, period, provenience, collection/object identifiers and external identifiers such as Pleiades/CDLI where present. ORACC-TF remains a conversion target rather than a finalized released ontoTF profile, so mappings remain prototype-level until the target schema is frozen.

Recommended mapping pattern:

| ORACC native evidence | first ontoTF treatment |
|---|---|
| object/document identity | CIDOC CRM physical-object candidate if catalogue semantics denote physical artefact |
| museum/catalogue/inventory identifier | CRM identifier + native authority context; not ontology class |
| collection/institution value | source keeper/collection metadata; map current custody/location only if field semantics warrant |
| material string | native value + reviewed AAT authority candidate |
| object type string | native value + reviewed AAT candidate |
| provenience string / place ID | source provenience assertion + place authority link when justified |
| Pleiades URI | external place authority identity, not automatic findspot relation |
| period string | native scholarly category; PeriodO candidate only after definition-level review |
| ruler/date catalogue metadata | source assertion; CRMinf only if an attributed inference/assessment is represented |
| damage/missing | native/editorial/material state; not CRMsci observation automatically |

Current ORACC source distributions do not, merely by carrying catalogue metadata, establish excavation trenches, stratigraphic units, embedding contexts, sample-taking, or measurement activities. Therefore initial ORACC pilot capability should report CRMarchaeo/CRMsci **unsupported/not activated** unless a selected project provides and maps those native structures explicitly.

### 9.2 TLHdig-TF

TLHdig-TF provides physical/documentary identities, fragments/witnesses, CTH/project/source provenance, edit logs, and inventory-like manuscript/document identifiers.

Important native guardrails already documented by the converter include:

- `src_file` is release-scoped provenance, not a persistent external identity;
- source directory/project components are provenance, not semantic project classification;
- CTH/subcorpus metadata describes textual/catalogue organization, not excavation context;
- fragment/witness relations are documentary relations, not stratigraphic embedding.

Recommended mapping pattern:

- document/manuscript/fragment carrier → CIDOC CRM where physical identity is justified;
- inventory/catalogue number → identifier;
- source path/CTH/project → provenance/catalogue metadata, not archaeological provenience;
- line→fragment witness relation → R-009 textual/documentary layer, not CRMarchaeo embedding;
- editor/date/src/comment edit records → source/editorial provenance; CRMinf only when an attributed proposition/inference is represented;
- damage clusters → native condition/editorial state, not CRMsci observation by default.

Current pinned evidence does not supply excavation stratigraphy or scientific analysis. CRMarchaeo/CRMsci capabilities should therefore be absent in the initial TLH profile.

### 9.3 CUC

CUC provides physical tablet identity, sign text, tablet/column/line structure and limited tablet metadata. R-005 did not establish a rich excavation/stratigraphic or scientific-analysis graph.

Therefore:

- tablet identity may map to CRM physical object where source semantics warrant;
- `tablet_info` and related metadata remain source values until field semantics are reviewed;
- physical written-text structure belongs primarily to R-009 CRMtex mappings;
- ancient/Ugaritic context does **not** activate CRMarchaeo;
- no first-pilot CRMsci capability without actual observation/measurement source structures.

### 9.4 Non-archaeological control

BHSA or ETCBC Syriac should explicitly advertise archaeology/material-culture capability as absent/unsupported in the inspected versions.

A query such as “find clay objects from the Late Bronze Age” must not silently return an empty result as though those corpora contain material/object metadata. It should report that the capability is not available.

## 10. Capability contract

R-014 owns final identifiers. R-010 requires enough granularity to distinguish at least:

- heritage physical-object identity;
- identifier/catalogue identity;
- material/object-type authority mapping;
- place/provenience metadata;
- custody/current-location metadata;
- excavation context;
- stratigraphy/embedding;
- scientific observation;
- measurement;
- sampling;
- period-authority mapping;
- scholarly dating/provenance inference.

A corpus may activate physical-object/material capability while excavation and scientific-analysis capabilities remain absent.

Do not expose one boolean `archaeology=true`.

## 11. Canonical mapping/IR requirements for P-003

### 11.1 Authority resource vs ontology target

Mappings must distinguish:

```text
semantic ontology target
  e.g. CIDOC CRM class/property

external authority value/resource
  e.g. AAT material concept, PeriodO period definition, Pleiades place
```

R-017 owns final field names and publication semantics. R-010 establishes that the distinction is mandatory for archaeology/material mappings.

### 11.2 Assertion role/direction

A place/value mapping needs its native relation, not just a URI:

```text
object --source provenience--> place X
object --current location--> place Y
object --production place--> place Z
object --keeper--> institution K
```

The target place identity alone cannot recover those semantics.

### 11.3 Source assertion vs interpreted claim

IR must record whether a date/place/material/period is:

- direct source field/assertion;
- deterministic converter normalization;
- reviewed authority mapping;
- attributed scholarly inference;
- ontoTF query/runtime derivation.

### 11.4 Versioned authority binding

For AAT/PeriodO/external authority resources retain at least:

- stable resource URI;
- authority/dataset identity;
- exact reviewed snapshot/retrieval revision/digest where available;
- native source value;
- mapping assessment;
- evidence/review identity;
- parent corpus release.

Updating an authority dataset does not silently mutate an existing ontoTF mapping release.

### 11.5 Optional ontology dependencies

CRMarchaeo and CRMsci profile activation must be explicit. Absence is not an error for corpora without those semantics.

If CRMarchaeo is activated, the effective ontology bundle must include its version-faithful dependencies/bridges. Loading current CRMsci 3.2 beside CRMarchaeo 2.1.1 is not enough.

## 12. Period semantics and query policy

ontoTF should support two distinct query families:

### 12.1 Period-concept query

> Objects classified by the source/mapping as PeriodO definition X.

This is semantic/category filtering. It preserves the source definition and mapping evidence.

### 12.2 Temporal-overlap query

> Objects dated between 1800 and 1600 BCE, including uncertain ranges.

This is temporal filtering over source/derived date assertions. It must not infer that every object mapped to a named period has one universal exact interval unless the mapping contract explicitly says the PeriodO structured approximation may be used for that query mode.

PeriodO bounds are structured approximations of published period definitions, not necessarily object dates.

## 13. Representative agent queries

### 13.1 Material/object type

> Find clay tablets and show the source material value plus any reviewed AAT concept.

Expected:

- ORACC participates where material metadata exists;
- source literal remains visible;
- AAT mapping is separate authority evidence;
- BHSA/Syriac report unsupported material capability.

### 13.2 Provenience vs current location

> Find objects from Nineveh that are currently held in London.

Expected:

- resolver requires distinct source provenience/place and current keeper/location semantics;
- same place/institution field cannot satisfy both roles without native evidence;
- Pleiades/TGN IDs identify places but do not manufacture the relationship.

### 13.3 Period comparison

> Compare objects classified as Old Babylonian in two corpora.

Expected:

- native labels and authority mappings are reported;
- different PeriodO definitions remain distinguishable;
- no global hard-coded date range replaces source period semantics.

### 13.4 Excavation context

> Which objects were embedded in the same stratigraphic unit?

Expected:

- execute only for a profile with actual reviewed CRMarchaeo embedding/stratigraphic assertions;
- current ORACC/TLH/CUC initial profiles should report unsupported rather than infer context from provenience or collection metadata.

### 13.5 Scientific measurement

> Show material analyses with measured values and sampling provenance.

Expected:

- require actual CRMsci-compatible source activity/result semantics;
- a material category string is insufficient.

## 14. Adversarial/negative cases

P-003/R-011 should include:

1. **ancient-object→archaeology trap:** tablet object exists ⇒ CRMarchaeo capability → reject;
2. **provenience→findspot trap:** catalogue provenience string ⇒ excavated/findspot relation → reject without source semantics;
3. **museum→location trap:** institution/collection string ⇒ current physical location → reject without field semantics;
4. **material→measurement trap:** `material=clay` ⇒ CRMsci measurement → reject;
5. **damage→observation trap:** damage flag ⇒ CRMsci observation event → reject;
6. **period-label universalization:** same `Old Babylonian` label ⇒ same fixed date interval across sources → reject;
7. **temporal-overlap equivalence:** overlapping period bounds ⇒ same period concept → reject;
8. **authority-as-ontology trap:** AAT/PeriodO/Pleiades URI treated as CRM class/property target → reject;
9. **CRMarchaeo version union:** CRMarchaeo 2.1.1 + current CRMsci 3.2 loaded without bridge and reasoned as one upstream closure → fail closed;
10. **source-path provenience trap:** TLH `src_file`/CTH path treated as archaeological provenience → reject;
11. **witness→embedding trap:** TLH line→fragment witness relation treated as CRMarchaeo embedding → reject;
12. **source date→inference trap:** flat catalogue date automatically materialized as CRMinf belief/inference → reject;
13. **authority drift:** mapping silently follows changed AAT/PeriodO data without new lock/review → reject.

## 15. Ontology/profile gaps

Current evidence does **not** demonstrate a recurring semantic gap requiring new ontoTF archaeology ontology terms.

The main gaps are contract/governance problems rather than missing concepts:

- distinguish ontology targets from authority resources;
- distinguish provenance/findspot/current location/custody relations;
- version-lock AAT/PeriodO mappings;
- bridge optional CRMarchaeo old dependencies if the capability is ever activated;
- represent source assertion vs scholarly inference;
- advertise absent optional capabilities explicitly.

R-017 and R-015 address the first two infrastructure classes; R-011 will test empirical coverage.

## 16. Inputs to R-011

The pilot should test at least:

- ORACC physical-object and identifier semantics through CIDOC CRM candidates;
- ORACC material/object-type values with reviewed AAT candidates where defensible;
- ORACC native period values with selected PeriodO definitions only where source-definition correspondence is evidenced;
- ORACC provenience/place authority while distinguishing relationship from place identity;
- TLH physical object/fragment identifiers and source/editor provenance without false archaeology projection;
- CUC tablet identity as a sparse material-culture case;
- BHSA/Syriac unsupported material/archaeology controls;
- explicit negative result showing no CRMarchaeo/CRMsci activation from ancient-object/catalogue metadata alone.

Coverage metrics must not reward invented excavation/scientific semantics.

## 17. Inputs to R-015

R-015's ontology-bundle research must include the newly confirmed optional dependency edge:

```text
CRMarchaeo 2.1.1
  -> CIDOC CRM 7.1.2
  -> CRMsci 2.0

ontoTF current optional/current stack
  -> CIDOC CRM 7.1.3
  -> CRMsci 3.2
```

A future active CRMarchaeo profile therefore needs version-aware bundle/bridge identity just as CRMtex does. R-010 does not decide the actual cross-version bridge assertions because no first-pilot execution requires them.

## 18. Inputs to P-003

P-003 should preserve:

1. CIDOC CRM is the default heritage/material backbone;
2. CRMarchaeo and CRMsci are optional capability-gated profiles, never implied by corpus age/object type;
3. current first-pilot evidence does not activate CRMarchaeo/CRMsci for ORACC/TLH/CUC by default;
4. provenience/findspot/current location/custody/production place are separate relations;
5. AAT, PeriodO and place IDs are external authority resources distinct from ontology targets;
6. period mappings preserve source-specific scholarly definition, temporal approximation and geography;
7. source date/provenience/material facts remain source assertions unless explicit inference/measurement semantics exist;
8. authority snapshot/revision/digest and mapping review belong in canonical provenance;
9. CRMarchaeo 2.1.1 dependency skew with current CRM/CRMsci must be represented by R-015 bundle semantics before activation;
10. no local ontoTF archaeology vocabulary is justified by current evidence.

## 19. Rejected alternatives

### A. Activate CRMarchaeo for every ancient object

Rejected. CRMarchaeo models excavation/stratigraphic processes and contexts.

### B. Treat catalogue provenience as findspot

Rejected. Provenience can be a source claim of different granularity/epistemic status and may not record an excavation event.

### C. Normalize period names to fixed date ranges

Rejected. PeriodO demonstrates that period concepts are source-defined and geographically scoped.

### D. Use AAT as the heritage ontology backbone

Rejected. AAT is a controlled vocabulary/authority complementing CRM object/relation semantics.

### E. Treat every material value as a CRMsci observation

Rejected. A scientific activity/result model requires source evidence for observation/measurement/sampling semantics.

### F. Union CRMarchaeo 2.1.1 with CRMsci 3.2 by local URI/code similarity

Rejected. The upstream model explicitly references CRMsci 2.0 and CRM 7.1.2; current-version composition requires reviewed bridge semantics.

### G. Mint ontoTF archaeology terms now

Rejected. Current gaps are chiefly authority/provenance/version-contract gaps, not recurring missing archaeological concepts.

## 20. Acceptance-criteria trace

- [x] Uses CRMarchaeo only for evidence-backed excavation/stratigraphic semantics and explicitly rejects ancient-object activation.
- [x] Distinguishes findspot/excavation location, source provenience, production/origin place, current location, keeper/custody and place identity.
- [x] Handles PeriodO periods as source-defined scholarly concepts rather than universal date intervals.
- [x] Defines AAT/PeriodO authority-resource mapping and version/provenance requirements.
- [x] Tests the mapping policy against actual ORACC-TF, TLHdig-TF and CUC semantic evidence plus a non-archaeological control.
- [x] Separates source assertions from CRMinf scholarly inference and CRMsci observation/measurement activities.
- [x] Identifies CRMarchaeo 2.1.1's CRM 7.1.2 / CRMsci 2.0 dependency mismatch with the current ontoTF stack and routes it into R-015.
- [x] Produces implementable capability, IR, authority, provenance and negative-test requirements for P-003/R-011.
- [x] Finds no evidence-based need for a local ontoTF archaeology ontology.

## 21. References

### ontoTF research

- [R-002 ontology governance](R-002-ontology-governance.md)
- [R-005 corpus semantic census](R-005-corpus-semantic-census.md)
- [R-006 common ontology pivot](R-006-common-ontology-pivot.md)
- [R-007 TF structural semantics](R-007-tf-structural-semantics.md)
- [R-009 textology/codicology profile](R-009-textology-codicology-profile.md)
- [R-012 CRMtex modern bridge](R-012-crmtex-modern-bridge.md)

### Standards and authorities

- CIDOC CRM: <https://cidoc-crm.org/>
- CRMarchaeo 2.1.1: <https://cidoc-crm.org/crmarchaeo/ModelVersion/version-2.1.1>
- CRMarchaeo declarations: <https://cidoc-crm.org/extensions/crmarchaeo/html/CRMarchaeo_v2.1.1.html>
- CRMsci 3.2 declarations: <https://cidoc-crm.org/extensions/crmsci/html/CRMsci_v3.2.html>
- Getty Vocabularies licensing/access: <https://www.getty.edu/research/tools/vocabularies/obtain/>
- PeriodO technical overview: <https://perio.do/technical-overview/>
- PeriodO license: <https://perio.do/license/>
- PROV-O: <https://www.w3.org/TR/prov-o/>

Corpus evidence is pinned by R-005. R-010 additionally checked current ORACC-TF/TLHdig-TF documentation only as a consistency check; released mappings must remain bound to exact reviewed corpus/profile revisions.