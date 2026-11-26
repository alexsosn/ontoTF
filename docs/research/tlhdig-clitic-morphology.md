# TLHdig enclitic morphology — follow-up to #444 / #445

## Research and plan

Actual loaded TF census job 140033142601 on pinned TLHdig TF 0.4.0: 388,870 populated analysis.clitic_morph records, 822 distinct values, 24,896 populated on distinct selected analysis nodes. These are candidate-level feature observations, not distinct clitic tokens. The source [feature contract](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/features/clitic_morph.md) calls this the enclitic morphological tag; a raw string can be a chain or alternative set.

HFR [annotation handbook](https://www.hethport.uni-wuerzburg.de/HFR/material/Handreichung_Annotation.pdf), §1.3, gives CNJadd additive and CNJctr contrastive conjunctions, PPRO enclitic anaphoric pronoun, POSS enclitic possessive pronoun, REFL reflexive particle, QUOT quotative particle, FOC focus particle and OBP spatial particles. Real annotated examples include [IBoT 3.24](https://hethport.net/HFR/bascorp_xtx.php?d=IBoT+3.24&lang=EN&o=CTH+670) and [KUB 20.35](https://hethport.net/HFR/bascorp_xtx.php?d=KUB+20.35). The exact pinned OLiA OWL blob 5c5e8bda93eaeab2940472a167ff8d3107be8d43 was read directly: Conjunction defines a word linking syntactic constituents; Pronoun is a nominal pro-form; PersonalPronoun is irreflexive, and the general Particle class is explicitly discouraged. No ReflexiveParticle, QuotativeParticle or FocusParticle class exists in that reference. DiscourseMarker is a German syntactic-edge label; do not map sentence connectors to it. Do not equate enclitic reflexive particle to ReflexivePronoun.

Plan: explicit single-clitic and two reviewed alternative-set selectors; conjunction close due to clitic/word distinction, PPRO narrower Pronoun and invariant person/number/case, common gender close, D/L unresolved. POSS.3SG.ALL.SG related PossessivePronoun only; avoid confusing possessor and possessed number/case. Particle labels without a defensible target remain native-only. Chains with = are outside this batch; no host POS inference or exact execution. Test first, implement source-version-scoped rows, check actual frequencies and selected frequencies, independent adversarial review before merge. The complete clitic domain needs its own loaded census before adding it to dashboard coverage.

| Source value | Candidate assignments | Selected-analysis assignments | Positive |
|---|---:|---:|---|
| `CNJadd` | 105734 | 4716 | yes |
| `CNJctr` | 36985 | 7453 | yes |
| `PPRO.3SG.C.ACC` | 35383 | 368 | yes |
| `PPRO.3PL.C.ACC` | 15113 | 84 | yes |
| `PPRO.3SG.D/L` | 2014 | 60 | yes |
| `PPRO.3PL.D/L` | 1177 | 40 | yes |
| `{ R → PPRO.3SG.C.NOM} { S → PPRO.3PL.C.ACC}` | 40368 | 121 | yes |
| `{ R → PPRO.3SG.N.NOM} { S → PPRO.3SG.N.ACC} { T → PPRO.3PL.C.NOM} { U → PPRO.3PL.N.NOM} { V → PPRO.3PL.N.ACC}` | 7914 | 87 | yes |
| `POSS.3SG.ALL.SG` | 1567 | 11 | yes |
| `REFL` | 28174 | 765 | no |
| `OBPk` | 10964 | 2711 | no |
| `OBPs` | 10577 | 524 | no |
| `OBPst` | 8815 | 190 | no |
| `FOC` | 4925 | 1795 | no |
| `QUOT` | 3576 | 548 | no |
