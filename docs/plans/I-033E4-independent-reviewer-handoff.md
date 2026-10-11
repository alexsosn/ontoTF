# I-033E4 / #325 — research-plan-TDD gate

1. Research frozen candidate packet in #324, review strict parser and trust boundary, upstream source coordinates and GitHub APPROVED review mechanics. No author-controlled reviewer shortcut.
2. **RED** create `tests/i033e/test_reviewer_handoff.py`: dossier grounded in pinned existing BHSA/Syriac source evidence and ten-selector cohort; template null decisions cannot pass `parse_structured_review`; explicit mixed dispositions render an existing-parser-compatible message; missing/extra/duplicated/nonstring disposition/digest, unsupported values and packet tampering fail; every review ID and original row digest must match.
3. Implement `src/tfont/reviewer_handoff.py` generic 1–50 row logic and CLI `scripts/mappings/prepare_external_review.py` for `--dossier`, `--template`, `--review-decisions FILE`. Default CLI reads only the locally validated current manifest, never GitHub privileges. Dossier includes source link/line, meaning, rationale, target, and warning. Template never defaults any decision.
4. Test `python -m unittest tests.i033e.test_reviewer_handoff -v` plus full exact-head Python 3.10/3.12 CI; inspect real PR #324 packet in review instructions without adding it to main.
5. Independently challenge authority leakage, stale digests, foreign row IDs, unreviewed dispositions, evidence source drift, resource path handling, and JSON parser edge cases. Fix failures using fresh RED tests and rerun final-head CI; squash merge only after skeptical review posted and green checks.
6. Keep #325 open until the user/repository installs or invites a genuinely independent authorized reviewer and #324 receives a real approved review. No self-approval or published mapping change in this PR.

## Independent-review CLI correction

The subprocess regression reproduced `ModuleNotFoundError: scripts` for the documented direct script command under Python 3.10. In-process tests had hidden this import-path failure. Use `python -m scripts.mappings.prepare_external_review` from the trusted repository root, which resolves the repository scripts package without importing candidate checkout code. Verify the command copied from the documentation in a fresh Python process before rerunning the full gate.

A second independent finding reproduced candidate rationale `<!--` hiding subsequent dossier rows in a Markdown preview. A verified RED regression also includes a forged heading and link. The renderer now escapes HTML and Markdown controls and flattens embedded line breaks in free candidate text; original ledger, packet, evidence and decision digests are unchanged. This is display safety, not source validation or scholarly approval.
