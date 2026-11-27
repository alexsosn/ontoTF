"""Sparse UNSEALED coverage previews derived solely from a verified batch pack.

This module never accepts a GitHub review body, attestation assertion or
local authority flag. Only the protected release writer can install a signed,
versioned catalogue entry. The output is a deterministic candidate delta and
an in-memory parity check against the unmodified packaged denominator.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any

from .coverage import (
    load_packaged_coverage_manifest, validate_coverage_manifest,
)
from .digests import canonical_json_bytes
from .overlay_handoff import verify_overlay_handoff_integrity


class CoverageOverlayError(ValueError):
    """Unsealed delta, source or immutable denominator differs."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CoverageOverlayError(message)


def _digest(data: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(data)).hexdigest()


def build_sparse_coverage_delta(pack: dict[str, Any]) -> dict[str, Any]:
    """Make one sparse production assignment per *accepted* source-bound row.

    No historical coverage manifest or currently installed release is changed.
    All rejected/needs-evidence rows are intentionally absent from the delta.
    """
    try:
        verify_overlay_handoff_integrity(pack)
    except (ValueError, KeyError, TypeError) as exc:
        raise CoverageOverlayError("unsealed source-bound handoff invalid") from exc

    corpora = []
    for corpus in sorted(pack["corpora"], key=lambda c: c["corpus_id"]):
        by_id = {m["mapping_id"]: m for m in corpus["mappings"]}
        entries = []
        for row in sorted(corpus["coverage_assignments"], key=lambda x: x["item_id"]):
            mapping = by_id[row["mapping_id"]]
            _need(mapping["profiles"] == ["linguistic"]
                  and mapping["capabilities"] == ["linguistic.part-of-speech"],
                  "pilot mapping must declare its reviewed linguistic POS capability")
            assessment = "exact" if mapping["native_state"] == "positive" else "native-only"
            _need(row["assessment"] == assessment
                  and row["common_target"] == (assessment == "exact"),
                  "accepted coverage assessment differs from reviewed native mapping")
            entries.append({
                "item_id": row["item_id"],
                "mapping_id": mapping["mapping_id"],
                "decision_digest": row["decision_digest"],
                "production": {
                    "assessments": [assessment],
                    "common_target": assessment == "exact",
                    "source_ids": [mapping["mapping_id"]],
                    "profiles": ["linguistic"],
                    "capabilities": ["linguistic.part-of-speech"],
                },
            })
        _need(len(entries) == len(by_id), "accepted mapping lacks coverage assignment")
        corpora.append({
            "corpus_id": corpus["corpus_id"],
            "coverage_base": copy.deepcopy(corpus["coverage_base"]),
            "assignments": entries,
        })
    delta = {
        "schema_version": 1,
        "authority": "unsealed-coverage-preview-only",
        "pack_digest": pack["content_digest"],
        "corpora": corpora,
    }
    delta["content_digest"] = _digest(delta)
    return delta


def apply_sparse_coverage_delta(
    pack: dict[str, Any], delta: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return validated full manifests *only in memory* for parity checks.

    Caller-controlled delta bytes must exactly match the delta *rederived*
    from a verified, separately supplied pack. Even a recomputed self-digest
    cannot introduce a new accounting claim or authorize a release.
    """
    expected = build_sparse_coverage_delta(pack)
    try:
        _need(type(delta) is dict
              and canonical_json_bytes(delta) == canonical_json_bytes(expected),
              "delta does not exactly match verified candidate handoff")
    except (TypeError, ValueError) as exc:
        raise CoverageOverlayError("delta malformed or inconsistent with signed handoff input") from exc

    result = {}
    for corpus in expected["corpora"]:
        ident, base = corpus["corpus_id"], corpus["coverage_base"]
        try:
            manifest = load_packaged_coverage_manifest(base["resource_set"], ident)
        except (ValueError, TypeError, OSError, KeyError) as exc:
            raise CoverageOverlayError("frozen coverage manifest cannot be loaded") from exc
        _need(_digest(manifest) == base["manifest_digest"]
              and manifest["denominator_digest"] == base["denominator_digest"]
              and manifest["corpus_id"] == ident,
              "packaged coverage baseline or denominator has changed")
        updated = copy.deepcopy(manifest)
        by_id = {row["item_id"]: row for row in updated["semantic_items"]}
        _need(len(by_id) == len(updated["semantic_items"]),
              "baseline contains duplicate semantic denominator IDs")
        for row in corpus["assignments"]:
            item = by_id.get(row["item_id"])
            _need(item is not None and item["accounting"]["production"] is None,
                  "sparse delta changes missing or inherited production accounting")
            item["accounting"]["production"] = copy.deepcopy(row["production"])
        try:
            validate_coverage_manifest(updated)
        except (ValueError, TypeError, KeyError) as exc:
            raise CoverageOverlayError("sparse accounting violates coverage manifest contract") from exc
        _need(updated["denominator_digest"] == manifest["denominator_digest"],
              "sparse overlay must preserve denominator identity")
        result[ident] = updated
    return result


__all__ = [
    "CoverageOverlayError", "build_sparse_coverage_delta",
    "apply_sparse_coverage_delta",
]
