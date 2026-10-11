# I-033G: sparse, source-bound production coverage delta for reviewed handoff

**Parent:** #303, #300, #290; follows PR #332. **Source base:** `2398b61bb3876fe24fe985680ade0dba2c1994f2`.

## Research findings from installed files and protected handoff

- Protected run [38149670546](https://github.com/alexsosn/ontoTF/actions/runs/38149670546) generated an attested native-only ten-row handoff (9 BHSA, 1 Syriac, 0 shared ontology targets). Its GitHub-verified attestation/pack is **not yet a packaged release**, nor was it produced by a local test approval.
- `tfont.overlay_handoff.verify_overlay_handoff_integrity` checks the handoff structure, exact source registry pins/parent/lock, 10–50 complete adjudications, 1–50 accepted additions, inherited installed mapping/selector noncollision, and an independent `coverage_assignments` array per corpus. It intentionally returns `None`, **not authority**.
- `load_packaged_coverage_manifest("p004-i027c2-bhsa-adj-adv-v1", "bhsa")` has **219** semantic denominator items; `"node_value:sp=\\\"art\\\""` is in the denominator and `accounting.production=null`. Syriac `p004-i027c2-syriac-adj-adv-v1` has **74** items; `"node_value:sp=\\\"pron\\\""` likewise is unreviewed. Both are fixed source-pinned 0.4.0 manifests. A full copy-forward per mapping would be wasteful.
- Production coverage accounting examples use exactly `assessments`, `common_target`, `source_ids`, `profiles`, `capabilities`; an accepted mapping should set `source_ids=[mapping_id]`, `profiles=["linguistic"]`, `capabilities=["linguistic.part-of-speech"]`, and assessment exact/native-only depending on accepted reviewed projection. A native-only row must have `common_target=false`. Preserve prior research accounting, coverage exclusions, denominator and any gaps verbatim.
- `tfont.coverage.validate_coverage_manifest` and `coverage_report` can prove in-memory recomposition without modifying historical package files. The handoff records `coverage_base.resource_set`, `manifest_digest`, `denominator_digest` and exact accepted assignments, so a sparse delta can use them as a frozen baseline.

## Proposed architecture

A pure **offline, unsealed** `tfont.coverage_overlay` module:
1. `build_sparse_coverage_delta(pack)`: verify complete handoff integrity; emit only per-corpus accepted `item_id` → `production` records and baseline/digest commitments. No full coverage manifest, rejected/needs-evidence rows, duplicate denominator entries or new ontology projections. Mark `authority="unsealed-coverage-preview-only"`; no `release_authorized` field or published release alias.
2. `apply_sparse_coverage_delta(pack, delta)`: regenerate exact canonical delta from the same verified pack and compare (not just rehash untrusted input); load the original packaged manifest by strict ID, verify baseline commitment, clone in memory, apply only previously-null production cells and validate the result. Return a **preview** with updated `coverage_report` and exact original denominator digest, not a published record.
3. Fail closed if candidate review, exact source commitments, delta digest, contents, production accounting, baseline denominator or immutable historical data drift. Preserve rejected/needs-evidence items unchanged. Work for 1–50 accepted decisions in a 10–50-item review.
4. Inference boundary: this transforms already-reviewed native-only/exact *candidate claims* into a sparse accounting preview; **does not** certify live GitHub attestation, install a release, prove real TF corpus occurrence counts, or add any non-reviewed exact ontology mappings.

## Follow-on after this bounded slice

Only a protected release installer may consume a separately attested handoff from GitHub Actions and commit immutable versioned registry files, with retained old `0.4.0` identity and source/ontology pins. It must validate the released semantic bundle, forward/reverse semantic IR, wheel packaging, real TF API and updated coverage. The unsealed preview must never become authority on its own.
