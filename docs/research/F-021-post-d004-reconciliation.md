# F-021 research amendment — post-D-004 ownership reconciliation

**Issue:** #99  
**Baseline:** `main` `696b2c050e9d8fca518a9a129a11760d30e5c3b0`  
**Type:** research amendment / implementation unblocking

## Trigger

The accepted F-021 research correctly chose current-tree F-series research ownership as the allocation authority and already stated the intended post-migration rule: every `docs/research/F-NNN-*.md` artifact must declare exactly one issue owner, and multiple same-ID research/evidence/amendment files are legal only when they share that owner.

However, the older inventory text predates one later-added supporting artifact and still describes the prerequisite as four headerless *primary* research files.

D-004 (#104, merged by PR #108) re-audited the complete current research namespace and found a fifth headerless artifact:

- `F-019-cpython-path-conversion-evidence.md` -> issue #94.

That note is not a second F-019 allocation, but it is still an `F-NNN-*.md` research artifact. D-004 therefore added the same #94 owner carried by the primary F-019 research and completed ownership metadata across the whole F-series research namespace.

## Current prerequisite state

At baseline `696b2c050e9d8fca518a9a129a11760d30e5c3b0`:

- every current `docs/research/F-[0-9][0-9][0-9]-*.md` artifact has exactly one `**Issue:** #N` owner in its header region;
- all artifacts sharing one F ID currently agree on one owner;
- the historical backfills are F-012/#80, F-014/#84, F-016/#88, F-017/#91, and F-019 evidence/#94;
- no legacy allowlist is needed;
- F-021 implementation is no longer blocked on D-004.

The older four-primary inventory is retained as historical evidence of the earlier repository state, not as the implementation contract.

## Authority surface

F-021 v1 must enumerate **every** file matching:

```text
docs/research/F-[0-9][0-9][0-9]-*.md
```

There is no primary-vs-supporting exemption in the ownership checker.

For each matching artifact:

1. derive the F ID from the filename prefix;
2. inspect only a bounded metadata/header region;
3. require exactly one well-formed `**Issue:** #<positive integer>` owner declaration;
4. group artifacts by F ID;
5. require every artifact in a group to declare the same owner;
6. emit deterministic sorted diagnostics for missing, malformed/duplicate, or conflicting ownership.

Multiple same-ID files remain legal when they share the same owner. This supports primary research plus evidence/amendment documents without creating a second allocation.

## What v1 can prove

A pure checked-out-tree invariant can reliably detect:

- a new headerless F-series research artifact;
- duplicate valid owner headers in one artifact;
- one F ID represented by artifacts carrying different issue owners;
- malformed/missing owner metadata when the parser treats anything other than one canonical owner line as invalid;
- the observed duplicate-allocation class after mandatory integration with current `main` exposes both ownership claims in one tree.

It does not prove that a sole historical owner declaration was not edited in place. Detecting that requires prior-state authority such as Git history, an immutable generated baseline, or an external service and remains outside F-021 v1.

## Downstream plans, workflows, and tests

The accepted research suggested optionally checking `docs/plans/F-NNN-*`, `.github/workflows/fNNN-*`, and `tests/fNNN/**` as downstream consistency namespaces.

The current-tree audit shows why this must not be overstated:

- plans generally carry enough document metadata to be checked more deeply if a future contract requires it;
- workflows and test directories encode an F ID in their path/name but usually do not carry an issue owner;
- checking only that a workflow/test F ID exists in research would not have identified the historical stale `f015` artifacts from the later-renumbered #90 lane, because F-015 is itself a legitimate feature owned by #87.

Therefore F-021 v1 should **not** claim to detect wrong-owner downstream workflow/test artifacts from filenames alone.

The core v1 merge-blocking invariant is research ownership. Downstream path checks may be added only where they prove a precise property without pretending to infer issue ownership that is not encoded.

A richer downstream-ownership scheme can be researched separately if needed, for example by deciding whether plans/workflows/tests should carry explicit machine-readable owner metadata.

## Implementation shape

The implementation should be repository tooling / CI infrastructure, not runtime ontoTF behavior.

Preferred properties:

- pure Python;
- no GitHub API calls;
- no Git/merge-base requirement;
- no hand-maintained feature registry or legacy allowlist;
- deterministic results independent of filesystem enumeration order;
- reusable classifier/check function that can be exercised on synthetic fixtures and the checked-out repository;
- repository-state CI that fails closed on invalid ownership metadata.

The implementation location should be frozen in the plan. A small repository tool/module is preferable to embedding the logic only inside a unittest so agents and local developers can invoke the checker directly.

## RED requirements

Before implementation, deterministic tests should pin at least:

1. two artifacts with one F ID and two different issue owners -> fail;
2. two artifacts with one F ID and the same owner -> pass;
3. one new F ID with one owner -> pass;
4. missing owner -> fail;
5. duplicate valid owner lines -> fail;
6. malformed owner-like metadata -> fail rather than being silently accepted as owned;
7. body prose containing issue numbers does not count as ownership;
8. unrelated R/P/I/A/D research files are ignored;
9. diagnostics are sorted and stable across input/enumeration order;
10. the post-D-004 checked-out repository passes once the checker exists.

The implementation RED must fail because the checker/API does not yet exist, not because repository metadata is still incomplete.

## Scope and non-goals

- no automatic renumbering;
- no permanent ownership registry;
- no network lookup in normal CI;
- no Git-history dependency;
- no historical owner-immutability guarantee;
- no attempt to observe two completely independent never-integrated branches simultaneously;
- no runtime/schema/digest/ontology behavior change;
- no claim that workflow/test filenames alone reveal their issue owner;
- no broad ticket-taxonomy redesign.

## Reconciled decision

D-004 has completed the metadata prerequisite. F-021 may proceed to plan/TDD implementation using **all F-series research artifacts** as the current-tree ownership authority.

The v1 checker should enforce one explicit issue owner per F-series research artifact and one owner per F ID, with deterministic local diagnostics and no registry/network/history dependency. Any downstream ownership guarantee beyond that must be separately justified by metadata that actually encodes the owner.
