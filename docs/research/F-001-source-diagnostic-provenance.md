# F-001: source diagnostic provenance research

**Issue:** #18  
**Recorded:** 2026-09-06  
**Scope:** stability/ergonomics follow-up to I-001 only

## Question

How should ontoTF preserve the identity of the user source being validated when structural JSON Schema validation fails, without changing the established I-001 error categories or conflating source-file failures with schema-file failures?

## Current contract

I-001 introduced `ValidationProblem` with:

- `category`;
- `message`;
- `source_name`;
- `instance_path`;
- `schema_path`.

The accepted I-001 research states that the stable diagnostic boundary is category plus source path plus instance/schema paths. Parse and loading errors already follow that contract because `load_source(path)` sets `source_name = str(path)` before decoding/parsing.

## Reproduced control flow

Current `load_and_validate(path, schema_name)` performs two independent operations:

1. `load_source(path)` — file-aware, so decode/parse failures name `str(path)`;
2. `validate_source(data, schema_name, ...)` — file-unaware, so schema-validation failures currently set `ValidationProblem.source_name` to `schema_name`.

Therefore the same invalid file has inconsistent diagnostic provenance depending on which gate rejects it. A malformed `/tmp/profile.yaml` names `/tmp/profile.yaml`; a well-formed but structurally invalid `/tmp/profile.yaml` names only `profile`.

This is directly visible in `src/ontotf/source_validation.py`: `validate_source()` has no source identity parameter, and the `schema_validation` branch constructs `source_name=schema_name`.

## Direct in-memory validation compatibility

`validate_source(data, schema_name)` is also a public API and has no file path by design. It still needs deterministic source identity in errors. Using the schema name as the default is compatible with current behavior and avoids inventing a pseudo-path.

The smallest compatible API extension is therefore an optional keyword-only `source_name` argument whose default preserves the current in-memory behavior.

## Schema-file failure ownership

`validate_source()` also loads and self-validates the selected schema file. Failures in that phase are not failures in the user's source instance. Existing behavior correctly names the concrete schema file path for:

- schema read/decode/JSON failures;
- wrong/missing Draft 2020-12 declaration;
- JSON Schema meta-schema failures.

The new source identity must not override those diagnostics. `source_name` applies only to validation of the user instance against a valid schema.

## Proposed behavior

- `validate_source(data, schema_name)` remains unchanged from a caller perspective and defaults instance-validation errors to `source_name=schema_name`.
- `validate_source(data, schema_name, source_name=...)` uses the supplied identity only for `schema_validation` problems.
- `load_and_validate(path, ...)` passes `str(Path(path))` as that source identity after loading succeeds.
- schema-file failures continue to report the schema file path.
- decode/parse failures remain owned by `load_source()` and are unchanged.
- category, message, instance path and schema path remain unchanged.

## Rejected alternatives

### Put the path into the schema name

Rejected. `schema_name` selects the registered machine contract and should not carry instance provenance.

### Wrap and rewrite errors in `load_and_validate`

Rejected. Reconstructing `SourceValidationError` after the fact duplicates error-ownership logic and risks losing `instance_path`, `schema_path`, exception chaining, or future diagnostic fields.

### Change `validate_source` to require a source path

Rejected. Direct in-memory validation is a supported API and has no natural filesystem path.

### Add a second exception type for file-backed validation

Rejected. The defect concerns one missing provenance field, not a distinct failure class.

## Regression matrix

1. File-backed schema failure reports the exact source path.
2. Direct in-memory schema failure retains current deterministic schema-name identity.
3. File decode/parse failure still reports the source path.
4. Invalid schema file still reports the schema file path.
5. `instance_path` and `schema_path` remain populated exactly as before for schema-validation errors.
6. Success return values are unchanged.

## Scope boundary

No canonicalization, hashing, semantic reference resolution, evidence validation, parent identity, compatibility evaluation, or profile compilation belongs in this change.

## Recommendation

Add one optional keyword-only source identity parameter to `validate_source()` and have `load_and_validate()` supply the concrete file path. Lock the behavior with a file-backed RED regression plus direct/in-memory and invalid-schema controls.