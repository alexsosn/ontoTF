# F-011: migrate workflow actions off deprecated Node 20 runtimes

**Issue:** #78  
**Status:** research complete  
**Recorded:** 2026-09-08

## Problem

Current ontoTF GitHub Actions logs repeatedly emit warnings that `actions/checkout@v4` and `actions/setup-python@v5` target deprecated Node 20 and are being forced to run on Node 24 by GitHub-hosted runners. This is CI/runtime-maintenance debt: the workflow logic itself passes, but it relies on compatibility coercion that can eventually disappear.

## Upstream evidence

Official upstream sources consulted:

- `actions/checkout` releases: https://github.com/actions/checkout/releases
- `actions/checkout` changelog: https://github.com/actions/checkout/blob/main/CHANGELOG.md
- `actions/setup-python` releases: https://github.com/actions/setup-python/releases
- `actions/setup-python` README: https://github.com/actions/setup-python/blob/main/README.md

Relevant findings:

- `actions/checkout` v5 moved the action runtime to Node 24. Newer majors exist, but v5 is the narrowest major that removes the Node-20 runtime dependency.
- `actions/setup-python` v6 moved the action runtime to Node 24. Newer majors exist, but v6 is the narrowest major that removes the Node-20 runtime dependency.
- `setup-python` v6 requires Actions runner v2.327.1 or later.
- Current ontoTF hosted CI logs show runner `2.337.0`, so the documented runner compatibility floor is already satisfied.

## Version decision

Use:

- `actions/checkout@v5`
- `actions/setup-python@v6`

Do **not** jump to the latest major solely for freshness. The purpose of this ticket is to remove the deprecated Node-20 runtime with the smallest compatibility surface. A future action-major refresh can be reviewed independently if upstream behavior changes warrant it.

## Repository scope

The migration is workflow-only. Existing workflow semantics must remain unchanged:

- triggers and path filters;
- permissions;
- matrices and Python versions;
- exact-head `ref:` expressions where already present;
- `fetch-depth`, `persist-credentials`, and other checkout inputs;
- setup-python inputs;
- install commands;
- focused and full test commands;
- concurrency behavior.

No Python package, schema, digest, semantic, ontology, or corpus code is in scope.

## Validation strategy

A static contract should scan every tracked `.github/workflows/*.yml` file and require:

1. no `actions/checkout@v4` remains;
2. no `actions/setup-python@v5` remains;
3. checkout usages are `actions/checkout@v5`;
4. setup-python usages are `actions/setup-python@v6`;
5. the migration does not erase known exact-head checkout expressions in workflows that currently pin source heads.

The test must be committed before workflow edits and must fail on current `main`, establishing RED.

After GREEN, at least one exact-head job log should be inspected to confirm the old forced-Node-20 warning is absent.

## Risks

The main risk is accidental workflow drift while touching many files. Therefore implementation should be mechanical version-token replacement only. Any unrelated workflow cleanup, trigger changes, action input edits, or CI deduplication belongs elsewhere.

The migration must also remain compatible with pending F-007 centralized-CI work: that branch can replay the same action-major policy when it is rebuilt on a final base.