"""Immutable-format, *unapproved* source-bound batch mapping review requests.

A review packet is a proposal for external human/agent adjudication, NEVER an
approval or a released Mapping v2 artifact. Its decision digest intentionally
includes scholarly rationale which mapping_semantic_digest_v2 excludes.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from .batch_proposals import compile_candidate_batch
from .digests import canonical_json_bytes


class BatchReviewPacketError(ValueError):
    """Invalid, changed, or self-authorizing review-request packet."""


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require(ok: bool, detail: str) -> None:
    if not ok:
        raise BatchReviewPacketError(detail)


def build_review_packet(ledger: dict[str, Any]) -> dict[str, Any]:
    """Derive a new unreviewed request; do not trust stored review/digest flags.

    Every row binds the *whole compiler-produced candidate*, not a handpicked
    subset of semantic fields, along with the full original corpus-source pin,
    original batch identity and exact intended coverage ID.
    """
    compilation = compile_candidate_batch(ledger)
    _require(compilation["mode"] == "proposal-only"
             and compilation["release_authorized"] is False,
             "not an unreviewed batch proposal")
    batch_id = compilation["batch_id"]
    model = ledger["ontology_model"]
    ontology_revision = ledger["ontology_revision"]
    registry = ledger["source_registry"]
    _require(type(registry) is dict, "missing source registry")

    rows: list[dict[str, Any]] = []
    for mapping in compilation["candidates"]:
        # Compiler source integrity and format tests already verified all
        # proposed native and ontology evidence and their canonical digests.
        _require("review" not in mapping, "mapping attempts self-review")
        _require(type(mapping.get("projections")) is list
                 and len(mapping["projections"]) == 1,
                 "review packet requires exactly one supported projection")
        projection = mapping["projections"][0]
        _require("review" not in projection, "projection attempts self-review")
        native = mapping["native_binding"]
        _require(
            native["node_type"] == "word"
            and native["feature"] == "sp"
            and native["execution_shape"] == "value-predicate",
            "unsupported mapping source for review packet")
        corpus = mapping["corpus_id"]
        _require(corpus in registry, "unknown corpus source pin")
        coverage_ids = [f'node_value:sp="{native["value"]}"']
        source_pin = copy.deepcopy(registry[corpus])
        commitment = {
            "schema_version": 1,
            "batch_id": batch_id,
            "ontology_model": model,
            "ontology_revision": ontology_revision,
            "source_pin": source_pin,
            "coverage_item_ids": coverage_ids,
            "candidate": mapping,
        }
        rows.append({
            "mapping_id": mapping["mapping_id"],
            "corpus_id": corpus,
            "native_binding": copy.deepcopy(native),
            "ontology_target": projection["target"],
            "formal_kind": projection["formal_kind"],
            "semantic_role": projection["semantic_role"],
            "assessment": projection["assessment"],
            "rationale": mapping["rationale"],
            "source_pin": source_pin,
            "evidence": copy.deepcopy(mapping["evidence"]),
            "coverage_item_ids": coverage_ids,
            "mapping_semantic_digest": mapping["mapping_semantic_digest"],
            "projection_semantic_digest": projection["projection_semantic_digest"],
            "decision_digest": _digest(commitment),
        })
    rows.sort(key=lambda row: row["mapping_id"])
    ids = [row["mapping_id"] for row in rows]
    _require(len(ids) == len(set(ids)), "duplicate review decision")
    packet = {
        "schema_version": 1,
        "packet_id": f"review-request:{batch_id}",
        "authority": "unreviewed-proposal",
        "release_authorized": False,
        "batch_id": batch_id,
        "ontology_model": model,
        "ontology_revision": ontology_revision,
        "source_registry": copy.deepcopy(registry),
        "count": len(rows),
        "rows": rows,
    }
    packet["batch_digest"] = _digest(packet)
    return packet


def verify_review_packet(packet: dict[str, Any], ledger: dict[str, Any]) -> bool:
    """Fail closed on both checksum drift and compiler/ledger substitution.

    A writer cannot legitimize new source, target or rationale by recomputing
    the batch hash. This only confirms packet provenance from the supplied
    locally validated ledger; it does NOT authenticate an independent reviewer.
    """
    _require(type(packet) is dict, "packet must be a JSON object")
    try:
        computed = build_review_packet(ledger)
    except (TypeError, ValueError, KeyError) as exc:
        raise BatchReviewPacketError("invalid source ledger") from exc
    if packet != computed:
        raise BatchReviewPacketError("packet differs from pinned unreviewed source decisions")
    return True


def serialized(value: dict[str, Any]) -> str:
    """Canonical presentation (not the JCS digest wire format)."""
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = [
    "BatchReviewPacketError", "build_review_packet",
    "verify_review_packet", "serialized",
]
