#!/usr/bin/env python3
"""Live GitHub PR review gate, intended ONLY for trusted-base release CI.

Do not run a PR-head checkout with the token used here. This command reads
untrusted packet/ledger JSON as DATA but imports verified policy CODE from a
protected branch. Its JSON output is an audit record, not a signed certificate.
"""
from __future__ import annotations

import argparse
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
    if env.get("GITHUB_EVENT_NAME") != "pull_request_target":
        _abort("live gate requires a trusted-base pull_request_target job")
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
    parser.add_argument("--packet",required=True,type=Path)
    parser.add_argument("--ledger",required=True,type=Path)
    args=parser.parse_args()
    try:
        result=evaluate_live_gate(_json_file(args.packet),_json_file(args.ledger))
    except (ExternalReviewError, KeyError, TypeError, ValueError) as exc:
        print(f"REJECTED: {exc}",file=sys.stderr)
        return 1
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
