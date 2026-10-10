#!/usr/bin/env python3
"""Build pinned, non-authoritative POS evidence from original corpus sources.

This never creates ontology mappings. Corpus labels and enums are independent
and remain separate even when native codes have identical spellings.
"""
from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/research/data/generated/i027c1/native-pos-matrix.json"
BHSA = ROOT / "upstream-bhsa/docs/features/sp.md"
SYRIAC = ROOT / "upstream-syriac/data/lib/syriac/word_grammar"
EXTRA = ROOT / "upstream-extra/source/0.2/extraBiblical.mql.bz2"
SOURCE_SPECS = {
    "bhsa": {
        "source_repository": "ETCBC/bhsa",
        "source_revision": "4db00e2157915495e1a4d3d57e41223df24775da",
        "target_corpus_revision": "4db00e2157915495e1a4d3d57e41223df24775da",
        "source_path": "docs/features/sp.md",
        "count": 14,
    },
    "syriac": {
        "source_repository": "ETCBC/linksyr",
        "source_revision": "3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6",
        "target_corpus_revision": "bb0eaa7e21b020a26b7566d2e495da9b1f84a919",
        "source_path": "data/lib/syriac/word_grammar",
        "count": 10,
    },
    "extrabiblical": {
        "source_repository": "ETCBC/extrabiblical",
        "source_revision": "9a56288e6777bad6328856acf055c780e65dd5d9",
        "target_corpus_revision": "9a56288e6777bad6328856acf055c780e65dd5d9",
        "source_path": "source/0.2/extraBiblical.mql.bz2",
        "count": 14,
    },
}
MQL_BLOB = "4ba717b1716b747bb94d0359b950a55d8624b109"
MQL_SIZE = 1992719


def parse_bhsa(doc: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(doc.splitlines(), start=1):
        match = re.match(r"^\s*`([a-z]+)`\s*\|\s*([^|]+?)\s*$", line)
        if not match:
            continue
        code, gloss = match.group(1), match.group(2).strip()
        if code in result:
            raise ValueError(f"duplicate BHSA POS category {code}")
        result[code] = {"line": line_number, "gloss": gloss}
    if not result:
        raise ValueError("BHSA source has no POS category table")
    return result


def parse_syriac(grammar: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    within = False
    for line_number, line in enumerate(grammar.splitlines(), start=1):
        if not within:
            if re.match(r'^\s*sp\s*:\s*"part of speech"\s*=', line):
                within = True
            continue
        if re.match(r'^\s*(st|vo|vs|vt|ls|nu|gn)\s*:', line):
            break
        match = re.match(r'^\s*([a-z]+)\s*:\s*"([^"]+)"', line)
        if match:
            code, gloss = match.group(1), match.group(2)
            if code in result:
                raise ValueError(f"duplicate Syriac POS category {code}")
            result[code] = {"line": line_number, "gloss": gloss}
    if not result:
        raise ValueError("Syriac grammar has no POS category values")
    return result


def parse_mql(doc: str) -> dict[str, dict[str, Any]]:
    lines = doc.splitlines()
    open_line = None
    for i, line in enumerate(lines):
        if re.search(r"\bCREATE\s+ENUMERATION\s+part_of_speech_t\s*=\s*\{", line, re.I):
            if open_line is not None:
                raise ValueError("duplicate original MQL POS enum")
            open_line = i
    if open_line is None:
        raise ValueError("original MQL is missing part_of_speech_t enumeration")
    tail = lines[open_line + 1 :]
    result: dict[str, dict[str, Any]] = {}
    ids: set[int] = set()
    closed = False
    for offset, line in enumerate(tail):
        if re.match(r"^\s*\}\s*;?\s*$", line):
            closed = True
            break
        match = re.match(r"^\s*([a-z][A-Za-z0-9_]*)\s*=\s*(\d+)\s*,?\s*$", line)
        if match:
            name, code_id = match.group(1), int(match.group(2))
            if name in result or code_id in ids:
                raise ValueError(f"duplicate MQL native code or numeric ID: {name}")
            ids.add(code_id)
            result[name] = {"line": open_line + offset + 2, "gloss": None, "numeric_id": code_id}
        elif line.strip():
            raise ValueError(f"unparsed original MQL POS declaration: line {open_line + offset + 2}")
    if not closed or not result:
        raise ValueError("incomplete original MQL part_of_speech_t enumeration")
    if not re.search(r"\bsp\s*:\s*part_of_speech_t\s*;", doc):
        raise ValueError("original MQL sp not typed as part_of_speech_t")
    return result


def decode_pinned_mql(
    raw: bytes,
    *,
    expected_size: int = MQL_SIZE,
    expected_blob: str = MQL_BLOB,
) -> str:
    if len(raw) != expected_size:
        raise ValueError("original MQL compressed size mismatch")
    blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if blob != expected_blob:
        raise ValueError("original MQL Git blob digest mismatch")
    try:
        decoded = bz2.decompress(raw)
    except (OSError, EOFError, ValueError) as err:
        raise ValueError("original MQL bzip2 decompression failed") from err
    try:
        return decoded.decode("utf-8", "strict")
    except UnicodeDecodeError as err:
        raise ValueError("original MQL encoding not UTF-8") from err


def reconcile(
    corpus: str,
    definitions: dict[str, dict[str, Any]],
    observed: dict[str, int],
    source_path: str,
    source_revision: str,
    target_revision: str,
) -> list[dict[str, Any]]:
    missing = sorted(set(observed) - set(definitions))
    if missing:
        raise ValueError(f"{corpus}: source missing observed native POS codes: {missing}")
    source_only = sorted(set(definitions) - set(observed))
    if source_only:
        raise ValueError(f"{corpus}: source-only native POS codes need explicit review: {source_only}")
    result = []
    for code in sorted(observed):
        definition = definitions[code]
        gloss = definition["gloss"]
        if corpus == "extrabiblical" and gloss is not None:
            raise ValueError("MQL numeric enum must not claim unverified English gloss")
        if type(observed[code]) is not int or observed[code] <= 0:
            raise ValueError(f"{corpus}: invalid R-005 observed frequency: {code}")
        result.append({
            "corpus_id": corpus,
            "native_feature": "sp",
            "native_code": code,
            "source_definition_kind": "enum-only" if gloss is None else "explicit-gloss",
            "source_gloss": gloss,
            "source_numeric_id": definition.get("numeric_id"),
            "source_line": definition["line"],
            "source_path": source_path,
            "source_revision": source_revision,
            "target_corpus_revision": target_revision,
            "observed_feature_records": observed[code],
            "ontology_mapping_authorized": False,
        })
    return result


def build_from_pinned_paths() -> dict[str, Any]:
    definitions = {
        "bhsa": parse_bhsa(BHSA.read_text(encoding="utf-8")),
        "syriac": parse_syriac(SYRIAC.read_text(encoding="utf-8")),
        "extrabiblical": parse_mql(decode_pinned_mql(EXTRA.read_bytes())),
    }
    rows = []
    counts = {}
    for corpus, spec in SOURCE_SPECS.items():
        inventory = json.loads(
            (ROOT / f"docs/research/data/generated/r005/{corpus}.json").read_text(encoding="utf-8")
        )
        feature = inventory["node_features"]["sp"]
        if "word" not in feature["applies_to"]:
            raise ValueError(f"{corpus}: sp does not apply to word nodes")
        observed = feature["observed_frequencies"]
        parts = reconcile(
            corpus, definitions[corpus], observed,
            spec["source_path"], spec["source_revision"], spec["target_corpus_revision"],
        )
        if len(parts) != spec["count"] or sum(observed.values()) != feature["observation_count"]:
            raise ValueError(f"{corpus}: source/TF inventory POS count drifted")
        counts[corpus] = len(parts)
        rows.extend(parts)
    if len(rows) != 38 or any(row["ontology_mapping_authorized"] for row in rows):
        raise ValueError("I-027C1 output must have 38 non-authoritative source rows")
    return {
        "schema_version": 1,
        "matrix_id": "i027c1-three-corpus-source-pos",
        "source_locks": SOURCE_SPECS,
        "original_mql_blob_sha": MQL_BLOB,
        "original_mql_size": MQL_SIZE,
        "counts": counts,
        "semantic_rows": rows,
        "production_ontology_mapping_authorized": False,
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    value = serialized(build_from_pinned_paths())
    if args.stdout:
        print(value, end="")
    elif args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != value:
            raise SystemExit("I-027C1 frozen source POS evidence matrix missing or stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(value, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
