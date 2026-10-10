"""Strict offline eligibility check for externally observed GitHub PR reviews.

IMPORTANT TRUST BOUNDARY: evaluate_review_snapshot accepts *caller-supplied*
JSON and does NOT authenticate it. It is a testable predicate, never proof
of approval. The release gateway must obtain all records freshly from GitHub
over TLS in a protected trusted job and recheck this same exact-head policy.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from typing import Any

from .digests import canonical_json_bytes


class ExternalReviewError(ValueError):
    """Malformed, unauthorized, revoked, stale or contradictory external review."""


_HEADER = "ontoTF-batch-review-v1\n"
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_DECISIONS = frozenset({"accept", "reject", "needs-evidence"})
_ROLES = frozenset({"admin", "maintain", "write"})
_STATES = frozenset({"APPROVED", "DISMISSED", "COMMENTED", "CHANGES_REQUESTED", "PENDING"})


def _require(ok: bool, explanation: str) -> None:
    if not ok:
        raise ExternalReviewError(explanation)


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in obj, f"duplicate review key: {key}")
        obj[key] = value
    return obj


def _invalid_constant(value: str) -> None:
    raise ExternalReviewError(f"invalid review JSON constant: {value}")


def parse_structured_review(body: str) -> dict[str, Any]:
    """Parse a reviewer-authored per-row decision set (not an approval)."""
    _require(type(body) is str and body.startswith(_HEADER)
             and len(body) <= 80_000, "missing review v1 header or excessive body")
    try:
        value = json.loads(
            body[len(_HEADER):], object_pairs_hook=_strict_pairs,
            parse_constant=_invalid_constant,
        )
    except (ValueError, TypeError, RecursionError) as exc:
        raise ExternalReviewError("review body is not valid unambiguous JSON") from exc
    _require(type(value) is dict and set(value) == {"packet_digest", "rows"},
             "review body must have exactly packet_digest and rows")
    _require(type(value["packet_digest"]) is str
             and bool(_SHA256.fullmatch(value["packet_digest"])),
             "review references malformed packet digest")
    rows = value["rows"]
    _require(type(rows) is list and 1 <= len(rows) <= 50,
             "review must adjudicate 1–50 distinct rows")
    for row in rows:
        _require(type(row) is dict
                 and set(row) == {"mapping_id", "decision_digest", "disposition"},
                 "review row fields invalid")
        _require(type(row["mapping_id"]) is str and bool(row["mapping_id"])
                 and len(row["mapping_id"]) <= 256,
                 "review mapping ID invalid")
        _require(type(row["decision_digest"]) is str
                 and bool(_SHA256.fullmatch(row["decision_digest"])),
                 "review row decision digest invalid")
        _require(type(row["disposition"]) is str
                 and row["disposition"] in _DECISIONS,
                 "unsupported review row disposition")
    ids = [row["mapping_id"] for row in rows]
    _require(len(ids) == len(set(ids)), "duplicate review mapping ID")
    return value


def _review_time(review: dict[str, Any]) -> tuple[datetime, int]:
    at = review.get("submitted_at")
    ident = review.get("id")
    _require(type(at) is str and type(ident) is int and ident > 0,
             "GitHub review missing exact submission time / ID")
    try:
        stamp = datetime.fromisoformat(at.replace("Z", "+00:00"))
        _require(stamp.tzinfo is not None, "GitHub review time must have timezone")
    except (ValueError, OverflowError) as exc:
        raise ExternalReviewError("invalid GitHub review timestamp") from exc
    return (stamp, ident)


def _packet_rows(packet: dict[str, Any]) -> dict[str, str]:
    _require(type(packet) is dict
             and packet.get("authority") == "unreviewed-proposal"
             and type(packet.get("release_authorized")) is bool
             and packet.get("release_authorized") is False
             and type(packet.get("schema_version")) is int
             and packet.get("schema_version") == 1,
             "only unreviewed I-033D packets accepted")
    rows=packet.get("rows")
    _require(type(rows) is list and 1 <= len(rows) <= 50,
             "candidate packet lacks bounded rows")
    digest=packet.get("batch_digest")
    _require(type(digest) is str and bool(_SHA256.fullmatch(digest)),
             "invalid packet digest")
    computed = "sha256:" + hashlib.sha256(canonical_json_bytes({
        key: value for key,value in packet.items() if key!="batch_digest"
    })).hexdigest()
    _require(computed == digest, "packet self-integrity mismatch")
    expected: dict[str,str] = {}
    for row in rows:
        _require(type(row) is dict, "candidate packet row invalid")
        mapping_id, decision_digest=row.get("mapping_id"), row.get("decision_digest")
        _require(type(mapping_id) is str and mapping_id
                 and type(decision_digest) is str
                 and bool(_SHA256.fullmatch(decision_digest))
                 and mapping_id not in expected,
                 "candidate packet row digest / duplicate invalid")
        expected[mapping_id]=decision_digest
    return expected


def evaluate_review_snapshot(
    *,
    packet: dict[str, Any],
    repository: str,
    pr_number: int,
    expected_head_sha: str,
    pull_request: dict[str, Any],
    reviews: list[dict[str, Any]],
    reviewer_permissions: dict[str, str],
) -> dict[str, Any]:
    """Evaluate raw, *UNAUTHENTICATED* review JSON for eligibility.

    This routine must never serve as a release authorization API. The trusted
    gateway performs fresh authenticated PR/review/permission lookups and
    revalidates the packet against the source ledger before using this result.
    """
    expected_rows = _packet_rows(packet)
    _require(type(repository) is str and bool(_REPO.fullmatch(repository))
             and type(pr_number) is int and pr_number > 0
             and type(expected_head_sha) is str
             and bool(_SHA.fullmatch(expected_head_sha)),
             "invalid expected exact PR identity")
    _require(type(pull_request) is dict, "missing externally read PR")
    base = pull_request.get("base")
    head = pull_request.get("head")
    author = pull_request.get("user")
    _require(type(base) is dict and type(head) is dict
             and type(author) is dict and type(head.get("repo")) is dict
             and type(base.get("repo")) is dict
             and type(author.get("login")) is str and bool(author.get("login"))
             and pull_request.get("number") == pr_number
             and type(pull_request.get("number")) is int
             and pull_request.get("state") == "open"
             and pull_request.get("draft") is False
             and head["sha"] == expected_head_sha
             and head["repo"].get("full_name") == repository
             and base["repo"].get("full_name") == repository,
             "PR repository, state or exact head mismatch")
    _require(type(reviews) is list and len(reviews) <= 500
             and type(reviewer_permissions) is dict,
             "unbounded review page or missing permission evidence")
    latest: dict[str, dict[str, Any]] = {}
    seen_ids: set[int] = set()
    for event in reviews:
        _require(type(event) is dict and type(event.get("user")) is dict,
                 "GitHub review event shape invalid")
        user = event["user"]
        login = user.get("login")
        state = event.get("state")
        _require(type(login) is str and login
                 and type(state) is str and state in _STATES,
                 "review lacks state or account identity")
        if state == "PENDING":
            continue
        when, identifier = _review_time(event)
        _require(identifier not in seen_ids, "duplicate GitHub review ID")
        seen_ids.add(identifier)
        # GitHub account identities are case-insensitive. Revocations must
        # invalidate an earlier APPROVED review under any login casing.
        identity = login.casefold()
        previous = latest.get(identity)
        if previous is None or (when,identifier) > _review_time(previous):
            latest[identity]=event

    candidates: list[tuple[dict[str, Any], list[dict[str,str]]]] = []
    for identity,event in latest.items():
        if event["state"] != "APPROVED":
            continue
        user = event["user"]
        login = user["login"]
        role = reviewer_permissions.get(login)
        if (identity == author["login"].casefold()
                or user.get("type") != "User" or role not in _ROLES):
            continue
        if event.get("commit_id") != expected_head_sha:
            # Never accept an approval carried across a later code update.
            continue
        parsed=parse_structured_review(event.get("body"))
        _require(parsed["packet_digest"] == packet["batch_digest"],
                 "GitHub approval is for a different review packet")
        actual={row["mapping_id"]:row for row in parsed["rows"]}
        _require(set(actual)==set(expected_rows),
                 "GitHub approval omitted or added a mapping decision")
        for mapping_id,row in actual.items():
            _require(row["decision_digest"]==expected_rows[mapping_id],
                     "GitHub approval row digest is stale")
        decisions=[copy.deepcopy(actual[mapping_id]) for mapping_id in sorted(actual)]
        candidates.append((event,decisions))

    _require(bool(candidates), "no current independent privileged GitHub approval")
    canonical={canonical_json_bytes(rows) for _,rows in candidates}
    _require(len(canonical)==1, "independent reviewers made contradictory decisions")
    # Deterministic choice only among *identical* externally attested decisions.
    event,decisions = sorted(
        candidates, key=lambda entry: (entry[0]["user"]["login"],entry[0]["id"])
    )[0]
    counts={kind:sum(row["disposition"]==kind for row in decisions)
            for kind in ("accept","reject","needs-evidence")}
    return {
        "schema_version": 1,
        "packet_id": packet["packet_id"],
        "batch_digest": packet["batch_digest"],
        "repository": repository,
        "pr_number": pr_number,
        "approved_head_sha": expected_head_sha,
        "reviewer_login": event["user"]["login"],
        "review_id": event["id"],
        "submitted_at": event["submitted_at"],
        "counts": counts,
        "rows": decisions,
        "provenance": "untrusted-json-evaluation-only",
    }


__all__ = ["ExternalReviewError","parse_structured_review","evaluate_review_snapshot"]
