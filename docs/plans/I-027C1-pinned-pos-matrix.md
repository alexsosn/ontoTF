# I-027C1 plan — pinned native POS evidence reconciliation

**Issue:** #284. **Research:** `docs/research/I-027C1-pinned-pos-matrix.md`.

## TDD / implementation gates

1. RED: tests before builder/frozen output. Synthetic source definitions for BHSA Markdown and Syriac grammar, and bz2-compressed MQL enum; test duplicate code, missing inventory code, corrupt compressed source, checksum/size mismatch, non-UTF-8 bytes and source-only code drift.
2. GREEN: dependency-free offline builder `scripts/research/build_i027c1_pos_matrix.py`, reading three explicitly supplied pinned source paths. Load only the committed R-005 inventory JSON. Use Git repository revisions and immutable MQL blob identity hard-coded in source policy.
3. Scope: one row per (corpus, observed native `sp` code), sorted deterministically. Expected totals: BHSA 14, Syriac 10, ExtraBiblical 14 = 38. Include source line numbers, source labels only when explicitly provided, TF observation count, and separate original/target revision identities.
4. Do not derive an English gloss for MQL numeric enum entries. No `common_target`, OLiA class, or `exact` authority may be emitted by the matrix.
5. CI: exact pinned checkout of three upstream repositories, test source SHA/revision and run `--check` against the committed generated artifact on Python 3.10/3.12. Any changed corpus source or missing row fails closed.
6. Independent adversarial review must compare the matrix to actual BHSA/Syriac source and original MQL evidence; check source-only/missing observations and count arithmetic.
7. Expected-head merge only after focused and full repository test CI are green. Then select a *bounded positive* POS mapping slice for #283, not a broad automatic mass mapping.
