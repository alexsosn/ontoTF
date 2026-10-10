"""Sparse parity deltas for *already published*, explicitly selected coverage.

No proposed mapping or review receipt can be published using this module.
It reads two validated, installed immutable coverage sources and proves that
the target adds only new production-review accounts to an unchanged native
denominator. This is a compact representation, NOT release authorization.
"""
from __future__ import annotations

import copy
import hashlib
import re
from typing import Any

from .coverage import load_packaged_coverage_manifest, validate_coverage_manifest
from .digests import canonical_json_bytes


class PublishedCoverageDeltaError(ValueError):
    """Invalid, non-additive or non-parity published coverage delta."""


_RESOURCE = re.compile(r"p004-[a-zA-Z0-9._-]+-v[0-9]+\\Z")
_CORPUS = re.compile(r"[a-z][a-z0-9_-]*\\Z")
_AUTHORITY = "published-registry-parity-only"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise PublishedCoverageDeltaError(message)


def _digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def _allowed_identifiers(corpus: str, base: str, target: str) -> None:
    _require(
        type(corpus) is str and bool(_CORPUS.fullmatch(corpus))
        and type(base) is str and bool(_RESOURCE.fullmatch(base))
        and type(target) is str and bool(_RESOURCE.fullmatch(target))
        and base != target,
        "must select two different explicit immutable P-004 coverage resource sets",
    )


def _manifest(root: str, corpus: str) -> dict[str, Any]:
    try:
        return load_packaged_coverage_manifest(root, corpus)
    except (ValueError, OSError) as exc:
        raise PublishedCoverageDeltaError("missing/invalid packaged immutable coverage source") from exc


def _build_delta_between(
    corpus_id: str,
    base_resource_set: str,
    target_resource_set: str,
    base: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    """Pure reviewed-release delta algebra; never accepts self-declared approval."""
    _allowed_identifiers(corpus_id, base_resource_set, target_resource_set)
    try:
        validate_coverage_manifest(base)
        validate_coverage_manifest(target)
        _require(
            base["manifest_id"] == f"coverage:{base_resource_set}:{corpus_id}"
            and target["manifest_id"] == f"coverage:{target_resource_set}:{corpus_id}"
            and base["corpus_id"] == target["corpus_id"] == corpus_id,
            "corpus / manifest identity mismatch",
        )
        # Required snapshot-wide invariance, not only a matching denominator
        # hash: research authority, source pins, gaps and exclusions are fixed.
        excluded = {"manifest_id", "semantic_items"}
        _require(
            {k: v for k,v in base.items() if k not in excluded}
            == {k: v for k,v in target.items() if k not in excluded},
            "coverage denominator, source, gaps or exclusions drift",
        )
        before_rows = base["semantic_items"]
        after_rows = target["semantic_items"]
        _require(len(before_rows) == len(after_rows),
                 "semantic denominator membership changed")
        added: list[dict[str, Any]] = []
        for old, current in zip(before_rows, after_rows):
            _require(
                {k:v for k,v in old.items() if k!="accounting"}
                == {k:v for k,v in current.items() if k!="accounting"},
                "reviewed coverage row identity/metadata changed",
            )
            prev, nxt = old["accounting"], current["accounting"]
            _require(
                prev["research"] == nxt["research"],
                "research-only authority changed in a production delta",
            )
            if prev["production"] is not None:
                _require(
                    canonical_json_bytes(prev["production"])
                    == canonical_json_bytes(nxt["production"]),
                    "previously reviewed production decision changed or vanished",
                )
            elif nxt["production"] is not None:
                _require(
                    type(nxt["production"]) is dict
                    and bool(nxt["production"].get("assessments"))
                    and bool(nxt["production"].get("source_ids")),
                    "new review disposition has no production authority/source IDs",
                )
                added.append({
                    "item_id": old["item_id"],
                    "production": copy.deepcopy(nxt["production"]),
                })
        _require(bool(added), "no new reviewed coverage decisions")
        added.sort(key=lambda row: row["item_id"].encode("utf-16-be"))
        return {
            "schema_version": 1,
            "authority": _AUTHORITY,
            "corpus_id": corpus_id,
            "base_resource_set": base_resource_set,
            "target_resource_set": target_resource_set,
            "base_manifest_digest": _digest(base),
            "target_manifest_digest": _digest(target),
            "added_production": added,
        }
    except PublishedCoverageDeltaError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise PublishedCoverageDeltaError("invalid immutable coverage delta source") from exc


def build_published_coverage_delta(
    corpus_id: str, base_resource_set: str, target_resource_set: str,
) -> dict[str, Any]:
    """Compose only the diff of two *already installed* approved resources.

    No source ledger, review flag, caller-asserted GitHub response or
    release_authorized field is an authority input to this function.
    """
    _allowed_identifiers(corpus_id, base_resource_set, target_resource_set)
    return _build_delta_between(
        corpus_id, base_resource_set, target_resource_set,
        _manifest(base_resource_set, corpus_id),
        _manifest(target_resource_set, corpus_id),
    )


def load_published_coverage_delta(delta: dict[str, Any]) -> dict[str, Any]:
    """Validate/recompose the pinned published target, failing on any drift.

    This does not interpret a supplied parity object as a new release approval.
    Every verification rereads both installed immutable sources.
    """
    _require(type(delta) is dict, "coverage delta must be a JSON object")
    keys={
        "schema_version", "authority", "corpus_id",
        "base_resource_set", "target_resource_set",
        "base_manifest_digest", "target_manifest_digest", "added_production",
    }
    _require(set(delta)==keys
             and type(delta.get("schema_version")) is int
             and delta["schema_version"]==1
             and delta.get("authority")==_AUTHORITY,
             "coverage delta has unknown fields or forged approval authority")
    corpus,source,destination=(
        delta["corpus_id"],delta["base_resource_set"],delta["target_resource_set"]
    )
    expected=build_published_coverage_delta(corpus,source,destination)
    _require(
        canonical_json_bytes(delta) == canonical_json_bytes(expected),
        "coverage delta differs from packaged reviewed releases",
    )
    base=_manifest(source,corpus)
    target=_manifest(destination,corpus)
    composite=copy.deepcopy(base)
    composite["manifest_id"]=target["manifest_id"]
    updated = {row["item_id"]:row for row in delta["added_production"]}
    _require(len(updated)==len(delta["added_production"]),
             "duplicate production delta item identity")
    for row in composite["semantic_items"]:
        update=updated.pop(row["item_id"],None)
        if update is not None:
            _require(row["accounting"]["production"] is None,
                     "delta overwrites an existing reviewed item")
            row["accounting"]["production"]=copy.deepcopy(update["production"])
    _require(not updated, "delta references a nonexistent native item")
    try:
        validate_coverage_manifest(composite)
    except ValueError as exc:
        raise PublishedCoverageDeltaError("recomposed coverage invalid") from exc
    _require(canonical_json_bytes(composite)==canonical_json_bytes(target),
             "composed sparse delta not equal to immutable packaged target")
    return composite


__all__ = [
    "PublishedCoverageDeltaError",
    "build_published_coverage_delta",
    "load_published_coverage_delta",
]
