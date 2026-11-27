# R-002 review reconciliation: formal mapping semantics and evidence policy

**Status:** normative amendment to `R-002-ontology-governance.md` for this research PR  
**Recorded:** 2026-09-05  
**Reason:** resolves blocking independent-review findings on PR #9

Where this amendment conflicts with the earlier R-002 draft, **this amendment supersedes it**. The final design ticket should fold these rules into one normative mapping contract.

## 1. Mapping strength and RDF relation are different layers

The original R-002 draft used SKOS mapping names too broadly. ontoTF needs a stable, formalism-neutral **mapping assessment** for agents/humans and a separate, target-appropriate **publication relation**.

Every ontoTF mapping is therefore a reified mapping assertion with at least:

```yaml
id: bhsa.word.sp.subs
source: <native corpus selector>
target: <external term URI>
assessment:
  strength: exact | close | broader | narrower | related | ambiguous | native-only | unsupported
formalization:
  relation: <optional RDF/OWL predicate or mapping pattern>
  status: asserted | not-asserted
```

The `assessment.strength` vocabulary controls ontoTF query planning and UX. It **does not by itself entail** a particular RDF predicate.

This allows R-003 to keep one comprehensible resolution vocabulary while R-002 remains faithful to the formal model of each target ontology.

## 2. Cross-formalism publication rules

### 2.1 OWL/RDFS class targets such as OLiA

OLiA's Reference Model uses OWL classes/properties and its Linking Models conventionally connect annotation models to reference terms with RDFS/OWL relations such as `rdfs:subClassOf` and `rdfs:subPropertyOf`.

ontoTF must not emit `skos:exactMatch`, `skos:broadMatch`, etc. directly merely because the target is an OLiA class.

For an OWL class/property target:

- use `rdfs:subClassOf` / `rdfs:subPropertyOf` when the native ontoTF-side modeled class/property is genuinely a specialization;
- use `owl:equivalentClass` / `owl:equivalentProperty` only when logical equivalence is justified in both directions, including relevant domain/range/extension assumptions;
- otherwise keep the reified ontoTF mapping assertion and **do not emit a stronger OWL axiom** merely to mirror the UI strength;
- mapping assessments such as `close` or `related` normally remain annotations/reified assertions rather than OWL subsumption axioms.

A ontoTF `strength: exact` can therefore mean “reviewed as exact for semantic query substitution in this profile” without automatically claiming global `owl:equivalentClass`.

### 2.2 SKOS concept targets

When both sides are legitimately `skos:Concept` resources in concept schemes, ontoTF may publish reviewed mappings using:

- `skos:exactMatch`;
- `skos:closeMatch`;
- `skos:broadMatch`;
- `skos:narrowMatch`;
- `skos:relatedMatch`.

Direction must be defined against ontoTF's source/target convention and tested. A human label such as “broader” is never sufficient to infer the RDF direction.

### 2.3 OntoLex lexical concepts

`ontolex:LexicalConcept` is a SKOS concept class, so SKOS concept mapping is appropriate for lexical-concept alignment where the resources really are lexical concepts.

Lexical entries, forms, senses and lexical relations themselves use the relevant OntoLex/LexInfo/VarTrans structures instead of being coerced into SKOS concepts.

### 2.4 CIDOC CRM and extensions

CIDOC CRM, CRMtex, LRMoo, CRMinf, CRMarchaeo and CRMsci are class/property ontologies. Alignments to them follow OWL/RDFS-compatible rules or remain reified ontoTF mapping assertions when no safe logical axiom exists.

ontoTF does not convert CRM classes into SKOS concepts for convenience.

### 2.5 External authority vocabularies

Getty AAT and PeriodO are used as controlled external concept authorities where applicable. Their native modeling/URI contracts are respected. ontoTF stores mapping assessment separately from whatever standards-conformant publication relation is appropriate.

## 3. Query semantics are governed by assessment, not RDF entailment

The POC runtime should not require a reasoner to decide whether a mapping is executable.

A reviewed mapping assertion contains a deterministic ontoTF assessment and applicability contract. R-003 may then implement:

- `exact` as executable in exact mode;
- `close`, `broader`, `narrower` only when the request explicitly permits the relevant approximation;
- `related` as informational/non-substitutive;
- `ambiguous`, `native-only`, `unsupported` as non-executable under exact semantic substitution.

The generated RDF representation is publication/interchange evidence for the same mapping, not the runtime decision engine.

## 4. SAWS licensing classification corrected

The authoritative Sharing Ancient Wisdoms ontology page establishes the SAWS ontology/version/PURL and its historical FRBRoo-oriented model, but the ontology page inspected for R-002 does not establish a clear reusable ontology license.

Therefore ontoTF records SAWS as:

```text
status: reference/prior-art only
license: not established from authoritative ontology distribution inspected
reason: licensing ambiguity + legacy FRBRoo-era modeling + no need to make it normative for the POC
```

Do **not** state that the SAWS ontology itself is known to be CC BY-NC-SA unless an authoritative rights statement for the ontology artifact is later found and pinned.

The consequence remains conservative: SAWS may inform terminology/research, but ontoTF must not copy/repackage its ontology terms as a normative dependency under an assumed license.

## 5. Local apparatus vocabulary is deferred

The earlier draft proposed ontoTF-local `VariationUnit`, `Reading`, `attestedBy`, and `explicitlyAbsentIn` terms. R-005 currently demonstrates those exact apparatus semantics robustly only in Pseudepigrapha-TF.

Peshitta `witness=A/B` and TLHdig-TF line-to-fragment `witness` are **related witness metadata**, not a second implementation of reading-at-locus attestation. They do not satisfy the draft's own recurrence criterion.

Decision for the POC foundation phase:

- do **not** mint apparatus-specific ontoTF domain terms yet;
- keep Pseudepigrapha-TF apparatus concepts as native/profile-local mappings and document the external ontology gap;
- continue evaluating CAO, SAWS and other textual-critical models as prior art/reference targets;
- mint a ontoTF-local apparatus term only after either:
  1. a second independent corpus requires the same semantic gap, or
  2. the term is demonstrably necessary for ontoTF's **mapping-contract infrastructure** rather than for one corpus domain.

This does not prevent the POC from querying Pseudepigrapha-TF native apparatus semantics. It only prevents premature standardization.

## 6. ontoTF-local infrastructure vocabulary remains allowed

The recurrence rule above applies to **domain concepts**. Some local terms may be unavoidable because they describe ontoTF itself rather than ancient-language scholarship, for example:

- mapping assertion;
- mapping assessment/strength;
- applicability/compatibility evidence;
- native selector;
- extent semantics such as `extent` vs technical `anchor` if no suitable external model expresses the TF distinction;
- profile/dependency identity.

Such terms may be minted when the design demonstrates that no existing open vocabulary expresses the required ontoTF contract cleanly. They do not need two independent corpora because their domain is the interoperability system itself.

## 7. OntoLex Morph and FrAC status policy

As of the research date, OntoLex Morph and FrAC are useful and actively maintained, but their final-community-report status was not established to the same level as the 2016 OntoLex core or the published Lexicog report in the evidence inspected.

Evidence to retain with the decision:

- OntoLex Morph public-review processing was still active in July 2026;
- OntoLex FrAC entered a second public-review period ending 30 August 2026;
- rendered specification pages may use mature/official wording, which is not by itself enough to infer W3C Community Group Final Report status.

Therefore for the initial POC:

- **Morph:** reference/experimental profile target, not normative core;
- **FrAC:** reference/experimental profile target, not normative core;
- record exact specification snapshot/commit/URI if a corpus mapping uses either;
- promote later through a governance PR when formal publication status, license and stability have been re-verified.

This is a status-management decision, not a claim that either model is technically unsuitable.

## 8. Web Annotation moves out of the core

W3C Web Annotation is useful for portable targeting/provenance of annotations, but R-005 does not require every ontoTF mapping to be serialized as a Web Annotation and the runtime is deliberately native-TF/Context-Fabric-first.

Decision:

- Web Annotation is a **supported optional publication/targeting profile**, not a mandatory ontology-core dependency;
- use it where external annotation exchange or robust target selectors justify it;
- do not require it for ordinary feature/value-to-ontology mapping bundles.

This keeps the common basis smaller while retaining an open standard when its targeting model is useful.

## 9. Reconciled support tiers

### Tier A — supported foundation vocabularies/models

Used when their domain applies; exact term/release locks still belong to a profile/release manifest.

- **SKOS — Simple Knowledge Organization System**: controlled concept schemes and mappings where resources are genuinely SKOS concepts;
- **OLiA — Ontologies of Linguistic Annotation**: linguistic reference categories and native-annotation-model alignment;
- **OntoLex-Lemon core**: lexical entries/forms/senses/concepts;
- **CIDOC CRM — Conceptual Reference Model**: cultural objects/events/provenance;
- **CRMtex**: written-text / inscription / writing-surface modeling;
- **LRMoo**: work/expression/manifestation/item and textual/bibliographic relationships;
- **CRMinf**: inference/argumentation/proposition provenance.

“Foundation” does not mean every corpus imports every ontology. A BHSA profile may need OLiA/OntoLex but no CRMtex; a manuscript profile may need CRM/CRMtex/LRMoo but little syntax.

### Tier B — supported optional domain profiles

- CRMarchaeo;
- CRMsci (current stable release must be pinned by the profile);
- LexInfo;
- OntoLex Lexicog;
- OntoLex VarTrans;
- Getty AAT;
- PeriodO;
- Web Annotation for publication/targeting.

### Tier C — experimental/reference targets

- OntoLex Morph;
- OntoLex FrAC;
- POWLA as structural prior art/alignment reference rather than runtime dependency;
- CAO (Critical Apparatus Ontology) as apparatus prior art;
- SAWS as ancient-textual-transmission prior art with licensing not established for normative reuse from the evidence inspected.

The supported set is **tiered and open-ended**, not a permanently closed whitelist. Promotion between tiers requires evidence for governance, licensing, URI stability, maintenance and actual corpus need.

## 10. License/openness rule

A normative/repackaged ontoTF dependency must have sufficiently clear rights for the way ontoTF uses/distributes it.

Classify every external resource independently as:

- **normative/repackaged** — license permits required redistribution/use;
- **linked normative** — stable public terms may be referenced by URI without repackaging ontology data, with usage rights sufficiently clear;
- **reference only** — useful prior art but licensing/status/stability is insufficient for normative dependency;
- **forbidden to redistribute** — rights explicitly prohibit the intended distribution.

“Open website” is not evidence of an open ontology license. Absence of a license is `unknown`, not permissive.

## 11. Version/deprecation rule retained and tightened

For every used ontology term a ontoTF profile/release records:

- stable term URI;
- ontology/model identifier;
- exact tested ontology release/version or immutable snapshot identity;
- release status (`official`, `stable`, `draft`, etc. as defined by that ontology project);
- license/reference classification;
- deprecation/replacement status when known.

Old profile releases remain reproducible against their recorded ontology lock. A newly deprecated term does not silently rewrite a historical mapping. A new ontoTF profile release may migrate the mapping with an explicit semantic diff and review.

## 12. Acceptance trace for review findings

- OWL-vs-SKOS cross-formalism rule: §§1-3;
- SAWS license corrected to unestablished: §4;
- apparatus-local terms deferred until recurrence/contract need: §§5-6;
- Morph/FrAC review-date evidence and experimental status: §7;
- Web Annotation made optional rather than core: §8;
- tiered/open-ended ontology support retained with a smaller foundation: §9;
- licensing/version/deprecation evidence strengthened: §§10-11.

A final independent reviewer must reconcile this amendment with accepted R-005 corpus evidence and R-003's final resolution vocabulary before R-002 merges.