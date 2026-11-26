# TLHdig morphological analysis mapping (#444)

## Research, scope and gates

The pinned TF 0.4.0 inventory (e954600d9f9cc7f16570729813cf6bf3954b8f6d) has 1,357,004 populated `analysis.morph` and 1,171,124 populated `analysis.stemclass`. All 15 observed `analysis.pos` labels have a disposition. These are candidate-analysis occurrences, not word tokens. The existing ontology catalog can express whole source tags with multiple positive ontology targets; individual component meanings must be proved, not inferred from punctuation or string similarity.

Source references:
- [Data model](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/data-model.md), [morph](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/features/morph.md), [stemclass](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/features/stemclass.md), [field4_kind](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/features/field4_kind.md), [selected](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/features/selected.md).
- [HFR annotation principles](https://hethport.net/HFR/annotation.php?lang=EN), [HFR protocols](https://hethport.net/HFR/doku.php?lang=EN), [real annotated examples CTH 573.80](https://hethport.net/txhet_hdivt/partitur.php?lang=DE&xst=CTH+573.80).

HFR annotates context-dependent paradigm positions; syncretism, logographic forms and automatically proposed alternatives are explicit source properties. D/L cannot be asserted simultaneously as exact dative and locative solely from the slash. Word-level selection cannot be inferred merely from a candidate tag, and source selected edges may select multiple alternatives. Stemclass numbers identify source paradigms, not universal morphosyntactic categories. Preserve original values and distinguish clitic features from main analysis features.

Plan:
1. Run existing scoped-census workflow on the actual pinned data; obtain domain sizes and top raw values with counts of distinct selected candidate nodes, not duplicated selected edges. Confirm known totals and endpoint types. No change to measured dashboard scope yet.
2. Review common single tags against HFR documented morphology and exact pinned OLiA definitions. If a composite selector denotes a specific intersection, individual broad class relations can be qualified; do not make exact bidirectional equivalence or collapse alternatives. Preserve raw tag ambiguity and source selection.
3. Add source-version-scoped XML in a small batch, tests first for counterexamples and exact execution guard. Do not invent a tag parser or a parallel mapping registry. Update applicability/denominator only with a complete justified measured domain, not a top-60 sample.
4. Actual TF query checks and independent adversarial review before final head CI and merge.

This draft is evidence generation, not a completed mapping contribution.

## Independently decoded native feature evidence (before implementation)

The Git blob of `tf/0.4.0/morph.tf`, b138fbf371e985a2cabac9df82fb87438ba01422, was decoded by expanding explicit comma-separated node/range lists and counting implicit one-node records. 1,626,939 assignments including 269,935 empty strings; 1,357,004 populated assignments in 4,581 distinct raw values. The largest raw value (234,935) is a 13-way unmarked-logogram alternative list. The most frequent simple tags include 2SG.IMP (71,845), 3SG.PRS (62,630), D/L.SG (37,672), 3PL.PRS (32,545). These are candidate records, not selected word tokens. This agrees with the existing actual scoped census population; the selected-candidate join is still running.

Official [HFR glossing abbreviation list](https://hethport.net/HFR/material/Abkuerzungen-morph-Glossierung.pdf), pp. 1–5, and [annotation principles](https://hethport.net/HFR/annotation.php?lang=EN) inspected. Verified actual class definitions in the pinned OLiA reference blob 5c5e8bda93eaeab2940472a167ff8d3107be8d43. OLiA MediopassiveVoice is a union of middle and passive, not both individual properties; CommonGender's reference examples are two-gender systems, so Hittite C is close. Present/Past are absolute tense classes, while HFR labels inflectional paradigms, so close. Composite tags with explicit number/person/case are narrower than individual category classes; unambiguous single POS/case labels can be exact at candidate level. Keep D/L case unresolved while mapping explicitly shared number, and leave ambiguous multi-tag examples native-only. No selected-word inference. First tests are written before XML changes; actual RED execution unavailable locally.

## First reviewed mapping batch

48 raw selectors (41 positive, 7 native-only), 121 mapping declarations; 359185 candidate annotations with positive mappings and 277107 reviewed native-only annotations out of 1,357,004 populated morph annotations. This is measured in raw feature assignments, not word tokens. The complete raw vocabulary (4,581 values) exceeds the dashboard's bounded categorical domain; do not pretend the top-value sample is a complete denominator. The scope remains analysis.morph and the current scoped dashboard remains unchanged until the accounting of open/composite domains is researched.

| Native value | Occurrences | Disposition |
|---|---:|---|
| ADV | 18534 | exact Adverb |
| POSP | 3631 | exact Postposition |
| CNJ | 2284 | exact Conjunction |
| QUANcar | 3545 | exact CardinalNumber |
| ABL | 10644 | exact AblativeCase |
| INS | 3887 | exact InstrumentalCase |
| ALL | 854 | exact AllativeCase |
| 2SG.IMP | 71845 | narrower Second; narrower Singular; narrower ImperativeVerb; narrower ImperativeMood |
| 3SG.PRS | 62630 | narrower Third; narrower Singular; close Present |
| 3PL.PRS | 32545 | narrower Third; narrower Plural; close Present |
| 3SG.PRS.MP | 16785 | narrower Third; narrower Singular; close Present; close MediopassiveVoice |
| 3SG.PST | 12987 | narrower Third; narrower Singular; close Past |
| 3PL.PRS.MP | 7411 | narrower Third; narrower Plural; close Present; close MediopassiveVoice |
| 1SG.PRS.MP | 5101 | narrower First; narrower Singular; close Present; close MediopassiveVoice |
| 3SG.IMP | 5078 | narrower Third; narrower Singular; narrower ImperativeVerb; narrower ImperativeMood |
| 3PL.PST | 4698 | narrower Third; narrower Plural; close Past |
| 1SG.PST | 4041 | narrower First; narrower Singular; close Past |
| 2SG.PRS | 3662 | narrower Second; narrower Singular; close Present |
| 2PL.IMP | 3326 | narrower Second; narrower Plural; narrower ImperativeVerb; narrower ImperativeMood |
| 3SG.PRS.IMPF | 2870 | narrower Third; narrower Singular; close Present; close ImperfectiveAspect |
| 1SG.PRS | 2754 | narrower First; narrower Singular; close Present |
| 3SG.IMP.MP | 2515 | narrower Third; narrower Singular; narrower ImperativeVerb; narrower ImperativeMood; close MediopassiveVoice |
| 3PL.PRS.IMPF | 2236 | narrower Third; narrower Plural; close Present; close ImperfectiveAspect |
| 2SG.PST | 2176 | narrower Second; narrower Singular; close Past |
| 3PL.IMP | 1556 | narrower Third; narrower Plural; narrower ImperativeVerb; narrower ImperativeMood |
| 1PL.PST | 1225 | narrower First; narrower Plural; close Past |
| 1PL.PRS | 740 | narrower First; narrower Plural; close Present |
| 2PL.PRS | 611 | narrower Second; narrower Plural; close Present |
| 2PL.PST | 137 | narrower Second; narrower Plural; close Past |
| D/L.SG | 37672 | narrower Singular |
| ACC.SG.C | 8025 | narrower Accusative; narrower Singular; close CommonGender |
| PTCP.NOM.SG.C | 11122 | narrower Participle; narrower Nominative; narrower Singular; close CommonGender |
| GEN.SG | 3806 | narrower GenitiveCase; narrower Singular |
| PTCP.ACC.SG.C | 2965 | narrower Participle; narrower Accusative; narrower Singular; close CommonGender |
| NOM.PL.C | 1967 | narrower Nominative; narrower Plural; close CommonGender |
| NOM.SG.C | 1337 | narrower Nominative; narrower Singular; close CommonGender |
| GEN.PL | 1199 | narrower GenitiveCase; narrower Plural |
| ACC.PL.C | 507 | narrower Accusative; narrower Plural; close CommonGender |
| D/L.SG.C | 234 | narrower Singular; close CommonGender |
| D/L.PL | 18 | narrower Plural |
| D/L.SG.N | 25 | narrower Singular; narrower Neuter |
| NEG | 5947 | native-only |
| PREV | 2591 | native-only |
| STF | 3545 | native-only |
| { a → 3SG.PRS} { b → 2SG.IMP} | 15174 | native-only |
| { a → …:ABL} { b → …:INS} | 8031 | native-only |
| { a → GEN.SG} { b → GEN.PL} { c → D/L.PL} | 6884 | native-only |
| { a → NOM.SG(UNM)} { b → ACC.SG(UNM)} { c → NOM.PL(UNM)} { d → ACC.PL(UNM)} { e → GEN.SG(UNM)} { f → GEN.PL(UNM)} { g → D/L.SG(UNM)} { h → D/L.PL(UNM)} { i → ALL(UNM)} { j → ABL(UNM)} { k → INS(UNM)} { l → VOC.SG(UNM)} { m → VOC.PL(UNM)} | 234935 | native-only |

## Second batch research and acceptance

Loaded census job [140033142601](https://github.com/alexsosn/ontoTF/actions/runs/45855637678/job/140033142601) confirms 4,581 populated raw morph labels and 339,019 populated morph values on 461,223 distinct selected analysis nodes; the source has words with up to 14 selected analyses. A whole alternative list can carry a shared property when every explicitly listed alternative includes it, but cannot resolve a difference among alternatives. Review six such native selectors against HFR definitions already documented above: PTCP shared across NOM/ACC/INDCL or STF; common gender shared across NOM/ACC.COLL.C; plural and common gender shared across NOM/ACC.PL.C; singular and past shared across 2SG/3SG.PST; third person shared across 3SG.PRS/3SG.PST/3PL.PRS. None is exact equivalence with an individual OLiA class. Collective number is left unasserted. Three mixed lists with no established shared relevant category are ambiguous, not negative evidence that no ontology is applicable. In particular HURR.ESS||HITT.D/L.SG cannot be treated as Hittite singular or one case. Source frequency and selected frequency are taken from the loaded-TF join, and no selected-word claim is made. Write regressions before XML implementation, re-run the loaded-data smoke, and independently compare expected shared properties and counts against raw records. Preserve CRMtex additions from merged #437.
