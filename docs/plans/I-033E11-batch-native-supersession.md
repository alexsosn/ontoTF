# I-033E11 implementation gates

1. Research and primary-source audit: #329; existing `mapping_supersession.py`, `overlay_handoff.py`, BHSA 0.4.0 native adj/adv records and OLiA ontology evidence.
2. TDD RED before implementation: `tests/i033e11` constructs two **synthetic predecessors from real v0.4.0 reviewed mappings** and confirms new batch APIs are absent. Test exact deterministic 2-row preview/verification, count bounds, unchanged inputs, same base index, collisions (retired/new mapping/projection/bindings), forged authority and input modification.
3. GREEN: implement `plan_native_only_supersession_batch` and `verify_supersession_batch_preview`, calling existing per-transition `plan_native_only_supersession` and comparing entire source-bound records. No new mapping semantics or review syntax; allow 1–50 accepted transitions (10–50 candidates handled by earlier packet stage).
4. Emit compact deterministic untrusted preview only: base release, active-base digest, transition count, ordered per-selector previews, and content digest. No signed manifest, production status, review fields or auto-upgrade.
5. Focused Python 3.10/3.12 CI and exact-head full suite. Independent skeptical review of **actual code and pinned BHSA evidence**, following independent alternate failure reasoning, before expected-head merge.
6. Downstream parent #329 and #303 still need a separately reviewed protected publisher to use the preflight against an immutable base catalog and write a versioned release. Never call this helper sufficient for full coverage.
