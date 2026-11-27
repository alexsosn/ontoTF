from __future__ import annotations

import hashlib
from typing import Any, Callable

from .digests import canonical_json_bytes

Fail = Callable[[str, str, tuple[str | int, ...], str | None], None]

_LOCK_REQUIRED_FIELDS = (
    "lock_id", "ontology_id", "support_tier", "term_namespace", "release",
    "source_uri", "content_digest", "license", "terms_used",
)
_LOCK_OPTIONAL_FIELDS = (
    "upstream_release_status", "source_revision", "redistribution_policy",
)
_BRIDGE_CONTENT_FIELDS = (
    "source_lock_id", "source_lock_release", "source_lock_digest",
    "target_lock_id", "target_lock_release", "target_lock_digest",
    "assertion_kind", "scope", "compatibility", "evidence_id", "evidence_digest",
    "runtime_strength", "runtime_limitations",
)
_BRIDGE_IDENTITY_FIELDS = (
    "bridge_id", "digest", *_BRIDGE_CONTENT_FIELDS, "review_status",
    "reviewed_content_digest", "review_id", "reviewer_id", "reviewed_at",
)
_EDGE_FIELDS = (
    "id", "consumer", "requires", "satisfied_by", "active",
    "required_lock_release", "required_lock_digest", "required_bridge_scope",
)


def _utf16_key(value: str) -> bytes:
    return value.encode("utf-16be")


def _sorted_unique_strings(value: Any, *, path: tuple[str | int, ...], fail: Fail) -> list[str]:
    if type(value) is not list:
        fail("bundle_closure", "expected list of strings", path, None)
    seen: set[str] = set()
    result: list[str] = []
    for index, item in enumerate(value):
        if type(item) is not str or not item:
            fail("bundle_closure", "expected non-empty string", path + (index,), None)
        if item in seen:
            fail("duplicate_id", f"duplicate identity: {item}", path + (index,), item)
        seen.add(item)
        result.append(item)
    return sorted(result, key=_utf16_key)


def _lock_projection(lock: dict[str, Any], *, path: tuple[str | int, ...], fail: Fail) -> dict[str, Any]:
    for field in _LOCK_REQUIRED_FIELDS:
        if field not in lock:
            fail("bundle_closure", f"ontology lock missing semantic field: {field}", path + (field,), lock.get("lock_id"))
    result = {field: lock[field] for field in _LOCK_REQUIRED_FIELDS}
    for field in _LOCK_OPTIONAL_FIELDS:
        if field in lock:
            result[field] = lock[field]
    result["terms_used"] = _sorted_unique_strings(result["terms_used"], path=path + ("terms_used",), fail=fail)
    canonical_json_bytes(result)
    return result


def bridge_content_digest_v1(bridge: dict[str, Any]) -> str:
    projected = {field: bridge[field] for field in _BRIDGE_CONTENT_FIELDS if field in bridge}
    payload = canonical_json_bytes(projected)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _bridge_projection(bridge: dict[str, Any]) -> dict[str, Any]:
    return {field: bridge[field] for field in _BRIDGE_IDENTITY_FIELDS if field in bridge}


def _bridge_map(bridges: tuple[dict[str, Any], ...], *, fail: Fail) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, bridge in enumerate(bridges):
        bridge_id = bridge.get("bridge_id") if type(bridge) is dict else None
        if type(bridge_id) is not str or not bridge_id:
            fail("bridge_closure", "bridge artifact missing bridge_id", ("bridges", index, "bridge_id"), None)
        if bridge_id in result:
            fail("duplicate_id", f"duplicate bridge_id: {bridge_id}", ("bridges", index, "bridge_id"), bridge_id)
        result[bridge_id] = bridge
    return result


def _validate_bridge(
    bridge: dict[str, Any],
    *,
    canonical_locks: dict[str, dict[str, Any]],
    evidences: dict[str, dict[str, Any]],
    path: tuple[str | int, ...],
    fail: Fail,
) -> None:
    bridge_id = bridge.get("bridge_id")
    for side in ("source", "target"):
        lock_id = bridge.get(f"{side}_lock_id")
        if type(lock_id) is not str or lock_id not in canonical_locks:
            fail("bridge_closure", f"missing {side} endpoint lock: {lock_id!r}", path + (f"{side}_lock_id",), lock_id if type(lock_id) is str else None)
        lock = canonical_locks[lock_id]
        if bridge.get(f"{side}_lock_release") != lock.get("release"):
            fail("bridge_closure", f"{side} endpoint release mismatch", path + (f"{side}_lock_release",), bridge_id)
        if bridge.get(f"{side}_lock_digest") != lock.get("content_digest"):
            fail("bridge_closure", f"{side} endpoint digest mismatch", path + (f"{side}_lock_digest",), bridge_id)

    scope = bridge.get("scope")
    if type(scope) is not dict:
        fail("bridge_closure", "bridge scope must be an object", path + ("scope",), bridge_id)
    for field in ("source_term", "target_term", "relation"):
        if type(scope.get(field)) is not str or not scope.get(field):
            fail("bridge_closure", f"bridge scope missing {field}", path + ("scope", field), bridge_id)
    if scope["source_term"] not in canonical_locks[bridge["source_lock_id"]].get("terms_used", []):
        fail("bridge_closure", "bridge source term is outside endpoint terms_used", path + ("scope", "source_term"), bridge_id)
    if scope["target_term"] not in canonical_locks[bridge["target_lock_id"]].get("terms_used", []):
        fail("bridge_closure", "bridge target term is outside endpoint terms_used", path + ("scope", "target_term"), bridge_id)

    evidence_id = bridge.get("evidence_id")
    if type(evidence_id) is not str or evidence_id not in evidences:
        fail("bridge_closure", f"bridge evidence does not resolve: {evidence_id!r}", path + ("evidence_id",), evidence_id if type(evidence_id) is str else None)
    if bridge.get("evidence_digest") != evidences[evidence_id].get("content_digest"):
        fail("bridge_closure", "bridge evidence digest does not match current evidence artifact", path + ("evidence_digest",), evidence_id)

    computed = bridge_content_digest_v1(bridge)
    if bridge.get("digest") != computed:
        fail("bridge_closure", "bridge content digest mismatch", path + ("digest",), bridge_id)
    if bridge.get("review_status") != "reviewed":
        fail("bridge_closure", "active bridge must carry reviewed source provenance", path + ("review_status",), bridge_id)
    if bridge.get("reviewed_content_digest") != computed:
        fail("bridge_closure", "bridge review does not bind current content digest", path + ("reviewed_content_digest",), bridge_id)


def validate_bundle_source_closure(
    ontology_bundle: dict[str, Any] | None,
    *,
    canonical_locks: dict[str, dict[str, Any]],
    bridge_artifacts: tuple[dict[str, Any], ...],
    evidences: dict[str, dict[str, Any]],
    fail: Fail,
) -> str | None:
    if ontology_bundle is None:
        if bridge_artifacts:
            fail("bridge_closure", "bridge artifacts require an ontology bundle", ("bridges",), None)
        return None
    if type(ontology_bundle) is not dict:
        fail("bundle_closure", "ontology bundle must be an object", ("ontology_bundle",), None)
    if type(ontology_bundle.get("schema_version")) is not int or ontology_bundle.get("schema_version") != 1:
        fail("unsupported_contract_version", "ontology bundle schema_version must be exact integer 1", ("ontology_bundle", "schema_version"), None)

    _sorted_unique_strings(ontology_bundle.get("profile_contracts", []), path=("ontology_bundle", "profile_contracts"), fail=fail)

    embedded_locks = ontology_bundle.get("ontology_locks")
    if type(embedded_locks) is not list:
        fail("bundle_closure", "ontology_locks must be a list", ("ontology_bundle", "ontology_locks"), None)
    seen_lock_ids: set[str] = set()
    normalized_locks: list[dict[str, Any]] = []
    for index, embedded in enumerate(embedded_locks):
        if type(embedded) is not dict:
            fail("bundle_closure", "embedded ontology lock must be an object", ("ontology_bundle", "ontology_locks", index), None)
        lock_id = embedded.get("lock_id")
        if type(lock_id) is not str or lock_id not in canonical_locks:
            fail("bundle_closure", f"embedded ontology lock does not resolve: {lock_id!r}", ("ontology_bundle", "ontology_locks", index, "lock_id"), lock_id if type(lock_id) is str else None)
        if lock_id in seen_lock_ids:
            fail("duplicate_id", f"duplicate embedded lock_id: {lock_id}", ("ontology_bundle", "ontology_locks", index, "lock_id"), lock_id)
        seen_lock_ids.add(lock_id)
        embedded_projection = _lock_projection(embedded, path=("ontology_bundle", "ontology_locks", index), fail=fail)
        canonical_projection = _lock_projection(canonical_locks[lock_id], path=("ontology_locks", lock_id), fail=fail)
        if embedded_projection != canonical_projection:
            fail("bundle_closure", f"embedded ontology lock identity differs from canonical source: {lock_id}", ("ontology_bundle", "ontology_locks", index), lock_id)
        normalized_locks.append(embedded_projection)

    external_bridges = _bridge_map(bridge_artifacts, fail=fail)
    embedded_bridges = ontology_bundle.get("bridge_locks")
    if type(embedded_bridges) is not list:
        fail("bundle_closure", "bridge_locks must be a list", ("ontology_bundle", "bridge_locks"), None)
    bundle_bridges: dict[str, dict[str, Any]] = {}
    for index, bridge in enumerate(embedded_bridges):
        bridge_id = bridge.get("bridge_id") if type(bridge) is dict else None
        if type(bridge_id) is not str or not bridge_id:
            fail("bridge_closure", "embedded bridge missing bridge_id", ("ontology_bundle", "bridge_locks", index, "bridge_id"), None)
        if bridge_id in bundle_bridges:
            fail("duplicate_id", f"duplicate embedded bridge_id: {bridge_id}", ("ontology_bundle", "bridge_locks", index, "bridge_id"), bridge_id)
        if bridge_id not in external_bridges:
            fail("bridge_closure", f"embedded bridge has no source artifact: {bridge_id}", ("ontology_bundle", "bridge_locks", index, "bridge_id"), bridge_id)
        if _bridge_projection(bridge) != _bridge_projection(external_bridges[bridge_id]):
            fail("bridge_closure", f"embedded bridge identity differs from source artifact: {bridge_id}", ("ontology_bundle", "bridge_locks", index), bridge_id)
        _validate_bridge(bridge, canonical_locks=canonical_locks, evidences=evidences, path=("ontology_bundle", "bridge_locks", index), fail=fail)
        bundle_bridges[bridge_id] = bridge

    edges = ontology_bundle.get("dependency_edges")
    if type(edges) is not list:
        fail("bundle_closure", "dependency_edges must be a list", ("ontology_bundle", "dependency_edges"), None)
    active_bridge_ids: set[str] = set()
    seen_edge_ids: set[str] = set()
    active_edge_projections: list[dict[str, Any]] = []
    for index, edge in enumerate(edges):
        if type(edge) is not dict:
            fail("bundle_closure", "dependency edge must be an object", ("ontology_bundle", "dependency_edges", index), None)
        edge_id = edge.get("id")
        if type(edge_id) is not str or not edge_id:
            fail("bundle_closure", "dependency edge missing id", ("ontology_bundle", "dependency_edges", index, "id"), None)
        if edge_id in seen_edge_ids:
            fail("duplicate_id", f"duplicate dependency edge id: {edge_id}", ("ontology_bundle", "dependency_edges", index, "id"), edge_id)
        seen_edge_ids.add(edge_id)
        active = edge.get("active", True)
        if type(active) is not bool:
            fail("bundle_closure", "dependency active must be an exact boolean", ("ontology_bundle", "dependency_edges", index, "active"), edge_id)
        if not active:
            continue
        active_edge_projections.append({field: edge[field] for field in _EDGE_FIELDS if field in edge})
        consumer = edge.get("consumer")
        required = edge.get("requires")
        if consumer not in canonical_locks:
            fail("bundle_closure", f"active dependency consumer lock missing: {consumer!r}", ("ontology_bundle", "dependency_edges", index, "consumer"), consumer if type(consumer) is str else None)
        if required not in canonical_locks:
            fail("bundle_closure", f"active dependency required lock missing: {required!r}", ("ontology_bundle", "dependency_edges", index, "requires"), required if type(required) is str else None)
        satisfied_by = edge.get("satisfied_by")
        if type(satisfied_by) is not str:
            fail("bundle_closure", "active dependency satisfied_by must be a string", ("ontology_bundle", "dependency_edges", index, "satisfied_by"), edge_id)
        if satisfied_by.startswith("bridge:"):
            bridge_id = satisfied_by.removeprefix("bridge:")
            if not bridge_id or bridge_id not in bundle_bridges:
                fail("bridge_closure", f"active dependency references missing bridge: {bridge_id!r}", ("ontology_bundle", "dependency_edges", index, "satisfied_by"), bridge_id or None)
            bridge = bundle_bridges[bridge_id]
            if bridge.get("source_lock_id") != required:
                fail("bridge_closure", "bridge source lock does not match dependency requires", ("ontology_bundle", "dependency_edges", index, "requires"), bridge_id)
            if canonical_json_bytes(edge.get("required_bridge_scope")) != canonical_json_bytes(bridge.get("scope")):
                fail("bridge_closure", "dependency bridge scope differs from bridge source scope", ("ontology_bundle", "dependency_edges", index, "required_bridge_scope"), bridge_id)
            active_bridge_ids.add(bridge_id)
        elif satisfied_by.startswith("lock:"):
            lock_id = satisfied_by.removeprefix("lock:")
            if lock_id != required or lock_id not in canonical_locks:
                fail("bundle_closure", "exact-lock dependency does not resolve to required lock", ("ontology_bundle", "dependency_edges", index, "satisfied_by"), lock_id or None)
            required_release = edge.get("required_lock_release")
            required_digest = edge.get("required_lock_digest")
            lock = canonical_locks[lock_id]
            if type(required_release) is not str or not required_release or type(required_digest) is not str or not required_digest:
                fail("bundle_closure", "exact-lock dependency must bind required release and digest", ("ontology_bundle", "dependency_edges", index), edge_id)
            if required_release != lock.get("release") or required_digest != lock.get("content_digest"):
                fail("bundle_closure", "exact-lock dependency release/digest differs from canonical lock", ("ontology_bundle", "dependency_edges", index), edge_id)
        else:
            fail("bundle_closure", "unknown dependency satisfaction source", ("ontology_bundle", "dependency_edges", index, "satisfied_by"), edge_id)

    for bridge_id in bundle_bridges:
        if bridge_id not in active_bridge_ids:
            fail("bridge_closure", f"bridge is not referenced by an active dependency: {bridge_id}", ("ontology_bundle", "bridge_locks", bridge_id), bridge_id)

    projection = {
        "schema_version": 1,
        "profile_contracts": _sorted_unique_strings(ontology_bundle.get("profile_contracts", []), path=("ontology_bundle", "profile_contracts"), fail=fail),
        "ontology_locks": sorted(normalized_locks, key=canonical_json_bytes),
        "bridge_locks": sorted((_bridge_projection(item) for item in bundle_bridges.values()), key=canonical_json_bytes),
        "dependency_edges": sorted(active_edge_projections, key=canonical_json_bytes),
    }
    return "sha256:" + hashlib.sha256(canonical_json_bytes(projection)).hexdigest()
