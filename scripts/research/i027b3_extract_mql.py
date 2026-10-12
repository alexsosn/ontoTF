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



_ENUM_OPEN = re.compile(
    r"^\s*CREATE\s+ENUMERATION\s+part_of_speech_t\s*=\s*\{\s*$",
    re.IGNORECASE,
)
_ENUM_VALUE = re.compile(r"^\s*([a-z][a-z0-9_]*)\s*=\s*(\d+)\s*,?\s*$", re.IGNORECASE)
_ENUM_CLOSE = re.compile(r"^\s*\}\s*;?\s*$")
_SP_TYPE = re.compile(r"^\s*sp\s*:\s*part_of_speech_t\s*;\s*$", re.IGNORECASE)
_OBJECT_TYPE_OPEN = re.compile(r"^\s*CREATE\s+OBJECT\s+TYPE\s+\[\s*([a-z][a-z0-9_]*)\s*\]", re.IGNORECASE)


def extract_pos_enum(text: str) -> dict[str, object]:
    """Extract the original MQL POS enum and original one-based source lines.

    No BHSA gloss inference, fabricated target class, or source corpus payload.
    """
    if type(text) is not str:
        raise ValueError("decoded MQL must be text")
    lines = text.splitlines()
    openings = [i for i, line in enumerate(lines) if _ENUM_OPEN.fullmatch(line)]
    if len(openings) != 1:
        raise ValueError("expected exactly one part_of_speech_t enumeration")
    word_feature = [i for i, line in enumerate(lines) if _SP_TYPE.fullmatch(line)]
    if len(word_feature) != 1:
        raise ValueError("sp must use exactly one part_of_speech_t declaration")
    # A declaration of sp on a non-word object must not be mistaken for
    # original word.sp corpus semantics. Resolve the containing object from
    # the nearest preceding MQL object-type declaration.
    object_types = [(i, kind.group(1).lower())
                    for i, line in enumerate(lines)
                    if (kind := _OBJECT_TYPE_OPEN.match(line)) is not None
                    and i < word_feature[0]]
    if not object_types or object_types[-1][1] != "word":
        raise ValueError("part_of_speech_t sp must be declared for word object")
    start = openings[0]
    values: list[dict[str, object]] = []
    seen_names: set[str] = set()
    seen_codes: set[int] = set()
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if _ENUM_CLOSE.fullmatch(line):
            if not 1 <= len(values) <= 64:
                raise ValueError("part_of_speech_t enumeration has invalid bounded size")
            return {
                "enum_declaration_line": start + 1,
                "feature_type_line": word_feature[0] + 1,
                "values": values,
            }
        if not line.strip():
            continue
        value = _ENUM_VALUE.fullmatch(line)
        if value is None:
            raise ValueError(f"invalid POS enum declaration on original line {i + 1}")
        name, code_text = value.groups()
        code = int(code_text)
        if name in seen_names or code in seen_codes:
            raise ValueError("duplicate POS category name or integer code")
        seen_names.add(name)
        seen_codes.add(code)
        values.append({"value": name, "code": code, "line": i + 1})
        if len(values) > 64:
            raise ValueError("POS enumeration exceeds 64 records")
    raise ValueError("unterminated POS enum declaration")


def extract(
    raw: bytes,
    *,
    expected_blob_sha: str = PINNED_BLOB_SHA,
    expected_size: int = PINNED_COMPRESSED_SIZE,
    require_pos_enum: bool = False,
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

    # Legacy research callers also inspect partial/unrelated MQL. Preserve
    # their bounded occurrence scan without claiming an extracted POS enum.
    # Exact pinned-source verification opts into strict parsing below.
    try:
        pos_enum = extract_pos_enum(text)
    except ValueError:
        if require_pos_enum:
            raise
        pos_enum = None

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
        "part_of_speech_enum": pos_enum,
        "exact_mapping_authorized": False,
    }


def verify_frozen(report: dict[str, object], frozen: dict[str, object]) -> None:
    """Check the curated evidence against freshly extracted pinned source bytes."""
    for key in (
        "source_repository",
        "source_revision",
        "source_path",
        "compressed_size",
        "git_blob_sha",
        "compressed_sha256",
        "decompressed_size",
        "decompressed_sha256",
        "encoding",
    ):
        if report.get(key) != frozen.get(key):
            raise ValueError(f"frozen source evidence identity mismatch: {key}")
    if frozen.get("exact_mapping_authorized") is not False:
        raise ValueError("source evidence must not activate an exact mapping")
    if frozen.get("schema_version") == 2:
        # A digest-bound source pin without bytewise enum comparison would
        # allow invented value codes or original source line coordinates.
        actual = report.get("part_of_speech_enum")
        declared = frozen.get("part_of_speech_enum")
        if type(actual) is not dict or type(declared) is not dict or actual != declared:
            raise ValueError("frozen POS enum differs from original source declaration")

    excerpts = report["excerpts"]
    for statement in frozen.get("statements", []):
        if type(statement) is not dict:
            raise ValueError("frozen evidence statement must be an object")
        excerpt = statement.get("excerpt")
        line = statement.get("line")
        if type(excerpt) is not str or not excerpt or type(line) is not int:
            raise ValueError("frozen evidence has invalid line/excerpt")
        if not any(
            abs(sample["line"] - line) <= 1 and excerpt in sample["context"]
            for windows in excerpts.values()
            for sample in windows
        ):
            raise ValueError(f"frozen evidence statement not reproduced: {line}")

    if report["match_counts"]["part_of_speech_t"] == 0:
        raise ValueError("original source has no part_of_speech_t evidence")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--verify-frozen", type=Path)
    args = parser.parse_args()
    source = args.input.read_bytes()
    report = extract(source, require_pos_enum=True)
    if args.verify_frozen is not None:
        verify_frozen(report, json.loads(args.verify_frozen.read_text(encoding="utf-8")))
    result = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(result, end="")
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
