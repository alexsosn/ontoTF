# I-033E10 research → plan → TDD → review

**Issue #333. Research:** `docs/research/I-033E10-versioned-mapping-supersession.md`.

1. RED: `tests/i033e10/test_supersession_red.py` from actual packaged BHSA v0.3.0 `Verb` class mapping/evidence/lock. Explicitly mark synthetic predecessor `native-only`, reconstruct canonical digest and original reviewed binding; positive successor is the unchanged published positive content stripped of review, so we test the *algorithm*, not forged new ontology semantics.
2. Negative tests: unchanged/same mapping identity, no old verified review, stale semantic mapping or projection digest, wrong source evidence digest, changed source feature or corpus/node/selector, silent promotion to non-exact, unvendored target/unknown RDF type, wrong ontology revision/snapshot, spurious extra active evidence, forged `release_authorized`, duplicated active selector. No network required.
3. GREEN: one reusable `src/tfont/mapping_supersession.py` pure validator/closed-shape preview; require caller to provide the installed-pinned source/ontology evidence documents explicitly and validate normalized record digests. Include exact historical and current mapping/projection digests; no new per-item profile, coverage or GH workflow.
4. Tests from `python -m unittest tests.i033e10.test_supersession_red tests.i033e10.test_supersession_adversarial`; full repository exact-head Python 3.10/3.12 through existing `full-suite.yml`; no additional workflow.
5. Genuinely independent adversarial review on exact head against source BHSA mapping/evidence, ontology lock, hardening around untrusted caller-supplied review state, and failure simulations. No merge if CI red.
6. Follow-on issue #329/#303: protected release installer authenticates prior immutable native-only Mapping v2 **in registry** and newer two-pass GitHub reviews; applies versioned retiring transition and sparse reviewed coverage upgrade atomically. Distinguish coverage-only I-027A verbal stem counts from actual Mapping v2 instances.

**Outcome:** reusable migration contract for one or hundreds of future native-only→exact changes, but zero new production mapping authority in this PR.
