"""Single-agent TWO-PASS adversarial review predicate, not an external approval.

This offline function accepts caller-provided JSON and therefore cannot issue
authorization. Only protected-main CI may promote a result after fresh GitHub
REST reads of separate COMMENTED PR review events, live author permissions,
opt-in labels, corpus source pins, row commitments and current head.
"""
from __future__ import annotations

import copy
import json
from typing import Any

from .digests import canonical_json_bytes
from .external_review_gate import (
    ExternalReviewError, _require, _strict_pairs, _invalid_constant,
    _packet_rows, _review_time, parse_structured_review, _REPO, _SHA,
    _ROLES, _STATES,
)

_HEADER = "ontoTF-adversarial-review-v1\n"
_MIN_SUMMARY = 80
_MIN_CHALLENGE = 60
_MIN_SOURCE_CHECK = 80


def parse_adversarial_report(body: str, packet: dict[str, Any]) -> dict[str, Any]:
    """Validate auditable per-row challenges; does NOT prove mental independence."""
    expected = _packet_rows(packet)
    _require(type(body) is str and body.startswith(_HEADER)
             and len(body) <= 80_000, "adversarial review header or bound invalid")
    try:
        obj = json.loads(body[len(_HEADER):],
                         object_pairs_hook=_strict_pairs,
                         parse_constant=_invalid_constant)
    except (ValueError, TypeError, RecursionError) as exc:
        raise ExternalReviewError("adversarial review must be unambiguous JSON") from exc
    _require(type(obj) is dict
             and set(obj) == {"packet_digest", "summary", "rows"},
             "adversarial review has unexpected/missing fields")
    _require(obj["packet_digest"] == packet["batch_digest"],
             "adversarial review is for a different packet digest")
    _require(type(obj["summary"]) is str
             and _MIN_SUMMARY <= len(obj["summary"].strip()) <= 3000,
             "missing substantive independent adversarial method/summary")
    rows = obj["rows"]
    _require(type(rows) is list and len(rows) == len(expected),
             "adversarial review must challenge every exact candidate row")
    per_id = {item["mapping_id"]: item for item in packet["rows"]}
    observed: set[str] = set()
    for item in rows:
        _require(type(item) is dict and set(item) == {
            "mapping_id", "decision_digest", "challenge", "source_check",
        }, "adversarial row fields invalid")
        ident = item["mapping_id"]
        _require(type(ident) is str and ident in expected and ident not in observed,
                 "adversarial review omitted/repeated/forged mapping ID")
        observed.add(ident)
        _require(type(item["decision_digest"]) is str
                 and item["decision_digest"] == expected[ident],
                 "adversarial decision digest is stale or forged")
        challenge, source = item["challenge"], item["source_check"]
        original = per_id[ident]
        value = original["native_binding"]["value"]
        revision = original["source_pin"]["source_revision"]
        _require(type(challenge) is str
                 and _MIN_CHALLENGE <= len(challenge.strip()) <= 2000
                 and value in challenge
                 and challenge.strip() != original["rationale"].strip(),
                 "independent per-row counterargument missing or copied from proposal")
        _require(type(source) is str
                 and _MIN_SOURCE_CHECK <= len(source.strip()) <= 2000
                 and revision in source and value in source,
                 "per-row pinned original source check missing")
    _require(observed == set(expected), "adversarial report omitted decision rows")
    return obj


def adversarial_template(packet: dict[str, Any]) -> dict[str, Any]:
    """Unset challenge worksheet. It cannot pass the release gate as written."""
    expected = _packet_rows(packet)
    return {
        "packet_digest": packet["batch_digest"],
        "summary": None,
        "rows": [
            {
                "mapping_id": row["mapping_id"],
                "decision_digest": expected[row["mapping_id"]],
                "challenge": None,
                "source_check": None,
            }
            for row in sorted(packet["rows"], key=lambda x: x["mapping_id"])
        ],
    }


def render_adversarial_body(packet: dict[str, Any], worksheet: dict[str, Any]) -> str:
    """Format explicit challenge evidence only; never issue a GitHub review."""
    _require(type(worksheet) is dict, "adversarial worksheet must be an object")
    text = _HEADER + json.dumps(worksheet, ensure_ascii=False,
                                sort_keys=True, separators=(",", ":"))
    parse_adversarial_report(text, packet)
    return text


def evaluate_single_agent_snapshot(
    *,
    packet: dict[str, Any], repository: str, pr_number: int,
    expected_head_sha: str, pull_request: dict[str, Any],
    reviews: list[dict[str, Any]], reviewer_permissions: dict[str, str],
) -> dict[str, Any]:
    """Check a **snapshot**, never live authority, for two author review passes.

    External GitHub APPROVED mode is implemented separately and untouched.
    Here GitHub author's COMMENTED events are reviewed *only when* the live PR
    explicitly opts into the single-agent policy. Distinct events and order
    preserve an independently conducted adversarial pass, not a second person.
    """
    expected = _packet_rows(packet)
    _require(10 <= len(expected) <= 50,
             "single-agent protected batch requires 10–50 source-bound rows")
    _require(type(repository) is str and bool(_REPO.fullmatch(repository))
             and type(pr_number) is int and pr_number > 0
             and type(expected_head_sha) is str and bool(_SHA.fullmatch(expected_head_sha)),
             "invalid repository, PR number or exact head")
    _require(type(pull_request) is dict, "GitHub PR metadata absent")
    try:
        author = pull_request["user"]["login"]
        valid = (
            type(author) is str and bool(author)
            and type(pull_request["number"]) is int and pull_request["number"] == pr_number
            and pull_request["state"] == "open" and pull_request["draft"] is False
            and pull_request["head"]["sha"] == expected_head_sha
            and pull_request["head"]["repo"]["full_name"] == repository
            and pull_request["base"]["repo"]["full_name"] == repository
            and pull_request["base"]["ref"] == "main"
            and type(pull_request["labels"]) is list
            and {"ontology-batch-review", "ontology-single-agent-review"}.issubset({
                item.get("name") for item in pull_request["labels"] if type(item) is dict
            })
        )
    except (KeyError, TypeError):
        valid = False
    _require(valid, "single-agent PR head, base, state or explicit labels invalid")
    _require(type(reviews) is list and len(reviews) <= 500
             and type(reviewer_permissions) is dict,
             "GitHub review/permission snapshot invalid")
    permissions={login.casefold():role for login,role in reviewer_permissions.items()
                 if type(login) is str}
    _require(permissions.get(author.casefold()) in _ROLES,
             "author is not currently privileged to request release")
    seen: set[int] = set()
    author_reviews = []
    for event in reviews:
        _require(type(event) is dict and type(event.get("user")) is dict,
                 "GitHub review event malformed")
        user, state = event["user"], event.get("state")
        login = user.get("login")
        _require(type(login) is str and login
                 and type(state) is str and state in _STATES,
                 "GitHub review identity or state malformed")
        if state == "PENDING":
            continue
        stamp, ident = _review_time(event)
        _require(ident not in seen, "duplicate GitHub review event ID")
        seen.add(ident)
        if login.casefold() == author.casefold():
            _require(user.get("type") == "User",
                     "single-agent GitHub actor must be a real User")
            author_reviews.append((stamp, ident, event))
    author_reviews.sort(key=lambda item: (item[0], item[1]))
    _require(len(author_reviews) >= 2, "two distinct GitHub author review events required")
    first, second = author_reviews[-2:]
    _require(first[:2] < second[:2] and first[1] != second[1],
             "challenge and adjudication must be distinct chronological reviews")
    challenge, decision = first[2], second[2]
    _require(challenge["state"] == decision["state"] == "COMMENTED",
             "single-agent pass must be two COMMENTED GitHub reviews")
    _require(challenge.get("commit_id") == expected_head_sha
             and decision.get("commit_id") == expected_head_sha,
             "challenge or decision review is stale at current PR HEAD")
    parse_adversarial_report(challenge.get("body"), packet)
    parsed = parse_structured_review(decision.get("body"))
    _require(parsed["packet_digest"] == packet["batch_digest"],
             "decision review refers to foreign packet")
    proposed = {row["mapping_id"]:row["decision_digest"] for row in parsed["rows"]}
    _require(proposed == expected, "decision review omitted or altered row commitments")
    ordered = sorted(parsed["rows"], key=lambda r:r["mapping_id"])
    counts = {d:sum(row["disposition"] == d for row in ordered)
              for d in ("accept", "reject", "needs-evidence")}
    return {
        "schema_version": 1,
        "packet_id": packet["packet_id"],
        "batch_digest": packet["batch_digest"],
        "repository": repository,
        "pr_number": pr_number,
        "approved_head_sha": expected_head_sha,
        "reviewer_login": author,
        "review_id": second[1],
        "submitted_at": decision["submitted_at"],
        "counts": counts,
        "rows": copy.deepcopy(ordered),
        "provenance": "untrusted-json-evaluation-only;single-agent-adversarial-two-pass",
    }


__all__=[
    "parse_adversarial_report", "adversarial_template",
    "render_adversarial_body", "evaluate_single_agent_snapshot",
]
