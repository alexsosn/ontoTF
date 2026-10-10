# I-027B2 research — independent Syriac and ExtraBiblical Verb semantics

**Issue:** #277 (child of #274 / #264)  
**Stage:** research, not production mapping authority

## Syriac: positive source basis

The pinned Syriac TF inventory `docs/research/data/generated/r005/syriac.json` identifies `sp` as *part of speech of a word*, applies only to `word` nodes and observes `verb` 56,797 times at target corpus revision `bb0eaa7e21b020a26b7566d2e495da9b1f84a919` (TF 0.9).

The historical ETCBC grammar source `ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6:data/lib/syriac/word_grammar` explicitly declares `sp: "part of speech"` with `verb: "verb"`, and generates `sp=verb` through `exist(vbe)`. Unlike the BHSA code, Syriac `sp` here has word-level scope by construction. The rule source is a distinct repository/revision and its relationship to the pinned rendered TF data must be documented; do not silently replace its revision with the TF revision.

**Research disposition:** likely reviewed-exact candidate `word.sp="verb" -> olia:Verb` at the annotation-category level, pending target-source/projection evidence and release validation.

## ExtraBiblical: evidence gap remains

The pinned ExtraBiblical TF inventory `docs/research/data/generated/r005/extrabiblical.json` identifies `sp` on word nodes and records 6,100 observed `verb` values at TF version 0.2 and revision `9a56288e6777bad6328856acf055c780e65dd5d9`. Historical R-011 proposes an exact `olia:Verb` mapping, but that is explicitly research-only authority.

Unlike BHSA, the pinned `ETCBC/extrabiblical` tree does **not** carry human-readable `docs/features/sp.md`. Its source `source/0.2/extraBiblical.mql.bz2` is compressed MQL; a source enum/value definition or an equivalently explicit verified encoding reference is required before publishing an independently reviewed *exact* mapping.

**Research disposition:** evidence-gated candidate, not an automatically promoted exact mapping.

## Shared target

The vendored pinned OLiA core `olia.owl` at revision `d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6` explicitly contains `<owl:Class rdf:about="http://purl.org/olia/olia.owl#Verb">`, subclass of `olia-top#MorphosyntacticCategory`. This class is an annotation reference class; it does not imply shared verbal-stem, morphological voice, tense, aspect, mood or argument-structure equivalence across corpora.

## Recommended execution

1. Syriac: ship a separately versioned `0.3.0` semantic bundle and one-item production accounting successor, **preserving** the unrelated unresolved `ls="prop"` outside-denominator gap.
2. ExtraBiblical: extract and review the `part_of_speech_t` native enum from the pinned compressed MQL (or an equally strong source). Only if `verb` genuinely denotes verb at `word` level should an exact class projection be released.
3. Keep old 0.1.0/0.2.0 profiles immutable and verify every new content digest, ontology lock, parent identity and mapping review.
4. TDD RED → GREEN → all exact-head tests → fresh logically-independent skeptical reviews for both stages.

## Decision

**Syriac: GO to implementation planning. ExtraBiblical: HOLD exact mapping until source semantics verified.** This is a specific evidence gate, not a reason to divert the dev loop into unrelated formal-semantics research.
