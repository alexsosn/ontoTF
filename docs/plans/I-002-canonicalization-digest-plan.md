# I-002 canonicalization and semantic digest plan

**Issue:** #16  
**Recorded:** 2026-09-06  
**Research dependency:** `docs/research/I-002-canonicalization-digest-research.md` at `aeeac1b9a913083983ec14ba8ebd79404682a4ca`  
**Design dependency:** P-001 merged as `e9ab50a759ba72c89047704ac70958fce6376951`  
**Implementation dependency:** I-001 merged as `f7d358fe7e90680b6216ed6cb4b6f624dd2bcdd2`

## 1. Scope

I-002 implements deterministic canonical bytes and digest projections only.

It creates:

- a strict RFC 8785/JCS wrapper over the accepted I-001 JSON value model;
- source-file and source-bundle digest helpers;
- evidence payload and normalized-record digest helpers;
- mapping semantic projection/digest helpers;
- profile semantic projection/digest helpers;
- stable algorithm identifiers and a ontoTF-owned digest/canonicalization error contract;
- independent fixed vectors and CI.

It does **not** resolve IDs, inspect corpus bytes, compose parent component identities, verify evidence against external files, verify review equality, fetch ontology terms, calculate compatibility states/reports, compile semantic IR, generate runtime artifacts, or resolve queries.

## 2. Dependency change

Add one runtime dependency:

```toml
rfc8785>=0.1.4,<0.2
```

The package is used only behind `ontotf.digests`; callers do not depend on its exception classes or permissive tuple handling.

## 3. Production layout

```text
src/ontotf/
  digests.py
  __init__.py        # exports stable public helpers/errors

tests/i002/
  __init__.py
  test_canonical_json.py
  test_source_digests.py
  test_semantic_digests.py
.github/workflows/i002-validation.yml
```

No schema change is required for I-002.

## 4. Stable constants

`digests.py` exports:

```python
JCS_FORMAT = "rfc8785-jcs"
SOURCE_FILE_ALGORITHM = "ontotf-source-file-sha256-v1"
SOURCE_BUNDLE_ALGORITHM = "ontotf-source-bundle-sha256-v1"
EVIDENCE_PAYLOAD_ALGORITHM = "ontotf-evidence-payload-sha256-v1"
EVIDENCE_RECORD_ALGORITHM = "ontotf-evidence-record-sha256-v1"
MAPPING_SEMANTIC_ALGORITHM = "ontotf-mapping-semantic-sha256-v1"
PROFILE_SEMANTIC_ALGORITHM = "ontotf-profile-semantic-sha256-v1"
```

An algorithm's projection or byte semantics must never change while reusing its `v1` identifier.

Digest-returning APIs use one representation consistently:

```text
sha256:<64 lowercase hexadecimal digits>
```

Algorithm identifiers are separate metadata constants; the digest value itself remains compatible with P-001's `sha256:...` fields.

## 5. Error contract

```python
@dataclass(frozen=True)
class DigestProblem:
    category: str
    message: str
    path: tuple[str | int, ...] = ()

class DigestError(ValueError):
    problem: DigestProblem
```

Stable categories:

- `non_json_value` — ontoTF JSON-domain violation such as tuple, bytes, non-string key, custom object;
- `integer_domain` — integer outside JCS safe interoperability domain;
- `float_domain` — NaN or infinity / non-representable JCS float;
- `unicode_domain` — lone surrogate or otherwise non-UTF-8-serializable string;
- `invalid_utf8` — source bytes cannot decode as UTF-8;
- `duplicate_logical_path` — source bundle has two entries for the same logical path;
- `projection_error` — required projection field missing, prohibited/unknown field present, or wrong local projection shape.

Third-party exception strings are diagnostic only. Tests assert ontoTF category/path.

## 6. Strict JCS input guard

### API

```python
canonical_json_bytes(value: JSONValue) -> bytes
```

Before delegating to `rfc8785.dumps`, recursively accept only exact ontoTF JSON values:

- `None`;
- exact `bool`;
- exact `int` in `[-9007199254740991, 9007199254740991]`;
- exact finite `float`;
- exact `str`;
- exact `list`;
- exact `dict` with exact `str` keys.

Reject:

- tuple even though `rfc8785` accepts it;
- `Decimal`;
- bytes/bytearray;
- set/frozenset;
- custom mapping/sequence subclasses;
- non-string keys;
- integers outside safe range;
- NaN/infinities;
- recursive/cyclic containers;
- lone surrogate strings (converted from the library's canonicalization failure to `unicode_domain`).

No Unicode normalization, sorting or type coercion occurs in the guard. JCS owns canonical property sorting and primitive serialization.

### Required RFC-derived vectors

At minimum test literal expected bytes for:

```python
{"numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27]}
```

using the RFC's ECMAScript-compatible spellings, and the RFC 8785 §3.2.3 non-ASCII property-order sample including CR, `1`, U+0080, `ö`, `€`, 😀 and Hebrew U+FB33.

Also test:

- `-0.0 -> b"0"`;
- object insertion order does not change bytes;
- array order does change bytes;
- nested objects inside arrays are recursively sorted;
- composed/decomposed Unicode strings remain distinct because JCS does no normalization.

## 7. SHA-256 helper

Private helper:

```python
_sha256_digest(data: bytes) -> str
```

returns `sha256:` plus lowercase `hashlib.sha256(data).hexdigest()`.

No hashing API accepts text implicitly; callers must pass bytes or use the documented canonical/source helpers.

## 8. Source-file normalization and digest

### APIs

```python
normalize_source_bytes(raw: bytes) -> bytes
source_file_digest(raw: bytes) -> str
```

Algorithm:

1. reject invalid UTF-8 by strict decode;
2. if the decoded input begins with one U+FEFF originating from an optional UTF-8 BOM, remove exactly that leading BOM;
3. normalize `\r\n` to `\n` and remaining bare `\r` to `\n`;
4. preserve every other Unicode scalar and whitespace exactly;
5. re-encode UTF-8;
6. hash for `source_file_digest`.

Important distinction: an actual U+FEFF character after the first character is ordinary content and is preserved. No `.strip()`, Unicode normalization, parsing, reformatting or sorting is allowed.

### Source fixed vectors

Hard-code expected normalized bytes/digests for:

- UTF-8 BOM + CRLF;
- bare CR;
- already-LF input;
- tabs/trailing spaces preserved;
- invalid UTF-8 rejected.

## 9. Source-bundle digest

### API

```python
source_bundle_digest(files: Iterable[tuple[str, bytes]]) -> str
```

The iterable form permits explicit duplicate detection; a `dict` input would hide duplicate logical paths before the helper sees them.

For each entry:

1. `logical_path` must be non-empty exact `str` and must not duplicate another entry;
2. calculate `source_file_digest(raw)`;
3. construct `{"logical_path": logical_path, "file_sha256": digest}`;
4. sort records by `logical_path` using Python string order only for the pre-JCS semantic list ordering because logical paths are constrained in this POC to portable ASCII repository paths (`[A-Za-z0-9._/-]+`, no `.`/`..` empty segments, no backslash, no absolute path);
5. JCS-canonicalize the resulting list;
6. SHA-256 it.

The ASCII path restriction prevents a hidden mismatch between repository path ordering and JCS UTF-16 property ordering and makes bundle manifests transport-independent.

Tests prove input iteration order does not affect the digest and duplicate paths fail.

## 10. Evidence payload digest

### API

```python
evidence_payload_digest(payload: bytes) -> str
```

This is exactly SHA-256 of exact bytes. It performs no UTF-8 decoding or normalization.

## 11. Evidence normalized-record projection

### APIs

```python
evidence_record_projection(record: dict[str, JSONValue]) -> dict[str, JSONValue]
evidence_record_digest(record: dict[str, JSONValue]) -> str
```

Accepted source shape is the I-001 `content_mode: normalized-record` evidence object.

Required semantic fields:

- `evidence_id`;
- `kind`;
- `source_uri`;
- `reviewed_content`.

Optional semantic fields copied when present:

- `source_revision`;
- `license_ref`.

Explicitly excluded:

- `content_digest` (self-reference);
- `content_mode` (the algorithm identifier already fixes normalized-record mode);
- `citation` and other display metadata.

Unknown source fields fail with `projection_error` rather than being silently ignored; the helper is intentionally coupled to the accepted I-001 evidence schema shape.

The digest is SHA-256 of `canonical_json_bytes(projection)`.

Changing `content_digest` alone must not change the recomputed digest. Changing reviewed content, pinned source revision or `license_ref` must change it.

## 12. Mapping semantic projection

### APIs

```python
mapping_semantic_projection(mapping: dict[str, JSONValue]) -> dict[str, JSONValue]
mapping_semantic_digest(mapping: dict[str, JSONValue]) -> str
```

Required semantic fields copied:

- `mapping_id`;
- `profile_id`;
- `native_selector`;
- `native_dependencies`;
- `external_target`;
- `candidate_projections`;
- `assessment`;
- `publication_relation`;
- `applicability`;
- `ontology_lock`;
- `evidence`.

Explicitly excluded:

- `mapping_semantic_digest`;
- entire `review` record;
- `rationale`;
- `introduced_in`;
- `changed_in`.

Unknown source fields fail with `projection_error` so a future behavior-affecting mapping field cannot accidentally be omitted from v1 hashing.

### Set-like normalization inside the projection

P-001 says set-like collections are sorted while semantically ordered arrays preserve order.

For v1:

- `native_dependencies` is set-like: sort/deduplicate is **not** allowed; duplicates fail `projection_error`, then sort lexically by ID;
- top-level mapping `evidence` is set-like: duplicates of `(evidence_id, content_digest)` fail, then sort by `(evidence_id, content_digest)`;
- `candidate_projections` is set-like because P-001 explicitly states candidate ordering must not affect resolution. Normalize each candidate's evidence bindings as above, then sort candidates by their JCS bytes; exact duplicate candidates fail;
- all arrays nested inside `native_selector`, `applicability`, or `reviewed_content` are opaque/semantically ordered and retain their supplied order unless a later design explicitly classifies them otherwise.

The helper does not check that referenced IDs exist or that the mapping assessment is valid; schema/I-004 own those checks.

### Review binding implication

Changing any audit-only field in `review` must not change mapping digest. Changing the evidence `(evidence_id, content_digest)` binding must change mapping digest.

## 13. Profile semantic projection boundary

A raw profile manifest is insufficient for P-001 profile semantic identity because the digest includes resolved parent/dependency/ontology/mapping/readiness semantics. I-002 therefore does not resolve profile paths.

### API

```python
profile_semantic_digest(projection: dict[str, JSONValue]) -> str
```

The input is an **already assembled v1 profile semantic projection** with exactly these top-level keys:

```text
profile_id
schema_version
semantic_contract_version
semantic_domains
expected_parent_manifest_digest
dependencies
ontology_locks
mappings
review_readiness
applicability
publication_semantics
```

All keys are required except `applicability` and `publication_semantics`, which default conceptually to empty objects but must be supplied explicitly in v1 to avoid hidden defaults. Therefore in code **all eleven keys are required**.

No additional top-level keys are accepted. In particular the helper rejects `profile_version`, timestamps, paths, CI IDs, generated metadata, audit-only reviewer provenance and transport/session data instead of silently dropping them.

This means the regression “profile_version does not affect semantic digest” is expressed as:

- release wrapper A has `profile_version=0.1.0` and semantic projection P;
- release wrapper B has `profile_version=0.1.1` and the same semantic projection P;
- `profile_semantic_digest(P)` is identical because `profile_version` is outside the API's semantic projection by construction;
- passing `profile_version` into P itself fails closed as `projection_error`.

The projection helper/hash does not validate cross-artifact truth; I-004/I-006 assemble and validate these fields.

### Set-like normalization

For v1:

- `semantic_domains`: unique strings sorted;
- `dependencies`: normalized records sorted by stable `dependency_id`; duplicate IDs fail;
- `ontology_locks`: normalized records/identity records sorted by stable `lock_id`; duplicate IDs fail;
- `mappings`: records sorted by stable `mapping_id`; duplicate IDs fail;
- `review_readiness`: records sorted by stable `mapping_id`; duplicate IDs fail;
- arrays nested inside the records are otherwise preserved unless the record contract already identifies them as set-like.

This helper does not invent or resolve those records; it only gives the assembled projection deterministic collection order.

## 14. Public exports

`ontotf.__init__` adds:

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

Projection helpers and algorithm constants remain importable from `ontotf.digests`; only the common end-user helpers are promoted at package root.

## 15. RED sequence

Before `src/ontotf/digests.py` or the new dependency exists, add focused tests and workflow that import the missing module and fail for the intended missing-production reason.

RED tests must already contain literal independent expectations for:

1. RFC 8785 primitive/number sample bytes;
2. RFC non-ASCII UTF-16 property sorting sample;
3. safe integer boundaries and out-of-domain rejection;
4. NaN/infinity rejection;
5. tuple/custom/non-string-key rejection;
6. source BOM/CRLF/CR normalization bytes and fixed SHA-256 digests;
7. source-bundle order invariance + duplicate path failure;
8. exact evidence payload hash vector;
9. normalized evidence self-reference exclusion;
10. mapping review/self-digest/rationale/release-navigation exclusion;
11. evidence-binding mutation changes mapping digest;
12. candidate/dependency/evidence set-order invariance;
13. profile projection stable under release-wrapper `profile_version` change and rejects `profile_version` inside semantic projection;
14. audit-only reviewer provenance cannot enter profile semantic projection;
15. duplicate set-like IDs fail rather than being silently deduplicated.

Confirm exact-head RED in CI before production code.

## 16. GREEN implementation order

1. update `pyproject.toml` dependency only after RED is recorded;
2. add `src/ontotf/digests.py` and public exports;
3. make RFC vectors green first;
4. make source digest vectors green;
5. make evidence/mapping/profile projection vectors green;
6. run focused I-002 suite;
7. run full repository suite;
8. verify installed `rfc8785` version in CI.

## 17. CI

`.github/workflows/i002-validation.yml` triggers on:

- `pyproject.toml`;
- `src/ontotf/**`;
- `tests/i002/**`;
- I-002 research/plan;
- the workflow itself.

It installs `-e .`, prints Python and `rfc8785` versions, runs:

```text
python -m unittest discover -s tests/i002 -v
python -m unittest discover -s tests -v
```

Exact-head success is mandatory before review and merge.

## 18. Independent-review attack surface

The adversarial reviewer should specifically try to falsify:

- UTF-16 key ordering versus Python/UTF-8 ordering;
- ECMAScript number serialization and `-0` behavior;
- unsafe integers, NaN, infinities, lone surrogates;
- accidental tuple/custom-type coercion;
- BOM and line-ending normalization boundaries;
- source digest accidentally parsing/reformatting content;
- duplicate source paths;
- self-reference through `content_digest` or `mapping_semantic_digest`;
- audit-only review provenance leaking into semantic identity;
- candidate/evidence/dependency set ordering affecting semantic digest;
- unknown future mapping fields being silently omitted;
- profile helper secretly performing cross-artifact resolution or accepting volatile fields;
- any I-003+ parent identity or I-004+ semantic validation leakage.

## 19. Non-goals

- parent TF/file/directory/sidecar identity composition;
- parent manifest composition;
- external evidence verification;
- ontology-term existence;
- review-digest equality enforcement;
- compatibility state/report generation;
- normalized IR compilation;
- runtime/resolver/reference generation;
- corpus profiles/mappings.

## 20. Acceptance trace

- research commit precedes this plan;
- this plan must precede all production I-002 changes;
- RED must be observed on an exact commit;
- fixed vectors, focused suite and full suite must be green on the final exact head;
- a fresh logically-independent adversarial review is required after the final head is stable;
- any head move invalidates review.
