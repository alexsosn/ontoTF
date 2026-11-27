# F-021 research — detect duplicate F-series ticket identifiers before merge

**Issue:** #99  
**Baseline:** `main` `200dcaba593d02d4d903aa424d6c7fec574f2ff2`  
**Type:** repository ergonomics / agentic-loop collision prevention

## Question

Can ontoTF mechanically prevent two distinct feature tickets from claiming the same `F-NNN` namespace without adding a permanently hand-maintained feature registry or a network-dependent GitHub lookup to ordinary CI?

## Trigger

Two independent active lanes were assigned `F-015`:

- #87 — direct source-validation boundary;
- #90 — file-object identity hardening, later renumbered to F-018.

Before the collision was noticed, the second lane had accumulated research, plan, workflow and `tests/f015/**` artifacts. Once both lines are integrated, those names are not cosmetic: they collide in test packages, workflow families, documentation identity and review traceability.

The failure mode is therefore suitable for a repository invariant.

## Current F-series inventory

Current `main` contains one primary research file for each of `F-001` through `F-014`, then `F-016` and `F-017`. `F-015` is intentionally absent from this baseline because #87 is still in final review at the time of this research.

Research is the correct allocation authority because research-only conclusions such as F-013 and F-017 legitimately have no implementation workflow/test family. Plans, workflows and tests can only be downstream consistency checks.

### Explicit issue metadata

The earlier feature research files consistently declare an owner near the top:

- F-001 -> #18;
- F-002 -> #21;
- F-003 -> #26;
- F-004 -> #28;
- F-005 -> #30;
- F-006 -> #32;
- F-007 -> #34;
- F-008 -> #66;
- F-009 -> #69;
- F-010 -> #71;
- F-011 -> #78;
- F-013 -> #81.

At least F-012, F-014, F-016 and F-017 are accepted research without an `**Issue:**` header even though their authoritative tickets are #80, #84, #88 and #91.

That historical gap is small but materially affects what a pure current-tree checker can prove.

## What a pure current-tree check can and cannot know

A checker that sees only the checked-out tree can group `docs/research/F-NNN-*.md` by F ID and inspect explicit issue declarations. It can therefore reject the observed collision once both allocations are visible in one integrated tree: two files under one F ID that declare different issue numbers are contradictory.

It cannot, without prior-state authority, prove that the sole owner declaration of an existing file was not edited in place. For example, if the only F-001 file changes from `**Issue:** #18` to `**Issue:** #999`, a current-tree-only checker sees only `#999`. Detecting that reassignment requires a real merge-base/history input, an immutable generated baseline/registry, or an external authority. F-021 does **not** claim to solve owner-header tampering.

Likewise, while accepted headerless legacy files remain in the tree, a current-tree checker cannot distinguish a newly introduced headerless `F-022` from an accepted headerless `F-012` without either prior-state knowledge or a hard-coded legacy allowlist.

Those two limits invalidate the earlier idea that no metadata migration is needed.

## Decision: migrate the small legacy metadata gap first

For the simplest durable invariant, perform a separately reviewed metadata-only migration that adds the known authoritative issue headers to the four accepted legacy research files:

- F-012 -> #80;
- F-014 -> #84;
- F-016 -> #88;
- F-017 -> #91.

After that migration, every committed primary F-series research artifact can be required to carry exactly one explicit `**Issue:** #N` declaration. No permanent legacy allowlist is then necessary.

This migration does not rewrite issue numbers or research conclusions; it only makes existing ownership machine-readable. It should be completed before F-021's enforcement implementation becomes merge-blocking.

## Post-migration authority model

After legacy ownership metadata is complete, the static current-tree contract can be simple:

1. every `docs/research/F-NNN-*.md` carries exactly one well-formed `**Issue:** #N` declaration in a bounded metadata/header region;
2. all research artifacts sharing one F ID declare the same issue number;
3. multiple research/evidence/amendment files for one F ID are legal when ownership is consistent;
4. two distinct explicit issue numbers for one F ID fail deterministically;
5. plans/workflows/test-package namespaces may be checked against the set of owned research IDs, but cannot allocate an ID themselves;
6. diagnostics are sorted deterministically.

The observed collision is then rejected after mandatory current-main integration: once #87's F-015 research lands, a stale F-015 artifact for #90 creates two owners in the same current tree.

### New IDs

A brand-new feature ID is accepted only when its research artifact declares one issue owner. A new headerless F-series file fails without needing to know whether the ID existed on an earlier commit, because headerless F-series research is no longer valid after the migration.

### Existing IDs

Additional research/evidence/amendment files under an existing ID must declare the same owner as the other files currently present under that ID. A conflicting allocation fails.

This is a current-tree consistency guarantee, not an immutable-history guarantee. Editing the sole existing owner declaration in place is outside F-021's guarantee and should be a separate research problem if it becomes an operational threat.

## Why not a permanent hand-maintained registry

A registry such as `feature-ids.json` would duplicate information already mandatory in research artifacts and create another file agents must update atomically. After the small legacy metadata migration, the research files themselves are sufficient current-tree authority for collision detection.

## Why not GitHub API lookup in ordinary CI

GitHub issue/PR lookup would add network availability, authentication, pagination/rate-limit handling and mutable external titles. It is unnecessary for the demonstrated merge-time collision: mandatory current-main integration brings the first allocation into the second branch's tree, where conflicting explicit owner metadata becomes locally visible.

The checker cannot see two completely independent branches before either allocation lands. That limitation is explicit and accepted by issue #99.

## Why not Git history in the v1 invariant

A Git-aware merge-base checker could additionally detect owner-header reassignment, but it would require a sufficiently deep checkout, base-ref availability and a more complicated local invocation contract. None of that is necessary for the issue's required fail condition: one F ID mapping to multiple issue numbers after current-main integration.

F-021 v1 should therefore stay current-tree-only after the metadata migration. A future anti-tampering ticket may deliberately adopt Git/base-state authority if needed.

## Proposed static contract

A later plan may implement a pure-Python current-tree classifier/check with no GitHub or Git calls at test runtime:

1. enumerate `docs/research/F-[0-9][0-9][0-9]-*.md`;
2. extract the `F-NNN` prefix from each path;
3. extract exactly one issue declaration from a bounded metadata/header region;
4. reject missing, malformed or duplicate declarations;
5. group by F ID and reject multiple distinct issue numbers;
6. permit multiple artifacts only when ownership is consistent;
7. optionally verify downstream `docs/plans/F-NNN-*`, `.github/workflows/fNNN-*` and `tests/fNNN/**` namespaces refer to an owned research ID;
8. return sorted deterministic diagnostics.

Synthetic classifier tests can permute path/content inputs. A repository-state test validates the checked-out tree. No test needs a synthetic "real merge base" because the v1 production invariant does not claim to compare history.

## Plans/workflows/tests as consistency checks

Research ownership remains authoritative. A future plan should strongly consider checking that newly/currently present downstream feature namespaces resolve to an owned research ID. This catches stale renames such as the current file-identity lane's `f015-*` workflow/tests after issue #90 was renumbered to F-018.

These checks must not require every research-only feature to have downstream artifacts.

## RED strategy after research approval and metadata migration

Before implementation, tests should pin at least:

1. two different explicit issues under one F ID -> fail;
2. two files with the same F ID and same issue -> pass;
3. brand-new F ID with one explicit issue -> pass;
4. any F-series research file with no issue metadata -> fail;
5. malformed or duplicate `**Issue:**` declarations -> fail deterministically;
6. unrelated R/P/I/A/D research files are ignored;
7. research-only F ID without plans/workflows/tests remains valid;
8. downstream plan/workflow/test artifact with unknown or mismatched feature ID fails if that consistency layer is adopted;
9. diagnostics are sorted and stable across filesystem enumeration/input order;
10. the post-migration checked-out repository passes the invariant.

The RED must fail because the ownership classifier/check does not yet exist, not because accepted historical research still lacks metadata. That is why the metadata migration is a prerequisite rather than an allowlist inside the checker.

## Scope and non-goals

- no automatic renumbering;
- no rewriting historical issue numbers or research conclusions;
- no live GitHub API dependency in normal CI;
- no Git/merge-base dependency in the v1 checker;
- no promise to detect two completely independent, never-integrated branches simultaneously;
- no promise to detect in-place reassignment of the sole owner header without prior-state authority;
- no runtime/schema/digest/ontology behavior change;
- no general ticket taxonomy redesign beyond the F-series collision demonstrated here.

## Conclusion

F-021 is implementable as a local deterministic merge-time namespace invariant, but a small metadata-only prerequisite is required first.

After F-012/F-014/F-016/F-017 receive their already-known issue headers, every F-series research artifact can carry one machine-readable owner. The checked-out tree can then reject duplicate/conflicting allocations and stale downstream feature namespaces without a permanent registry, Git history or GitHub API lookup. Mandatory current-main integration is sufficient to catch the observed class of collision before merge; immutable owner-history enforcement is explicitly outside the v1 guarantee.
