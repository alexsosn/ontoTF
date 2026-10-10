# F-030 phase-1 research-plan-TDD-test gates

**Issue:** #291

1. Baseline exact-head runs: PR #294 triggered 24 workflows; a tree inventory identified seven missing test-package markers in addition to now-fixed I-033A.
2. TDD RED: create `tests/ci/test_python_test_discovery.py` to discover importable test packages, reject missing `__init__.py` and verify that `tests/ci` itself runs under `unittest discover -s tests`. Confirm current seven omissions before fix.
3. GREEN: add the seven package markers; do not change the original tests or their expected results. Analyze any newly observed errors.
4. CI changes: full-suite adds `python -m build --wheel --outdir dist`, with packaging resources already covered by tests. Prune only eight redundant broad-path filters on legacy unittest-focused workflows; keep their topic triggers.
5. Full/targeted tests: full suite Python 3.10/3.12; all triggered workflows. Contract assertions enforce exact policy for modified workflows. Check wheel resources and unchanged source-bound ontology digests.
6. Logically-independent adversarial review: verify that each pruned workflow's unique checks remain covered and that broad-source changes cannot skip the mandatory full suite. Confirm new tests were discovered, not just importable in isolation.
7. Only merge with all expected-head checks green. Measure workflow run count for the next ordinary mapping/loader PR compared to #294; continue migrating unique workflows only after proving parity.
