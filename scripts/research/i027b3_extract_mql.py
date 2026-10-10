#!/usr/bin/env python3
"""Extract bounded, reproducible POS evidence from the original pinned ExtraBiblical MQL.

This is research tooling, not a semantic mapper. In particular, textual
occurrence of "verb" never authorizes an ontology correspondence.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import re
from pathlib import Path


PINNED_SOURCE_REVISION = "9a56288e6777bad6328856acf055c780e65dd5d9"
PINNED_BLOB_SHA = "4ba717b1716b747bb94d0359b950a55d8624b109"
PINNED_COMPRESSED_SIZE = 1992719
PINNED_SOURCE_PATH = "source/0.2/extraBiblical.mql.bz2"

PATTERNS = {
    "part_of_speech_t": re.compile(r"\bpart_of_speech_t\b", re.IGNORECASE),
    "sp": re.compile(r"\bsp\b", re.IGNORECASE),
    "verb": re.compile(r"\bverb\b", re.IGNORECASE),
}


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def extract(
    raw: bytes,
    *,
    expected_blob_sha: str = PINNED_BLOB_SHA,
    expected_size: int = PINNED_COMPRESSED_SIZE,
) -> dict[str, object]:
    if type(raw) is not bytes:
        raise ValueError("source must be exact bytes")
    if len(raw) != expected_size:
        raise ValueError(
            f"compressed source size mismatch: got {len(raw)}, expected {expected_size}"
        )
    digest = git_blob_sha(raw)
    if digest != expected_blob_sha:
        raise ValueError(
            f"source Git blob mismatch: got {digest}, expected {expected_blob_sha}"
        )

    try:
        decompressed = bz2.decompress(raw)
    except (OSError, EOFError, ValueError) as exc:
        raise ValueError("source bzip2 payload could not be decompressed") from exc

    try:
        text = decompressed.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("source is not valid UTF-8") from exc

    lines = text.splitlines()
    counts: dict[str, int] = {}
    excerpts: dict[str, list[dict[str, object]]] = {}
    for category, pattern in PATTERNS.items():
        indices = [i for i, line in enumerate(lines) if pattern.search(line)]
        counts[category] = len(indices)
        samples: list[dict[str, object]] = []
        for i in indices[:6]:
            # Only short adjacent lines; no full source, tables, or large catalogs.
            snippet = " | ".join(
                lines[j][:180] for j in range(max(0, i - 1), min(len(lines), i + 2))
            )[:600]
            samples.append({"line": i + 1, "context": snippet})
        excerpts[category] = samples

    return {
        "schema_version": 1,
        "source_repository": "ETCBC/extrabiblical",
        "source_revision": PINNED_SOURCE_REVISION,
        "source_path": PINNED_SOURCE_PATH,
        "compressed_size": len(raw),
        "git_blob_sha": digest,
        "compressed_sha256": hashlib.sha256(raw).hexdigest(),
        "decompressed_size": len(decompressed),
        "decompressed_sha256": hashlib.sha256(decompressed).hexdigest(),
        "encoding": "UTF-8",
        "match_counts": counts,
        "excerpts": excerpts,
        "exact_mapping_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    source = args.input.read_bytes()
    report = extract(source)
    result = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(result, end="")
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
