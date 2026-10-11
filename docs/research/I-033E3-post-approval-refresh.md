# I-033E3 / #303: protected post-approval recheck trigger

**Issue:** #303
**Base:** `23f57bf1f0d03f437c3269aebccd28e319d938fb`
**Observed source:** `.github/workflows/i033e3-protected-batch-review.yml`, `scripts/mappings/check_external_review.py`, `tests/i033e/test_protected_pr_batch_gate_red.py`.

## Gap confirmed in code

The protected job uses `pull_request_target` only for `opened,reopened,synchronize,ready_for_review,labeled`. An independent GitHub reviewer typically submits APPROVED **after** a PR is labeled; no configured event then re-runs the live external review gate. Thus a valid reviewer decision cannot produce the attested accepted-only handoff without an extra user workaround (remove/reapply the label or push another commit, which can invalidate approval).

Simply enabling `pull_request_review` is unsafe for this protected release path: GitHub's event uses the PR merge ref, and there is no permission to execute PR-supplied workflow code with tokens. GitHub's Actions event reference confirms `issue_comment` runs from the repository default branch with `GITHUB_SHA` the latest default branch commit and that `github.event.issue.pull_request` identifies PR comments. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows.

## Alternatives

- Rerun by toggling the `ontology-batch-review` label: secure but a fragile manual workaround without explicit review-refresh command.
- Listen directly to `pull_request_review`: rejected because this event may execute PR merge-ref workflow code.
- `workflow_dispatch` with supplied PR/SHA: would require widening a protected event trust boundary; current tests explicitly reject this and operator input can be stale. Not necessary.
- **Adopt an explicit, maintainer-issued PR comment recheck** `/ontoTF verify-review`. `issue_comment: [created]` loads workflow from default branch. Restrict job eligibility to actual PR comments, an existing review label, and OWNER/MEMBER/COLLABORATOR author association. The comment **must not be treated as approval**: trusted Python fetches current head at GitHub API, still requires a distinct APPROVED reviewer with permission and exact packet/decision SHA, and revalidates live GitHub records before publishing.

## Trust boundaries and residual risks

- Never execute PR code or pull_request_review-triggered code with token. `issue_comment` checkout is protected default branch only.
- No user-provided SHA is authoritative: read current PR `head.sha` over authenticated GitHub API, validate open/non-draft/base main/same repo, bind all packet and ledger fetches to that SHA and recheck freshness before signing.
- Treat unsolicited PR comments, ordinary issues, unapproved reviewers, stale reviews, changed head and missing labels as **not authorizations**. Author association is a *CI trigger throttle*, not approval.
- Preserve unchanged `pull_request_target` path as fail-closed. Recheck comment contents and PR metadata in trusted Python, rather than relying solely on GitHub YAML `if`.
- `issue_comment` event might incur a small queued event for all repository comments; the condition prevents jobs for unrelated requests. This PR does **not** create an actual independently signed 10-row ontology release or circumvent missing external reviewer identity.
