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
