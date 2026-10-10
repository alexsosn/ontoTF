# I-033E4 implementation — research/plan/TDD

**Issue:** #306.

1. RED: test fixture uses real installed BHSA/Syriac/ExtraBiblical coverage manifests. Require generic `build_published_coverage_delta()` and `load_published_coverage_delta()`, deterministic small data-only delta and exact reconstructed equality to existing snapshots. Explicitly require `native-only` remaining non-common.
2. RED adversarial controls: no-op release, unknown corpus or path traversal, forged target/denominator signatures, changed source ids/delta per-item mapping, dropping or modifying inherited production review, changed research, item IDs/kinds, gap/exclusion and target corpus pins.
3. GREEN: one `src/tfont/coverage_deltas.py` module, composed from existing packaged `coverage` validator and canonical JCS digest primitives; no changes to historical source manifests.
4. Add no new workflow: canonical exact-head `full-suite.yml` discovers the new focused unit tests on Python 3.10 and 3.12. A local red gate before implementation is sufficient.
5. Fresh skeptical source/data review, then exact-head all green CI and expected-head merge.
6. Explicit future #303 integration gate: a delta *derived from new untrusted JSON* is never independently approved; only a verified, externally authenticated and sealed review can publish novel production authority. This PR supports parity/read API only.
