# F-030 phase 3: consolidate redundant Linux-focused CI, preserve unique gates

**Issue:** #336; parent #291, supports #290.

## Actual architecture audit (main @ 24213071f62e961df559db16a23a5a9f058dc3e2)

The repository has **57** workflow YAML files (down from 82 earlier), including a canonical `.github/workflows/full-suite.yml`. This unconditional exact-PR-head gate uses Python 3.10 + 3.12 and performs:
- `python -m unittest discover -s tests -v` over all retained per-ticket test packages;
- `pytest tests/research` and `pytest tests/architecture`;
- pinned historical and updated coverage snapshot `--check`;
- wheel build and isolated installation tests.

This duplicates six **Ubuntu-only** two-version focused workflows whose core commands are included by above discovery:
1. `f015-direct-validation-boundary.yml`: `tests/f015`, `f006`, `i001`.
2. `f016-custom-schema-recursion.yml`: `tests/f016`, `f006/f015/f019/f020/i001/i004`, `tests.packaging.test_schema_authority`.
3. `f021-feature-id-ownership.yml`: `tests/f021`, `d004`, conditional script `scripts/check_f_series_ownership.py`.
4. `f022-semantic-digest-json-boundary.yml`: `tests/f022`, `f009/i002/i004`.
5. `f023-downstream-ownership-enforcement.yml`: `tests/f023/f021/d006`, direct ownership checker.
6. `f024-namespace-scan-failures.yml`: `tests/f024/f023/f021/d006`, direct ownership checker.

The only unique *direct command* above is the ownership script `python scripts/check_f_series_ownership.py .`; move it **unconditionally** into canonical full-suite so the root-level ownership contract is not weakened. Keep all original test modules unchanged. The explicit script owner is needed beyond unit tests because a direct run checks actual tree metadata.

## Nonredundant workflows to keep

- Windows-specific F-014/F-018/F-019/F-020 are **not** equivalent to Ubuntu full-suite. No Windows coverage may be removed in this slice.
- Pinned external source checkout workflows (e.g. ExtraBiblical original compressed MQL) remain.
- `i008-exact-execution.yml` Context-Fabric 3.13 real integration remains.
- Protected-base batch review `i033e3-protected-batch-review.yml` executes secret-bearing GitHub operations under `pull_request_target`, distinct from untrusted PR-head test execution; must not be touched.
- F-series ownership tests for all six retired workflows must remain discoverable.

## Expected impact and limitations

6 retired x2-version focused jobs = up to **12 redundant runner jobs** avoided when all six paths overlap (not a wall-clock guarantee); shared suite still runs once per Python version and retains direct checker. Workflow files 57→51. Mapping-only PRs may not have triggered all six; do not claim 12 jobs saved for every PR. CI caching/queue time still depends on GitHub.

## Release gates

RED test asserts six workflows are removed, all suites remain, canonical suite directly invokes ownership checker, and each Windows/external/protected owner remains. Implement after RED; green full matrix; independent source-oriented skeptical review of workflow diff, exact head; only then merge. Historical release profiles, semantic mapping data, protected review authority unchanged.
