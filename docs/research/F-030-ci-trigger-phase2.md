# F-030 phase 2 — CI trigger consolidation with preserved unique gates

**Issue:** #291

**Dependency:** F-030 phase 1 PR #295 / stable exact-head `.github/workflows/full-suite.yml`.

## Code-grounded trigger audit

The existing canonical full suite checks out the exact PR head, runs all importable unittest suites on Python 3.10 and 3.12, executes separate pytest research contracts, and builds a wheel on both. Phase 1 proved this caught hidden tests and reduced simple architecture PR #304 to F-007 + F-011 + full-suite.

The remaining redundant `pull_request.paths` source triggers include:
- `i009-production-bundles.yml` broad `src/tfont/resources/**`: triggers 2 focused jobs + regression + dedicated isolated wheel job on **every** resource overlay/data edit.
- `i016-coverage.yml` broad `src/tfont/resources/coverage/**`: triggers 2 jobs with baseline coverage generation and wheel resource smoke even for unrelated immutable successor manifests.
- `i026-work-queue.yml` broad `src/tfont/resources/coverage/**`: triggers 2 jobs for a frozen historical queue on every successor manifest.
- `i027b1-bhsa-verb.yml`, `i027b2-syriac-verb.yml`, `i027b4-extrabiblical-verb.yml`: immutable historical release validation spuriously triggered by generic `src/tfont/production_bundles.py` changes.
- `i027c2-adj-adv.yml`: same for `src/tfont/production_bundles.py` and `src/tfont/__init__.py`.

## Must-preserve unique tests

Full suite unittest covers I-004/009/016/026, old I-027B and C2 tests and their adversarial controls. **But not everything is redundant:**
- I-009 isolated wheel install tests are `@skipUnless(I009_WHEEL_TEST=1)`, so a normal full unittest run skips them. Before pruning I-009's broad trigger, move this *unique* test into the full-suite once per exact-head on Python 3.12.
- I-016 baseline generator `scripts/coverage/build_p004_r011_baseline.py --check`, I-026 historical queue `scripts/coverage/build_i026_work_queue.py --check`, and I-016 baseline wheel resource membership should be preserved as explicit full-suite steps.
- Other focused workflows keep their own tests, source-specific triggers and manual dispatch. No historical workflow file is deleted.
- The full suite remains a Python 3.10/3.12 required exact-head gate for code/resources/tests/workflows.

## Outcome and non-goals

This is CI trigger hygiene, not a production mapping or coverage promotion. A typical new immutable coverage or mapping data release should not spawn 2–4 legacy jobs per historical component on top of the canonical full suite. Unique wheel/source checks must run at least once per final candidate head, not disappear.

Do not disable explicit source-specific, tests, generator, documentation, or workflow self-triggers; do not change branch protection status names. Later F-030 work may further consolidate 84 historical workflows after equivalent proof.
