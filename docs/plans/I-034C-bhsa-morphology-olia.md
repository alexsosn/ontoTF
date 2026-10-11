# I-034C — batch-first BHSA morphology mapping TDD

**Research:** `docs/research/I-034C-bhsa-morphology-olia.md`. **Issue:** #264. No new workflow or per-row issue.

1. **RED:** Commit `tests/i034c/test_bhsa_morphology_semantics.py` before data. It requires a nonexistent 29-row research artifact and exact IDs matching the original BHSA 0.4.0 219-item denominator. Assert exact target URIs/OLiA source lines, 12 positives and 17 native-only, source-feature distinctions, no released authority.
2. **GREEN:** Commit one bounded machine-readable 29-row source/ontology evidence ledger `docs/research/data/i034c/bhsa-morphology-olia.json`. Individual row rationales, original source pins and declaration lines; no new generic pipeline code. Proof that every listed OLiA target exists as an `owl:Class` in the actual packaged immutable OLiA snapshot. Specific suffix-vs-host semantics and Hebrew tense caution in rationales.
3. Run exact-head Python 3.10 and 3.12 full suite, no reduced test targets or synthetic approval. **Skeptical** original-source/OWL/denominator review, record findings, fix and re-review on SHA as needed.
4. SHA-guarded merge if green. Newly **proposed** class alignments = 12; newly **installed** targets remain 0 until protected batch attestation and versioned release, which is separate from doing source-grounded mapping decisions.
