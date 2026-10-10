# I-033E3 — protected review-gate wiring (integration slice)

Parent #303 / #300 / #290. Source audit 2026-10-10: `src/tfont/external_review_gate.py` correctly rejects author, stale, revoked, unauthenticated and conflicting reviewer decisions; `scripts/mappings/check_external_review.py` requires `GITHUB_EVENT_NAME=pull_request_target` and caller-supplied packet/ledger files. **No protected-base workflow invokes it or fetches the two untrusted inputs from the exact PR SHA.**

## Threat model and decision

The trust boundary must be GitHub API-observed **review principal and exact head**, not a JSON declaration from a proposed batch. `pull_request` workflows that check out PR HEAD are untrusted, even if `GITHUB_TOKEN` is read-only. Avoid running PR-authored Python, workflows, shell, build instructions, JS Actions, or executable files inside a token-bearing reviewer job.

This integration permits **only protected-base code**: workflow executed from default branch, `actions/checkout` pinned to `main` (never a PR ref), `pip install -e .` on protected base, then fixed Python CLI under `scripts/mappings/`. The only PR-head inputs are a closed-shape JSON manifest at `docs/research/data/batch_review/inputs.json`, a proposal ledger beneath `src/tfont/resources/batch_pilots/`, and a review packet beneath `docs/research/data/generated/i033d/`. Fetch these as *raw data at the exact Git SHA* using GitHub REST contents API, verify encoding/size/Git-blob checksum/path. No filename/path from the manifest may escape the allowlisted directories.

A protected reviewer trigger must run **after** a review submission too. `pull_request_target` open/synchronize events alone are insufficient because submission does not retrigger them. Add `pull_request_review` submitted/edited/dismissed as a second trigger, while checking out protected base and enforcing the exact PR head in the same existing evaluator. Review-submit events are safe only with explicit base checkout and no PR code execution.

Only same-repository PRs bearing `ontology-batch-review` label are evaluated in this initial deployment. Label only schedules validation; it **never authorizes** a release. Real qualifying GitHub `APPROVED` review must be a separate privileged human (or separately justified trusted reviewer principal) and include the entire structured packet digest and per-row decision digests. A bot/single author cannot obtain approval by editing its own receipt; unreviewed PR is rejected.

`evaluate_live_gate` already rereads the PR after reviews and reviewer-permission requests; retrieve input bytes by the event PR head and require exact GitHub PR head before fetching. If the current head changes at any step the gate fails; a stale approval cannot pass.

## Deliberate boundary

This slice **does not itself publish** newly accepted mappings. `src/tfont/published_deltas.py` operates on *already published* registry releases and explicitly forbids authorizing new ones. The integration job will check authenticated approval and emit a non-signature JSON audit artifact, never a new runtime mapping. #303 remains open for a protected reviewer-driven delta publisher and source-bundle overlay. This is an actual deployable independent review gate, not a claim of end-to-end release throughput.

Live GitHub review checks remain required for a real batch: offline mocked API unit tests are never counted as real approval.
