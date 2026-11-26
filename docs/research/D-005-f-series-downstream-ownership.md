# D-005 research — explicit ownership metadata for F-series downstream artifacts

**Issue:** #112  
**Baseline:** `main` `458d087ef7a55049ec6555282d84e6a782ecad74`  
**Type:** repository ergonomics / agentic-loop collision prevention

## Question

Can ontoTF extend F-021's research-authority model to plans, focused workflows, and `tests/fNNN` packages so stale downstream artifacts can be attributed to the wrong issue after current-main integration, without adding a central hand-maintained feature registry or a live GitHub dependency?

## Trigger

The historical collision that motivated F-021 had two lanes using F-015. The later file-identity lane belonged to issue #90 but temporarily created `f015` workflow/test artifacts before being renumbered to F-018. Once legitimate F-015/#87 research exists, filenames alone still cannot distinguish a stale #90 `tests/f015` or `f015-*.yml` artifact from legitimate #87 downstream artifacts.

F-021 deliberately stopped at the property its current tree could prove: research artifacts explicitly carry issue ownership. Issue #112 asks whether downstream artifacts can expose enough local metadata to prove the stronger cross-namespace property.

## Reproducible current-tree audit

The audit is implemented by `scripts/research/d005_downstream_ownership_inventory.py` and run by `.github/workflows/d005-downstream-ownership-research.yml`.

Exact inventory head: `9fa165eb46894748895c8899d1d6c522176e8c8b`  
Workflow run: `34347365306` (Python 3.12, success)

The script first derives the authoritative `F-NNN -> issue` mapping from the post-F-021 `docs/research/F-NNN-*.md` tree. It found 22 feature IDs and no research-authority errors.

It then compares every present downstream F-series namespace against that authority.

### Plans

Current tree contains **22** `docs/plans/F-NNN-*.md` artifacts, including amendments.

- **19** already contain exactly one canonical `**Issue:** #N` header matching research authority.
- **3** are headerless:
  - `docs/plans/F-012-file-hash-object-binding-plan.md` -> research owner #80;
  - `docs/plans/F-014-windows-exact-file-paths-plan.md` -> research owner #84;
  - `docs/plans/F-015-error-precedence-amendment.md` -> research owner #87.
- no current plan declares a conflicting or malformed owner.

Plan ownership is therefore already the dominant convention. It only needs a small compatibility migration and enforcement.

### Focused workflows

Current tree contains **19** `.github/workflows/fNNN-*.yml` files.

- **0/19** currently expose explicit issue ownership under the audited header-comment convention;
- every workflow F ID resolves to a valid research owner;
- therefore filename identity is currently the only ownership signal in the workflow itself.

This is exactly the gap exposed by the historical stale-F-015 case.

### Test packages

Current tree contains **13** `tests/fNNN` directories.

- **0/13** currently expose package-level issue ownership;
- 12 contain `__init__.py`, but `tests/f008` does not;
- some packages contain multiple test modules (for example F-018 and F-021), so per-test-file metadata would duplicate one package ownership fact.

Using `__init__.py` as the owner carrier would also require adding Python package structure to F-008 merely for metadata. Ownership should therefore be stored in a non-Python package-local sidecar.

## Required property

After migration, a current-tree checker should be able to prove all of the following without Git history or network state:

1. F-series research remains the sole allocation authority for `F-NNN -> issue`.
2. Every present `docs/plans/F-NNN-*.md` plan/amendment carries exactly one explicit owner and that owner equals research authority for its F ID.
3. Every present `.github/workflows/fNNN-*.yml` carries exactly one explicit owner and that owner equals research authority for its F ID.
4. Every present `tests/fNNN` package carries exactly one package owner and that owner equals research authority for its F ID.
5. A downstream F ID with no research authority is rejected rather than allocating a feature implicitly.
6. Missing, malformed, duplicate, or conflicting downstream owner metadata fails deterministically.
7. Research-only features remain valid: the checker validates downstream artifacts that exist; it does not require every research feature to have plans/workflows/tests.

This is still a current-tree consistency guarantee. It does not make historical owner metadata immutable and cannot see two never-integrated branches simultaneously.

## Recommended metadata forms

The three namespaces have different native formats; forcing one representation everywhere creates unnecessary semantic side effects.

### Plans

Keep the existing canonical Markdown metadata line in the bounded header region:

```text
**Issue:** #87
```

This reuses the convention already present in 19/22 plan artifacts and can use the same bounded-header grammar as F-021 research ownership.

### Workflows

Use one bounded top-of-file YAML comment:

```yaml
# Issue: #87
```

The checker should read the raw workflow text and accept the owner only from a small fixed header region (for example the first 12 physical lines).

A comment is preferable to adding a workflow-level `env` value: ownership metadata should not alter job environments. An invented top-level YAML key would depend on GitHub accepting schema extensions and is therefore inappropriate. Embedding the issue into `name:` would conflate human display text with machine authority.

### Test packages

Add one package-local sidecar:

```text
tests/f015/issue-owner.txt
```

with exactly:

```text
Issue: #87
```

The sidecar avoids Python import/discovery effects, works for F-008 without introducing `__init__.py`, and records package ownership once even when the package contains multiple test modules.

## Rejected alternatives

### Central feature/downstream manifest

A central JSON/TOML registry mapping F IDs or downstream paths to issues duplicates the authority already present in research and recreates a merge hotspot that every agent must update. It weakens F-021's design advantage: authority should live with the artifact that allocates or claims the namespace.

A generated manifest would be derivable output with no additional authority value. It may be useful as a cache someday but should not become the source of truth.

### Infer downstream owner from filename only

This is the current failure mode. `f015-*` and `tests/f015` prove only that the artifact claims F-015; they do not prove whether the creating lane belongs to #87 or stale #90.

### Put ownership in every test module

Package ownership would be duplicated across files and would become inconsistent as tests are added or split. One package-local sidecar is sufficient.

### Put test ownership in `__init__.py`

F-008 currently has no `__init__.py`; adding one merely for metadata changes Python package structure. A text sidecar has no import semantics.

### Workflow `env` owner

A top-level workflow environment variable would be parseable but would propagate process environment into jobs for a repository-bookkeeping concern. The ownership fact has no runtime meaning.

## Migration cost

A clean enforcement baseline requires **35 current metadata additions**:

- 3 plan header insertions;
- 19 workflow owner comments;
- 13 test-package `issue-owner.txt` sidecars.

No current downstream artifact has a conflicting explicit owner, so this is a deterministic backfill rather than a semantic dispute.

The migration should be separately reviewed before enforcement becomes merge-blocking. Otherwise a tests-only RED for the future checker would fail primarily on accepted legacy gaps rather than on the absence of the checker.

## Recommended implementation sequence

### Phase 1 — metadata migration prerequisite

Create a dedicated repository-metadata ticket that:

1. freezes the exact current 35-artifact migration set from this audit;
2. adds tests/workflow-only RED that independently verifies the research-authority mapping and reports exactly those missing metadata carriers;
3. adds only the three plan headers, 19 workflow comments, and 13 sidecars in GREEN;
4. performs focused/full exact-head regression and fresh independent review;
5. does not implement the reusable downstream checker.

### Phase 2 — downstream ownership enforcement

After the migration merges, create F-023 as the enforcement feature:

1. research authority remains `docs/research/F-NNN-*.md` and can reuse/refactor F-021 parsing semantics rather than create a second registry;
2. plans, workflows and test packages are enumerated from current tree and cross-checked against research owners;
3. deterministic diagnostics distinguish missing, malformed, duplicate, unknown-feature and conflicting-owner cases;
4. a directly runnable repository checker and focused CI gate prevent a stale wrong-owner downstream artifact from merging;
5. plans/workflows/tests are claims only and never allocate a new F ID.

The historical stale-F-015/#90 fixture should be an explicit RED case: research says F-015/#87 while a synthetic workflow comment or test sidecar says #90, and the checker must reject it.

## Interaction with F-021

F-021 remains responsible for research ownership completeness and same-ID consistency. Downstream enforcement should consume the same authority semantics rather than modify F-021 into a heterogeneous multi-namespace parser.

Implementation may share a small repository-tool helper if plan/review shows that doing so avoids duplicated parser rules without creating an installed public API. The architectural ownership split remains:

- research files allocate feature IDs;
- downstream files declare which already-allocated feature/issue they belong to;
- the checker compares claims to authority.

## Non-goals

- no automatic renumbering;
- no immutable-history guarantee;
- no detection of never-integrated competing branches;
- no runtime/schema/digest/ontology behavior change;
- no live GitHub API dependency in normal CI;
- no requirement that research-only features acquire downstream artifacts;
- no central hand-maintained feature registry.

## Conclusion

Explicit downstream ownership is both feasible and useful, but it should not use one physical metadata representation everywhere.

The existing repository already provides the right authority model: F-series research owns the feature ID. Plans are nearly ready for direct cross-checking, while workflows and test packages need local ownership carriers. A three-form local metadata convention—Markdown plan header, workflow header comment, package sidecar—would make the historical wrong-owner stale-artifact case mechanically detectable after integration without adding network/history dependencies or a central registry.

Because the current tree has 35 accepted metadata gaps, migration and enforcement should remain separate reviewed/TDD phases.
