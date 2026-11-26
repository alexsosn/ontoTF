# F-021 implementation plan — enforce unique F-series research ownership

**Issue:** #99  
**Research:** `docs/research/F-021-feature-id-uniqueness.md` + `docs/research/F-021-post-d004-reconciliation.md`  
**Baseline:** `main` `696b2c050e9d8fca518a9a129a11760d30e5c3b0`  
**Type:** repository ergonomics / merge-time invariant

## 1. Goal

Add a deterministic, directly runnable repository checker that prevents one `F-NNN` research namespace from carrying multiple GitHub issue owners and rejects invalid/missing ownership metadata before merge.

The checker operates only on current checked-out repository state. It does not use Git history, a hand-maintained feature registry, or the GitHub API.

## 2. Frozen authority surface

F-021 v1 scans every regular file matching:

```text
docs/research/F-[0-9][0-9][0-9]-*.md
```

The `F-NNN` prefix in the filename is the feature identifier. There is no primary/supporting/evidence exemption.

Research artifacts are allocation authority. Multiple same-ID artifacts are legal only when every valid artifact declares the same issue owner.

F-021 v1 does **not** infer issue ownership from `docs/plans`, workflow filenames, or `tests/fNNN` paths. Follow-up issue #112 owns research for richer downstream ownership metadata.

## 3. Implementation location and repository-tool surface

Create:

- `scripts/check_f_series_ownership.py`
- `tests/f021/__init__.py`
- `tests/f021/test_feature_id_ownership.py`
- `.github/workflows/f021-feature-id-ownership.yml`

No `src/ontotf/**`, schema, package metadata, digest, semantic-validator, runtime, or ontology file is in scope.

The script is repository tooling rather than an installed ontoTF API. It must remain directly executable with the repository Python:

```bash
python scripts/check_f_series_ownership.py
```

It also exposes pure functions that tests load by exact file path; `scripts` does not become an installed/importable package.

Planned functions:

```python
check_artifacts(artifacts: Mapping[str, str]) -> list[str]
scan_repository(root: Path) -> tuple[dict[str, str], list[str]]
check_repository(root: Path) -> list[str]
main(argv: Sequence[str] | None = None) -> int
```

`artifacts` maps repository-relative POSIX-style paths to UTF-8 Markdown content. Returned diagnostics are sorted strings.

The CLI accepts at most one optional repository-root positional argument. With no argument, the default root is `Path(__file__).resolve().parents[1]`. It prints one diagnostic per line to stderr and exits `1` when diagnostics exist; it prints nothing and exits `0` on success. Invalid CLI argument count may use `argparse`'s normal behavior and is outside the ownership contract.

## 4. Filename, authority, and enumeration contract

The checker recognizes artifact paths with this semantic shape:

```regex
^docs/research/(F-[0-9]{3})-.*\.md$
```

`check_artifacts()` ignores mapping entries that do not match that path shape. This makes synthetic use deterministic and preserves the same authority surface as repository scanning. It must not reinterpret R/P/I/A/D paths as F-series ownership.

The repository checker must fail closed when the authority surface itself is absent. Before enumeration, `scan_repository(root)` checks `root / "docs" / "research"`:

- missing or non-directory authority path ->
  `authority_error: docs/research: missing_or_not_directory`
- existing authority directory with zero matching F-series research artifacts after enumeration ->
  `authority_error: docs/research: no_f_series_artifacts`

These repository-level diagnostics are distinct from per-file read errors. They prevent an incorrect CLI root, accidental removal of the authority directory, or deletion of all F-series research from producing a vacuous success.

When the authority directory exists, `scan_repository(root)`:

1. enumerates entries matching `F-[0-9][0-9][0-9]-*.md`;
2. includes entries for which `Path.is_file()` is true;
3. stores repository-relative POSIX-style paths such as `docs/research/F-019-...md`;
4. attempts to read UTF-8 text;
5. returns `(artifacts, scan_diagnostics)`;
6. does not give filesystem enumeration order semantic meaning.

A per-file read failure must not silently remove an artifact from the invariant. Catch only ordinary repository-read failures (`OSError`, `UnicodeError`, `ValueError`) and emit a stable diagnostic without platform-dependent exception text:

```text
read_error: <path>: <ExceptionClass>
```

A file with a read error is absent from `artifacts` and represented by that diagnostic. Enumeration/authority diagnostics and read diagnostics share the `scan_diagnostics` return list. `check_repository(root)` returns the lexical sort of `scan_diagnostics + check_artifacts(artifacts)`.

Process-fatal exceptions are not broadly swallowed.

Unrelated R/P/I/A/D research files are outside enumeration and ignored.

## 5. Bounded ownership metadata grammar

For each F-series artifact, inspect a bounded header region only:

- physical lines 2 through 12 inclusive (line 1 is the H1/title position);
- stop earlier at the first line beginning exactly `## `;
- body prose after that boundary is never ownership metadata.

A canonical owner line is:

```text
**Issue:** #<positive decimal integer>
```

with optional trailing whitespace only.

Canonical regex:

```regex
^\*\*Issue:\*\* #([1-9][0-9]*)\s*$
```

### Owner-like malformed lines

Within the bounded header region, any line whose left-stripped text begins with `**Issue:**` but does not match the canonical regex is malformed ownership metadata.

Examples include:

- `**Issue:** #0`
- `**Issue:** 99`
- `**Issue:** #abc`
- ` **Issue:** #99` (leading indentation is not canonical)
- `**Issue:** #99 extra`

A file containing one canonical owner plus one malformed owner-like line remains invalid. Malformed metadata cannot be hidden by also supplying a valid line.

Lines elsewhere containing `#99`, `Issue`, or prose references do not count unless they are owner-like inside the bounded header region.

## 6. Per-artifact validity contract

For each scanned/matching path, ownership is valid only when:

1. there are zero malformed owner-like header lines; and
2. there is exactly one canonical owner line.

Diagnostics are frozen as follows:

- no canonical owner and no malformed owner-like line:
  `missing_owner: <path>`
- one or more malformed owner-like lines:
  one diagnostic per malformed physical line:
  `malformed_owner: <path>:<line>: <repr(line_text)>`
- two or more canonical owner lines, regardless of whether values match:
  `duplicate_owner: <path>: lines <comma-separated line numbers>`

When an artifact has any malformed or duplicate-owner diagnostic, it contributes no owner to cross-artifact conflict grouping. This prevents syntactically invalid files from manufacturing secondary conflict noise.

If an artifact has malformed lines and zero canonical owners, do not additionally emit `missing_owner`; malformed diagnostics are sufficient and more specific.

If an artifact has malformed lines plus multiple canonical owners, emit malformed diagnostics and the duplicate-owner diagnostic; do not use the artifact for conflict grouping.

## 7. Cross-artifact ownership contract

After validating artifacts independently, group valid artifacts by filename-derived `F-NNN`.

If one feature ID has more than one distinct issue number among valid artifacts, emit exactly one deterministic conflict diagnostic:

```text
conflicting_owner: F-NNN: #<issue>=<path>[,<path>...]; #<issue>=<path>[,<path>...]
```

Issue groups are sorted numerically; paths within each issue group are lexically sorted.

Same-feature/same-owner multi-artifact groups pass.

## 8. Global determinism

`check_artifacts()` returns the complete diagnostic list sorted lexically after all per-artifact and conflict diagnostics are generated.

`check_repository()` lexically sorts the combined scan + ownership diagnostic set.

Synthetic tests must permute input dictionary insertion order and still receive byte-identical diagnostic ordering.

The checker must not depend on filesystem enumeration order, locale, Git state, network state, issue titles, or timestamps.

## 9. Tests-only RED

Before `scripts/check_f_series_ownership.py` exists, add `tests/f021/**` and the focused workflow only. Do not add an empty/placeholder checker.

The test module has two classes.

### `RepositoryMetadataControls`

These controls do not import the planned checker. They independently establish the post-D-004 prerequisite state:

- `docs/research` exists and contains F-series research artifacts;
- every current F-series research artifact has one canonical owner in the reviewed bounded region;
- no current same-ID group has multiple owner values;
- F-019 primary and CPython evidence both carry #94;
- no unexpected headerless artifact exists.

These controls must pass on the tests-only RED head.

### `FeatureOwnershipCheckerREDTests`

The test file defines the exact expected checker path and a loader using `importlib.util.spec_from_file_location`.

RED behavior is deliberately narrow:

- `test_checker_module_exists` is the single intended failing test while the checker path is absent;
- all remaining checker-contract tests are decorated/skipped when that exact path does not exist;
- no placeholder module is added merely to make imports work.

This produces one attributable RED failure rather than a wall of repeated `FileNotFoundError`/import errors. After GREEN creates the checker, the skip condition disappears and the already-authored contract tests execute unchanged.

Required checker-contract cases:

1. different owners under one F ID -> one `conflicting_owner` failure;
2. same owner under one F ID -> pass;
3. new F ID with one canonical owner -> pass;
4. missing owner -> `missing_owner`;
5. duplicate same owner lines -> `duplicate_owner`;
6. duplicate different owner lines -> `duplicate_owner` and no conflict from that invalid artifact;
7. malformed owner alone -> `malformed_owner`, no redundant `missing_owner`;
8. malformed owner plus canonical owner -> still `malformed_owner`;
9. malformed plus duplicate canonical -> both malformed and duplicate diagnostics, no conflict grouping from that file;
10. body prose issue mention after `## ` does not count;
11. owner on physical line 12 is accepted; line 13 is outside the contract;
12. first `## ` stops metadata scanning earlier;
13. unrelated namespace paths supplied to `check_artifacts()` are ignored;
14. diagnostics are stable across input order;
15. `scan_repository()` returns a stable `read_error` diagnostic on an injected ordinary read failure;
16. missing/non-directory `docs/research` -> `authority_error: docs/research: missing_or_not_directory`;
17. existing `docs/research` with zero F-series artifacts -> `authority_error: docs/research: no_f_series_artifacts`;
18. `check_repository(current_root)` passes on the post-D-004 tree;
19. CLI exits `0` and is silent on current repository;
20. CLI pointed at a wrong/empty repository root exits `1` with the authority diagnostic;
21. CLI on a temporary synthetic repository with a conflict exits `1` and prints the sorted conflict diagnostic.

The RED workflow is valid only when repository metadata controls pass and exactly the module-existence contract fails because the planned checker file is absent—not because current ownership metadata is broken.

## 10. Focused workflow

Create `.github/workflows/f021-feature-id-ownership.yml`.

Matrix:

- Ubuntu 24.04
- Python 3.10
- Python 3.12

Steps:

1. checkout exact PR/source head;
2. setup Python;
3. run repository metadata controls;
4. run intended F-021 checker tests;
5. under `if: always()`, run D-004 repository-state ownership tests as a migration regression;
6. under `if: always()`, run `python scripts/check_f_series_ownership.py` only when the checker file exists; on RED the file-existence guard skips this direct invocation so failure attribution remains the single module-existence test.

Repository-wide discovery remains owned only by `.github/workflows/full-suite.yml`.

Workflow triggers cover:

- `docs/research/F-*.md`
- `docs/research/F-021-*.md`
- `docs/plans/F-021-*.md`
- `scripts/check_f_series_ownership.py`
- `tests/f021/**`
- `tests/d004/**`
- `.github/workflows/f021-feature-id-ownership.yml`

## 11. Minimal GREEN

After valid RED evidence, add only `scripts/check_f_series_ownership.py` as the implementation needed to make the checker-contract tests pass.

Do not weaken/change RED assertions unless a test defect is independently demonstrated. Any new production/runtime ontoTF code is out of scope.

No third-party dependency should be required; do not add one.

## 12. Documentation / contributor ergonomics

Baseline `CONTRIBUTING.md` describes the research process but does not yet state the F-series owner-header invariant or direct checker command.

After core GREEN, add a docs/static assertion **before** changing `CONTRIBUTING.md`. That RED must demonstrate the missing contributor-facing rule. Then make a docs-only GREEN that states concisely:

- new `docs/research/F-NNN-*.md` artifacts require exactly one canonical `**Issue:** #N` header;
- same F ID may have multiple research/evidence/amendment artifacts only when all share the same issue owner;
- run `python scripts/check_f_series_ownership.py` before opening/finalizing a PR.

This documentation substep must not alter checker semantics. If current main moves and independently gains an equivalent rule before this substep, rerun the docs assertion and reconcile rather than duplicate it.

## 13. Exact-head regression gate

Before final review require:

- focused F-021 Python 3.10/3.12 green;
- D-004 ownership regression green;
- authoritative full repository suite green on Python 3.10/3.12;
- F-007 single-full-suite ownership green;
- F-011 Node-24 action-major policy green;
- direct CLI invocation green on exact head;
- compare against then-current `main` contains only F-021 research amendment, plan, tests/workflow, repository checker, and the separately TDD-gated CONTRIBUTING change;
- no `src/**`, schemas, package metadata, digest/runtime/semantic code, or unrelated docs changes.

If `main` moves, integrate current main and rerun exact-head CI. Re-scan current F-series research ownership after integration; a newly added artifact must satisfy the checker rather than be added to an allowlist.

## 14. Fresh independent adversarial review

Final review must attack at least:

- primary/supporting exemption accidentally reintroduced;
- authority directory/all-artifact deletion vacuously passing;
- malformed owner-like lines accepted because one canonical line also exists;
- duplicate same-owner lines accepted;
- invalid artifacts participating in conflict grouping and producing misleading extra diagnostics;
- body prose or line-13 owner references counted as metadata;
- unrelated synthetic paths treated as ownership input;
- nondeterminism from dict/filesystem ordering;
- conflict formatting/order instability;
- read failures silently dropping artifacts;
- CLI wrong-root success;
- CLI exit/output contract;
- use of Git, GitHub API, registry, or hidden allowlist;
- downstream workflow/test owner claims leaking into v1 despite lack of metadata;
- accidental ontoTF runtime/package changes;
- current-main integration drift.

Any blocker returns to the earliest affected research/plan/RED/GREEN gate.

## 15. Exit condition

F-021 completes when the checked-out repository can deterministically enforce exactly one valid issue owner per F-series research artifact and exactly one owner per F ID through a directly runnable pure-Python checker and CI gate, fails closed when its research authority surface is absent, uses no registry/network/history dependency, has contributor instructions updated, passes focused/full exact-head CI, and receives a fresh logically-independent adversarial review approving the exact final head.
