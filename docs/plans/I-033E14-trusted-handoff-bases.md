# I-033E14 research → plan → TDD → test/review

1. Verify actual registry/current profile and reviewed immutable coverage sets for BHSA, Syriac, ExtraBiblical and original handoff hardcode (research file).
2. RED: new focused tests `tests/i033e14` for explicit base selection; disallow arbitrary corpus IDs, wrong coverage-set names, unsupported historical releases, detached candidate overrides and malformed protected registry. Existing ten-decision fixture must still recompose/verify exactly.
3. GREEN: protected packaged `resources/batch_release_bases/v1.json`; one strict pure base resolver; both `build_overlay_handoff` and `verify_overlay_handoff_integrity` call the same resolver. No corpus-specific branch or implicit timestamp/latest path scan.
4. Verify actual source corpus and coverage denominator through loaders; old evidence and catalog audit bytes untouched; ExtraBiblical must be recognized as installed `0.3.0`, but not receive an invented production OLiA alignment.
5. Focused tests under Python 3.10 and 3.12 plus exact-head full repository suite (no separate CI per ontology term). Tests challenge recomputed untrusted pack digests/coverage/resource swaps; preserve live GitHub review trust boundary.
6. Independent adversarial review grounded in code and packaged original manifests. Merge exact-head only if checks green, document scope separately from #303 actual publisher.

One PR per shared *release infrastructure capability*, not one PR per mapped POS value.
