# F-030 / #291: retire duplicate validator and semantic-foundation workflows

**Issue:** #291

Research: `docs/research/F-030-validator-ci-pilot.md`

## Test and implementation contract

1. Introduce `tests/ci/test_ci_consolidation_validator_pilot.py` first: demand that 11 historic workflow YAML files are absent, while `tests/i001`, `i002`, `i003`, `i004`, `i005`, `i006`, `i007`, `i015` and `tests/packaging` remain importable and have `test_*.py`; `tests/i002` retains the three focused regression modules.
2. Assert that `full-suite.yml` retains unconditional PR event, exact-head checkout, `unittest discover -s tests -v`, separate research pytest, Python 3.10 and 3.12, wheel build, and existing frozen coverage checks. Keep distinct `i008` Context-Fabric integration, `i027b3` and `i027c1` upstream-source validation and `i033e3` protected review.
3. RED: commit the contract before deleting any historical workflow; it must fail solely because the 11 files still exist.
4. GREEN: atomic Git tree deletion of exactly these 11 workflows; retain all Python tests, runtime resources and other workflow YAML. Run CI for the final exact head. If older tests assert presence of retired YAML, change them to assert the actual retained owner/invariant, with an explicit regression test, rather than disabling protection.
5. Independently challenge coverage, workflow event boundaries, test discovery, packaging and branch-protection assumptions on the exact final head. Merge only after all active CI workflows pass and a fresh independent skeptical review is recorded.

No release artifact is built or promoted in this change; closing #291 is out of scope. Expected reduction: 77 → 66 workflow files.
