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
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from tfont.batch_proposals import packaged_resource
from tfont.candidate_evidence import CandidateEvidenceResources, MAX_CANDIDATE_EVIDENCE

from tfont.external_review_gate import (
    ExternalReviewError, evaluate_review_snapshot,
)
from tfont.single_agent_review import evaluate_single_agent_snapshot
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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward reviewer tokens through an HTTP(S) redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


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
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=20) as response:
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
    kind = env.get("GITHUB_EVENT_NAME")
    if kind not in {"pull_request_target", "issue_comment"}:
        _abort("live gate requires a trusted-base PR or authorized PR-comment event")
    repo = env.get("GITHUB_REPOSITORY")
    event_path = env.get("GITHUB_EVENT_PATH")
    token = env.get("GITHUB_TOKEN")
    if (not token or not repo or not event_path
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)):
        _abort("trusted GitHub event, repository or read token not available")
    event = _json_file(Path(event_path))
    if kind == "pull_request_target":
        pr = event.get("pull_request")
        if type(pr) is not dict or type(pr.get("head")) is not dict:
            _abort("GitHub event contains no PR head")
        n = pr.get("number", event.get("number"))
        sha = pr["head"].get("sha")
        if type(n) is not int or type(sha) is not str:
            _abort("GitHub event PR number / SHA invalid")
        return repo, n, sha

    # GitHub's issue_comment workflow file and GITHUB_SHA are on the default
    # branch. The comment is only a request to RECHECK: it is not approval.
    # Read the current PR head from GitHub, never from the comment/issue JSON.
    if env.get("GITHUB_REF") != "refs/heads/main" or event.get("action") != "created":
        _abort("PR review-refresh comment is not on protected default branch")
    issue, comment = event.get("issue"), event.get("comment")
    if type(issue) is not dict or type(comment) is not dict:
        _abort("PR review-refresh requires real issue and comment objects")
    n = issue.get("number")
    user = comment.get("user")
    if (type(n) is not int or n <= 0 or type(issue.get("pull_request")) is not dict
            or type(user) is not dict or not isinstance(user.get("login"), str)
            or not user["login"]):
        _abort("PR review-refresh comment is not a valid pull request comment")
    expected_url = f"https://api.github.com/repos/{repo}/pulls/{n}"
    if issue["pull_request"].get("url") != expected_url:
        _abort("PR comment does not identify the current repository pull request")
    if (comment.get("body") != "/ontoTF verify-review"
            or comment.get("author_association") not in {"OWNER", "MEMBER", "COLLABORATOR"}):
        _abort("PR comment lacks a maintainer review-refresh request")
    labels = issue.get("labels")
    if (type(labels) is not list
            or "ontology-batch-review" not in {
                item.get("name") for item in labels if type(item) is dict
            }):
        _abort("PR review label missing from trusted comment event")
    path = "/repos/" + "/".join(urllib.parse.quote(part, safe="") for part in repo.split("/"))
    current = _api(path + f"/pulls/{n}", token)
    if type(current) is not dict:
        _abort("GitHub current PR metadata unavailable")
    head, base = current.get("head"), current.get("base")
    current_labels = current.get("labels")
    try:
        sha = head["sha"]
        valid = (
            type(current.get("number")) is int and current["number"] == n
            and current.get("state") == "open" and current.get("draft") is False
            and type(sha) is str and re.fullmatch(r"[0-9a-f]{40}", sha) is not None
            and head["repo"]["full_name"] == repo
            and base["repo"]["full_name"] == repo and base["ref"] == "main"
            and type(current_labels) is list
            and "ontology-batch-review" in {
                item.get("name") for item in current_labels if type(item) is dict
            }
        )
    except (KeyError, TypeError):
        valid = False
    if not valid:
        _abort("PR review-refresh current head, base, state, or label invalid")
    return repo, n, sha


def _checked_candidate_path(value: Any, prefix: str) -> str:
    """Never let untrusted manifest choose a script, branch, or foreign path."""
    if type(value) is not str or not value.startswith(prefix + "/") or not value.endswith(".json"):
        _abort("candidate batch input path is outside the allowed JSON directory")
    parts = value.split("/")
    if any(
        not part or part in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.-]+", part)
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


def fetch_pr_head_context() -> tuple[
    dict[str, Any], dict[str, Any], Callable[[str], dict[str, Any]],
]:
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
    version = meta.get("schema_version")
    keys = {"schema_version", "ledger", "packet"}
    if type(version) is not int or version not in {1, 2}:
        _abort("candidate batch manifest version is invalid")
    if version == 2:
        keys.add("evidence_resources")
    if set(meta) != keys:
        _abort("candidate batch manifest has unexpected or missing fields")
    ledger_path = _checked_candidate_path(
        meta["ledger"], "src/tfont/resources/batch_pilots"
    )
    packet_path = _checked_candidate_path(
        meta["packet"], "docs/research/data/generated/i033d"
    )
    ledger = _pr_head_file(repository, sha, ledger_path, token)
    packet = _pr_head_file(repository, sha, packet_path, token)
    read = packaged_resource
    try:
        if version == 2:
            paths = meta["evidence_resources"]
            if type(paths) is not dict or not 1 <= len(paths) <= MAX_CANDIDATE_EVIDENCE:
                _abort("candidate evidence manifest exceeds 1–32 resource bounds")
            checked = {name: _checked_candidate_path(path, "docs/research/data/batch_review/evidence")
                       for name, path in paths.items()}
            if len(set(checked.values())) != len(checked):
                _abort("candidate evidence manifest repeats an input path")
            evidence = {name: _pr_head_file(repository, sha, path, token)
                        for name, path in checked.items()}
            read = CandidateEvidenceResources(ledger, evidence)
        verify_review_packet(packet, ledger, resource_loader=read)
    except (KeyError, TypeError, ValueError) as exc:
        raise ExternalReviewError("PR-supplied batch packet does not reproduce pinned ledger") from exc
    return packet, ledger, read


def fetch_pr_head_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    """Legacy manifest-v1 interface; never silently discard evidence context."""
    packet, ledger, read = fetch_pr_head_context()
    if read is not packaged_resource:
        _abort("candidate evidence requires the complete PR-head resource context")
    return packet, ledger


def evaluate_live_gate(
    packet: dict[str, Any], ledger: dict[str, Any], *,
    resource_loader: Callable[[str], dict[str, Any]] = packaged_resource,
) -> dict[str, Any]:
    """The **only** trusted data path. Cannot authorize using supplied snapshots."""
    try:
        verify_review_packet(packet,ledger,resource_loader=resource_loader)
    except (KeyError, TypeError, ValueError) as exc:
        raise ExternalReviewError("packet does not reproduce pinned source ledger") from exc
    repository, pr_number, sha = _github_event()
    token=os.environ["GITHUB_TOKEN"]
    path="/repos/"+"/".join(urllib.parse.quote(x,safe="") for x in repository.split("/"))
    pr=_api(path+f"/pulls/{pr_number}",token)
    labels = pr.get("labels") if type(pr) is dict else None
    single_agent = (
        type(labels) is list and
        "ontology-single-agent-review" in {
            item.get("name") for item in labels if type(item) is dict
        }
    )
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
        state = review.get("state")
        login=review["user"].get("login")
        # A sole author cannot use GitHub APPROVED on their own PR. Under
        # explicit single-agent opt-in, two COMMENTED exact-head reviews by
        # the author must record challenge-first scrutiny and later decisions.
        # The external APPROVED route is still the default and unchanged.
        author_login = pr.get("user", {}).get("login")
        if not (
            state == "APPROVED" or
            (single_agent and state == "COMMENTED"
             and type(login) is str and type(author_login) is str
             and login.casefold() == author_login.casefold())
        ):
            continue
        if type(login) is not str or not login:
            _abort("reviewer account identity missing")
        if login not in permissions:
            encoded=urllib.parse.quote(login,safe="")
            data=_api(path+f"/collaborators/{encoded}/permission",token)
            if type(data) is not dict or type(data.get("permission")) is not str:
                _abort("cannot establish current GitHub reviewer permission")
            permissions[login]=data["permission"]

    # Review state can be dismissed/edited during collaborator-permission
    # requests. An unchanged head alone does not prove approval still exists.
    # Fail closed when the live reviewer snapshot has changed mid-verification.
    current_reviews = []
    for page in range(1, MAX_REVIEW_PAGES + 1):
        chunk = _api(path + f"/pulls/{pr_number}/reviews?per_page=100&page={page}", token)
        if type(chunk) is not list or len(chunk) > 100:
            _abort("invalid second GitHub review page")
        current_reviews.extend(chunk)
        if len(chunk) < 100:
            break
    else:
        _abort("second GitHub review pagination exceeds configured bound")
    if current_reviews != reviews:
        _abort("GitHub independent reviewer decisions changed during verification")

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
    reviewer = (
        evaluate_single_agent_snapshot if single_agent else evaluate_review_snapshot
    )
    # No mode fallback. If the explicit label is present, fail closed unless
    # two source-bound, chronological author COMMENTED review events exist.
    result=reviewer(
        packet=packet,repository=repository,pr_number=pr_number,
        expected_head_sha=sha,pull_request=fresh_pr,reviews=reviews,
        reviewer_permissions=permissions,
    )
    # This is a live GitHub workflow observation, NOT an independent reviewer
    # signature. In single-agent mode the identity is intentionally the author.
    result["provenance"]=(
        "github-live-rest-verified-single-agent-adversarial-two-pass;not-offline-signed"
        if single_agent else
        "github-live-rest-verified-at-this-run;not-offline-signed"
    )
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--from-pr-head",action="store_true")
    mode.add_argument("--packet",type=Path)
    parser.add_argument("--ledger",type=Path)
    parser.add_argument("--publish-handoff", action="store_true")
    args=parser.parse_args()
    if args.from_pr_head and args.ledger is not None:
        parser.error("--ledger cannot override PR-head protected source selection")
    if args.packet is not None and args.ledger is None:
        parser.error("--packet requires --ledger")
    if args.publish_handoff and not args.from_pr_head:
        parser.error("--publish-handoff requires protected --from-pr-head data")
    try:
        packet, ledger, read = (
            fetch_pr_head_context() if args.from_pr_head
            else (_json_file(args.packet), _json_file(args.ledger), packaged_resource)
        )
        result=evaluate_live_gate(packet, ledger, resource_loader=read)
        if args.publish_handoff:
            from tfont.overlay_handoff import (
                build_overlay_handoff, verify_overlay_handoff_integrity,
            )
            pack = build_overlay_handoff(packet, ledger, result, resource_loader=read)
            # Independent structural check does NOT issue review authority.
            # Live GitHub approval is still fetched again immediately below.
            verify_overlay_handoff_integrity(pack)
            encoded = json.dumps(pack, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            fresh = evaluate_live_gate(packet, ledger, resource_loader=read)
            if fresh != result:
                _abort("review authority changed before handoff publication")
            # Exclusive fixed output: no overwrite, symlink following, caller
            # path or offline receipt. Signing is performed by the workflow.
            with Path("batch-review-pack.json").open("x", encoding="utf-8") as output:
                try:
                    output.write(encoded)
                    output.flush()
                except OSError:
                    Path("batch-review-pack.json").unlink()
                    raise
    except (ExternalReviewError, KeyError, TypeError, ValueError, OSError) as exc:
        print(f"REJECTED: {exc}",file=sys.stderr)
        return 1
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
