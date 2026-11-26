from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable

import rfc8785

JCS_FORMAT = "rfc8785-jcs"
SOURCE_FILE_ALGORITHM = "tfont-source-file-sha256-v1"
SOURCE_BUNDLE_ALGORITHM = "tfont-source-bundle-sha256-v1"
EVIDENCE_PAYLOAD_ALGORITHM = "tfont-evidence-payload-sha256-v1"
EVIDENCE_RECORD_ALGORITHM = "tfont-evidence-record-sha256-v1"
MAPPING_SEMANTIC_ALGORITHM = "tfont-mapping-semantic-sha256-v1"
MAPPING_SEMANTIC_ALGORITHM_V2 = "tfont-mapping-semantic-sha256-v2"
PROJECTION_SEMANTIC_ALGORITHM = "tfont-projection-semantic-sha256-v1"
PROFILE_SEMANTIC_ALGORITHM = "tfont-profile-semantic-sha256-v1"
MAX_JSON_NESTING = 128

_SAFE_INT_MIN = -(2**53) + 1
_SAFE_INT_MAX = 2**53 - 1
_PORTABLE_PATH = re.compile(r"^[A-Za-z0-9._/-]+$")


@dataclass(frozen=True)
class DigestProblem:
    category: str
    message: str
    path: tuple[str | int, ...] = ()


class DigestError(ValueError):
    def __init__(self, problem: DigestProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


def _fail(category: str, message: str, path: tuple[str | int, ...] = ()) -> None:
    raise DigestError(DigestProblem(category=category, message=message, path=path))


def _validate_json(
    value: Any,
    *,
    path: tuple[str | int, ...] = (),
    active: set[int] | None = None,
    depth: int = 0,
) -> None:
    if active is None:
        active = set()

    value_type = type(value)
    if value is None or value_type is bool:
        return
    if value_type is int:
        if value < _SAFE_INT_MIN or value > _SAFE_INT_MAX:
            _fail("integer_domain", f"integer outside safe JCS domain: {value}", path)
        return
    if value_type is float:
        if not math.isfinite(value):
            _fail("float_domain", f"non-finite float: {value}", path)
        return
    if value_type is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            _fail("unicode_domain", str(exc), path)
        return

    if value_type is list:
        identity = id(value)
        if identity in active:
            _fail("non_json_value", "recursive list is outside the ontoTF JSON model", path)
        container_depth = depth + 1
        if container_depth > MAX_JSON_NESTING:
            _fail("non_json_value", f"JSON nesting exceeds maximum depth {MAX_JSON_NESTING}", path)
        active.add(identity)
        try:
            for index, item in enumerate(value):
                _validate_json(
                    item,
                    path=path + (index,),
                    active=active,
                    depth=container_depth,
                )
        finally:
            active.remove(identity)
        return

    if value_type is dict:
        identity = id(value)
        if identity in active:
            _fail("non_json_value", "recursive object is outside the ontoTF JSON model", path)
        container_depth = depth + 1
        if container_depth > MAX_JSON_NESTING:
            _fail("non_json_value", f"JSON nesting exceeds maximum depth {MAX_JSON_NESTING}", path)
        active.add(identity)
        try:
            for key, item in value.items():
                if type(key) is not str:
                    _fail("non_json_value", "object keys must be exact strings", path)
                try:
                    key.encode("utf-8")
                except UnicodeEncodeError as exc:
                    _fail("unicode_domain", str(exc), path + (key,))
                _validate_json(
                    item,
                    path=path + (key,),
                    active=active,
                    depth=container_depth,
                )
        finally:
            active.remove(identity)
        return

    _fail("non_json_value", f"unsupported ontoTF JSON value type: {value_type.__name__}", path)


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json(value)
    try:
        return rfc8785.dumps(value)
    except RecursionError:
        _fail("non_json_value", "RFC 8785 canonicalizer recursion failure")
    except rfc8785.IntegerDomainError as exc:
        _fail("integer_domain", str(exc))
    except rfc8785.FloatDomainError as exc:
        _fail("float_domain", str(exc))
    except rfc8785.CanonicalizationError as exc:
        message = str(exc)
        category = "unicode_domain" if "UTF-8" in message or "codepoint" in message else "non_json_value"
        _fail(category, message)


def _sha256_digest(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def normalize_source_bytes(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        _fail("projection_error", "source payload must be exact bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        _fail("invalid_utf8", str(exc))
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def source_file_digest(raw: bytes) -> str:
    return _sha256_digest(normalize_source_bytes(raw))


def _validate_logical_path(
    path: Any,
    *,
    error_path: tuple[str | int, ...] = (),
) -> str:
    if type(path) is not str or not path or not _PORTABLE_PATH.fullmatch(path):
        _fail("projection_error", "logical path must use portable ASCII repository-path characters", error_path)
    if path.startswith("/") or "\\" in path:
        _fail("projection_error", "logical path must be relative and use forward slashes", error_path)
    if any(segment in {"", ".", ".."} for segment in path.split("/")):
        _fail("projection_error", "logical path contains an empty/dot traversal segment", error_path)
    return path


def source_bundle_digest(files: Iterable[tuple[str, bytes]]) -> str:
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        iterator = iter(files)
    except TypeError:
        _fail("projection_error", "source bundle must be an iterable of (logical_path, bytes) pairs")
    for index, entry in enumerate(iterator):
        if type(entry) is not tuple or len(entry) != 2:
            _fail("projection_error", "source bundle entry must be an exact 2-tuple", (index,))
        path = _validate_logical_path(entry[0], error_path=(index, 0))
        if path in seen:
            _fail("duplicate_logical_path", f"duplicate logical path: {path}", (index, 0))
        seen.add(path)
        raw = entry[1]
        if type(raw) is not bytes:
            _fail("projection_error", "source bundle payload must be exact bytes", (index, 1))
        records.append({"logical_path": path, "file_sha256": source_file_digest(raw)})
    records.sort(key=lambda record: record["logical_path"])
    return _sha256_digest(canonical_json_bytes(records))


def evidence_payload_digest(payload: bytes) -> str:
    if type(payload) is not bytes:
        _fail("projection_error", "evidence payload must be exact bytes")
    return _sha256_digest(payload)


def _exact_dict(value: Any, *, path: tuple[str | int, ...] = ()) -> dict[str, Any]:
    if type(value) is not dict:
        _fail("projection_error", "projection source must be an exact object", path)
    return value


def _check_source_keys(
    source: dict[str, Any],
    *,
    allowed: set[str],
    required: set[str],
    path: tuple[str | int, ...] = (),
) -> None:
    if any(type(key) is not str for key in source):
        _fail("projection_error", "projection object keys must be exact strings", path)
    missing = sorted(required - source.keys())
    if missing:
        _fail("projection_error", f"missing required projection fields: {', '.join(missing)}", path)
    unknown = sorted(source.keys() - allowed)
    if unknown:
        _fail("projection_error", f"unknown projection fields: {', '.join(unknown)}", path)


def _require_nonempty_string(value: Any, *, path: tuple[str | int, ...]) -> str:
    if type(value) is not str or not value:
        _fail("projection_error", "expected a non-empty exact string", path)
    return value


def _utf16_sort_key(value: str, *, path: tuple[str | int, ...] = ()) -> bytes:
    try:
        return value.encode("utf-16be")
    except UnicodeEncodeError as exc:
        _fail("unicode_domain", str(exc), path)


def evidence_record_projection(record: dict[str, Any]) -> dict[str, Any]:
    source = _exact_dict(record)
    allowed = {
        "evidence_id",
        "kind",
        "source_uri",
        "source_revision",
        "content_mode",
        "reviewed_content",
        "content_digest",
        "license_ref",
        "citation",
    }
    required = {"evidence_id", "kind", "source_uri", "content_mode", "reviewed_content"}
    _check_source_keys(source, allowed=allowed, required=required)
    if source["content_mode"] != "normalized-record":
        _fail("projection_error", "evidence record digest requires content_mode=normalized-record", ("content_mode",))
    projection = {
        "evidence_id": source["evidence_id"],
        "kind": source["kind"],
        "source_uri": source["source_uri"],
        "reviewed_content": source["reviewed_content"],
    }
    if "source_revision" in source:
        projection["source_revision"] = source["source_revision"]
    if "license_ref" in source:
        projection["license_ref"] = source["license_ref"]
    _validate_json(projection)
    return projection


def evidence_record_digest(record: dict[str, Any]) -> str:
    return _sha256_digest(canonical_json_bytes(evidence_record_projection(record)))


def _normalize_unique_strings(value: Any, *, path: tuple[str | int, ...]) -> list[str]:
    if type(value) is not list:
        _fail("projection_error", "expected an exact list", path)
    result: list[tuple[str, tuple[str | int, ...]]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        item_path = path + (index,)
        item = _require_nonempty_string(item, path=item_path)
        if item in seen:
            _fail("projection_error", f"duplicate set-like identifier: {item}", item_path)
        seen.add(item)
        result.append((item, item_path))
    keyed = [(_utf16_sort_key(item, path=item_path), item) for item, item_path in result]
    keyed.sort(key=lambda pair: pair[0])
    return [item for _, item in keyed]


def _normalize_evidence_bindings(value: Any, *, path: tuple[str | int, ...]) -> list[dict[str, str]]:
    if type(value) is not list:
        _fail("projection_error", "evidence bindings must be an exact list", path)
    result: list[tuple[dict[str, str], tuple[str | int, ...]]] = []
    seen: set[tuple[str, str]] = set()
    for index, binding in enumerate(value):
        item_path = path + (index,)
        obj = _exact_dict(binding, path=item_path)
        _check_source_keys(
            obj,
            allowed={"evidence_id", "content_digest"},
            required={"evidence_id", "content_digest"},
            path=item_path,
        )
        evidence_id = _require_nonempty_string(obj["evidence_id"], path=item_path + ("evidence_id",))
        content_digest = _require_nonempty_string(obj["content_digest"], path=item_path + ("content_digest",))
        key = (evidence_id, content_digest)
        if key in seen:
            _fail("projection_error", "duplicate evidence binding", item_path)
        seen.add(key)
        result.append(({"evidence_id": evidence_id, "content_digest": content_digest}, item_path))
    keyed: list[tuple[bytes, bytes, dict[str, str]]] = []
    for item, item_path in result:
        keyed.append(
            (
                _utf16_sort_key(item["evidence_id"], path=item_path + ("evidence_id",)),
                _utf16_sort_key(item["content_digest"], path=item_path + ("content_digest",)),
                item,
            )
        )
    keyed.sort(key=lambda entry: (entry[0], entry[1]))
    return [item for _, _, item in keyed]


def _normalize_candidates(value: Any) -> list[dict[str, Any]]:
    if type(value) is not list:
        _fail("projection_error", "candidate_projections must be an exact list", ("candidate_projections",))
    normalized: list[tuple[bytes, dict[str, Any]]] = []
    seen: set[bytes] = set()
    required = {"external_target", "ontology_lock", "assessment_candidate", "evidence"}
    for index, candidate in enumerate(value):
        item_path = ("candidate_projections", index)
        obj = _exact_dict(candidate, path=item_path)
        _check_source_keys(obj, allowed=required, required=required, path=item_path)
        item = {
            "external_target": obj["external_target"],
            "ontology_lock": obj["ontology_lock"],
            "assessment_candidate": obj["assessment_candidate"],
            "evidence": _normalize_evidence_bindings(obj["evidence"], path=item_path + ("evidence",)),
        }
        encoded = canonical_json_bytes(item)
        if encoded in seen:
            _fail("projection_error", "duplicate candidate projection", item_path)
        seen.add(encoded)
        normalized.append((encoded, item))
    normalized.sort(key=lambda pair: pair[0])
    return [item for _, item in normalized]


def mapping_semantic_projection(mapping: dict[str, Any]) -> dict[str, Any]:
    source = _exact_dict(mapping)
    semantic = {
        "mapping_id",
        "profile_id",
        "native_selector",
        "native_dependencies",
        "external_target",
        "candidate_projections",
        "assessment",
        "publication_relation",
        "applicability",
        "ontology_lock",
        "evidence",
    }
    excluded = {"review", "mapping_semantic_digest", "rationale", "introduced_in", "changed_in"}
    _check_source_keys(source, allowed=semantic | excluded, required=semantic)
    projection = {
        "mapping_id": source["mapping_id"],
        "profile_id": source["profile_id"],
        "native_selector": source["native_selector"],
        "native_dependencies": _normalize_unique_strings(source["native_dependencies"], path=("native_dependencies",)),
        "external_target": source["external_target"],
        "candidate_projections": _normalize_candidates(source["candidate_projections"]),
        "assessment": source["assessment"],
        "publication_relation": source["publication_relation"],
        "applicability": source["applicability"],
        "ontology_lock": source["ontology_lock"],
        "evidence": _normalize_evidence_bindings(source["evidence"], path=("evidence",)),
    }
    _validate_json(projection)
    return projection


def mapping_semantic_digest(mapping: dict[str, Any]) -> str:
    return _sha256_digest(canonical_json_bytes(mapping_semantic_projection(mapping)))


def _normalize_record_set(
    value: Any,
    *,
    id_field: str,
    path: tuple[str | int, ...],
) -> list[dict[str, Any]]:
    if type(value) is not list:
        _fail("projection_error", "set-like record collection must be an exact list", path)
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, record in enumerate(value):
        item_path = path + (index,)
        obj = _exact_dict(record, path=item_path)
        identifier = _require_nonempty_string(obj.get(id_field), path=item_path + (id_field,))
        if identifier in seen:
            _fail("projection_error", f"duplicate {id_field}: {identifier}", item_path + (id_field,))
        seen.add(identifier)
        _validate_json(obj, path=item_path)
        result.append(dict(obj))
    result.sort(key=lambda item: _utf16_sort_key(item[id_field]))
    return result


def _normalize_ontology_lock_identities(value: Any) -> list[dict[str, Any]]:
    path = ("ontology_locks",)
    if type(value) is not list:
        _fail("projection_error", "ontology_locks must be an exact list", path)

    required = {
        "lock_id",
        "ontology_id",
        "support_tier",
        "term_namespace",
        "release",
        "source_uri",
        "content_digest",
        "license",
        "terms_used",
    }
    optional = {"upstream_release_status", "source_revision", "redistribution_policy"}
    scalar_fields = (required - {"terms_used"}) | optional
    result: list[tuple[dict[str, Any], tuple[str | int, ...]]] = []
    seen: set[str] = set()

    for index, record in enumerate(value):
        item_path = path + (index,)
        obj = _exact_dict(record, path=item_path)
        _check_source_keys(obj, allowed=required | optional, required=required, path=item_path)

        lock_id = _require_nonempty_string(obj["lock_id"], path=item_path + ("lock_id",))
        if lock_id in seen:
            _fail("projection_error", f"duplicate lock_id: {lock_id}", item_path + ("lock_id",))
        seen.add(lock_id)

        normalized: dict[str, Any] = {}
        for field in scalar_fields:
            if field in obj:
                normalized[field] = _require_nonempty_string(obj[field], path=item_path + (field,))
        normalized["terms_used"] = _normalize_unique_strings(obj["terms_used"], path=item_path + ("terms_used",))
        result.append((normalized, item_path + ("lock_id",)))

    keyed = [(_utf16_sort_key(item["lock_id"], path=lock_path), item) for item, lock_path in result]
    keyed.sort(key=lambda pair: pair[0])
    return [item for _, item in keyed]


def _normalize_mapping_identities(value: Any) -> list[dict[str, str]]:
    path = ("mappings",)
    if type(value) is not list:
        _fail("projection_error", "mappings must be an exact list", path)
    fields = {"mapping_id", "mapping_semantic_digest"}
    result: list[tuple[dict[str, str], tuple[str | int, ...]]] = []
    seen: set[str] = set()
    for index, record in enumerate(value):
        item_path = path + (index,)
        obj = _exact_dict(record, path=item_path)
        _check_source_keys(obj, allowed=fields, required=fields, path=item_path)
        mapping_id = _require_nonempty_string(obj["mapping_id"], path=item_path + ("mapping_id",))
        digest = _require_nonempty_string(
            obj["mapping_semantic_digest"], path=item_path + ("mapping_semantic_digest",)
        )
        if mapping_id in seen:
            _fail("projection_error", f"duplicate mapping_id: {mapping_id}", item_path + ("mapping_id",))
        seen.add(mapping_id)
        result.append(({"mapping_id": mapping_id, "mapping_semantic_digest": digest}, item_path + ("mapping_id",)))
    keyed = [(_utf16_sort_key(item["mapping_id"], path=mapping_path), item) for item, mapping_path in result]
    keyed.sort(key=lambda pair: pair[0])
    return [item for _, item in keyed]


def _normalize_review_readiness(value: Any) -> list[dict[str, Any]]:
    if type(value) is not list:
        _fail("projection_error", "review_readiness must be an exact list", ("review_readiness",))
    allowed = {"mapping_id", "status", "reviewed_digest_matches"}
    result: list[tuple[dict[str, Any], tuple[str | int, ...]]] = []
    seen: set[str] = set()
    for index, record in enumerate(value):
        item_path = ("review_readiness", index)
        obj = _exact_dict(record, path=item_path)
        _check_source_keys(obj, allowed=allowed, required=allowed, path=item_path)
        mapping_id = _require_nonempty_string(obj["mapping_id"], path=item_path + ("mapping_id",))
        if mapping_id in seen:
            _fail("projection_error", f"duplicate mapping_id: {mapping_id}", item_path + ("mapping_id",))
        seen.add(mapping_id)
        if obj["status"] not in {"reviewed", "provisional", "disputed"}:
            _fail("projection_error", "invalid review readiness status", item_path + ("status",))
        if type(obj["reviewed_digest_matches"]) is not bool:
            _fail(
                "projection_error",
                "reviewed_digest_matches must be boolean",
                item_path + ("reviewed_digest_matches",),
            )
        result.append(
            (
                {
                    "mapping_id": mapping_id,
                    "status": obj["status"],
                    "reviewed_digest_matches": obj["reviewed_digest_matches"],
                },
                item_path + ("mapping_id",),
            )
        )
    keyed = [(_utf16_sort_key(item["mapping_id"], path=mapping_path), item) for item, mapping_path in result]
    keyed.sort(key=lambda pair: pair[0])
    return [item for _, item in keyed]


def profile_semantic_digest(projection: dict[str, Any]) -> str:
    source = _exact_dict(projection)
    required = {
        "profile_id",
        "schema_version",
        "semantic_contract_version",
        "semantic_domains",
        "expected_parent_manifest_digest",
        "dependencies",
        "ontology_locks",
        "mappings",
        "review_readiness",
        "applicability",
        "publication_semantics",
    }
    _check_source_keys(source, allowed=required, required=required)
    normalized = {
        "profile_id": source["profile_id"],
        "schema_version": source["schema_version"],
        "semantic_contract_version": source["semantic_contract_version"],
        "semantic_domains": _normalize_unique_strings(source["semantic_domains"], path=("semantic_domains",)),
        "expected_parent_manifest_digest": source["expected_parent_manifest_digest"],
        "dependencies": _normalize_record_set(source["dependencies"], id_field="dependency_id", path=("dependencies",)),
        "ontology_locks": _normalize_ontology_lock_identities(source["ontology_locks"]),
        "mappings": _normalize_mapping_identities(source["mappings"]),
        "review_readiness": _normalize_review_readiness(source["review_readiness"]),
        "applicability": source["applicability"],
        "publication_semantics": source["publication_semantics"],
    }
    _validate_json(normalized)
    return _sha256_digest(canonical_json_bytes(normalized))


# Public mapping-v2 digest API. The implementation lives in a dedicated module
# to keep the v1 projection code stable; imports are lazy to avoid a module cycle.
def mapping_semantic_digest_v2(mapping: dict[str, Any]) -> str:
    from .semantic_digest_v2 import mapping_semantic_digest_v2 as implementation

    return implementation(mapping)


def projection_semantic_digest_v1(projection: dict[str, Any]) -> str:
    from .semantic_digest_v2 import projection_semantic_digest_v1 as implementation

    return implementation(projection)
