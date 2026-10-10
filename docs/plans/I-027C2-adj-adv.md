# I-027C2 research-plan / TDD / adversarial review

**Issue:** #288. **Research:** `docs/research/I-027C2-adj-adv.md`.

1. RED: first commit tests for two `0.4.0` versioned corpus profiles with `Adjective` and `Adverb` POS-class targets in their pinned ontology locks, validated exact `word.sp=adjv/advb` value predicates, untouched reviewed `0.3.0` Noun/morphology/Verb assets and no ExtraBiblical implicit release. Negative controls forge selector feature `pdp`, node type `lex`, category `verb` and evidence/review binding.
2. GREEN: clone 0.3.0 resources byte-identically within 0.4.0 for unchanged mappings and components. Supply new original-source normalized evidence and OLiA class evidence records with canonical RFC8785 content digests. New ontology `lock-linguistic-0.4.0.json` reuses immutable OLiA snapshot with two additional terms.
3. Implement a separately named explicit versioned loader for the adjective/adverb release; do not retroactively change `load_production_verb_bundle` or `load_production_linguistic_bundle`. Compile exact IR for a 2-corpus, 2-target matrix.
4. Review new mapping and projection semantic v2/v1 digests and their `reviewed_mapping_digest` pins against the *repo canonical hashing* algorithm; independently verify ontology RDF class declarations and corpus glosses. Do not blindly inherit BHSA/Syriac semantics across corpora.
5. Make two immutable coverage successors from latest BHSA/Syriac 0.3.0 **coverage** manifests, adding only two new exact target dispositions each. Preserve BHSA 27 native-only stem reviews and Syriac outside-denominator `ls="prop"` gap. Deterministic offline builders with `--check`.
6. Add focused GitHub Actions Python 3.10/3.12 and full exact-head suite, packaging tests and negative selector/evidence controls.
7. Post independent adversarial review grounded in pinned original source, pinned ontology OWL, real R-005 inventories, exact code and coverage. Merge only if *all checks for final head* green. Parent #264/#283 remain open; update current queue only via a separate snapshot after release.

Do not fake content digests, and do not claim that the 0.1.1 published wheel carries this new development-only profile.
