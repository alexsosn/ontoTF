# F-023 implementation plan — enforce downstream ownership against research authority

**Issue:** #115  
**Research:** `docs/research/F-023-downstream-ownership-enforcement.md` and `docs/research/F-023-d007-prerequisite-amendment.md`  
**Baseline:** `main` `23b1df3c86606c1fc9be246328f3e4505604d7d3`

## 1. Goal

Extend the existing repository-local F-series ownership checker so research remains the sole `F-NNN -> issue` allocation authority while every present F-series plan, focused workflow, and test package is checked as a one-way downstream claim.

The historical failure this ticket must reject is a downstream `F-015 -> #90` claim when research owns `F-015 -> #87`.

This ticket does not add a registry, Git/GitHub lookup, installed ontoTF API, runtime/schema/digest/ontology behavior, automatic renumbering, or history-wide collision guarantee.

## 2. Files and phase ownership

### Plan phase

This file only.

### Tests-only RED phase

Add only:

- `tests/f023/__init__.py`;
- `tests/f023/issue-owner.txt` containing exactly `Issue: #115\n`;
- `tests/f023/test_downstream_ownership_enforcement.py`;
- `.github/workflows/f023-downstream-ownership-enforcement.yml`, carrying `# Issue: #115` within its first 12 physical lines.

Do **not** edit `scripts/check_f_series_ownership.py` before the RED run is recorded.

The plan, workflow, and test sidecar are themselves valid D-006 ownership carriers so D-006 remains green during RED. Intended RED failures must come only from the existing checker ignoring downstream namespaces.

### Minimal GREEN phase

Edit only `scripts/check_f_series_ownership.py` for behavioral enforcement. No `src/**` changes.

### Documentation substep

After behavioral GREEN, add a focused documentation-contract test first, observe RED, then update `CONTRIBUTING.md`. This is a separate RED/GREEN substep inside F-023.

## 3. Compatibility surface

Preserve the existing F-021 callable behavior and exact diagnostics:

- `check_artifacts(artifacts)` continues to mean research-artifact ownership checking only;
- `scan_repository(root)` keeps its current two-tuple return shape `(research_artifacts, diagnostics)` and existing authority/read diagnostics;
- `check_repository(root)` remains the repository-wide checker entry point and is the surface that gains downstream enforcement;
- `main(argv)` keeps `python scripts/check_f_series_ownership.py [root]`, silent success, stderr diagnostics, and exit 0/1.

Existing F-021 tests are compatibility tests and must remain unchanged unless an independently demonstrated defect requires a separately gated amendment.

## 4. Internal research-state model

The production implementation may add private helpers, but must not make downstream scanners a second authority source.

Freeze this internal information flow:

1. scan research artifacts using the existing F-021 path/header grammar;
2. preserve all existing research diagnostics;
3. derive a valid authority map `feature -> issue` only from research artifacts;
4. derive an `invalid_features` set for any F ID whose research authority is unusable because any same-ID research artifact is unreadable, missing/malformed/duplicate, or the valid same-ID group conflicts;
5. scan downstream carriers and validate local metadata;
6. compare a locally valid downstream claim to research only when that feature is not in `invalid_features`;
7. sort the combined diagnostics lexically.

A private richer research scanner may return extra state, but the existing public-to-tool `scan_repository(root)` wrapper must continue returning exactly the F-021 two-tuple.

### Read-error feature attribution

A research path that matches `F-NNN` is known before its bytes are read. If reading fails, add `F-NNN` to `invalid_features` while preserving the existing stable `read_error` diagnostic. This prevents a valid downstream claim for that feature from being mislabeled `unknown_feature`.

### Mixed valid/invalid same-ID research paths

If any research artifact under a feature is locally invalid, that feature is unresolved for relationship checks even if another same-ID research artifact is individually valid. Research authority must be conflict-free as a group before it can authorize downstream claims.

## 5. Downstream namespace and parser contracts

### Plans

Enumerate regular files matching exactly:

`docs/plans/F-[0-9][0-9][0-9]-*.md`

Feature comes from the filename. Reuse the existing bounded Markdown header scan: physical lines 2–12, stopping before the first `## ` section. Canonical owner:

`**Issue:** #N`

### Focused workflows

Enumerate regular files in `.github/workflows` matching exactly, case-sensitively:

- `fNNN-*.yml`;
- `fNNN-*.yaml`.

Inspect raw UTF-8 text, first 12 physical lines only. Canonical owner:

`# Issue: #N`

Do not parse YAML merely to recover ownership metadata.

### Test packages

Enumerate direct child directories of `tests` matching exactly `fNNN`.

Required carrier:

`tests/fNNN/issue-owner.txt`

Canonical content is exactly one line `Issue: #N`, with or without one final newline. Presence of Python files or `__init__.py` cannot substitute for the sidecar.

Missing downstream collection directories are empty namespaces, not errors. The research authority directory retains F-021's required/fail-closed semantics.

## 6. Stable downstream diagnostics

Use repository-relative POSIX paths. Read failures report exception **type**, never platform-specific exception text.

### Read failures

`read_error: <path>: <ExceptionType>`

Catch only the existing stable boundary: `OSError`, `UnicodeError`, `ValueError`.

### Malformed owner-like line in plan/workflow

`malformed_owner: <path>:<line>: <repr(line)>`

As in F-021, every malformed owner-like line is reported. A malformed owner cannot be hidden by a canonical owner.

### Duplicate canonical declarations in plan/workflow

`duplicate_owner: <path>: lines <comma-separated-line-numbers>`

If malformed and duplicate declarations coexist, both structural diagnostics may be emitted, matching the existing F-021 research parser philosophy. Once either structural error exists, suppress `missing_owner`, `unknown_feature`, and `conflicting_owner` for that path.

### Missing declaration/carrier

`missing_owner: <path>`

For a missing test sidecar, `<path>` is the expected `tests/fNNN/issue-owner.txt` path.

### Test sidecar malformed/duplicate distinction

Parse physical lines without accepting extra content:

- exactly one canonical `Issue: #N` line and no other content -> valid;
- two or more canonical lines and no non-canonical content -> `duplicate_owner: <path>: lines <line-numbers>`;
- any non-canonical/extra content -> `malformed_owner: <path>: invalid_sidecar_content`.

A malformed sidecar does not also receive duplicate/missing/relationship diagnostics.

### Unknown feature

Only after one locally valid owner exists:

`unknown_feature: <path>: F-NNN`

### Conflicting downstream owner

Only after one locally valid owner and one valid research authority exist:

`conflicting_owner: <path>: F-NNN: expected #<research>, found #<declared>`

### Invalid research authority suppression

For any feature in `invalid_features`, retain downstream local structural diagnostics but emit neither `unknown_feature` nor downstream `conflicting_owner`. The research diagnostic is the root cause.

### Global authority failure

If F-021 reports `authority_error` because `docs/research` is missing/not a directory or has no F-series artifacts, return the research authority failure without relationship scanning. Preserve current wrong-root/no-authority behavior exactly.

## 7. Tests-only RED contract

Use deterministic temporary filesystem fixtures and load the real checker module as F-021 does. Avoid timing races, network access, Git state, or third-party dependencies.

The focused test module must prove at least:

1. research F-015/#87 + workflow F-015/#90 -> exact downstream `conflicting_owner`;
2. research F-015/#87 + test sidecar F-015/#90 -> exact downstream `conflicting_owner`;
3. matching plan + `.yml` workflow + test sidecar all pass;
4. `.yaml` is independently in scope;
5. present plan with no owner -> `missing_owner`;
6. present workflow with no owner -> `missing_owner`;
7. present `tests/fNNN` package with no sidecar -> `missing_owner` at the expected sidecar path;
8. malformed plan/workflow owner is stable and suppresses relationship noise;
9. duplicate plan/workflow owner is stable;
10. duplicate test sidecar is distinguished from arbitrary malformed extra content;
11. locally valid downstream feature with no research allocation -> `unknown_feature`;
12. research-only feature with no downstream namespaces passes;
13. multiple plans/amendments for one feature pass only when every claim matches research;
14. invalid/conflicting research authority suppresses downstream unknown/conflict noise while local downstream errors remain visible;
15. research read failure suppresses relationship noise for that known F ID;
16. downstream read/decode failure -> stable `read_error` and no relationship noise;
17. diagnostics are stable across different creation/enumeration order;
18. global missing/no research authority preserves exact F-021 authority-error behavior without downstream avalanche;
19. direct CLI output/exit matches `check_repository` on a downstream failure;
20. current real repository passes `check_repository(ROOT)`.

### Intended RED attribution

On the tests-only head, the existing checker ignores plans/workflows/test packages. Therefore tests requiring downstream conflict/missing/malformed/duplicate/unknown/read diagnostics must fail. Controls for research-only behavior, F-021, D-006, and the current repository must pass.

A valid RED run must not fail because F-023's own plan/workflow/test package lacks ownership metadata.

## 8. RED workflow

Add `.github/workflows/f023-downstream-ownership-enforcement.yml` with `# Issue: #115` in its first 12 lines.

Events:

- push on `impl/f023-downstream-ownership-enforcement`;
- pull requests touching:
  - `docs/research/F-*.md`;
  - `docs/plans/F-*.md`;
  - `.github/workflows/f*.yml`;
  - `.github/workflows/f*.yaml`;
  - `tests/f*/**`;
  - `scripts/check_f_series_ownership.py`;
  - `tests/f023/**`;
  - F-023 research/plan/workflow files;
  - `CONTRIBUTING.md`.

Matrix: Python 3.10 and 3.12.

Steps:

1. exact-head checkout;
2. Python setup;
3. run `python -m unittest discover -s tests/f023 -v`;
4. `if: always()` run F-021 regressions;
5. `if: always()` run D-006 regressions;
6. `if: always()` run `python scripts/check_f_series_ownership.py .`.

Do not run the generic repository-wide unittest command here; `full-suite.yml` owns it.

## 9. Minimal GREEN implementation

After observed RED, edit only `scripts/check_f_series_ownership.py` to add the richer internal research state and downstream scanners required above.

Implementation constraints:

- reuse F-021 research parsing instead of copying it into a second authority parser;
- do not import `scripts/research/d005_downstream_ownership_inventory.py`;
- preserve `check_artifacts()` and `scan_repository()` compatibility;
- use exact filename regexes, not broad prefix matching;
- sort filesystem candidates and final diagnostics;
- no broad `except Exception`;
- no filesystem mutation;
- no Git/GitHub/network access;
- no runtime package dependency.

After GREEN require F-023, F-021, D-006, direct CLI, and centralized full suite green on Python 3.10/3.12.

## 10. Contributor documentation TDD substep

Only after behavioral GREEN:

1. add a focused F-023 test that reads `CONTRIBUTING.md` and requires contributor-facing statements for:
   - research as sole allocation authority;
   - plan `**Issue:** #N`;
   - workflow `# Issue: #N`;
   - test sidecar `tests/fNNN/issue-owner.txt` with `Issue: #N`;
   - `python scripts/check_f_series_ownership.py .`;
2. commit and observe this documentation test RED while checker behavior remains GREEN;
3. edit only `CONTRIBUTING.md` to satisfy the contract;
4. rerun F-023/F-021/D-006/full suite GREEN.

Do not weaken the test into phrase-only trivia that could pass misleading guidance; it must check all five concrete contributor obligations.

## 11. Integration and final review

Before final review:

- integrate current `main` if it moved;
- compare against current main and verify scope is limited to F-023 plan/tests/workflow, checker, and separately gated contributor docs;
- require focused F-023 Python 3.10/3.12 GREEN;
- F-021 GREEN;
- D-006 GREEN;
- direct checker GREEN;
- authoritative full suite Python 3.10/3.12 GREEN;
- relevant F-007/F-011 CI policy gates GREEN when triggered.

Then obtain a fresh logically independent adversarial review of the exact final head. Review must attack at least:

- accidental second authority model or downstream allocation;
- invalid-authority suppression errors;
- global authority-error avalanche behavior;
- local diagnostic precedence/noise;
- `.yml`/`.yaml` and exact namespace matching;
- test-sidecar duplicate-vs-malformed parsing;
- read/decode failure determinism;
- F-021 callable/diagnostic compatibility;
- D-006 migration-oracle independence;
- missing CI path coverage;
- docs drifting from enforced behavior;
- unrelated runtime/schema/digest changes.

Any material repair invalidates that review and requires exact-head CI plus fresh review again.

## 12. Exit condition

F-023 is complete when a single local checker command deterministically rejects stale/wrong-owner downstream F-series plans, workflows, and test packages against research-owned authority, while preserving F-021 semantics, D-006 migration evidence, research-only feature validity, contributor ergonomics, and all exact-head test/review gates.