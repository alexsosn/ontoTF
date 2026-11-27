# D-001: README current-status research

**Issue:** #24  
**Recorded:** 2026-09-06  
**Baseline:** `main` at `67f55b52cc75eb3704357e4ed70851c5d7db6ad2`  
**Phase:** research only; README unchanged in this commit

## Question

What can the repository landing page truthfully present as implemented and usable on the exact merged baseline, without turning active PRs or later POC design into shipped functionality?

## Observed README drift

`README.md` currently says:

- status is `research bootstrap / proof-of-concept planning`;
- the first project phase is `research only`;
- implementation tickets are blocked until research contracts are established.

Those statements describe the pre-P-001 repository but are stale on the baseline. P-001 is merged, I-001 and I-002 are merged production code, and the package has an importable public API.

The introductory semantic principles remain accurate: ontoTF is an experimental semantic interoperability layer for Text-Fabric / Context-Fabric corpora, corpus-native semantics remain authoritative, and the listed corpora are interoperability targets rather than claims of completed mappings.

## Exact merged production surface

`src/ontotf/__init__.py` on the baseline exports these I-001 source-validation APIs:

```text
SourceValidationError
load_source
loads_source
validate_source
load_and_validate
```

I-001 behavior implemented on main includes:

- strict UTF-8 YAML/JSON source loading;
- duplicate-key rejection;
- recursive conversion/rejection to the exact plain JSON-compatible model;
- stable structural error categories;
- local Draft 2020-12 validation against seven structural source schemas;
- structural assessment-dependent mapping shapes without cross-artifact semantic resolution.

The same public module exports these I-002 digest/canonicalization APIs:

```text
DigestError
canonical_json_bytes
normalize_source_bytes
source_file_digest
source_bundle_digest
evidence_payload_digest
evidence_record_digest
mapping_semantic_digest
profile_semantic_digest
```

I-002 behavior implemented on main includes:

- RFC 8785/JCS canonical JSON for the accepted ontoTF JSON domain;
- safe-number/non-finite/lone-surrogate failure behavior;
- source BOM and line-ending normalization for source digests;
- deterministic source-bundle digest;
- exact evidence-payload digest;
- normalized evidence-record digest;
- mapping semantic digest/projection rules;
- already-assembled profile semantic digest rules.

The README must not imply that profile semantic digest assembles or validates a whole profile: I-002 explicitly requires an already assembled semantic projection and does not perform I-004/I-006 work.

## Package and installation facts

`pyproject.toml` on the baseline states:

```text
name = ontotf
version = 0.0.0
requires-python = >=3.10
```

Runtime dependencies are bounded `jsonschema`, `rfc8785`, and `ruamel.yaml` lines.

The repository CI installs the checkout with:

```bash
python -m pip install -e .
```

This is therefore a supported source/development installation example. There is no evidence in the baseline that a public PyPI release is part of the current contract, so the README must not say `pip install ontotf` installs a published release.

## Minimal usage examples grounded in merged APIs

### Parse + structural validation from a source file

The current public API supports:

```python
from ontotf import load_and_validate

profile = load_and_validate("profiles/example/profile.yaml", "profile")
```

This is structurally correct as an API example, but the repository does not yet ship a final example profile at that path. To avoid implying a committed profile exists, README prose should label the path as a user's own profile file or use a text-based example instead.

### In-memory strict source parsing

A self-contained example can use:

```python
from ontotf import loads_source

data = loads_source("schema_version: 1\nprofile_id: demo\n", format="yaml")
```

That demonstrates loading but not a complete schema-valid profile. It should not pretend the two-field object passes the profile schema.

### Canonical JSON / digest primitive

A fully self-contained implemented example is:

```python
from ontotf import canonical_json_bytes, source_file_digest

canonical_json_bytes({"b": 2, "a": 1})
source_file_digest(b"a: 1\r\n")
```

The README need not hard-code output digests; contract vectors already live in tests and the I-002 plan.

## Merged foundation versus pending work

Merged foundation that may be referenced as design/background:

- R-001 through R-005 research;
- P-001 first POC design;
- I-001 structural validator;
- I-002 canonicalization/digest library.

At the baseline, the following are not merged and must not be presented as available:

- I-003 parent component identity;
- cross-artifact semantic validation;
- compatibility evaluation/report generation;
- normalized IR compiler;
- runtime semantic resolver/search surface;
- generated reference/publication outputs;
- final corpus profiles or mappings;
- the source-diagnostic and package-resource follow-up PRs active elsewhere.

A compact status statement should say that implementation has started and the foundational validator/digest layers are merged, while the POC compiler/runtime/profile layers remain under development.

## Documentation pointers

The landing page should route readers to authoritative deeper material without duplicating it:

- `AGENTS.md` — semantic principles and required development/review loop;
- `docs/plans/P-001-foundation-poc-design.md` — accepted POC architecture/semantic contracts;
- `docs/research/` — empirical and standards research;
- `docs/plans/` — implementation/design plans;
- GitHub issues/PRs — current implementation state.

The README should not restate detailed ontology governance or compatibility semantics that already have authoritative documents and are still only partially implemented.

## Documentation test boundary

A small README contract can safely assert facts unlikely to be formatting-sensitive:

- stale exact phrase `first project phase is **research only**` is absent;
- README names structural validation and canonicalization/digests as currently implemented;
- README includes `python -m pip install -e .`;
- README contains actual root public API names such as `load_and_validate` and `canonical_json_bytes`;
- README does not claim I-003+ surfaces such as `verified-compatible`, `semantic_search`, or a finished corpus profile are currently shipped.

Tests should avoid pinning prose sentences or section order beyond those factual markers.

## Recommendation

Replace the bootstrap-era status text with a compact implementation-status README grounded strictly in `67f55b52...`. Keep the project purpose and target-corpus list, add source installation and minimal public-API examples, point to authoritative research/design documents, and state later compiler/runtime/profile work as development roadmap rather than available behavior.
