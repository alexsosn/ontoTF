# D-001: README current-status implementation plan

**Issue:** #24  
**Research:** `docs/research/D-001-readme-current-status.md` at `b481405fa25e25e6ceba8a3aa04cdeea2e250640`  
**Baseline:** `67f55b52cc75eb3704357e4ed70851c5d7db6ad2`

## Goal

Make the repository landing page accurately describe the merged POC foundation and current public Python surface, without documenting active/unmerged work as shipped.

## Scope

README/documentation-only production change plus a narrow documentation contract test and CI workflow.

No Python, schema, digest, mapping, profile, runtime, packaging, or compatibility behavior changes.

## README structure

### 1. Title and one-paragraph purpose

Retain the core statement that ontoTF is an experimental semantic interoperability layer for Text-Fabric / Context-Fabric corpora and that corpus-native scholarly semantics remain authoritative.

Avoid claims that shared ontology projections replace native annotations.

### 2. Current status

Replace bootstrap-era `research only` language with a short factual status:

- foundational research and P-001 design are merged;
- structural source validation (I-001) and deterministic canonicalization/digest primitives (I-002) are implemented on main;
- parent identity, cross-artifact validation, compatibility evaluation, compiler/runtime, and corpus mappings are still being implemented.

Do not mention active PR numbers as stable product documentation.

### 3. Implemented capabilities

Two compact groups:

**Structural source validation**
- strict UTF-8 YAML/JSON loading;
- duplicate-key and non-JSON-value rejection;
- Draft 2020-12 structural schemas;
- stable `SourceValidationError` boundary.

**Canonicalization and digests**
- RFC 8785/JCS canonical JSON;
- source/evidence digest helpers;
- mapping semantic digest;
- profile semantic digest for an already assembled projection;
- stable `DigestError` boundary.

Explicitly avoid saying semantic references/evidence/reviews are cross-validated; that is later work.

### 4. Development/source installation

Document only the verified repository checkout path:

```bash
python -m pip install -e .
```

State Python `>=3.10`.

Do not claim a published PyPI package or stable release channel.

### 5. Minimal usage

Use actual public root exports.

Example A — strict parsing:

```python
from ontotf import loads_source

data = loads_source("a: [1, true, null, text]\n", format="yaml")
```

Example B — file structural validation, clearly described as a caller-owned source path:

```python
from ontotf import load_and_validate

profile = load_and_validate("path/to/profile.yaml", "profile")
```

Example C — canonicalization/digest primitives:

```python
from ontotf import canonical_json_bytes, source_file_digest

canonical = canonical_json_bytes({"b": 2, "a": 1})
digest = source_file_digest(b"a: 1\r\n")
```

No hard-coded hash output is necessary.

### 6. Interoperability targets

Retain the existing target list, framed explicitly as targets rather than completed profile support.

### 7. Project contracts / contributing

Link readers to:

- `AGENTS.md`;
- `docs/plans/P-001-foundation-poc-design.md`;
- `docs/research/`;
- `docs/plans/`;
- GitHub issues.

## RED documentation contract

Before editing README, add `tests/docs/test_readme_status.py` that reads the baseline README and asserts:

1. obsolete phrase `first project phase is **research only**` is absent;
2. `Structural source validation` appears;
3. `Canonicalization and digests` appears;
4. source-install command `python -m pip install -e .` appears;
5. public API names `load_and_validate` and `canonical_json_bytes` appear;
6. README does not claim currently shipped later surfaces by using phrases such as `semantic_search is implemented`, `verified-compatible is implemented`, or `I-003 is implemented`.

On the baseline, at least assertions 1-5 fail for the intended stale-README reason.

Avoid brittle snapshots or exact section prose.

## Workflow

Add `.github/workflows/d001-readme-status.yml` triggered by README, D-001 research/plan/test, and workflow changes.

The workflow:

1. checks out exact head;
2. sets up Python 3.12;
3. installs the package editable so the repository full suite has its normal dependencies;
4. runs `python -m unittest tests.docs.test_readme_status -v`;
5. runs `python -m unittest discover -s tests -v`.

The README test itself requires only stdlib and must not inspect network state.

## GREEN change

After exact-head RED is recorded, rewrite `README.md` according to the structure above, preserving concise prose and the target corpus list.

No other documentation files should need semantic edits.

## Acceptance checks

- README no longer describes implementation as blocked/research-only;
- all implemented-capability statements are supported by exact baseline code/public exports;
- examples use current exported functions;
- no pending implementation is described as available;
- focused documentation and full repository suites pass on exact head;
- diff contains no production-code or schema changes.

## Independent review

Fresh logically-independent adversarial exact-head review must compare README claims to baseline/current merged code and specifically search for:

- overclaiming active PR functionality;
- accidental promise of PyPI/release availability;
- semantic-validation language that exceeds I-001 structural validation;
- wording that makes profile digest look like a whole-profile compiler;
- stale research-only language;
- examples referencing nonexistent committed profile files as though they were shipped fixtures.

Any content change after final review requires a new exact-head review.
