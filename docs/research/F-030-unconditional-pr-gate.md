# F-030 phase 3 — complete PR event coverage and duplicate event cost

Issue #308, child of #291. Observed 2026-10-11 at main `2cca620`.

## Observed code and CI

`full-suite.yml` filters both push and PR events to `pyproject.toml`, `src/**`,
`tests/**`, and workflow files. A scripts-only fix, new decision ledger, or
evidence/documentation-only PR can therefore miss the canonical regression.
The workflow already executes exact PR-head code on Python 3.10 and 3.12,
pytest research contracts, historical coverage reproducibility and wheel checks.
Its identity is `Full repository suite` / job `validate`; these remain stable.

Live Actions evidence for PR #307 head `48827a172ee523a481853ce54170999f86d4f1aa`:
push run 38082506847 was cancelled; PR run 38082509842 succeeded. PR #305
head `caa1faf5c225621ce89c9944682ad3495f6c8943` likewise had cancelled push
38081213376 and successful PR 38081216521. Each canonical event has a two-job
matrix. This proves duplicate event starts, not a measured runner-minute saving.

The live main protection API returned zero required check contexts and zero
required approving reviews; rulesets returned an empty list. Application of
expected-head merge and all-checks verification remains a project process gate.
This change does not modify repository settings or infer enforced protection.

## External specification and alternatives

[GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
defines path/branch filters and default PR actions (opened, synchronize,
reopened). [Required-check troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
explains that path-skipped required checks stay pending, while conditional job
skips can satisfy checks. Removing event filters is preferable to proliferating
ledger/source glob lists that silently become stale as authoring formats evolve.

Keep the PR event unfiltered, with no conditional matrix/job skip. Restrict push
to main, without path filters, to keep post-merge coverage and avoid branch-push
duplication. Pre-PR branch regression remains available through dispatch; this
is an explicit scheduling tradeoff. Retain reusable workflow invocation.
Do not add pull_request_target or execute candidate code with a privileged token.

No ontology/source revisions, runtime semantics, licensing or public mapping
contracts change. All frozen scholarly/ontology assertions remain authoritative.
No new dependencies are needed: existing ruamel.yaml safely parses Actions YAML
in contract tests. Full consolidation, fast preflight, source-only ownership,
merge queues and external mapping-review authority remain separate deliverables.
