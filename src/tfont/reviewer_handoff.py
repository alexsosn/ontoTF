"""Offline scholarly review handoff; NEVER an approval or release capability.

The reviewer's explicit decisions are put into an authenticated GitHub
APPROVED review by a separate privileged principal, not by this module.
"""
from __future__ import annotations

import json
import html
import re
from typing import Any, Callable

from .batch_proposals import packaged_resource
from .digests import evidence_record_digest
from .external_review_gate import (
    ExternalReviewError, _packet_rows, parse_structured_review,
)


class ReviewerHandoffError(ValueError):
    """Invalid unreviewed packet, evidence, or explicit reviewer selections."""


_CHOICES = frozenset({"accept", "reject", "needs-evidence"})
_HEADER = "ontoTF-batch-review-v1\n"


def _markdown_text(value: str) -> str:
    """Display candidate text literally without HTML or Markdown structure."""
    text = " ".join(value.splitlines())
    text = re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)
    return html.escape(text, quote=True)


def _require(ok: bool, explanation: str) -> None:
    if not ok:
        raise ReviewerHandoffError(explanation)


def _source_rows(packet: dict[str, Any]) -> dict[str, str]:
    try:
        result = _packet_rows(packet)
    except (ExternalReviewError, ValueError, TypeError, KeyError) as exc:
        raise ReviewerHandoffError("invalid or altered candidate packet") from exc
    _require(1 <= len(result) <= 50, "review packet exceeds 1–50 rows")
    return result


def reviewer_template(packet: dict[str, Any]) -> dict[str, Any]:
    """Generate a review worksheet with UNSET decisions; cannot be approval."""
    bound = _source_rows(packet)
    return {
        "packet_digest": packet["batch_digest"],
        "rows": [
            {"mapping_id": mapping_id, "disposition": None}
            for mapping_id in sorted(bound)
        ],
    }


def render_review_body(packet: dict[str, Any], choices: dict[str, Any]) -> str:
    """Prepare a GitHub review BODY, never a GitHub APPROVED review event.

    Only an authenticated, distinct, authorized GitHub reviewer can submit
    that event; authors cannot turn this body into release authority.
    """
    expected = _source_rows(packet)
    _require(type(choices) is dict and set(choices) == {"packet_digest", "rows"},
             "review decision worksheet contains unexpected/missing fields")
    _require(type(choices["packet_digest"]) is str
             and choices["packet_digest"] == packet["batch_digest"],
             "decisions refer to a stale or foreign review packet")
    entries = choices["rows"]
    _require(type(entries) is list and len(entries) == len(expected),
             "explicit disposition required for every candidate row")
    seen: dict[str, str] = {}
    for choice in entries:
        _require(type(choice) is dict
                 and set(choice) == {"mapping_id", "disposition"},
                 "decision row must include only mapping_id and disposition")
        mapping_id, decision = choice["mapping_id"], choice["disposition"]
        _require(type(mapping_id) is str and mapping_id in expected
                 and mapping_id not in seen,
                 "missing, duplicate, or foreign decision mapping ID")
        _require(type(decision) is str and decision in _CHOICES,
                 "each disposition must be explicitly accept/reject/needs-evidence")
        seen[mapping_id] = decision
    _require(set(seen) == set(expected),
             "reviewer did not decide every exact packet row")
    rows = [
        {
            "mapping_id": mapping_id,
            "decision_digest": expected[mapping_id],
            "disposition": seen[mapping_id],
        }
        for mapping_id in sorted(expected)
    ]
    obj = {"packet_digest": packet["batch_digest"], "rows": rows}
    body = _HEADER + json.dumps(obj, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"))
    try:
        parse_structured_review(body)
    except ExternalReviewError as exc:
        raise ReviewerHandoffError("generated body is not valid for GitHub review") from exc
    _require(len(body) <= 80_000, "GitHub review body exceeds strict gate size")
    return body


def review_dossier(
    packet: dict[str, Any], *,
    resource_loader: Callable[[str], dict[str, Any]] = packaged_resource,
) -> str:
    """Render evidence-rich, non-authoritative scholarly review notes.

    Source coordinates come from the candidate evidence object, so the
    reviewer must still verify them against the original pinned primary source.
    """
    expected = _source_rows(packet)
    rows = packet["rows"]
    _require(type(rows) is list, "invalid packet rows")
    header = [
        "# ontoTF — UNREVIEWED batch-review dossier",
        "",
        "**WARNING:** These are candidate assertions and do not automatically",
        "constitute verified cross-ontology mappings or GitHub approval.",
        "Independently check the cited upstream immutable revision and original",
        "source line for each item before selecting any disposition.",
        "",
        f"Packet digest: `{packet['batch_digest']}`",
        f"Batch: {_markdown_text(packet.get('batch_id', 'unknown'))}",
        f"Rows requiring independent decisions: **{len(expected)}**",
        "",
        "Every row needs one explicit `accept`, `reject`, or `needs-evidence` decision.",
        "A native-only proposal does not establish the absence of ontology equivalents.",
        "",
    ]
    for row in sorted(rows, key=lambda x: x["mapping_id"]):
        _require(type(row) is dict
                 and row.get("mapping_id") in expected
                 and row.get("decision_digest") == expected[row["mapping_id"]],
                 "candidate review row identity mismatch")
        native, pin = row.get("native_binding"), row.get("source_pin")
        _require(type(native) is dict and type(pin) is dict,
                 "candidate row lacks native selector/source pin")
        name = pin.get("evidence_resource")
        _require(type(name) is str and name.startswith("resources/"),
                 "candidate source evidence identity missing")
        try:
            record = resource_loader(name)
            content = record["reviewed_content"]
            definition = content["source_definitions"][native["value"]]
            line, gloss = definition["line"], definition["gloss"]
            _require(type(line) is int and line > 0
                     and type(gloss) is str and bool(gloss.strip()),
                     "source coordinate or gloss invalid")
            _require(record["source_revision"] == pin["source_revision"]
                     and record["source_uri"]
                     and record["content_digest"] == evidence_record_digest(record)
                     and any(e.get("evidence_id") == record["evidence_id"]
                             and e.get("content_digest") == record["content_digest"]
                             for e in row["evidence"]),
                     "candidate source record does not match decision evidence")
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise ReviewerHandoffError("cannot verify candidate's original source coordinates") from exc
        header.extend([
            f"### {row['mapping_id']}",
            "",
            f"- Native selector: `{native['node_type']}.{native['feature']}={native['value']}`",
            f"- Source definition: **{_markdown_text(gloss)}**, line {line}",
            f"- Source: {_markdown_text(record['source_uri'])}",
            f"- Pinned source revision: `{record['source_revision']}`",
            f"- Proposal: `{row['assessment']}`; ontology target: "
            + (f"`{row['ontology_target']}`" if row["ontology_target"] else "**none proposed**"),
            f"- Author's rationale (requires challenge): {_markdown_text(row['rationale'])}",
            f"- Decision digest: `{row['decision_digest']}`",
            "",
        ])
    return "\n".join(header)


__all__ = [
    "ReviewerHandoffError",
    "reviewer_template", "render_review_body", "review_dossier",
]
