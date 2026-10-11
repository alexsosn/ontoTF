# I-028A — implementation and TDD plan

**Issue:** #340. **Research:** [I-028A](../research/I-028A-bhsa-syriac-lexical-depth.md).

1. **RED:** add `tests/i028a/test_lexical_depth.py` that asserts a proposal-only source-bound ledger exists, covers the **exact** 22+5 current D identities from frozen I-026, agrees with the two pinned R-005 inventories, carries no production authority or unreviewed ontology target, and survives adversarial negative mutations. Confirm RED specifically because the new ledger is absent.
2. **GREEN:** add only `docs/research/data/i028a/bhsa-syriac-lexical-depth.json`, 27 human-reasoned source-specific rows. Preserve all immutable published profiles, I-026 historical queue, source inventories, coverage manifests, runtime and GitHub Actions ownership; no new workflow or release.
3. Run `python -m unittest tests.i028a.test_lexical_depth -v` plus existing full suite on the exact PR head (Python 3.10 and 3.12 in CI). Ensure negative tests reject a changed inventory source description, missing/extra rows, a second claimed entry identity, and any injection of `review` or `target` fields.
4. Conduct a **fresh logically independent adversarial semantic review** from the original R-005 feature definitions/R-008, record counterexamples on the PR and amend/redo review for any material change. Merge only after exact-head green CI and review.
5. Post-merge handoff: this is **27 researched candidates / 0 production released**. Promote only through the explicit independently reviewed and source-/ontology-bound batch publication gate tracked by #300/#303, once operational. Do not inflate coverage metrics before then.
