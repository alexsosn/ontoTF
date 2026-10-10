# F-030 phase 3 — event contract

**Issue:** #291

Implementation ticket #308. Research: `docs/research/F-030-unconditional-pr-gate.md`.

1. Commit research and this plan before implementation.
2. RED: parse the real workflow with the existing safe YAML parser; require
   an unfiltered PR event, main-only unfiltered push, manual and reusable events,
   no job-level conditional bypass, unchanged two-version matrix, exact-head
   checkout, read-only token and stable workflow/job names. Confirm failure
   against the filtered/duplicate-trigger baseline.
3. GREEN: change only canonical workflow event scheduling. Inputs remain GitHub
   PR/push events; outputs remain the existing validate matrix and wheel checks.
   Every eligible opened/synchronized/reopened PR runs both versions regardless
   of paths; GitHub merge-conflict, fork-approval and commit-skip rules still apply.
   Main pushes run the same gate; other branch pushes use PR or manual dispatch.
4. Run focused CI tests, full unittest and research pytest, frozen generators,
   build wheel and isolated wheel test. Final candidate GitHub CI must pass both
   Python 3.10 and 3.12. No runtime or historical release changes are allowed.
5. Independent adversarial reviewer checks real event YAML against GitHub
   specification, parent acceptance, skip/security boundaries, lost scheduling,
   preserved unique steps/check identity, and measured versus predicted savings.
   Any material fix requires renewed review of the final head.
6. Verify exact-head checks and merge by expected SHA. Report actual canonical
   run/job starts for this PR; do not claim #291 complete or new semantic rows.

Failure behavior remains a failing matrix check for regression/packaging errors;
neither event filters nor job `if` may silently suppress the canonical PR gate.
Commit-message skip directives remain a GitHub platform behavior, not solved here.
