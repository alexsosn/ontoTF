# I-033E10 — source-bound native-only supersession preview

**Owner:** #333, child of #329 / #303 / #290.

## Existing production constraints

1. `overlay_handoff.build_overlay_handoff` and `verify_overlay_handoff_integrity` refuse an inherited mapping ID, projection ID, or native selector. This is a sound additive-release safeguard but makes a reviewed `native-only` selector impossible to upgrade to a shared ontology target without a separate non-additive migration.
2. Source-backed 10-row native-only BHSA/Syriac proposals from #324 and the protected two-pass single-agent reviewer now exist. Partial acceptance (1–50 accepted from 10–50 reviewed proposals) was fixed in #331. These records are **attested handoff candidates**, not yet installed release-catalog mappings; do not claim any existing original-source native-only release has been promoted.
3. Existing BHSA `word.sp=verb` `mapping:bhsa:olia-verb` is a validated, **positive** exact class record from immutable v0.3.0 (with its native source `evidence:bhsa:word-sp-verb-code` and vendored `evidence:olia:verb-class`). It is useful to construct a *synthetic historical native-only predecessor* fixture by cloning its selector and source-binding, not by inventing a corpus category or release claim.
4. A new shared target must cite a separately pinned source ontology lock and normalized class-definition evidence, and must not silently change corpus, selector, dependency, source evidence, or old review.

## Architecture decision

Introduce one shared **pure, untrusted preview** `tfont.mapping_supersession.plan_native_only_supersession` that validates:

- predecessor is content-digest-bound `reviewed` native-only Mapping v2 with no projection;
- proposed successor is a still-UNREVIEWED, digest-bound positive Mapping v2 with one exact target class;
- corpus/native selector and source-bound dependencies, profile/capability scope are identical;
- caller must also supply its *full active mapping index*; one and only one active mapping may own the native selector, it must be byte-identical to the predecessor, and no inherited active mapping/projection ID may collide with the replacement; a digest of that active-index identity set is part of the preview;
- predecessor/source provenance remains intact, original category evidence explicitly supports word-level feature scope, and new ontology class evidence has a matching canonical digest, RDF type, target URI and immutable lock snapshot;
- mapping IDs differ, so the old mapping remains addressable in release history and cannot be overwritten. A separate transition explicitly retires the old mapping from the *effective* active index and selects the new one. No active duplicate selector.
- the returned closed-shape deterministic preview has a content digest and a literal non-authoritative marker. A caller-provided old `review.status=reviewed` is **not** an independently verified GitHub signoff and must NEVER be treated as authority by itself.

## Trust boundary / follow-on

This is a **planner**, not an authenticated overlay publisher, signed reviewer receipt or versioned registry installation. Only protected-main runtime after authenticating the actual immutable base bundle and current GitHub two-pass review may convert a preview into a signed active-release supersession. Until #303 wires that trust boundary, tests use published BHSA evidence and a clearly synthetic historical predecessor and report no new production coverage.

Do not create a PR or release per promoted native code. This source-agnostic transition primitive works for whole batches and future ontology packs. Do not relax the current protected overlay writer's inherited-selector collision checks in this slice.
