# I-027B4 research-plan-TDD-implementation gates

**Issue:** #281. **Research:** `docs/research/I-027B4-extrabiblical-verb.md`

1. Source: use merged source-evidence #280, exact corpus `9a56288...`, OLiA reference lock and real R-005 inventory. Do not use Syriac/BHSA as an ExtraBiblical source authority.
2. RED: tests require new immutable `0.3.0` profile and explicit versioned loader; test exact IR key `olia:Verb` with `node_type=word`, `sp=verb`, `value-predicate`. Historical `0.2.0` semantics and all reviewed mapping digests remain unchanged. No `vs`, `vt` or `nu` projection fabricated. Negative controls mutate selector/evidence/review and demand a fail-closed validation.
3. GREEN: add `extrabiblical/0.3.0/profile.json`, parent expected components, mapping documents for existing noun/morphology unchanged, `mappings/verb.json`, `evidence/native-verb-pos.json`, and a `load_production_verb_bundle("extrabiblical")` branch explicitly opted into v0.3.0.
4. Content digests: compute evidence normalized-record SHA256 and semantic projection/mapping digests with the *repo canonical algorithm*. Pin production review separately from source extraction. Confirm no stale review references.
5. Coverage: offline deterministic generator with `--check`. New immutable coverage successor to the existing ExtraBiblical baseline. The one updated row is `node_value:sp="verb"`; keep full denominator, inventory pin, old accounting and exclusions unchanged. Expect 8/136 production reviewed, 8/136 exact common-target.
6. Tests: positive + negative semantic IR and coverage successor tests; wheel resource inclusion; no edits to old releases. CI matrix 3.10/3.12 and full repository suite.
7. Review: logically-independent skeptical assessment of exact source MQL evidence, controlled ontology target, profile-lock identity, canonical digest binding, negative controls and actual underlying corpus limits.
8. Merge: only after exact-head all-green CI. Keep parent I-027 (#264) open for remaining C items.

No hidden automatic work: each phase proceeds through actual commits/CI in this PR.
