# I-033F — TDD plan for read-only TF observation of uninstalled overlay

**Issue:** #303. Research: `docs/research/I-033F-native-overlay-smoke.md`.

1. RED add `tests/i033e/test_native_overlay_smoke.py` using actual ten native POS selectors, real frozen pack builder and installed BHSA/Syriac parent manifests. The mock TF API exposes `Fall()`, `F.otype.s('word')` and `F.sp.v(node)` so no source claims are invented. Require accepted-only results, deterministic counts, unchanged packet, `shared_target_count=0`, absence of release authority.
2. RED negative cases: wrong corpus, wrong parent/TF-component SHA, absent/unknown `sp`, missing `word`, malformed/nonmonotonic/repeated node IDs, feature read error, invalid feature value types, tampered pack, a forged positive projection, no accepted rows for requested corpus, and evidence/source digest mismatch. Ensure one pass over nodes for a corpus rather than O(n_words × n_mappings).
3. GREEN `src/tfont/native_overlay_smoke.py` read-only streaming filter using existing verified pack + existing loaded-context types, with fail-closed typed exceptions and no TF import, auto loading or network. Return only minimal observations; never a `SemanticSourceBundle`, registry entry or certificate.
4. Exact-head Python 3.10/3.12 full-suite and all workflow checks. Conduct logically independent adversarial review of failure modes and real original corpora source pins; correct and re-review final SHA. Merge only with verified tests, exact-head SHA and expected-head merge.
5. Advance #303 with an execution *capability* but do not count any new installed or shared ontology mappings. Follow-up must exercise real pinned TF corpus API and signed handoff, install immutable registry release, verify sparse coverage and wheel.
