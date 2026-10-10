# F-030 phase 2 — research / plan / TDD / test gates

**Issue:** #291

**Research:** `docs/research/F-030-ci-trigger-phase2.md`.

1. RED: `tests/ci/test_mapping_ci_scope_red.py` requires canonical full suite preserving exact SHA, both Python versions, isolated wheel installation, baseline wheel seven-corpus membership, baseline generator --check and I-026 historical queue --check; it requires absence of broad old resource and generic loader triggers in eight named legacy YAML files.
2. GREEN: add the *unique* wheel smoke + immutable baseline/queue checks to full suite. Only then prune PR broad path triggers in I-009/I-016/I-026/I-027B1/I-027B2/I-027B4/I-027C2; retain their own explicit source, tests and workflow triggers.
3. Focus tests: `python -m unittest tests.ci.test_mapping_ci_scope_red tests.ci.test_full_suite_workflow_contract`.
4. Full exact-head CI on Python 3.10/3.12; source/workflow changes must not skip the full suite. Confirm all generated artifacts remain frozen.
5. Independent adversarial review: compare before/after trigger sets and unique command ownership, check no removal of source-only MQL gates, no hidden pytest/wheel test regressions, and enforce exact-head CI before expected-head merge.
6. Report concrete saved workflow/job triggers for a hypothetical new `src/tfont/resources/coverage/new-snapshot` change and a `src/tfont/production_bundles.py` change. No fabricated wall-clock savings.
