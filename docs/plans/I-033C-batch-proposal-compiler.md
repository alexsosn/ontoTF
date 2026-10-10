# I-033C — research → plan → RED → implementation → independent review

**Issue:** #296. Research: `docs/research/I-033C-batch-proposal-compiler.md`.

1. **RED first:** tests demand an offline cohort compiler and one ledger. For four *already published* exact Adjective/Adverb mappings, compute Mapping V2 and Projection V1 semantic digests and compare to immutable published release data. Test duplicate, source/evidence tampering, forbidden claimed reviews and production-schema refusal.
2. **GREEN:** add `src/tfont/batch_proposals.py`, a closed-shape source/ontology-registered proposal ledger at `src/tfont/resources/batch_pilots/i033c-adj-adv-proposals.json`, and a CLI `scripts/mappings/build_proposals.py --check` generating a compact reproducible report under `docs/research/data/generated/i033c`.
3. Contract is *not* self-authorizing: intentionally omit all `review` objects; do not let unreviewed proposals be loaded via registry. No changes to historical profile, source evidence, ontology lock, production coverage or released Mapping v2.
4. Validation is anchored in the actual **current source** evidence, original corpus revisions, target OWL class definition and vendor-locked OLiA model; value must appear in source `source_definitions`. No cross-corpus string heuristics. RFC8785 hashing uses the production `semantic_digest_v2` functions.
5. CLI validates from installed packaged resources and has deterministic `--check`; no new GitHub Actions workflow for this ticket. Exact-head full suite runs both Python 3.10/3.12 and focused tests are part of discovery.
6. Independent skeptical review must independently compare all four hashes to *existing immutable published artifacts*, check negative cases and explicitly call out the missing independent approval/release writer. Do not merge until CI green.
7. Next issue under #290: independently verifiable batch approval receipts + immutable release writer/coverage delta. Require review of changed **ledger rows** instead of one PR per mapping.

**Throughput metric:** four reviewed semantics reproduced from one small ledger; no new per-value workflow, profile version or denominator snapshot. This is a compiler-parity proof, not yet full production-throughput gain.
