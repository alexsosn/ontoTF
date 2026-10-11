# I-033E3 / #303: safe post-approval recheck command

**Issue:** #303
**Research:** `docs/research/I-033E3-post-approval-refresh.md`

## TDD RED first

Add `tests/i033e/test_comment_review_refresh.py`. Require `issue_comment: types: [created]`, exact `/ontoTF verify-review` command, real PR-only and trusted commenter gate, same package label, protected-base only checkout and no `pull_request_review`. Test `_github_event()` accepts only this tightly validated event and derives current head SHA via authenticated live API; rejects ordinary issues, invalid/edited body, unauthorized affiliation, wrong ref, closed/fork/draft/missing label, malicious/stale SHA, and no token. Preserve pull_request_target behavior.

## Implementation

1. `_github_event` dispatches between existing `pull_request_target` and newly restricted `issue_comment`. On comment, read bounded event payload, require trusted default-branch ref, canonical command, PR issue shape and author association; call `GET /repos/<repo>/pulls/<n>` with trusted GitHub token, validate repo/head/base, state, label, SHA. Return exact SHA read **live**. Keep all existing live permission/review/packet/ledger checks unchanged.
2. `.github/workflows/i033e3-protected-batch-review.yml`: add `issue_comment: [created]`; gate both attestation and publish by corresponding branch conditions with same existing review + publish labels. Keep two trusted-base checkouts, no PR-head code, no write GitHub permissions beyond attestation, immutable artifact names keyed by PR number and run ID.
3. Run focused historical and new tests before full suite. Re-run 3.10 and 3.12 exact-head CI, post logically independent skeptical review of the actual code/security boundaries, merge only with expected SHA if green.

## Important non-goals

A comment is a **re-check request** and never substitutes for a distinct GitHub APPROVED review or semantically justified source/ontology decisions. Current issue #303 remains open for the real 10+ mapping row external signoff and publish demonstration.
