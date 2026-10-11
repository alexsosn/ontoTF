# F-030 / #291: validator and semantic-foundation CI retirement — research

**Issue:** #291
**Repository baseline:** `main` at `5e3843168446c7f3fb0fa9e95c1cf78605c6da8b` (2026-10-11).
**Prior pilot:** PR #319 retired seven POS workflows after preserving all seven formerly unique `--check` commands.

## Evidence: independent inspection of existing workflow jobs

The current repository has 77 workflow YAML files. The following 11 historical focused jobs execute only tests/environment diagnostics already subsumed by the unconditional `full-suite.yml`, with no original-source checkout, externally signed review, or new generated artifact command:

| Workflow being retired | Only substantive commands |
| --- | --- |
| i001-validation.yml | `unittest discover -s tests/i001` |
| i002-validation.yml | `unittest discover -s tests/i002` |
| i003-validation.yml | `unittest discover -s tests/i003` |
| i004-semantic-validation.yml | `unittest discover` for i004/i001/i002/i003/p002/packaging |
| i005-semantic-ir.yml | `unittest` for i005/i004 |
| i006-semantic-resolver.yml | `unittest` for i006/i005/i004 |
| i007-runtime-prerequisites.yml | `unittest` for i007/i006/i005/i004 |
| i015-noun-morphology.yml | `unittest discover -s tests/i015` |
| f003-digest-projection-key-errors.yml | `unittest` for i002 regression and full i002 |
| f004-source-bundle-diagnostic-paths.yml | `unittest` for i002 regression and full i002 |
| f005-utf16-diagnostic-paths.yml | `unittest` for i002 regression and full i002 |

All eight named `tests/i001`–`i007`, `tests/i015` packages have `__init__.py`, as does `tests/packaging`, so standard `unittest discover -s tests` imports them. F-003/004/005 focus on actual test modules under i002 and do not have unique standalone scripts. `full-suite.yml` already runs that discovery on exact PR SHA for both Python 3.10 and 3.12, plus separate pytest research contracts, package build, immutable source/coverage reproducibility, and isolated wheel smoke. Deprecating the old workflow names must not delete their regression tests.

**Explicit exclusions:** I-008's separate Context-Fabric 3.13 integration (not equivalent to the canonical suite); I-010/I-011 direct pytest runs until equivalence is checked; I-020/I-021 unique research anchor checks and wheel API smoke; I-022–I-024 pinned online Text-Fabric checkouts; I-025 wheel metadata; I-027B3/I-027C1 upstream corpus evidence; I-033E3 protected reviewer. These workflows remain untouched.

## Alternatives, compatibility and risks

- Keep focused CI triggered by stale historical paths: rejected, repeats package setup with no new validation on a typical source edit.
- Remove broad `unittest` without checking package discovery: rejected; the existing F-030 phase-1 research found silently skipped test directories and required packaging markers.
- Move all 11 job bodies verbatim into full-suite: rejected as it would duplicate exactly the same tests already discovered.
- Preferred: remove only these 11 YAML files, add one automated invariant test requiring importable existing suites, focused F-003/004/005 test files, full exact-head Python 3.10/3.12 checks, and retention of all known distinct upstream/release workflows.

GitHub branch-protection settings are not fully readable by this connector (403 on protection endpoint), so no claim is made that historic checks are unrequired. The parent #291 remains open until remaining workflows are fully audited; savings in workflow count are measurable but runner-minutes require comparison on later PRs. No semantic mapping, ontology license, runtime, or source artifacts are changed.
