# F-002: wheel-safe schema resources

**Issue:** #21  
**Recorded:** 2026-09-06  
**Phase:** research only; no production/package changes in this commit  
**Baseline:** `main` at `67f55b52cc75eb3704357e4ed70851c5d7db6ad2`

## Question

How should ontoTF ship and resolve its seven structural JSON Schemas so that the same default validator works from a source checkout, editable install, ordinary wheel install, and import loaders that do not expose repository-relative files?

## Observed repository state

At the baseline:

- `pyproject.toml` discovers packages only under `src/` with `[tool.setuptools.packages.find] where = ["src"]`;
- the seven runtime schemas are stored at repository-root `schemas/`, outside `src/ontotf`;
- `src/ontotf/source_validation.py` resolves the default schema root with `Path(__file__).resolve().parents[2] / "schemas"`;
- I-001 CI installs with `pip install -e .`, so its passing tests exercise the source checkout rather than the contents and runtime layout of a built wheel;
- callers may pass `schema_root=` explicitly, and that override is already part of the validator API used by tests.

The current default lookup therefore depends on repository layout. It is not a package-resource lookup.

## Setuptools packaging evidence

Current setuptools 84.0.0 documentation defines package data as non-Python files installed alongside Python packages and recommends the common runtime-data case be kept inside the package directory. Its `package_data` configuration maps package names to file globs and does not require `MANIFEST.in` or a VCS integration. The documentation also notes that `include-package-data` only concerns files found inside package directories; repository-root files are not made package resources merely because they are tracked by Git.

Primary source:

- https://setuptools.pypa.io/en/latest/userguide/datafiles.html

Relevant project consequence: the present root `schemas/*.json` files are outside the discovered `ontotf` package and no package-data rule maps them into the wheel. A wheel-content regression is needed rather than relying only on static inference.

## Python package-resource evidence

Python 3.10+ provides `importlib.resources.files()` (added in 3.9), returning a `Traversable` for package-associated resources. The API is deliberately loader-independent: resources need not be ordinary filesystem paths and can be read directly from the returned traversable. `as_file()` is only necessary when downstream code requires a concrete path.

Primary source:

- https://docs.python.org/3/library/importlib.resources.html

ontoTF only needs to read UTF-8 JSON schema bytes/text, so direct `Traversable.read_bytes()` is sufficient; no extraction to a temporary path is required.

## Layout alternatives

### A. Keep root `schemas/` and duplicate/copy them into `src/ontotf`

Rejected. It creates two mutable schema trees and an authority/drift problem. A generated-copy workflow would add machinery whose only purpose is repairing an avoidable layout split.

### B. Install repository-root schemas as generic `data_files`

Rejected. Runtime location is platform/install-scheme dependent and remains outside the Python package resource model. It also preserves the fragile assumption that `__file__` can navigate to a sibling installation directory.

### C. Move the canonical schemas under `src/ontotf/schemas/` and ship them as package data

Recommended. The package contains the single canonical schema set, setuptools can include `schemas/*.json` explicitly, and runtime lookup uses `importlib.resources`. Source-tree tests and wheel installs then exercise the same resource path.

The directory does not need to become an importable Python subpackage; it can remain package data beneath `ontotf`.

## API compatibility

`validate_source(data, schema_name, *, schema_root=None, ...)` should preserve `schema_root=` as an explicit filesystem override. Only the `None`/default branch changes:

- explicit `schema_root`: read `<schema_root>/<filename>` exactly as today and retain filesystem-path diagnostics;
- default: read `files("ontotf").joinpath("schemas", filename)` and use a deterministic package-resource label for invalid-schema diagnostics.

The public schema names and `SCHEMA_FILES` mapping do not change.

## Wheel regression strategy

A useful packaging test must not import from the checkout accidentally. It should:

1. build a wheel with the standard PEP 517 frontend (`python -m build --wheel` or equivalent isolated wheel build);
2. install that wheel into a temporary target directory;
3. launch a child Python process with `cwd` outside the repository and `PYTHONPATH` pointing only at the temporary installed target;
4. import installed `ontotf` and validate representative/minimal instances using default schema lookup;
5. additionally inspect the wheel archive or installed target for all seven `ontotf/schemas/*.json` resources.

The RED version should fail on the baseline because no such installed resources exist/default lookup escapes toward a nonexistent repository-level `schemas` directory.

## Test and dependency implications

The current project does not declare a runtime dependency on `importlib_resources`; none is required because Python >=3.10 already includes the needed standard-library API.

A wheel-building regression needs a build frontend in CI. Prefer adding the PyPA `build` package only to the CI/test command environment rather than as a ontoTF runtime dependency. The wheel itself should remain dependent only on actual runtime libraries.

## Interaction with active work

F-002 is independent of I-003 parent identity. It changes packaging/resource location and validator schema lookup only. It must not alter digest algorithms, component identity, semantic validation, compatibility state, or mappings.

Moving the schema directory can require path updates in existing I-001 tests/workflow triggers. Those updates are mechanical consequences of making the package resource canonical, not semantic schema changes.

## Risks

- **Editable install hides packaging defects:** retain an explicit non-editable wheel test permanently.
- **Zip/import-loader assumptions:** use `importlib.resources` traversables rather than converting package resources to `Path`.
- **Schema authority drift:** move, do not copy, the canonical schema files.
- **I-003 branch conflict:** avoid changing schema contents; only relocate them and adapt lookup/tests. Rebase conflicts, if any, should therefore be path-level rather than semantic.
- **Invalid-schema diagnostics:** explicit `schema_root` must continue naming the concrete schema path; packaged-default failures need a stable package-resource label.

## Recommendation

Move the single canonical schema set to `src/ontotf/schemas/`, declare `ontotf = ["schemas/*.json"]` package data, resolve default schemas with `importlib.resources.files("ontotf")`, and add an isolated wheel-install regression that proves all seven schemas are usable without the repository checkout. Preserve `schema_root=` as the filesystem override and keep this ticket out of I-003/I-004 semantics.
