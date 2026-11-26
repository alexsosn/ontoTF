# F-011 plan: migrate workflow actions off Node 20 runtimes

**Issue:** #78  
**Research:** `docs/research/F-011-node24-actions.md`

## Goal

Move all tracked ontoTF workflow uses of `actions/checkout@v4` to `actions/checkout@v5` and `actions/setup-python@v5` to `actions/setup-python@v6`, with no other workflow-semantic changes.

## Gate sequence

### 1. RED contract

Add `tests/ci/test_node24_action_versions.py` before editing workflows.

The test scans `.github/workflows/*.yml` and fails if:

- any `actions/checkout@v4` remains;
- any `actions/setup-python@v5` remains;
- any checkout invocation uses a major other than v5 for this migration contract;
- any setup-python invocation uses a major other than v6;
- known exact-head checkout expressions in exact-head workflows disappear.

Add a focused workflow `.github/workflows/f011-node24-actions.yml` that runs only the static contract on the migration branch / relevant PR paths. It must itself use the already-selected Node-24 action majors so the focused gate does not introduce another deprecated occurrence.

Record a failing run before production workflow migration. Expected RED is the static contract reporting baseline v4/v5 usages in existing workflows.

### 2. GREEN implementation

Mechanically replace version tokens only:

- `uses: actions/checkout@v4` -> `uses: actions/checkout@v5`
- `uses: actions/setup-python@v5` -> `uses: actions/setup-python@v6`

Do not modify:

- event triggers / path filters;
- permissions;
- runner OS;
- matrices;
- `with:` inputs;
- exact-head checkout refs;
- install commands;
- test commands;
- concurrency;
- job names unless required by existing YAML formatting (not expected).

### 3. GREEN verification

Require:

- focused F-011 static contract GREEN;
- all workflows triggered by the broad `.github/workflows/**` change GREEN;
- representative job log contains no warning that checkout/setup-python target Node 20 and are being forced to Node 24;
- repository compare against current main contains only research, plan, focused CI contract/workflow, and workflow action-version token changes.

### 4. Final integration/review

Before final review, rebuild on then-current `main` if another relevant workflow-producing PR merged. Re-run the static scan so newly added workflows cannot retain deprecated action majors.

A logically independent reviewer must inspect exact final head for:

- accidental trigger/input/test-command drift;
- missing workflow coverage;
- unsupported runner compatibility assumptions;
- interaction with pending centralized full-suite CI;
- exact-head checkout preservation;
- absence of Node-20 runtime warnings.

Any material head change invalidates that review.