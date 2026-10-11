#!/usr/bin/env python3
"""Build/check a source-bound, UNAPPROVED review packet from the protected manifest.

This is an authoring tool, not an external GitHub reviewer, signature, or
release gate. The real protected publishing gate must independently re-fetch
all PR-head data and verify a distinct approved GitHub review.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from tfont.batch_proposals import packaged_resource
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.review_packets import build_review_packet, serialized, verify_review_packet
from tfont.source_validation import loads_source


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "docs/research/data/batch_review/inputs.json"
LEDGER_PREFIX = "src/tfont/resources/batch_pilots"
PACKET_PREFIX = "docs/research/data/generated/i033d"
EVIDENCE_PREFIX = "docs/research/data/batch_review/evidence"
MAX_INPUT = 1_000_000
MAX_PACKET = 3_000_000
MAX_EVIDENCE = 32
_SEGMENT = re.compile(r"[A-Za-z0-9_.-]+\Z")


def _required(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _relative_path(name: Any, prefix: str) -> str:
    _required(type(name) is str and name.startswith(prefix + "/")
              and name.endswith(".json") and len(name) <= 512,
              "candidate input not in allowed JSON directory")
    segments = name.split("/")
    _required(all(_SEGMENT.fullmatch(p) and p not in {".", ".."}
                  for p in segments),
              "candidate input path contains unsafe segment")
    return name


def _local(root: Path, name: str) -> Path:
    # root is chosen by the invoking local author, not by the JSON manifest.
    base = root.resolve(strict=True)
    candidate = base
    for segment in name.split("/"):
        candidate = candidate / segment
        _required(not candidate.is_symlink(), "candidate path traverses a symlink")
    _required(candidate.resolve(strict=False).is_relative_to(base),
              "candidate path escapes repository root")
    return candidate


def _read_json(root: Path, name: str) -> dict[str, Any]:
    path = _local(root, name)
    try:
        size = path.stat().st_size
        _required(0 < size <= MAX_INPUT, "candidate JSON file size out of bounds")
        content = path.read_text(encoding="utf-8")
        value = loads_source(content, format="json", source_name=name)
    except (OSError, UnicodeError, TypeError) as exc:
        raise ValueError("cannot read bounded candidate JSON input") from exc
    _required(type(value) is dict, "candidate JSON must be an object")
    return value


def build_packet(root: Path, *, mode: str) -> str:
    """Deterministically author/check a packet without ever issuing approval."""
    _required(mode in {"write", "check", "stdout"}, "unknown packet authoring mode")
    manifest = _read_json(root, MANIFEST)
    version = manifest.get("schema_version")
    _required(type(version) is int and version in (1, 2),
              "unsupported candidate input manifest version")
    keys = {"schema_version", "ledger", "packet"}
    if version == 2:
        keys.add("evidence_resources")
    _required(set(manifest) == keys, "unknown/missing manifest keys")
    ledger_name = _relative_path(manifest["ledger"], LEDGER_PREFIX)
    output_name = _relative_path(manifest["packet"], PACKET_PREFIX)
    ledger = _read_json(root, ledger_name)

    loader = packaged_resource
    if version == 2:
        paths = manifest["evidence_resources"]
        _required(type(paths) is dict and 1 <= len(paths) <= MAX_EVIDENCE,
                  "candidate evidence manifest must contain 1–32 resources")
        _required(all(type(k) is str and k.startswith("resources/")
                      and k.endswith(".json")
                      and all(_SEGMENT.fullmatch(p) and p not in {".", ".."}
                              for p in k.split("/"))
                      for k in paths),
                  "candidate evidence identity is malformed")
        _required(len(set(paths.values())) == len(paths),
                  "candidate evidence paths must be unique")
        records = {
            key: _read_json(root, _relative_path(value, EVIDENCE_PREFIX))
            for key, value in paths.items()
        }
        loader = CandidateEvidenceResources(ledger, records)

    packet = build_review_packet(ledger, resource_loader=loader)
    verify_review_packet(packet, ledger, resource_loader=loader)
    _required(packet["authority"] == "unreviewed-proposal"
              and packet["release_authorized"] is False,
              "local packet cannot grant release authority")
    content = serialized(packet)
    _required(len(content.encode("utf-8")) <= MAX_PACKET,
              "review packet exceeds bounded output size")

    if mode == "stdout":
        return content
    output = _local(root, output_name)
    if mode == "check":
        try:
            actual = output.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError("unapproved review packet is absent") from exc
        _required(actual == content,
                  "candidate review packet changed or is not reproducible")
        return content
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive write prevents silent mutation of a packet someone may
    # already have reviewed. A changed packet must use a new path/revision.
    with output.open("x", encoding="utf-8") as handle:
        handle.write(content)
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="Local repository root (tests may use a temporary root)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    selected = "write" if args.write else "check" if args.check else "stdout"
    result = build_packet(args.root, mode=selected)
    if args.stdout:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
