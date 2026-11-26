# I-002 canonicalization and digest research

**Issue:** #16  
**Recorded:** 2026-09-06  
**Dependency:** I-001 merged as `f7d358fe7e90680b6216ed6cb4b6f624dd2bcdd2`

## 1. Research question

Choose the smallest reproducible implementation strategy for P-001 canonical JSON and digest primitives without leaking into parent identity, cross-artifact semantic validation, compatibility evaluation, or IR compilation.

The difficult part is not SHA-256. It is reproducing RFC 8785/JCS exactly across Python runtimes, especially number serialization and non-ASCII object-key ordering.

## 2. Primary specification: RFC 8785

Primary source: RFC 8785, *JSON Canonicalization Scheme (JCS)*, June 2020: https://www.rfc-editor.org/rfc/rfc8785.html

Relevant normative constraints:

- JCS uses the I-JSON subset: duplicate object names are prohibited; strings must be Unicode; number data must be representable as IEEE-754 double precision.
- Unicode string values are preserved as authored; JCS does **not** apply Unicode normalization.
- no insignificant whitespace is emitted.
- literals and strings use ECMAScript-compatible JSON serialization.
- finite numbers use the ECMAScript number serialization algorithm. RFC 8785 explicitly notes that this part is sufficiently complex that it does not reproduce the algorithm and points implementers to V8/Ryu/reference implementations.
- NaN and infinities are invalid and must terminate canonicalization.
- object properties are sorted recursively by raw property names interpreted as arrays of unsigned UTF-16 code units, not Python Unicode-code-point order, locale order, UTF-8 byte order, or case-folded order.
- array element order must not change, although objects nested inside arrays are recursively canonicalized.
- lone surrogate/non-UTF-8-compatible string data must fail.

Appendix B supplies number vectors and recommends the interoperability integer range `-(2**53)+1` through `2**53-1` for values intended as integers.

### Consequence for ontoTF

A private serializer built from `json.dumps(sort_keys=True)` is insufficient:

1. Python key sorting is not defined by RFC 8785's UTF-16-code-unit order for non-BMP/BMP edge cases.
2. Python's native JSON/float formatting is not an explicit implementation of the ECMAScript algorithm required by JCS.
3. default Python JSON APIs admit values/forms ontoTF has already excluded at the I-001 boundary unless they are guarded explicitly.

## 3. Candidate Python implementation: `rfc8785`

Package: https://pypi.org/project/rfc8785/  
Source: https://github.com/trailofbits/rfc8785.py

Observed release at research time: `0.1.4` (PyPI upload 2024-09-27), Python `>=3.8`, pure Python, no runtime dependencies, Apache-2.0.

The current implementation source inspected at commit `02ecc03315ff17dd90fc892da4faa6998fa9314b`, `src/rfc8785/_impl.py`, directly implements the RFC-specific behavior relevant to ontoTF:

- `dumps()` emits UTF-8 `bytes`.
- dictionary keys are sorted by `key.encode("utf-16be")`.
- invalid Unicode during UTF-8 encoding raises a canonicalization error.
- non-finite floats raise `FloatDomainError`.
- integers outside `-(2**53)+1 .. 2**53-1` raise `IntegerDomainError`.
- `-0.0` serializes as `0`.
- the package implements the ECMAScript-compatible float formatting logic rather than delegating to ordinary `json.dumps`.

One deliberate library behavior is **broader than ontoTF's data model**: `rfc8785` accepts both lists and tuples as JSON arrays. I-001 defines ontoTF JSON values as plain `list`, not tuple. Therefore ontoTF must validate the input recursively before delegating to the library rather than expose `rfc8785.dumps()` directly.

### Maintenance/risk assessment

The package is small, pure Python, no-dependency and purpose-specific. Depending on it is lower implementation risk than reimplementing ECMAScript number formatting. The public dependency should be bounded to the current compatible minor line for the POC:

```toml
rfc8785>=0.1.4,<0.2
```

The ontoTF fixed-vector suite remains authoritative for compatibility, so a future package upgrade cannot silently move canonical bytes.

## 4. ontoTF canonical JSON input boundary

I-002 should reuse the I-001 accepted JSON model and narrow numeric behavior where JCS requires it:

```text
None | bool | safe int | finite float | str | list[JSONValue] | dict[str, JSONValue]
```

Additional JCS guard:

- integer range: `-(2**53)+1 <= n <= 2**53-1`;
- floats finite only;
- tuple, Decimal, bytes, set, custom Mapping/Sequence subclasses, datetime and other values rejected rather than coerced;
- dictionary keys must be exact strings;
- Unicode is preserved without NFC/NFD normalization;
- invalid/lone surrogate strings fail during canonical UTF-8 serialization.

The wrapper should expose a ontoTF-owned stable error rather than make callers depend on third-party exception types.

## 5. Source digest is a separate byte-normalization contract

P-001 §16.1 does **not** define source-file identity as JCS over parsed YAML/JSON. It deliberately hashes authoring bytes after only these transformations:

1. bytes must decode as UTF-8;
2. remove one optional leading UTF-8 BOM;
3. normalize CRLF and bare CR to LF;
4. preserve every other character/whitespace byte;
5. SHA-256 the resulting UTF-8 bytes.

This means comments, spacing and other authoring-only changes can change `source_digest` while leaving semantic digests unchanged.

Implementation should normalize decoded text, then re-encode UTF-8. It must not call `.strip()`, normalize Unicode, rewrite tabs/spaces, sort YAML, or parse/re-emit the source.

The bundle `source_digest` is SHA-256 over JCS of a list of records:

```json
[
  {"logical_path": "...", "file_sha256": "sha256:..."}
]
```

The list is sorted by `logical_path` before canonicalization. Duplicate logical paths should fail locally because otherwise source-bundle identity is ambiguous.

## 6. Accepted P-001 evidence digest projections

P-001 fixes two evidence algorithms:

### `ontotf-evidence-payload-sha256-v1`

SHA-256 of the exact external payload bytes reviewed. No URI, filename, retrieval timestamp or transport metadata substitutes for the payload.

### `ontotf-evidence-record-sha256-v1`

SHA-256 of JCS over a normalized evidence projection containing:

- `evidence_id`;
- `kind`;
- `source_uri` when present;
- `source_revision` when present;
- `reviewed_content`;
- source/license fields that the schema declares normative.

The projection explicitly excludes `content_digest`, timestamps, local paths, human citation formatting and display-only metadata. `content_digest` must never be part of its own input.

I-001's evidence schema currently makes `license_ref` normative-looking and `citation` display-only. For the POC, `license_ref` should participate when present; `citation` must not.

## 7. Mapping semantic projection

P-001 §14.2 defines the mapping digest over behavior/publication-affecting fields:

- `mapping_id`;
- `profile_id`;
- `native_selector`;
- `native_dependencies`;
- `external_target` or `candidate_projections`;
- `assessment`;
- `publication_relation`;
- `applicability`;
- `ontology_lock` or candidate-specific locks;
- normalized `(evidence_id, content_digest)` evidence bindings.

Excluded:

- `mapping_semantic_digest` itself;
- the entire `review` record;
- rationale prose;
- `introduced_in` / `changed_in` release-navigation metadata.

The helper should be projection-only: it must not resolve dependencies, ontology locks or evidence IDs. Existence/equality checks remain I-004.

## 8. Profile semantic projection boundary

P-001 §16.3 says profile semantic identity includes information that spans multiple artifacts: expected parent-manifest semantic identity, dependencies, ontology locks/target pins, mapping semantic records/digests and review-readiness state.

Therefore I-002 must **not** define `profile_semantic_digest(raw_profile_manifest)` and silently resolve files. That would leak into I-004/I-006.

Recommended API accepts an already assembled, JSON-compatible **profile semantic projection** and canonicalizes/hashes it. I-002 owns deterministic bytes and an exclusion guard for volatile fields; later compiler/semantic-validator tickets own how the projection is assembled and validated.

Mandatory exclusion at this layer:

- `profile_version`;
- release-navigation metadata;
- rationale/display prose;
- local paths;
- CI/build IDs;
- timestamps/generated-at fields;
- audit-only reviewer provenance;
- MCP/session/transport metadata.

For stronger fail-closed behavior, the API should accept a documented projection shape rather than recursively deleting arbitrary field names from unknown nested data. I-002 tests can use a fixed POC projection record whose allowed fields are explicit.

## 9. Algorithm naming recommendation

P-001 explicitly names evidence and compatibility algorithms but not source-bundle, mapping-semantic or profile-semantic algorithm IDs. I-002 needs stable versioned names before shipping code.

Recommended names for the implementation plan:

- canonical JSON format: `rfc8785-jcs` (format label, not a hash identifier);
- normalized source file: `ontotf-source-file-sha256-v1`;
- source bundle: `ontotf-source-bundle-sha256-v1`;
- evidence payload: accepted `ontotf-evidence-payload-sha256-v1`;
- evidence normalized record: accepted `ontotf-evidence-record-sha256-v1`;
- mapping semantic digest: `ontotf-mapping-semantic-sha256-v1`;
- profile semantic digest: `ontotf-profile-semantic-sha256-v1`.

These names should be fixed in the I-002 plan and tests; changing an algorithm's byte/projection semantics later requires a new identifier rather than silently reusing `v1`.

## 10. Fixed-vector strategy

Tests should combine three independent categories:

1. **RFC vectors** — canonical primitive/object/key-order/number cases from RFC 8785, including UTF-16 key ordering and numeric edges.
2. **ontoTF byte vectors** — literal expected UTF-8 canonical bytes and SHA-256 hex/digest strings calculated independently in test fixtures, not by calling the function under test to form the expectation.
3. **metamorphic regressions** — reordered object keys give identical canonical bytes; array reorder changes bytes; `profile_version`/audit provenance changes do not affect semantic digest; evidence binding changes do.

A dependency upgrade must pass all vectors before merge.

## 11. Decision

Use `rfc8785>=0.1.4,<0.2` for JCS serialization behind a ontoTF-owned strict wrapper and fixed-vector suite.

Do **not** implement a bespoke ECMAScript float serializer in I-002.

Keep source-byte hashing separate from parsed semantic canonicalization. Keep mapping/profile digest helpers projection-only and free of cross-artifact resolution. This preserves the I-001/I-002/I-004/I-006 boundaries established by P-001.
