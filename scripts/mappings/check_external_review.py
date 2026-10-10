#!/usr/bin/env python3
"""Live GitHub PR review gate, intended ONLY for trusted-base release CI.

Do not run a PR-head checkout with the token used here. This command reads
untrusted packet/ledger JSON as DATA but imports verified policy CODE from a
protected branch. Its JSON output is an audit record, not a signed certificate.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from tfont.external_review_gate import (
    ExternalReviewError, evaluate_review_snapshot,
)
from tfont.review_packets import verify_review_packet
from tfont.source_validation import loads_source


MAX_BODY = 3_000_000
MAX_REVIEW_PAGES = 5
MAX_CANDIDATE_BYTES = 1_000_000
BATCH_INPUT_MANIFEST = "docs/research/data/batch_review/inputs.json"
API_HOST = "https://api.github.com"


def _abort(message: str) -> None:
    raise ExternalReviewError(message)


def _json_file(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size < 1 or size > MAX_BODY:
            _abort("review packet / ledger exceeds trusted input size bounds")
        value = loads_source(path.read_text(encoding="utf-8"),format="json",source_name=str(path))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ExternalReviewError("invalid JSON input document") from exc
    if type(value) is not dict:
        _abort("review packet / ledger must be a JSON object")
    return value


def _api(path: str, token: str) -> Any:
    if not path.startswith("/repos/") or "//" in path:
        _abort("untrusted GitHub API route")
    request = urllib.request.Request(
        API_HOST + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ontoTF-independent-review-gate",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                _abort("GitHub API did not return HTTP 200")
            raw = response.read(MAX_BODY + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ExternalReviewError("GitHub live review/permission API unavailable") from exc
    if len(raw) > MAX_BODY:
        _abort("GitHub API response body exceeds safety bound")
    try:
        return loads_source(raw.decode("utf-8"),format="json",source_name="github-api")
    except (UnicodeError, ValueError) as exc:
        raise ExternalReviewError("GitHub API returned invalid JSON") from exc


def _github_event() -> tuple[str, int, str]:
    env = os.environ
    if env.get("GITHUB_EVENT_NAME") not in {"pull_request_target", "pull_request_review"}:
        _abort("live gate requires a protected-base PR/review event")
    repo = env.get("GITHUB_REPOSITORY")
    event_path = env.get("GITHUB_EVENT_PATH")
    token = env.get("GITHUB_TOKEN")
    if not token or not repo or not event_path:
        _abort("trusted GitHub event, repository or read token not available")
    event = _json_file(Path(event_path))
    pr = event.get("pull_request")
    if type(pr) is not dict or type(pr.get("head")) is not dict:
        _abort("GitHub event contains no PR head")
    n = pr.get("number",event.get("number"))
    sha = pr["head"].get("sha")
    if type(n) is not int or type(sha) is not str:
        _abort("GitHub event PR number / SHA invalid")
    return repo, n, sha


def _checked_candidate_path(value: Any, prefix: str) -> str:
    """Never let untrusted manifest choose a script, branch, or foreign path."""
    if type(value) is not str or not value.startswith(prefix + "/") or not value.endswith(".json"):
        _abort("candidate batch input path is outside the allowed JSON directory")
    parts = value.split("/")
    if any(
        not part or part in {".", ".."} or "\\" in part
        or "?" in part or "#" in part or "%" in part
        for part in parts
    ):
        _abort("candidate batch input path is not canonical")
    return value


def _pr_head_file(repository: str, sha: str, name: str, token: str) -> dict[str, Any]:
    """Fetch JSON *data* at a GitHub-pinned PR SHA and verify Git blob identity."""
    if type(sha) is not str or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        _abort("malformed candidate Git head SHA")
    path = "/repos/" + "/".join(
        urllib.parse.quote(part, safe="") for part in repository.split("/")
    )
    escaped = "/".join(urllib.parse.quote(part, safe="") for part in name.split("/"))
    response = _api(path + "/contents/" + escaped + "?ref=" + sha, token)
    if type(response) is not dict or set(("path", "type", "size", "encoding", "content", "sha")) - response.keys():
        _abort("GitHub candidate content has missing file metadata")
    if (
        response["path"] != name or response["type"] != "file"
        or response["encoding"] != "base64"
        or type(response["size"]) is not int
        or not 1 <= response["size"] <= MAX_CANDIDATE_BYTES
        or type(response["content"]) is not str
        or type(response["sha"]) is not str
    ):
        _abort("GitHub candidate file metadata is inconsistent or oversized")
    # GitHub's base64 JSON commonly contains line breaks. Do not strip any
    # other characters (notably spaces), and reject malformed base64 strictly.
    encoded = response["content"].replace("\n", "").replace("\r", "")
    if len(encoded) > (MAX_CANDIDATE_BYTES + 2) // 3 * 4:
        _abort("GitHub candidate base64 exceeds bounded source size")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ExternalReviewError("GitHub candidate base64 invalid") from exc
    if len(raw) != response["size"]:
        _abort("GitHub candidate byte length inconsistent")
    actual_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + bytes((0,)) + raw
    ).hexdigest()
    if actual_blob != response["sha"]:
        _abort("GitHub candidate source blob checksum mismatch")
    try:
        value = loads_source(raw.decode("utf-8"), format="json", source_name=name)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ExternalReviewError("GitHub candidate JSON corrupt or ambiguous") from exc
    if type(value) is not dict:
        _abort("GitHub candidate document must be a JSON object")
    return value


def fetch_pr_head_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the only allowed manifest + packet/ledger from the exact PR HEAD.

    No PR script is imported, executed or checked out. The independently
    reviewed trusted-base compiler recomputes packet bytes from source pins.
    """
    repository, pr_number, sha = _github_event()
    token = os.environ["GITHUB_TOKEN"]
    prefix = "/repos/" + "/".join(
        urllib.parse.quote(part, safe="") for part in repository.split("/")
    )
    pr = _api(prefix + f"/pulls/{pr_number}", token)
    try:
        head = pr["head"]
        current_repo = head["repo"]["full_name"]
        base_repo = pr["base"]["repo"]["full_name"]
        correct = (
            pr["number"] == pr_number and pr["state"] == "open"
            and pr["draft"] is False and head["sha"] == sha
            and current_repo == base_repo == repository
        )
    except (KeyError, TypeError):
        correct = False
    if not correct:
        _abort("candidate PR head, author or repository changed before review fetch")
    meta = _pr_head_file(repository, sha, BATCH_INPUT_MANIFEST, token)
    if (
        set(meta) != {"schema_version", "ledger", "packet"}
        or type(meta["schema_version"]) is not int
        or meta["schema_version"] != 1
    ):
        _abort("candidate batch manifest has unexpected or missing fields")
    ledger_path = _checked_candidate_path(
        meta["ledger"], "src/tfont/resources/batch_pilots"
    )
    packet_path = _checked_candidate_path(
        meta["packet"], "docs/research/data/generated/i033d"
    )
    ledger = _pr_head_file(repository, sha, ledger_path, token)
    packet = _pr_head_file(repository, sha, packet_path, token)
    try:
        verify_review_packet(packet, ledger)
    except (KeyError, TypeError, ValueError) as exc:
        raise ExternalReviewError("PR-supplied batch packet does not reproduce pinned ledger") from exc
    return packet, ledger


def evaluate_live_gate(packet: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    """The **only** trusted data path. Cannot authorize using supplied snapshots."""
    try:
        verify_review_packet(packet,ledger)
    except (KeyError, TypeError, ValueError) as exc:
        raise ExternalReviewError("packet does not reproduce pinned source ledger") from exc
    repository, pr_number, sha = _github_event()
    token=os.environ["GITHUB_TOKEN"]
    path="/repos/"+"/".join(urllib.parse.quote(x,safe="") for x in repository.split("/"))
    pr=_api(path+f"/pulls/{pr_number}",token)
    reviews=[]
    for page in range(1,MAX_REVIEW_PAGES+1):
        chunk=_api(path+f"/pulls/{pr_number}/reviews?per_page=100&page={page}",token)
        if type(chunk) is not list or len(chunk)>100:
            _abort("invalid GitHub reviews page")
        reviews.extend(chunk)
        if len(chunk)<100:
            break
    else:
        _abort("GitHub review pagination exceeds configured bound")
    permissions={}
    for review in reviews:
        if type(review) is not dict or type(review.get("user")) is not dict:
            _abort("review has invalid user data")
        if review.get("state")!="APPROVED":
            continue
        login=review["user"].get("login")
        if type(login) is not str or not login:
            _abort("reviewer account identity missing")
        if login not in permissions:
            encoded=urllib.parse.quote(login,safe="")
            data=_api(path+f"/collaborators/{encoded}/permission",token)
            if type(data) is not dict or type(data.get("permission")) is not str:
                _abort("cannot establish current GitHub reviewer permission")
            permissions[login]=data["permission"]

    # Re-read the PR after the review + permission API round trips. Otherwise
    # a force-push in this window could make a correct-looking approval stale.
    fresh_pr=_api(path+f"/pulls/{pr_number}",token)
    def identity(record: dict[str, Any]) -> tuple[Any, ...]:
        try:
            return (
                record["number"], record["state"], record["draft"],
                record["head"]["sha"], record["head"]["repo"]["full_name"],
                record["base"]["repo"]["full_name"], record["user"]["login"],
            )
        except (KeyError, TypeError) as exc:
            raise ExternalReviewError("GitHub PR changed or became unreadable") from exc
    if type(fresh_pr) is not dict or identity(pr)!=identity(fresh_pr):
        _abort("PR head/author/state changed while verifying review authority")
    result=evaluate_review_snapshot(
        packet=packet,repository=repository,pr_number=pr_number,
        expected_head_sha=sha,pull_request=fresh_pr,reviews=reviews,
        reviewer_permissions=permissions,
    )
    # Not a cryptographic signature. Offline packages may validate the
    # digest and provenance but MUST NOT re-use this as live approval.
    result["provenance"]="github-live-rest-verified-at-this-run;not-offline-signed"
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--from-pr-head",action="store_true")
    mode.add_argument("--packet",type=Path)
    parser.add_argument("--ledger",type=Path)
    args=parser.parse_args()
    if args.from_pr_head and args.ledger is not None:
        parser.error("--ledger cannot override PR-head protected source selection")
    if args.packet is not None and args.ledger is None:
        parser.error("--packet requires --ledger")
    try:
        packet, ledger = (
            fetch_pr_head_inputs() if args.from_pr_head
            else (_json_file(args.packet), _json_file(args.ledger))
        )
        result=evaluate_live_gate(packet, ledger)
    except (ExternalReviewError, KeyError, TypeError, ValueError) as exc:
        print(f"REJECTED: {exc}",file=sys.stderr)
        return 1
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
