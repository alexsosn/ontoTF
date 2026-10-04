from __future__ import annotations

import hashlib
from typing import Any

from .digests import (
    MAX_JSON_NESTING,
    DigestError,
    DigestProblem,
    MAPPING_SEMANTIC_ALGORITHM_V2,
    PROJECTION_SEMANTIC_ALGORITHM,
    canonical_json_bytes,
)

# Compatibility alias for the internal implementation module. The public
# contract uses PROJECTION_SEMANTIC_ALGORITHM from tfont.digests.
PROJECTION_SEMANTIC_ALGORITHM_V1 = PROJECTION_SEMANTIC_ALGORITHM

_AUDIT_ONLY_TOP_LEVEL = {
    "review",
    "mapping_semantic_digest",
    "rationale",
    "introduced_in",
    "changed_in",
}
_AUDIT_ONLY_NESTED = {
    "review",
    "projection_semantic_digest",
}
_SET_LIKE_LIST_FIELDS = {
    "native_dependencies",
    "profiles",
    "capabilities",
    "evidence",
    "projections",
    "ambiguous_candidates",
    "external_references",
    "losses",
    "values",
    "match_values",
}


def _fail(message: str) -> None:
    raise DigestError(DigestProblem(category="projection_error", message=message))


def _json_boundary_fail(message: str, path: tuple[str | int, ...]) -> None:
    raise DigestError(
        DigestProblem(category="non_json_value", message=message, path=path)
    )


def _canonical_sort(items: list[Any]) -> list[Any]:
    encoded = [(canonical_json_bytes(item), item) for item in items]
    encoded.sort(key=lambda pair: pair[0])
    return [item for _, item in encoded]


def _project(
    value: Any,
    *,
    top_level: bool = False,
    field: str | None = None,
    path: tuple[str | int, ...] = (),
    active: set[int] | None = None,
    depth: int = 0,
) -> Any:
    if active is None:
        active = set()

    if type(value) is dict:
        identity = id(value)
        if identity in active:
            _json_boundary_fail(
                "recursive object is outside the TFont JSON model", path
            )
        container_depth = depth + 1
        if container_depth > MAX_JSON_NESTING:
            _json_boundary_fail(
                f"JSON nesting exceeds maximum depth {MAX_JSON_NESTING}", path
            )

        active.add(identity)
        try:
            excluded = _AUDIT_ONLY_TOP_LEVEL if top_level else _AUDIT_ONLY_NESTED
            result: dict[str, Any] = {}
            for key, item in value.items():
                if key in excluded:
                    continue
                result[key] = _project(
                    item,
                    field=key,
                    path=path + (key,),
                    active=active,
                    depth=container_depth,
                )
            return result
        finally:
            active.remove(identity)

    if type(value) is list:
        identity = id(value)
        if identity in active:
            _json_boundary_fail(
                "recursive list is outside the TFont JSON model", path
            )
        container_depth = depth + 1
        if container_depth > MAX_JSON_NESTING:
            _json_boundary_fail(
                f"JSON nesting exceeds maximum depth {MAX_JSON_NESTING}", path
            )

        active.add(identity)
        try:
            projected = [
                _project(
                    item,
                    path=path + (index,),
                    active=active,
                    depth=container_depth,
                )
                for index, item in enumerate(value)
            ]
            if field in _SET_LIKE_LIST_FIELDS:
                return _canonical_sort(projected)
            return projected
        finally:
            active.remove(identity)

    return value


def mapping_semantic_projection_v2(mapping: dict[str, Any]) -> dict[str, Any]:
    if type(mapping) is not dict:
        _fail("mapping semantic projection requires an exact object")
    projection = _project(mapping, top_level=True)
    canonical_json_bytes(projection)
    return projection


def mapping_semantic_digest_v2(mapping: dict[str, Any]) -> str:
    payload = canonical_json_bytes(mapping_semantic_projection_v2(mapping))
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def projection_semantic_projection_v1(projection: dict[str, Any]) -> dict[str, Any]:
    if type(projection) is not dict:
        _fail("projection semantic projection requires an exact object")
    result = _project(projection, top_level=False)
    if type(result) is not dict:
        _fail("projection semantic projection requires an exact object")
    canonical_json_bytes(result)
    return result


def projection_semantic_digest_v1(projection: dict[str, Any]) -> str:
    payload = canonical_json_bytes(projection_semantic_projection_v1(projection))
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
