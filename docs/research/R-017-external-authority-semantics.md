# R-017: external authority identifiers versus semantic-pivot targets

**Status:** research/prototype complete; pending exact-head CI and fresh logically-independent adversarial review  
**Issue:** #51  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-002/R-006/R-008/R-009/R-010 and current R-013/R-014/P-003 design inputs

## Decision

ontoTF must not treat every external URI, identifier, vocabulary record, catalogue number, DOI, or web link as a semantic-pivot target.

The first contract distinguishes six external-reference roles:

1. **semantic-pivot target** — shared ontology class/property/concept used to express corpus-neutral semantics and build semantic→native plans;
2. **authority-value reference** — a controlled vocabulary/resource identifying the value of a native assertion, e.g. a reviewed Getty AAT material/object/technique concept or a PeriodO period definition;
3. **entity-identity reference** — an external record intended to identify the same real/intellectual entity as a native entity;
4. **scoped catalogue identifier** — a literal/code meaningful under a namespace/issuing authority, such as museum/inventory/catalogue IDs;
5. **provenance/source reference** — DOI, bibliography record, source dataset/reference or documentation URL explaining where an assertion came from;
6. **locator/reference URL** — a navigational URL or downloadable resource pointer with no identity/semantic projection implied.

The governing invariant is:

> **Dereferenceability is not semantics. A URI may identify a vocabulary value, entity record, source, or web page without being the common concept/relation that an agent requested.**

## 1. Why the current `external_target` shape is insufficient

A single generic external target field collapses materially different operations:

```text
olia:Noun
    -> semantic category request

AAT concept for clay
    -> controlled material value

PeriodO ARK
    -> one scholarly period definition

museum inventory number
    -> scoped object identifier

CDLI / catalogue record URI
    -> external entity/catalogue identity candidate

DOI / source URL
    -> provenance/reference
```

Only the first is inherently a common semantic-pivot target. The others may still be useful and queryable, but through different resolver contracts.

## 2. Getty AAT role

Getty describes AAT as a structured vocabulary/knowledge base of generic concepts for art, architecture, conservation, archaeology and related cultural heritage domains. Each concept record has a unique persistent identifier and vocabulary releases are available as linked/open data under ODC-By 1.0.

Primary sources:

- <https://www.getty.edu/publications/vocabularies-editorial-guidelines/aat-guidelines/1_about_aat/1.1/>
- <https://www.getty.edu/publications/vocabularies-editorial-guidelines/aat-guidelines/1_about_aat/1.3/>

ontoTF role:

- AAT is an **authority-value system** for reviewed native values such as material, object type, or technique;
- an AAT concept URI does not replace the CIDOC CRM class/property saying *what relation is being asserted*;
- a CRM physical-object assertion and an AAT type/material value can be complementary projections;
- label equality is not sufficient for mapping;
- the exact Getty concept ID/snapshot/retrieval provenance remains part of the reference contract.

Example:

```text
native ORACC material = "clay"
    -> reviewed authority-value reference: AAT concept X

native object
    -> semantic pivot: CIDOC CRM physical object class

native has-material assertion
    -> semantic relation: reviewed CRM/material relation
```

Those are three different semantic/reference roles.

## 3. PeriodO role

PeriodO is a public-domain gazetteer of **scholarly definitions of periods**. Period definitions are modeled as SKOS concepts and grouped into authorities/concept schemes tied to published sources. Period records have stable ARK identifiers and preserve source wording, temporal extent and spatial/source context.

Primary sources:

- <https://perio.do/>
- <https://perio.do/technical-overview/>

ontoTF role:

- a PeriodO ARK is an **authority-value reference** to one published scholarly period definition;
- it is not a universal period class with one globally authoritative date interval;
- two corpora using the same label can map to different PeriodO definitions;
- time-range filtering and period-definition filtering are distinct operations;
- PeriodO's own `sameAs` to a source vocabulary record is provenance/identity inside PeriodO and does not force ontoTF `owl:sameAs` publication for native corpus values.

Example:

```text
native ORACC period = "Old Babylonian"
    -> reviewed PeriodO definition P
       + source authority P
       + spatial/temporal scope P

request "PeriodO P"
    -> may compile to native period selector only if this exact mapping is reviewed

request "objects dated 1900-1700 BCE"
    -> different query operation; do not replace it with PeriodO P automatically
```

## 4. Real corpus reference shapes

### 4.1 ORACC-TF

Accepted R-010/R-011 evidence distinguishes:

- catalogue/object identity and identifiers;
- material values;
- period values;
- provenience/place values;
- textual structure and lexical data.

Representative treatment:

| native shape | R-017 role | default query behavior |
|---|---|---|
| catalogue/P/Q/project identifier | scoped catalogue/entity identity depending source contract | exact native ID filter; external identity only if reviewed |
| museum/inventory number | scoped catalogue identifier | native identifier filter; namespace required |
| `material` | native value + optional AAT authority value | authority filter only after reviewed value mapping |
| `period` | native value + optional PeriodO definition | authority filter only after reviewed definition mapping |
| provenience/place string | native place assertion; optional place authority | not a CRM class and not automatically a TGN/Pleiades identity |
| source/project URL | provenance/locator | explanation/navigation by default |

### 4.2 TLHdig-TF

TLHdig distinguishes edition/document records from manuscript/tablet identity. `docid` is manuscript identity within the source model and `docgroup` groups records claiming the same tablet. Witness apparatus includes sigla/inventory identifiers and joins.

Consequences:

- `docid` is first a **native scoped identity key**, not an external ontology concept;
- an inventory number remains a catalogue identifier unless its issuing authority/resource is modeled;
- a link from that identifier to an external catalogue can become an entity-identity reference only after review;
- `document` record identity must not be equated to physical-object identity merely because both refer to the same tablet context.

### 4.3 Pseudepigrapha-TF

Pseudepigrapha manuscript nodes are textual witness identities with sigla, names, language and bibliography; citation-only synthetic witness identities can also exist. Resource records carry name/info/URL and are attached to exact textual versions.

Consequences:

- `ms_abbrev` is a native scoped witness identifier, not a global entity URI;
- bibliography/source URLs are provenance/reference links, not physical-manuscript identity by default;
- a resource URL is a locator/provenance reference unless the native/source contract explicitly says it is canonical entity identity;
- external links never upgrade synthetic witness nodes into physical carriers.

### 4.4 Linguistic control corpora

BHSA/Syriac/ExtraBiblical lexical keys are native corpus identifiers. A native `lex` key is not an OntoLex external lexical-entry resource merely because both concern lexical identity.

R-008 governs when a reviewed lexical entity projection is justified. R-017's negative control is that native identifiers remain native identifiers until such a mapping exists.

## 5. Controlled reference kinds

P-003 should preserve a controlled dimension equivalent to:

```text
semantic-pivot
authority-value
entity-identity
catalogue-identifier
provenance-source
locator
```

These are semantic roles, not RDF node types. R-013 owns final kind/role enum reconciliation.

A record should carry enough information to distinguish:

```text
reference kind
external identifier/URI or scoped literal
issuing authority / vocabulary identity
native subject/value selector
reviewed correspondence strength where applicable
query role
snapshot/retrieval/version provenance
optional publication relation
review/evidence identity
```

## 6. Query roles

External references can participate in different operations.

### `semantic-constraint`

Only semantic-pivot targets participate directly in ordinary corpus-neutral semantic resolution.

Example: `olia:Noun` -> native POS constraint.

### `authority-value-filter`

An authority-value reference may compile directly only when a reviewed mapping binds the exact authority resource to a native value/selector.

Example: reviewed PeriodO definition -> native ORACC period value.

This is not the same reverse index as semantic-pivot resolution; agents should know they are filtering by a selected authority definition.

### `identity-filter`

An entity-identity reference may resolve to a native entity if exact/accepted identity binding exists.

Example: external catalogue record -> native object record.

No ontology class inference is required.

### `identifier-filter`

A scoped catalogue identifier can be queried when namespace + literal/code are supplied and the native corpus exposes it.

Example: `{authority: "museum-X", value: "12345"}`.

### `metadata-filter`

Some provenance/source metadata can be filtered explicitly if the native corpus exposes the metadata field. That still does not make the URL/DOI a semantic pivot.

### `explanation-only`

Locator/reference links are explanation/navigation only unless a separate native query contract is defined.

## 7. Mapping assessment versus identity strength

Do not reuse every semantic mapping assessment for every reference kind.

### Semantic pivot / authority value

ontoTF's reviewed mapping assessment can be meaningful for native concept/value -> semantic/authority concept correspondence:

- `exact`, `close`, `broader`, `narrower`, `related`, `ambiguous`, `native-only`, `unsupported`.

But authority-value mappings do **not** automatically enter the common semantic reverse index. Their reference kind and query role remain authority-specific.

### Entity identity

Entity identity needs a different controlled assertion, conceptually:

- `same-entity`;
- `probable-same-entity`;
- `related-record`;
- `ambiguous-identity`.

Set-theoretic `broader`/`narrower` does not describe identity.

### Catalogue identifiers

Identifier equality is scoped by issuer/namespace. Two equal strings from different institutions are not equal identifiers.

## 8. Publication relation policy

R-017 keeps runtime review state separate from RDF publication predicates.

### SKOS

AAT and PeriodO concepts may participate in SKOS mapping relations only where the published/native concept representation and mapping semantics justify it. ontoTF must not mechanically translate runtime `exact` -> `skos:exactMatch`.

A native literal `material="clay"` is not itself a SKOS Concept merely because it maps to an AAT concept.

### OWL identity

`owl:sameAs` is exceptional and should be used only when genuine identity of RDF individuals/resources is established. Similar catalogue records, textual witnesses, editions and physical carriers are not automatically `owl:sameAs`.

### Identifiers/provenance

Catalogue identifiers should be published through the chosen domain model's identifier pattern (e.g. CIDOC CRM identifier modeling where appropriate), not through SKOS mapping predicates.

Source/provenance references may use provenance/source relations in generated RDF where justified; this does not affect runtime semantic-pivot meaning.

## 9. Authority lifecycle and reproducibility

Authority systems can evolve independently of corpus mappings.

Required provenance includes, depending on authority:

- authority/vocabulary ID;
- record/concept ID or URI;
- snapshot/release/retrieval identity;
- retrieved/accessed time as audit provenance;
- licensing/redistribution policy;
- mapping evidence/review;
- supersession/deprecation information if known.

For Getty, persistent numeric IDs are designed to disambiguate vocabulary records, while data releases are updated regularly. ontoTF should prefer persistent concept identity plus locked/retrieval provenance rather than English labels.

For PeriodO, stable ARKs identify exact scholarly period definitions; source authority identity remains part of explanation.

## 10. Agent-facing explanation

Compact explanation should show:

```json
{
  "reference_kind": "authority-value",
  "authority": "PeriodO",
  "reference": "http://n2t.net/ark:/99152/...",
  "native_binding": "period=...",
  "query_role": "authority-value-filter",
  "assessment": "close",
  "semantic_pivot": null
}
```

For semantic targets:

```json
{
  "reference_kind": "semantic-pivot",
  "target": "...OLiA...Noun",
  "query_role": "semantic-constraint"
}
```

For identifiers:

```json
{
  "reference_kind": "catalogue-identifier",
  "issuer": "museum/catalogue namespace",
  "value": "...",
  "query_role": "identifier-filter"
}
```

An agent should never have to infer role from URL hostname or string shape.

## 11. P-003 / normalized IR inputs

P-003 must distinguish at least:

- `semantic projections` — ontology pivot targets with target kind/role/assessment;
- `authority references` — vocabulary/value resources with authority identity and value mapping assessment;
- `identity links` — native entity <-> external entity record with identity strength;
- `identifiers` — scoped literal/code + issuer;
- `provenance/source links`;
- `locators`.

Required indexes should likewise be separate:

```text
semantic target -> native semantic plan

authority resource -> native authority-value filter

external entity identity -> native entity

issuer + identifier -> native entity/value
```

Do not put all four into one reverse lookup keyed only by URI/string.

## 12. Research prototype contract

A non-production validator/resolver prototype should test:

1. semantic pivot can produce semantic constraint;
2. authority value cannot masquerade as semantic pivot;
3. reviewed authority-value binding can produce authority filter;
4. unmapped AAT/PeriodO URI is informative-only;
5. entity identity requires explicit identity strength;
6. `same-entity` may produce identity filter when native selector exists;
7. `related-record` cannot substitute for identity;
8. catalogue identifier requires issuer/namespace;
9. equal literal identifiers under different issuers are distinct;
10. provenance DOI/URL is explanation-only by default;
11. locator URL is explanation-only;
12. native lexical key cannot become external lexical identity by string equality;
13. native period label cannot map to PeriodO by label equality;
14. native material label cannot map to AAT by label equality;
15. `owl:sameAs` is rejected for non-identity reference kinds;
16. SKOS mapping predicates are rejected for scoped identifiers/source links;
17. authority mapping assessment does not automatically create semantic reverse capability;
18. external URI hostname/type heuristics never infer role.

## 13. Non-goals

R-017 does not:

- select a universal place authority;
- require AAT/PeriodO for every corpus;
- convert every external reference to RDF;
- assert `owl:sameAs` from matching labels/IDs;
- define production schema field names;
- replace CIDOC CRM/OntoLex/OLiA semantic roles with authority vocabularies;
- make provenance URLs executable semantic concepts.

## 14. Acceptance trace

- [x] semantic-pivot targets separated from authority/identity/identifier/source/locator references;
- [x] ORACC, TLHdig, Pseudepigrapha and linguistic negative controls covered;
- [x] AAT and PeriodO roles defined without making them universal backbones;
- [x] direct authority/identity query conditions defined;
- [x] publication relation constraints defined without SKOS/OWL abuse;
- [x] agent explanation fields defined;
- [x] exact P-003 IR/index inputs identified;
- [x] executable prototype test contract specified.

## Review targets

A fresh logically-independent reviewer should challenge especially:

1. whether the six reference kinds are minimal and non-overlapping enough;
2. whether authority-value mappings should use ontoTF mapping assessments at all;
3. whether entity identity deserves its own strength vocabulary;
4. whether AAT/PeriodO direct filtering is separated cleanly from semantic-pivot resolution;
5. whether real ORACC/TLH/Pseudepigrapha examples are characterized correctly;
6. whether Getty persistent-ID and PeriodO scholarly-definition behavior is represented accurately;
7. whether publication relation restrictions are too strong/weak;
8. whether the P-003 reverse-index separation is sufficient to prevent another generic `external_target` collapse.