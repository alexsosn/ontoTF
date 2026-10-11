# I-033E12 — multi-corpus native-only → exact composition preflight

Parent #329 / #303 / #300 / #290 / P-004 #202. Extends source-backed I-033E10 single-row and I-033E11 1–50 same-corpus preflight. This is **one architecture ticket**, not an ontology mapping ticket.

## Actual interoperability bottleneck

The installed I-033E3 review packet and I-033E7 accepted-only overlay handoff can cover 10–50 candidate POS rows from multiple corpora in one separately attested review, while `plan_native_only_supersession_batch` validates just a **single corpus/release identity**. A later native-only → exact promotion spanning BHSA and Syriac would thus need separate ad hoc orchestration, reintroducing per-corpus release ceremony. Aggregate multiple corpus-scoped batch preflights deterministically into one 1–50 accepted transition *preview* without relaxing per-corpus immutable-base checks.

## Real primary-source fixture

Published `bhsa/0.4.0` contains original-source-reviewed `word.sp=adjv` and `word.sp=advb` exact OLiA Adjective/Adverb; evidence `evidence:bhsa:word-sp-adj-adv-source` ties native codes to pinned `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da` `docs/features/sp.md`. Target observation counts: 10,141 adjv and 4,603 advb feature records, not necessarily word-only totals.

Published `syriac/0.4.0` also has reviewed `word.sp=adjv` and `word.sp=advb` with separate `evidence:syriac:word-sp-adj-adv-source`, native grammar `ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6`, and TF target revision `bb0eaa7e21b020a26b7566d2e495da9b1f84a919`. Observations: 9,001/5,290. All four are distinct `corpus_id + word.sp` selectors. Shared OLiA OWL class IRIs do not imply identical original annotation distributions.

**Crucial:** Fixtures must derive *synthetic* native-only predecessors by modifying the real published positive mappings, stripping their projections and OLiA evidence, and recalculating semantic digests. None of those hypothetical predecessors was historically published or independently approved. The preflight must never claim otherwise.

## Decision / trust boundary

- Bundle 1–50 accepted upgrades across 1–7 corpus cohorts. Each cohort has its own exact `corpus/version`, immutable active base and 1–50 proposed transitions. Rerun the existing **single-corpus** batch validator for each cohort, don't reinvent source/ontology/review policy.
- Assert global total <=50 and unique corpus cohorts. Sort by corpus and stable predecessor IDs and compute a canonical digest independent of input permutations.
- Emit only `authority=untrusted-multi-corpus-supersession-preview`, `release_authorized=false`, per-corpus source-bound preview data, and digest. Do **not** create a new `SemanticSourceBundle`, overwrite installed profiles, edit coverage, use GitHub approvals, or publish an active registry.
- Provide exact-input verification by recomputing the full record. If base releases collide, a corpus is repeated or any single transition is altered, fail closed.
- The genuine missing capability after this stage remains the protected authenticated *publisher* (#303) that resolves former active selectors and writes validated immutable release overlays. This PR must not be counted as production OLiA coverage.

## Research verdict

GO for a compact pure multi-corpus preflight and tests on actual pinned BHSA/Syriac mappings/evidence. Keep CI to the shared full suite, not a new workflow per ticket. Independent adversarial review on final head before merge.
