# I-033E — independently attested batch review gate (phase 1)

**Issue:** #300; parent ADR-001 / #290. This is the first trust-boundary component for the future immutable delta-pack publisher; **it does not publish mappings or coverage**.

## Empirical starting point

Merged #299's `tfont.review_packets.build_review_packet` binds a source-validated Mapping v2 candidate, its **rationale**, source/ontology pins, exact intended coverage IDs and per-row `decision_digest` to a JCS `batch_digest`. `verify_review_packet` explicitly forbids self-declared approval and treats review requests as unauthoritative. The candidate compiler (#297) only supports reasoned word-level `sp` proposals from pinned source definitions and real OLiA target evidence; it does **not** claim mass coverage.

The missing authority is *who reviewed which exact bytes and what they decided*. `reviewed: true` in a PR file, a recalculated packet hash, GitHub comment text written by the PR author, or a synthesized JSON receipt is **not** evidence of independent review.

## Explicit external authority

Use GitHub's **live REST API as the primary authenticated observation** at a trusted release gate, not author-supplied payloads. A qualifying reviewer must:
- be a real GitHub user other than the PR author;
- have current repository `write`, `maintain` or `admin` permission as queried through GitHub's collaborators permission API (not a submitted `role` field);
- have a latest non-dismissed **APPROVED** PR review whose `commit_id` exactly equals the PR head being evaluated;
- submit a strict machine-readable body headed `ontoTF-batch-review-v1` followed by one JSON object containing `packet_digest` and exactly one `accept`, `reject` or `needs-evidence` adjudication per mapping ID, each bound to that row's `decision_digest`.

Accepting the same `mapping_semantic_digest_v2` with modified rationale must fail: only a matching *whole* I-033D packet is eligible. Missing/extra/repeated IDs, foreign packet revision, stale review, dismissed review, author approval or an unauthorized reviewer fail closed. A later `COMMENTED` / `CHANGES_REQUESTED` / `DISMISSED` review by the same reviewer invalidates older approvals for release purposes. Conflicting eligible reviewers fail closed, not silent majority selection. This is conservative release policy, not a claim that GitHub cryptographically proves logical independence.

## Host trust boundary

Run authenticated API calls in a **trusted GitHub Actions base-branch workflow / protected release job**. Do not execute PR-head-supplied scripts or untrusted source code in the context that has a token capable of checking review privileges. A PR may modify its own gate implementation; the gate's trusted implementation and workflow must be protected by branch rules. The artifact is not proof of its own authenticity.

GitHub REST responses are authenticated in transit by HTTPS with the workflow's token; **unsigned cached JSON alone does not prove it came from GitHub**. A permanently installed/offline ontoTF package can check an archived receipt for *digest consistency and provenance fields*, but must not mistake it for live independent GitHub authorization. Publication should preserve an immutable receipt in a protected/tagged release after a live gate; stricter offline cryptographic provenance requires a future explicit signed attestation design.

Permission fetch, review pagination and PR identity retrieval require `pull-requests:read`, `contents:read` and repository permission metadata scopes as appropriate; if absent or API fails, fail closed (no fallback to self-asserted roles). GitHub reviews made before code changes are stale even if GitHub has not automatically dismissed them.

## Coherent mapping batches

One reviewer adjudicates up to 50 homogeneous rows in one review; `accept` yields a potential released positive mapping, whereas `reject` and `needs-evidence` yield **no** positive projection or common-target coverage. Semantic Review `APPROVED` here approves the **adjudication packet**, not automatically every proposed exact correspondence. This enables conservative per-row exceptions in a single PR.

## Boundary to the next phase

This PR will provide an HTTP-independent strict evaluator and an explicit live-REST gateway (with injectable fake transport for tests), plus clear workflow integration guidance. **It will not** start distributing independently reviewed runtime outputs, write a claim of completed source/ontology coverage, or modify historical profile loaders/coverage. Phase 2 #300 must use the live gate result and publish only accepted mapping deltas (no copy-forward), with its own TDD/final-head review.

## Decision

GO for strict GitHub-attested reviewer decisions as a narrow initial authority contract. Do not treat the first passing mock REST response in tests as actual independent authorization. The final release gate must issue fresh HTTPS calls from protected code at the exact PR commit.
