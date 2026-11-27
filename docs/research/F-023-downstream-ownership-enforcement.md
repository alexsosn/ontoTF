# F-023 research — enforce downstream F-series ownership against research authority

**Issue:** #115  
**Baseline:** `main` `c18f86651174a500ba1c8ecf3fd7879bba180239`  
**Baseline tree:** `14da7d15e5ef6f81a04429d85354e677248a70af`  
**Type:** repository ergonomics / agentic-loop collision prevention

## 1. Question

After D-006 migrated explicit issue ownership into every current F-series plan, focused workflow, and test package, what is the smallest reusable current-tree enforcement architecture that rejects stale or wrong-owner downstream artifacts without creating a second feature registry or a second definition of research authority?

F-023 must preserve the F-021 authority model:

- `docs/research/F-NNN-*.md` allocates `F-NNN -> issue`;
- downstream plans, workflows, and test packages only claim an already allocated feature/issue;
- a downstream filename alone never allocates ownership;
- current-tree consistency is the guarantee; immutable history and never-integrated branches remain outside scope.

## 2. Post-D-006 baseline is clean

D-006/#114 merged as `c18f86651174a500ba1c8ecf3fd7879bba180239`.

The merge commit has tree `14da7d15e5ef6f81a04429d85354e677248a70af`, byte-identical to the independently reviewed D-006 final head `f16546ed2d9b31b0b231bcbec866bc5fe048578b`. Therefore the final D-006 inventory result applies exactly to current `main`, not merely to a similar branch state:

- 22 valid research-owned F-series feature IDs, zero research-authority errors;
- 22 F-series plan/amendment artifacts, all matching research ownership;
- 19 focused `fNNN-*` workflows, all matching research ownership;
- 13 `tests/fNNN` packages, all with matching `issue-owner.txt` ownership;
- zero missing, malformed, duplicate, conflicting, or unknown downstream claims in the migrated scope.

The final D-006 exact-head CI also ran the D-006 migration matrix, F-021 ownership checks, every touched F-series workflow, and the authoritative full suite successfully before merge.

This satisfies #115's prerequisite: F-023 RED can now fail because downstream enforcement behavior is absent, not because accepted legacy carriers remain unmigrated.

## 3. Existing implementations and their authority roles

### 3.1 F-021 checker is the durable authority engine

`scripts/check_f_series_ownership.py` is already the directly runnable repository checker for F-series research ownership. It provides:

- bounded research metadata parsing;
- exact `F-NNN` research enumeration;
- missing/malformed/duplicate owner diagnostics;
- same-ID conflicting-owner detection;
- deterministic sorted diagnostics;
- fail-closed handling for missing/non-directory authority root, empty authority, and read/decode failures;
- `python scripts/check_f_series_ownership.py [root]` CLI semantics with exit 0 on clean state and 1 on diagnostics.

F-021 tests already exercise this behavior through both pure artifact fixtures and filesystem/CLI fixtures.

That script should remain the authority engine. Creating a separate F-023 checker that reparses research ownership would create two definitions of the same authority contract and a future drift risk.

### 3.2 D-005 inventory is a research/migration oracle, not the enforcement implementation

`scripts/research/d005_downstream_ownership_inventory.py` already knows the three migrated downstream carrier forms and can classify them as matching/missing/malformed/duplicate/unknown/conflicting. D-006 hardened that script's carrier grammar before migration.

It should **not** be promoted into the permanent checker because:

- it has research-reporting semantics and a JSON inventory shape rather than fail-closed checker/CLI semantics;
- it owns its own research-authority parser, duplicating F-021;
- it uses repository-global paths and status summaries useful for audit, not the minimal reusable checker surface;
- retaining it as an independent regression oracle is more valuable than making production enforcement depend on the same code that proved the migration.

Recommendation: extend the F-021 checker in place and keep D-006/D-005 tests/inventory as independent regressions.

## 4. Downstream enumeration contract

F-023 should enforce only the namespaces already researched and migrated by D-005/D-006.

### Plans

Enumerate regular files matching:

`docs/plans/F-[0-9][0-9][0-9]-*.md`

The feature ID comes from the filename. Owner metadata uses the same bounded Markdown header grammar as research:

`**Issue:** #N`

The existing F-021 header boundary should be reused: physical lines 2–12, stopping before the first `## ` section heading. Trailing whitespace accepted by the existing canonical regex remains compatible.

Multiple plans/amendments under one feature are legal. Each present plan independently must carry exactly one valid owner matching research authority.

### Focused workflows

Enumerate regular files in `.github/workflows` whose basenames match case-sensitively:

`f[0-9][0-9][0-9]-*.yml` or `f[0-9][0-9][0-9]-*.yaml`

Owner metadata is one bounded raw-text header comment in the first 12 physical lines:

`# Issue: #N`

The checker must inspect raw text, not parsed YAML. Ownership is repository metadata and must not affect GitHub Actions semantics.

Both `.yml` and `.yaml` are part of the contract even though current migrated workflows use `.yml`.

### Test packages

Enumerate direct child directories of `tests` whose basenames match exactly:

`f[0-9][0-9][0-9]`

Each present package must contain a regular file:

`tests/fNNN/issue-owner.txt`

The accepted carrier is exactly one canonical line:

`Issue: #N`

with the D-006-compatible optional final newline. No `__init__.py`, test-module comment, `OWNER`, or other inferred source may satisfy the owner requirement.

A package directory exists independently of whether it currently contains Python files; if the `tests/fNNN` namespace is present, the ownership sidecar is required.

## 5. Authority remains one-way

The reusable checker must derive research authority first. Downstream carriers never add entries to that map.

For a downstream artifact with exactly one locally valid owner:

- if no research artifact claims that F ID, report `unknown_feature`;
- if research resolves the F ID to one issue and the downstream owner differs, report `conflicting_owner`;
- if the owner matches, the claim is valid.

A research-only feature with no plans, focused workflow, or test package remains valid.

This asymmetry is the point of the design: research allocates; downstream metadata only proves attribution.

## 6. Diagnostic precedence and invalid-authority handling

D-005's inventory was sufficient for migration, but permanent enforcement needs a sharper distinction between **unknown authority** and **invalid authority**.

If a research artifact for `F-015` exists but is unreadable, malformed, missing its owner, duplicated, or participates in a conflicting-owner group, downstream F-015 claims must not be mislabeled `unknown_feature`. The feature is known to the namespace but its authority is unusable.

Recommended precedence:

### Global authority failures

If `docs/research` is missing/not a directory or contains no F-series research artifacts, preserve F-021's existing `authority_error` and stop relationship enforcement. This prevents a wrong repository root from producing an avalanche of downstream `unknown_feature` noise.

### Research path/group failures

Preserve current F-021 diagnostics and semantics for:

- research `read_error`;
- `malformed_owner`;
- `duplicate_owner`;
- `missing_owner`;
- research same-ID `conflicting_owner`.

Track the F IDs of research paths/groups whose authority could not be resolved. Downstream local metadata may still be checked structurally, but **relationship diagnostics are suppressed for those invalid-authority features**. The research diagnostic is already the root cause.

### Downstream path-local failures

For each downstream carrier, classify local metadata before comparing it to authority:

1. `read_error` if required file content cannot be read/decoded;
2. `malformed_owner` for owner-like text that violates the carrier grammar or otherwise invalid sidecar content;
3. `duplicate_owner` when more than one canonical declaration appears where the format can express duplicates;
4. `missing_owner` when the required declaration/carrier is absent;
5. only after one canonical owner exists, `unknown_feature` if no research allocation exists;
6. only after one canonical owner and one valid research owner exist, `conflicting_owner` if issue numbers differ.

Do not add redundant `missing_owner`, `unknown_feature`, or `conflicting_owner` noise for a path already invalid at an earlier local stage.

For the test sidecar, two canonical `Issue: #N` lines should be classified as duplicate rather than merely as generic malformed content; arbitrary extra/invalid content remains malformed. This improves diagnostics without broadening the accepted one-line grammar.

### Ordering

Collect diagnostics across namespaces and return them in stable lexical order, as F-021 already does. Filesystem enumeration order must not affect output.

## 7. Filesystem/read failure policy

The permanent checker is repository tooling, not a general filesystem security API, but it must fail closed rather than silently skip unreadable carriers.

Preserve F-021's stable read boundary: catch `OSError`, `UnicodeError`, and `ValueError` from `Path.read_text()` and report the repository-relative path plus exception type, not platform-specific exception text.

Downstream namespace directories are optional as collections: a synthetic/reduced repository may legitimately have research-only features and no plans/workflows/test packages. Their absence is therefore an empty downstream namespace, not an authority error.

The **research authority directory is different**: it is required. Missing/non-directory/empty authority remains a fatal F-021 authority error.

An owner carrier that is required because its namespace exists but is absent as a regular file is `missing_owner`, not silently ignored.

## 8. Smallest reusable architecture

Recommended implementation architecture:

1. **Extend `scripts/check_f_series_ownership.py` in place.** Keep it repository-local; do not add an installed/public ontoTF runtime API.
2. Preserve the existing F-021 pure research checker behavior and tests.
3. Refactor only enough private parsing/scanning code to let research and plan Markdown share the same bounded parser without changing F-021 diagnostics.
4. Add downstream scanners/check functions for plans, workflows, and test packages.
5. Make the existing `check_repository(root)` and CLI enforce both research authority and downstream claims.
6. Do not import or call `scripts/research/d005_downstream_ownership_inventory.py` from the permanent checker.
7. Keep D-006 tests/inventory as an independent oracle/regression suite.

A separate `scripts/check_f_series_downstream_ownership.py` is rejected: it would either duplicate authority parsing or require users/CI to remember two commands for one repository invariant.

A new package under `src/ontotf` is also rejected: feature-ticket ownership is repository development metadata, not ontoTF runtime behavior.

## 9. CLI ergonomics

Retain the existing invocation:

`python scripts/check_f_series_ownership.py [root]`

No new command or third-party dependency is needed.

The CLI should remain silent on success, print sorted diagnostics to stderr on failure, and return 0/1 as today. Its description/help can be broadened from “research issue ownership” to F-series research/downstream ownership.

This is preferable to JSON output for enforcement. The D-005 inventory already provides JSON when an audit report is useful.

## 10. CI ownership and trigger coverage

F-023 should add a dedicated focused workflow rather than overload F-021's historical workflow identity.

The F-023 workflow should run on Python 3.10 and 3.12 and trigger on at least:

- `docs/research/F-*.md` because authority changes can invalidate downstream claims;
- `docs/plans/F-*.md`;
- `.github/workflows/f*.yml` and `.github/workflows/f*.yaml`;
- `tests/f*/**` so creating a new F-series test package without a sidecar cannot evade the gate;
- `scripts/check_f_series_ownership.py`;
- `tests/f023/**`;
- F-023 research/plan/workflow files;
- `CONTRIBUTING.md` if contributor documentation is included.

The focused workflow should run:

- F-023 focused tests;
- F-021 ownership regression tests;
- D-006 migration/metadata regressions;
- direct local checker invocation.

It must not duplicate the repository-wide test command owned by `full-suite.yml`. F-007/F-011 remain policy regressions where their path triggers cause them to run.

The existing F-021 workflow may continue to invoke the now-stronger checker on research changes. F-023's workflow supplies the missing downstream path coverage, so F-021's workflow need not be broadened merely to duplicate F-023.

## 11. RED strategy

Because the F-021 checker file already exists, F-023 RED should prove **absent downstream behavior**, not assert that the script file is absent.

Before checker implementation, tests should create synthetic repository trees with valid research authority and downstream carriers, then call the existing `check_repository(root)` or the reviewed public-to-repository-tool callable surface.

The current checker ignores downstream namespaces, so the historical wrong-owner fixture should incorrectly return success on the RED head. That is the intended failure.

Required RED cases from #115 remain:

1. research F-015/#87 + workflow F-015/#90 -> conflicting-owner failure;
2. research F-015/#87 + test sidecar F-015/#90 -> conflicting-owner failure;
3. matching plan/workflow/test claims -> pass;
4. present plan/workflow/test namespace missing its owner -> fail;
5. malformed owner -> deterministic fail;
6. duplicate owner declarations -> fail;
7. downstream F ID without research -> `unknown_feature`;
8. research-only feature with no downstream -> pass;
9. multiple plans/amendments for one feature pass only when each owner matches;
10. `.yml` and `.yaml` workflow forms both covered;
11. diagnostics stable across creation/enumeration order;
12. current post-D-006 repository passes metadata controls while the intended new synthetic enforcement assertions are RED.

Additional RED needed from this research:

13. invalid/conflicting research authority for a feature does not create downstream `unknown_feature` noise;
14. missing authority directory/no research short-circuits relationship diagnostics with existing F-021 authority error;
15. downstream read/decode failure is preserved as stable `read_error` rather than skipped;
16. a two-line canonical test sidecar is a duplicate-owner failure while arbitrary extra content is malformed;
17. a new `tests/fNNN` package containing Python files but no sidecar is detected;
18. direct CLI emits the same diagnostics/exit code as the callable checker.

RED must be committed and observed before modifying `scripts/check_f_series_ownership.py`.

## 12. Contributor documentation

Current `CONTRIBUTING.md` documents only the research `**Issue:** #N` requirement and says to run the checker for F-series research metadata. Once F-023 becomes merge-blocking, that is incomplete contributor guidance.

Recommendation: update `CONTRIBUTING.md` **inside the F-023 ticket but as a separate TDD-gated documentation substep** after the enforcement contract is frozen.

Before editing the document, add a focused test requiring it to explain:

- research is the allocation authority;
- plan owner line `**Issue:** #N`;
- workflow header comment `# Issue: #N`;
- test package sidecar `tests/fNNN/issue-owner.txt` with `Issue: #N`;
- direct checker invocation.

This is preferable to a separate ticket because the contributor contract is part of making this exact enforcement usable; the separate RED-before-doc-edit step preserves TDD discipline and prevents documentation from getting ahead of implementation.

## 13. Migration and regression interaction

D-006 is now a prerequisite regression, not implementation code for F-023.

F-023 must keep:

- F-021 research ownership tests green;
- D-006 current-tree metadata controls green;
- the D-005/D-006 inventory able to report the migrated tree as fully matching;
- no exemptions/allowlists for pre-D-006 carriers, because the migration removed the legacy gap.

If current `main` gains a new F-series downstream artifact before F-023 finalization, integrate main and require that artifact to satisfy the same explicit ownership contract. Do not add a temporary legacy exception.

## 14. Rejected alternatives

### Separate F-023 checker command

Rejected because it duplicates or depends on a second research-authority implementation and makes local/CI use two commands for one invariant.

### Promote the D-005 inventory script

Rejected because research inventory/reporting and merge-blocking enforcement have different interfaces. Keeping the inventory independent gives stronger regression evidence.

### Central feature registry

Rejected for the same reason as F-021/D-005: it duplicates artifact-local authority and creates a hand-maintained merge hotspot.

### Filename-only ownership

Rejected because it cannot detect the historical stale F-015/#90 artifact once legitimate F-015/#87 exists.

### Git/GitHub authority lookup

Rejected. The required property is fully representable in the migrated current tree. Network/history dependencies would add failure modes without strengthening the scoped guarantee.

### Installed `ontotf` runtime API

Rejected. Repository ticket ownership has no semantic/runtime role in ontoTF corpus interoperability.

## 15. Research conclusion

F-023 is unblocked and implementable without new architecture outside repository tooling.

The smallest durable design is to extend `scripts/check_f_series_ownership.py` so the existing F-021 research authority becomes the single source used to validate all present downstream claims. Plans reuse the bounded Markdown owner grammar, focused workflows use bounded raw comments, and test packages use one exact non-Python sidecar. Relationship diagnostics must distinguish truly unknown features from features whose research authority is present but invalid, and all output remains deterministic/fail-closed.

A dedicated F-023 workflow should provide downstream path coverage while F-021/D-006 stay as independent regressions. Contributor documentation should be updated in the same ticket only after a separate docs RED gate.

No Git history, GitHub API, central registry, installed runtime API, automatic renumbering, or requirement for every research feature to have downstream artifacts is justified by the current evidence.

Proceed to planning only after a fresh logically-independent review of this exact research head.