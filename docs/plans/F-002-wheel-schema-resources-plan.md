# F-002: package structural schemas in wheel — implementation plan

**Issue:** #21  
**Research:** `docs/research/F-002-wheel-schema-resources.md` at commit `5f429b649201824d58512c736fe655a91493cf8f`  
**Baseline:** `67f55b52cc75eb3704357e4ed70851c5d7db6ad2`

## Goal

Make default structural validation work from a normal non-editable ontoTF wheel without depending on repository layout, while preserving the existing explicit `schema_root=` override and all schema semantics.

## Scope

This ticket changes only schema resource layout, packaging, lookup, and packaging regressions.

It does not change schema contents, canonicalization/digests, parent-component identity, cross-artifact semantic validation, compatibility evaluation, IR/runtime resolution, or mappings.

## Canonical resource layout

Move the seven canonical JSON Schema files from:

```text
schemas/*.schema.json
```

to:

```text
src/ontotf/schemas/*.schema.json
```

There will be no retained duplicate root schema tree.

`SCHEMA_FILES` remains the public registry of logical schema name -> filename.

## Packaging contract

Add explicit package data in `pyproject.toml`:

```toml
[tool.setuptools.package-data]
ontotf = ["schemas/*.json"]
```

The JSON files are runtime resources of the `ontotf` package and must appear in built wheels below `ontotf/schemas/`.

No runtime dependency is added.

## Runtime lookup API

Keep the existing public signature:

```python
validate_source(data, schema_name, *, schema_root=None, ...)
```

Behavior:

1. Resolve `filename = SCHEMA_FILES[schema_name]` as today.
2. If `schema_root is not None`:
   - form `Path(schema_root) / filename`;
   - read bytes from the filesystem;
   - use `str(path)` for invalid-schema source identity.
3. If `schema_root is None`:
   - obtain `importlib.resources.files("ontotf").joinpath("schemas", filename)`;
   - read bytes from the returned traversable;
   - use stable label `tfont:schemas/<filename>` for invalid-schema source identity.
4. Decode with UTF-8 BOM tolerance exactly as today (`utf-8-sig`).
5. Parse JSON, reject duplicate keys/non-finite constants, require Draft 2020-12, self-check the schema, then validate the instance exactly as today.

A small private helper may return `(schema_bytes, source_label)` so explicit and packaged paths share all parse/meta-validation logic.

Do not convert package resources to `Path`; direct traversable reading keeps zip/import-loader compatibility.

## Existing test migration

Existing I-001 schema contract tests currently bind `SCHEMA_ROOT = ROOT / "schemas"`. Update the fixture path to the new canonical source location:

```python
SCHEMA_ROOT = ROOT / "src" / "ontotf" / "schemas"
```

Tests that intentionally pass `schema_root=SCHEMA_ROOT` continue exercising the explicit override. Existing schema contents and assertions remain unchanged.

Workflow path filters that currently watch `schemas/**` move to `src/ontotf/schemas/**` (or are already covered by `src/ontotf/**`; keep the explicit path only if it adds clarity without duplication).

## RED regression

Add `tests/packaging/test_wheel_schema_resources.py` before any production/package changes.

The RED test will:

1. create a temporary dist directory and install target;
2. run `python -m build --wheel --outdir <dist> .` from repository root;
3. inspect the wheel ZIP and require every `ontotf/schemas/<filename>` listed by `SCHEMA_FILES`;
4. install that exact wheel with `python -m pip install --no-deps --target <target> <wheel>`;
5. serialize the existing `minimal_valid_instances()` fixture to a temporary JSON file;
6. spawn child Python with:
   - `cwd` set to a temporary directory outside the repository;
   - `PYTHONPATH=<target>`;
   - code importing `ontotf.source_validation`, asserting the imported package originates under `<target>`, and calling `validate_source(instance, schema_name)` with no `schema_root` for all seven instances.

On the baseline this must fail because wheel contents lack `ontotf/schemas/*.json` and/or default lookup cannot resolve them.

`build` is a test/CI tool, not a runtime dependency. CI installs it explicitly before running the packaging regression/full suite.

## GREEN implementation

After the RED head is observed:

1. move all seven schema files under `src/ontotf/schemas/` without content edits;
2. add `tool.setuptools.package-data` for `ontotf` schemas;
3. replace repository-relative default lookup with `importlib.resources.files("ontotf")` traversable reads;
4. update existing schema fixture paths/workflow path filters;
5. run focused packaging tests, focused I-001 tests, then the full repository suite.

## Regression matrix

Required GREEN cases:

- wheel archive contains all seven schema JSON resources;
- isolated non-editable wheel import validates all seven minimal instances with default lookup;
- source-tree `validate_source(..., schema_root=explicit_path)` remains green;
- malformed custom schema still reports the custom schema filesystem path;
- packaged default schema errors use deterministic `tfont:schemas/<filename>` source labels;
- every schema still declares Draft 2020-12 and passes `Draft202012Validator.check_schema`;
- no root `schemas/` canonical duplicate remains;
- existing I-002 tests remain green.

## Failure behavior

Packaged resource read failures become `SourceValidationError(category="invalid_schema")`, matching existing schema-file read failures. The message retains the underlying `OSError`/resource error text where available.

Unknown logical schema names remain `unknown_schema` and are resolved before any resource access.

Instance `schema_validation` behavior is unchanged.

## CI

Add or adapt CI so an exact-head run installs `build`, executes the wheel regression, the I-001 suite, and the full repository suite. The packaging regression itself builds/installs a wheel and therefore provides the non-editable-install evidence missing from the existing editable-install job.

## Review gate

Before merge, a fresh logically-independent adversarial reviewer must check the exact head for:

- actual wheel ZIP contents, not only source-tree presence;
- accidental import of the editable/source package in the child process;
- duplicate schema authorities;
- preservation of explicit `schema_root=` behavior and schema error provenance;
- no schema-content changes or I-003/I-004 scope leakage;
- exact-head CI success.

Any material head change after that review invalidates it.
