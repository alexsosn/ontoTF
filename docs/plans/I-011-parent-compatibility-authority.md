# I-011 implementation plan: release-authored parent compatibility

Issue #158. Research gate: merged PR #159, `docs/research/I-011-parent-compatibility-authorization.md`.

## Frozen behavior and trust boundary

An exact-parent-only release must never execute against a different observed parent digest, even if all observed native dependencies pass. Compatible-parent execution remains supported only for an explicitly authored `dependency-verified` release with its entire current dependency closure passing. A request, caller-provided prerequisite, cached report, or a forged `verified-compatible` label cannot expand release authority. The existing exact `BundleVariantKey` remains the expected-parent identity; no new source adapter or compatibility registry.

Policy vocabulary is exactly `exact-only | dependency-verified`; an absent source field normalizes to `exact-only`. The normalized policy is always present in `ProfileReleaseSignature`, and its value participates in `profile_release_fingerprint`. This deliberately invalidates old fingerprints; do not attempt backward identity compatibility before v0.1.

## Ordered gates

1. **Tests-only RED** from merged plan. New `tests/i011/` uses existing I-005/I-006/I-007 fixtures, no semantic fixture invention. Document hosted RED with focused failures and unaffected legacy suite. Test source-schema invalid enum; missing versus explicit exact-only normalization; signature and release-fingerprint difference for opt-in; exact and changed parent under both modes; known fail and unknown dependencies take precedence; forged `verified-compatible` prerequisite rejected by I-006; old-policy prerequisite stale after change; execution inherited by I-008 with no caller flag. Include adversarial malformed signature test. Existing I-007 changed-parent compatibility test must be updated to expressly opt in, not disabled.
2. **Minimal GREEN**, only then: add optional `parent_compatibility` enum to profile schema v2; normalize from `profile.get('parent_compatibility', 'exact-only')` at `semantic_ir._bundle_context` into new required `ProfileReleaseSignature.parent_compatibility` field; validate exact string/known vocabulary in `semantic_resolver._validate_release_signature_rows` and include in `_profile_release_projection`. Reject any malformed compiled signature fail-closed. In `runtime_prerequisites.evaluate_runtime_prerequisites`, preserve fail/unknown precedence, classify exact parent `verified-exact`; mismatch `verified-compatible` ONLY when signature explicitly opts in, otherwise `incompatible`. In `semantic_resolver._prerequisite_problem`, reject incompatible verified-compatible state for exact-only signature independent of evaluator, using existing `parent_incompatible` problem category. Do not change `BundleVariantKey`, mappings, request shape, or runtime report schema.
3. **Fixture migration**: change the one I-007 compatibility test to construct an explicitly opted-in validated source/IR. Prefer helper derived from `tests.i005._fixtures.noun_sources` with profile field set before validation; avoid `dataclasses.replace` only when a test claims to verify source→compiled propagation. Keep generic fixtures exact-only by default.
4. **Verification**: focused I-011 tests Python 3.10/3.12; existing I-004–I-010 regression tests; full repository suite. Confirm exact-head CI on PR and any wheel/resource checks run. Fingerprint test should compare two source-compiled releases with identical mappings/parent/dependencies and differing policy only. For stale test, reuse a legitimate prerequisite from old release with new IR and assert `stale_prerequisite`.
5. **Independent adversarial review**: re-read final diff and exact SHA without relying on implementation notes; attempt malformed policy, forged compatible state, wrong parent with passing values, policy-change cache reuse, compatibility opt-in with incomplete/failed closure, and unexpected changes to existing APIs. Fix any blocker with RED→GREEN again, rerun CI, review latest exact SHA. Merge with `expected_head_sha` only.
6. **I-009 handoff**: after I-011 merges, rebase/update PR #156 and explicitly add `parent_compatibility: exact-only` to all three production profiles. Recheck source/profile release fingerprints and wheel/three-parent runtime tests, then separately adversarial-review #156 before merge.

## Implementation touchpoints

- `src/tfont/schemas/profile.schema.json` optional enum, schema version stays 2.
- `src/tfont/semantic_ir.py` signature field and normalization in `_bundle_context`.
- `src/tfont/semantic_resolver.py` signature shape guard, release fingerprint projection, independent prerequisite guard.
- `src/tfont/runtime_prerequisites.py` use validated signature policy to derive state.
- `tests/i011/*` and deliberate one-test migration under `tests/i007`.

## Out of scope

No arbitrary compatible-parent allowlist, review-signature/certification machinery, schema-v3 churn, new dependency kind, request flag, hidden version/name fallback, network, source ingestion, generic planner, or change to mappings/projection digests. Source authoring of opt-in is not itself evidence of truth; only complete independently reviewed dependency closure can validate a changed parent at runtime.
