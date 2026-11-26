# Applicability research: ETCBC and CUC granularity

Follow-up to #431. Use the actual nine scoped inventories, not a feature-name
cross product. The selection describes the current review workload, not
guaranteed ontology targets. In particular, excluding a separate whole-feature
unit when its finite categories are evaluated does not prohibit a later
property mapping. The corpus annotation itself is never removed.

## Evidence and decisions

* [BHSA language](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/language.md)
  and [languageISO](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/languageISO.md):
  language names and ISO codes identify the same source language domain,
  not independent grammatical classes. Review the features rather than
  separate literals; no claim that OLiA contains a class for each language.
  ExtraBiblical and CUC language names receive the same treatment.
* R-005 BHSA metadata records 27 localized book title features with
  languageCode, languageEnglish and title-source provenance. They are
  textual naming/appellation review candidates (LRMoo), not SKOS concepts
  merely by virtue of being translated labels. The title source does not
  establish a cross-corpus Work or Expression identity.
* [BHSA freq_lex](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/freq_lex.md)
  and [rank_lex](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/rank_lex.md)
  respect disambiguated lexemes. The word-level `lexeme_count` metadata
  likewise denotes its lexeme occurrence count. These warrant lexical
  statistics review; this is not a claim that core OntoLex defines an
  exact frequency or rank property. Conversely
  [freq_occ](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/freq_occ.md)
  and [rank_occ](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/rank_occ.md)
  count consonantal representations without accents, ignoring homonyms.
  Retain these as native corpus-specific quantitative descriptors outside
  the present ontology category workload. ExtraBiblical `lexeme_count`
  is all zero (39,862 observations) and lacks the equivalent documented
  semantics; leave it unresolved rather than infer a missing lexeme graph.
* [dist](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/dist.md)
  measures distance to a mother object in different native units. Include
  actual daughter scopes and assess `dist_unit` and `mother_object_type`
  at feature granularity, not each literal as a distinct linguistic class.
  [is_root](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/is_root.md)
  documents true/false but acknowledges a missing definition. Route these
  two values for syntax review, without claiming exact OLiA correspondence.
  [number](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/number.md)
  varies in numbering context by node type; retain the ordinal as native
  navigation data. [instruction](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/instruction.md)
  and [pargr](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/pargr.md)
  warrant discourse review, but the codebook flags incomplete instruction
  interpretation.
* [g_word](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/g_word.md),
  [g_cons](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/g_cons.md)
  and [trailer](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/trailer.md)
  distinguish pointed, consonantal and interword representations. Assess
  digital text representation rather than physical glyph identity;
  graphic morpheme realization fields warrant linguistic feature/form
  review. The Syriac pinned R-005 feature headers explicitly identify
  realized morphemes `g_emf/g_nme/g_pfm/g_pfx/g_vbe/g_vbs`.
  [SyrNT transcription](https://github.com/ETCBC/syrnt/blob/dae3eb6ff62b9b272fb503646796c25d248175ce/docs/transcription.md)
  and R-005 headers distinguish Unicode, ETCBC and SEDRA representations.
  Do not identify a surface token with an OntoLex lexical entry.
* The [CUC codebook](https://github.com/DT-UCPH/cuc/blob/ad69400f5446e1c8217af01659c7c10ab00c015b/README.md)
  calls `cont` line continuation and defines editorial certainty,
  emendation and alternatives; `cont=continued` is a textual annotation
  review candidate, not an assertion of physical adjacency.
* Every word node type warrants token-category assessment, including
  [Peshitta](https://github.com/ETCBC/peshitta/blob/9850f5addade26f681334aa475570bef9b0b440a/docs/transcription.md):
  whitespace segmentation includes enclitics. Existing exact surface
  guards remain separate from unconditional word types; no blank slot
  becomes a positive token by virtue of this research selection.
* Closed source annotation families already reviewed at value granularity
  do not generate a second mandatory whole-feature mapping. This is an
  explicit granularity exclusion in the denominator, not a prohibition
  on source-supported property mappings. In particular no technical
  exclusion is inferred merely from a low observed cardinality.

## Residual uncertainty

The BHSA `suffix_gender/number/person` histograms exactly match their
respective `prs_*` histograms, but no matching suffix_* source codebook
was found and the GitHub large-file response for BHSA suffix_gender.tf
returned no content. Equal marginals do not establish row-wise equality.
ExtraBiblical has only NA in all six fields. Leave the undocumented
suffix_* features and values unclassified pending source-generation or
node-by-node verification, rather than double count or silently discard.
This leaves 3 feature scopes / 11 values in BHSA and 4 feature scopes /
3 values in ExtraBiblical unresolved (including ExtraBiblical lexeme_count).

CUC, Syriac, SyrNT, and Peshitta now have a review route or explicit
granularity disposition for every **currently inventoried** unit. This
does not establish exhaustive eligibility for all potential ontologies,
all uncollected value domains or conditional selectors.

The remaining main families are the three converter corpora
(Pseudepigrapha, TLHdig, ORACC); continue source-feature documentation
research there. No mapping runtime or mapping registry changes are
needed for this batch.
