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

## CI-discovered migration dependency

The first PR head correctly failed D-006's repository test `test_frozen_carriers_are_missing_or_matching`: its historical F-series carrier inventory still expected F-003/F-004/F-005 workflows to exist. The correction updates that *active-path inventory*, explicitly classifies the three removed workflows as intentional retirements, and adds a test that requires their deletion while retaining their three `tests/i002` regression modules. All immutable research ownership documents and the F-series issue IDs remain intact; absence is not reclassified as a false owner declaration. This prevents a green result from merely bypassing D-006.

## Second exact-head CI failure and correction

On the subsequent PR head, the full Python 3.10 suite ran 1,372 tests and exposed two additional deprecated-file coupling paths:
- `tests/ci/test_python_test_discovery.py` still opened seven deleted I-series workflows to assert scoped triggers. The only *surviving* targeted workflow in this historical trigger test is F-002, so the scoped-filter check now targets F-002 alone. The new F-030 contract independently checks the retired workflows and the always-triggered full-suite.
- The D-007 forward-extensibility test copies only F-series research/plans/workflows and F-series sidecar test metadata into a synthetic repository. D-006 tests must operate on that intentionally limited fixture. Remove the three `tests/i002` module-existence checks from D-006's fixture-level test; the new F-030 repository-level test remains the authority for those modules. Retain D-006's assertions that retired carrier paths are absent and no longer in the active expected carrier set.

Both corrections preserve negative ownership/discovery invariants and adapt their **scope** to the new architecture, instead of skipping tests.
