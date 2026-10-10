# I-033A — research → plan → TDD → parity implementation

1. Research actual released `bhsa/syriac/extrabiblical/0.3.0/mappings/verb.json` and `p004-i027b1-bhsa-verb-v1/bhsa.json`; retain pinned external source and OLiA evidence identities. Do not change released files.
2. RED: tests expect deterministic compiler output for three real reviewed POS records and one native-only cohort of 27, check independent canonical digests, fail-closed modified native selector, target term, evidence digest, missing historical source, duplicate item, and forbidden unauthorized mapping.
3. GREEN: add `src/tfont/batch_compiler.py`, minimal explicit JSON input ledger and `scripts/mappings/build_parity_pilot.py --check`; prefer compatibility with existing Mapping v2 schema. The script requires no network or corpus download.
4. Only import historical excluded review/rationale fields **after** exact compiled semantic digest equality and audit-friendly field matching; never trust a new decision's self-review.
5. Cross-check against historical published artifacts. Output a reproducible summary of counts and hashes; don't emit 2500-line coverage manifest, copy unchanged noun/profiles, or modify production loaders.
6. Focused Python 3.10/3.12 tests and exact-head full repo suite; independent skeptical review of real data, false confidence and unknown external-approval risks. Merge only if CI and the review pass. Follow-on implement independent approval receipts and generation of a genuine new release for 10-50 decisions without per-item boilerplate.
