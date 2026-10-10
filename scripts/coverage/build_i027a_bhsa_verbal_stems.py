#!/usr/bin/env python3
"""I-027A: immutable BHSA verbal-stem coverage-accounting successor.

Uses only committed pinned data. Does not invent an OLiA mapping, modify
historical coverage resources, download corpora, or change TF runtime.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tfont.coverage import (  # noqa: E402
    coverage_denominator_digest,
    coverage_report,
    load_coverage_manifest,
    validate_coverage_manifest,
)

POLICY = ROOT / "docs/research/data/i027a/bhsa-verbal-stem-policy.json"
OUTPUT = ROOT / "src/tfont/resources/coverage/p004-i027a-bhsa-stems-v1/bhsa.json"
ROUTING = ROOT / "docs/research/data/generated/i026/p004-work-queue.json"

EXPECTED_CORPUS = "bhsa"
EXPECTED_REPOSITORY = "ETCBC/bhsa"
EXPECTED_REVISION = "4db00e2157915495e1a4d3d57e41223df24775da"
EXPECTED_TF_VERSION = "2021"
EXPECTED_DIGEST = (
    "sha256:0b260e21a1ebdb771f3d9975cb3e7b2560261dd99d9bd14d0eeabbb566852a03"
)
EXPECTED_SOURCE_MANIFEST = "src/tfont/resources/coverage/p004-r011-baseline-v1/bhsa.json"
EXPECTED_EVIDENCE = "docs/research/data/generated/r005/bhsa.json"
EXPECTED_POLICY_ID = "i027a-bhsa-vs-native-only-v1"
EXPECTED_MANIFEST_ID = "coverage:p004-i027a-bhsa-stems-v1:bhsa"
EXPECTED_SOURCE_ID = "i027a:bhsa-vs-pinned-source-review"
EXPECTED_DISPOSITION = {
    "assessments": ["native-only"],
    "common_target": False,
    "source_ids": [EXPECTED_SOURCE_ID],
    "profiles": ["linguistic"],
    "capabilities": ["linguistic.morphology"],
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def selected_ids(values: list[str]) -> set[str]:
    if (
        type(values) is not list
        or len(values) != len(set(values))
        or not values
        or any(type(value) is not str or not value for value in values)
    ):
        raise ValueError("code values must be unique non-empty strings")
    return {"node_feature:vs"} | {
        "node_value:vs=" + json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        for value in values
    }


def build_successor(*, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = copy.deepcopy(policy) if policy is not None else read_json(POLICY)

    expected_policy = {
        "schema_version": 1,
        "policy_id": EXPECTED_POLICY_ID,
        "corpus_id": EXPECTED_CORPUS,
        "repository": EXPECTED_REPOSITORY,
        "tf_version": EXPECTED_TF_VERSION,
        "corpus_revision": EXPECTED_REVISION,
        "source_manifest": EXPECTED_SOURCE_MANIFEST,
        "source_manifest_id": "coverage:p004-r011-baseline-v1:bhsa",
        "successor_resource": "p004-i027a-bhsa-stems-v1",
        "successor_manifest_id": EXPECTED_MANIFEST_ID,
        "denominator_digest": EXPECTED_DIGEST,
        "evidence_inventory": EXPECTED_EVIDENCE,
        "native_feature": "vs",
        "node_type": "word",
        "observed_word_records": 426590,
        "expected_selected_items": 27,
        "expected_existing_production": 7,
        "expected_production_after": 34,
        "expected_common_target_after": 7,
        "expected_unreviewed_after": 185,
        "review_source_id": EXPECTED_SOURCE_ID,
        "review_document": "docs/research/I-027A-bhsa-verbal-stem-dispositions.md",
    }
    for key, expected in expected_policy.items():
        if policy.get(key) != expected:
            name = (
                "native feature" if key == "native_feature"
                else "denominator" if key == "denominator_digest"
                else "revision" if key == "corpus_revision"
                else "corpus" if key in {"corpus_id", "repository"}
                else key
            )
            raise ValueError(f"I-027A {name} policy drift: {key}")
    if policy.get("production_disposition") != EXPECTED_DISPOSITION:
        raise ValueError(
            "I-027A review must remain native-only with linguistic.morphology "
            "and no common target"
        )
    if policy.get("production_disposition", {}).get("source_ids") != [
        policy.get("review_source_id")
    ]:
        raise ValueError("I-027A disposition source_id drifted")

    source = load_coverage_manifest(ROOT / EXPECTED_SOURCE_MANIFEST)
    for key, expected in (
        ("manifest_id", expected_policy["source_manifest_id"]),
        ("corpus_id", EXPECTED_CORPUS),
        ("repository", EXPECTED_REPOSITORY),
        ("tf_version", EXPECTED_TF_VERSION),
        ("denominator_source_revision", EXPECTED_REVISION),
        ("target_corpus_revision", EXPECTED_REVISION),
        ("denominator_digest", EXPECTED_DIGEST),
        ("scope_quality", "machine-exhaustive"),
    ):
        if source.get(key) != expected:
            raise ValueError(f"I-027A source corpus/revision/denominator drift: {key}")
    if source.get("accounting_gaps") != []:
        raise ValueError("I-027A unexpected baseline accounting gaps")
    basis = source["denominator_basis"]
    if basis["source"] != EXPECTED_EVIDENCE:
        raise ValueError("I-027A denominator evidence source drifted")
    if "vs" not in basis["bounded_node_features"]:
        raise ValueError("I-027A vs family is not an approved bounded denominator")

    inventory = read_json(ROOT / EXPECTED_EVIDENCE)
    feature = inventory["node_features"]["vs"]
    if feature.get("applies_to") != ["word"]:
        raise ValueError("I-027A native feature does not apply exactly to words")
    if feature.get("metadata", {}).get("version") != EXPECTED_TF_VERSION:
        raise ValueError("I-027A inventory corpus version drift")
    if feature.get("node_records_seen") != 426590:
        raise ValueError("I-027A inventory word observation count drift")

    values = policy.get("code_values")
    if type(values) is not list:
        raise ValueError("I-027A code values are absent")
    if values != feature.get("observed_values"):
        raise ValueError("I-027A stem family code values drifted from pinned inventory")
    ids = selected_ids(values)
    if len(ids) != 27:
        raise ValueError("I-027A stem family is not exactly 27 items")

    semantic = source["semantic_items"]
    by_id = {row["item_id"]: row for row in semantic}
    manifest_family = {
        item_id for item_id in by_id
        if item_id == "node_feature:vs" or item_id.startswith("node_value:vs=")
    }
    if manifest_family != ids:
        raise ValueError("I-027A stem family is not exactly the pinned denominator family")
    if any(by_id[item_id]["accounting"]["production"] is not None for item_id in ids):
        raise ValueError("I-027A selected item already has production authority")
    if sum(row["accounting"]["production"] is not None for row in semantic) != 7:
        raise ValueError("I-027A original production-review count drifted")

    queue = read_json(ROUTING)
    routed = {
        row["item_id"]: row
        for row in queue["semantic_rows"]
        if row.get("corpus_id") == "bhsa" and row.get("item_id") in ids
    }
    if set(routed) != ids or any(
        row.get("workstream") != "C" or row.get("owner_issue") != 264
        for row in routed.values()
    ):
        raise ValueError("I-027A I-026 semantic routing ownership drifted")

    successor = copy.deepcopy(source)
    successor["manifest_id"] = EXPECTED_MANIFEST_ID
    for item in successor["semantic_items"]:
        if item["item_id"] in ids:
            item["accounting"]["production"] = copy.deepcopy(EXPECTED_DISPOSITION)

    validate_coverage_manifest(successor)
    if coverage_denominator_digest(successor) != EXPECTED_DIGEST:
        raise ValueError("I-027A successor denominator digest drifted")
    report = coverage_report(successor)
    if (
        report.semantic_items != 219
        or report.production_reviewed_items != 34
        or report.production_common_target_items != 7
        or report.production_unreviewed_items != 185
        or report.production_outside_denominator_items != 0
        or report.corpus_wide_completion_claim_eligible
    ):
        raise ValueError(f"I-027A output coverage accounting drifted: {report}")
    return successor


def serialized(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    output = serialized(build_successor())
    if args.stdout:
        print(output, end="")
    elif args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != output:
            raise SystemExit("I-027A immutable coverage manifest is missing or stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
