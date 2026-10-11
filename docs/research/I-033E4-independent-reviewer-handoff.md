# I-033E4 / #325 — practical independent scholarly review handoff

**Parent:** #325, #303
**Base:** `02423525a6d814f2f1042950d607a4500203c3c4`
**Observed candidate:** PR #324, 10 native-only BHSA/Syriac POS proposals, full-suite green, live protected gate failed closed on missing independent authorized GitHub approval.

## Research: current repository code

- `src/tfont/external_review_gate.py::parse_structured_review` accepts **only** `ontoTF-batch-review-v1\\n` followed by a JSON object with exact `packet_digest` and `rows`, each with `mapping_id`, `decision_digest`, `disposition` ∈ {accept,reject,needs-evidence}. Full 1–50 rows and unique IDs are mandatory. `evaluate_review_snapshot` binds the GitHub APPROVED review to an independently authenticated current contributor with write/maintain/admin permission and exact PR HEAD.
- `scripts/mappings/check_external_review.py --from-pr-head` reads exact SHA data via GitHub API in `pull_request_target`/protected main; a local JSON body **cannot** grant approval.
- `scripts/mappings/build_candidate_review_packet.py --check` already verifies a candidate packet against a manifest, ledger, locked corpus source and supplementary candidate evidence; it is the one reusable local authoring path.
- The 10-item packet on PR #324 is ~16 KB JSON and presently requires writing a lengthy error-prone hand-authored GitHub review message with 10 exact row digests. Reviewers need a compact source/proposal dossier and a no-preapproval template for per-row dispositions.

## Platform trust boundary

GitHub documents [reviewing and approving PRs](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews): the PR author cannot approve their own PR. A separately authenticated collaborator must submit an actual GitHub `Approve` event. A COMMENTED review by the author is not adequate. The tool cannot create such principal, grant access or attest independent scholarly judgment.

## Proposed solution

One **reusable**, offline review handoff for any 1–50 candidate rows, without new Actions workflows or authored code per row:
- Dossier: human-readable per-row mapping selector, pinned source URI/revision, original source coordinates from bounded and revalidated source evidence, rationale, intended (possibly absent) ontology target, and clear `unreviewed` warning.
- Decision template: a JSON object with exact `packet_digest` and **unset/null dispositions** for every row. This is deliberately **not a valid GitHub review**, not an attestation, and may not be used for release.
- Renderer: takes explicitly filled decisions for all exact row IDs; rejects omissions, extra keys, duplicates, stale packet digest, invalid dispositions/types, JSON duplicate keys; uses packet-provided digest binding, emits only GitHub-review **body text** in the existing strict parser format. The authenticated reviewer must still submit it themselves in the GitHub PR review UI using **Approve** (not a comment), and the protected live gate independently verifies fresh head, reviewer permission and review state.

## Alternatives and residual risks

- Auto-default `accept` or `needs-evidence` for all rows: rejected; misleading scholarly approval.
- Author creating a secondary account or author-controlled app: rejected; separate credentials alone do not guarantee independent review.
- Reconstructing a GitHub approval JSON or manually importing a signed receipt: rejected as forged authority.
- A privileged chatbot plugin with token in PR-head context: rejected; protected-base evaluator must remain the sole publisher.
- Offline dossier fields are grounded in candidate source evidence but are still **proposed**; reviewers should consult the immutable primary source and ontology lock, not trust the candidate blindly. No new source semantic mapping publication is authorized by this change.

Outcome expected: one copy/paste review body after all independent decisions, not one PR/CI job per mapping. Separate issue #325 remains open until a real independent GitHub reviewer has been provisioned and submitted an approval.
