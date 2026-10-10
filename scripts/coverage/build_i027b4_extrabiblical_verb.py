#!/usr/bin/env python3
"""Generate immutable source-reviewed ExtraBiblical OLiA Verb coverage successor."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from tfont.coverage import (
    coverage_denominator_digest,
    coverage_report,
    load_coverage_manifest,
    validate_coverage_manifest,
)
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1
from tfont.digests import evidence_record_digest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/tfont/resources/coverage/p004-r011-baseline-v1/extrabiblical.json"
OUTPUT = ROOT / "src/tfont/resources/coverage/p004-i027b4-extrabiblical-verb-v1/extrabiblical.json"
MAPPING = ROOT / "src/tfont/resources/profiles/extrabiblical/0.3.0/mappings/verb.json"
EVIDENCE = ROOT / "src/tfont/resources/profiles/extrabiblical/0.3.0/evidence/native-verb-pos.json"
PINNED_SOURCE = ROOT / "docs/research/data/i027b3/extrabiblical-mql-pos-evidence.json"
ITEM = 'node_value:sp="verb"'
MAPPING_ID = "mapping:extrabiblical:olia-verb"
MANIFEST_ID = "coverage:p004-i027b4-extrabiblical-verb-v1:extrabiblical"
SOURCE_DIGEST = "sha256:58bdadddd54cc1848eddf0b5918137e37e85bbea52022cc2a40386ad46f1b46e"
SOURCE_REVISION = "9a56288e6777bad6328856acf055c780e65dd5d9"
EVIDENCE_DIGEST = "sha256:c4a1b0e8b81f3764dbc8350d3c10a214844df0cd5599e4ad78cfc01601cdc0d4"
ACCOUNTING = {
    "assessments": ["exact"],
    "common_target": True,
    "source_ids": [MAPPING_ID],
    "profiles": ["linguistic"],
    "capabilities": ["linguistic.part-of-speech"],
}


def build_successor() -> dict:
    source = load_coverage_manifest(SOURCE)
    if (
        source["manifest_id"] != "coverage:p004-r011-baseline-v1:extrabiblical"
        or source["corpus_id"] != "extrabiblical"
        or source["repository"] != "ETCBC/extrabiblical"
        or source["tf_version"] != "0.2"
        or source["scope_quality"] != "machine-exhaustive"
        or source["denominator_source_revision"] != SOURCE_REVISION
        or source["target_corpus_revision"] != SOURCE_REVISION
        or source["denominator_digest"] != SOURCE_DIGEST
        or coverage_denominator_digest(source) != SOURCE_DIGEST
    ):
        raise ValueError("ExtraBiblical corpus source/denominator drift")
    if source["accounting_gaps"] != [] or source["technical_exclusions"] != []:
        raise ValueError("ExtraBiblical accounting/exclusion baseline drift")

    pinned = json.loads(PINNED_SOURCE.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    reviewed = evidence.get("reviewed_content", {})
    if (
        pinned.get("git_blob_sha") != "4ba717b1716b747bb94d0359b950a55d8624b109"
        or pinned.get("decompressed_sha256")
        != "62540c8b4682121dd002f4c234c693259fb494c439ddfc06574537e5e398790e"
        or pinned.get("exact_mapping_authorized") is not False
        or pinned.get("source_revision") != SOURCE_REVISION
        or reviewed.get("source_blob_sha") != pinned["git_blob_sha"]
        or reviewed.get("source_decompressed_sha256") != pinned["decompressed_sha256"]
        or reviewed.get("enum_value") != "verb"
        or reviewed.get("enum_code") != 1
        or reviewed.get("feature") != "sp"
        or reviewed.get("target_node_type") != "word"
        or reviewed.get("target_corpus_revision") != SOURCE_REVISION
        or evidence_record_digest(evidence) != EVIDENCE_DIGEST
        or evidence.get("content_digest") != EVIDENCE_DIGEST
    ):
        raise ValueError("ExtraBiblical source semantic evidence drifted")

    data = json.loads(MAPPING.read_text(encoding="utf-8"))
    mappings = data["mappings"]
    if len(mappings) != 1 or mappings[0].get("mapping_id") != MAPPING_ID:
        raise ValueError("ExtraBiblical mapping identity drift")
    mapping = mappings[0]
    binding = {
        "component_id": "extrabiblical-tf",
        "execution_shape": "value-predicate",
        "feature": "sp",
        "node_type": "word",
        "value": "verb",
    }
    projections = mapping.get("projections", [])
    if (
        mapping.get("native_binding") != binding
        or mapping.get("native_dependencies") != ["dep:extrabiblical:word-sp:verb"]
        or mapping.get("review", {}).get("status") != "reviewed"
        or mapping.get("mapping_semantic_digest") != mapping_semantic_digest_v2(mapping)
        or mapping.get("review", {}).get("reviewed_mapping_digest")
        != mapping.get("mapping_semantic_digest")
        or len(projections) != 1
    ):
        raise ValueError("ExtraBiblical Verb mapping identity/digest drift")
    projection = projections[0]
    if (
        projection.get("target") != "http://purl.org/olia/olia.owl#Verb"
        or projection.get("assessment") != "exact"
        or projection.get("native_execution_binding") != binding
        or projection.get("review", {}).get("status") != "reviewed"
        or projection.get("projection_semantic_digest") != projection_semantic_digest_v1(projection)
        or projection.get("review", {}).get("reviewed_mapping_digest")
        != projection.get("projection_semantic_digest")
        or not any(
            x.get("evidence_id") == "evidence:extrabiblical:word-sp-verb-source"
            and x.get("content_digest") == EVIDENCE_DIGEST
            for x in projection.get("evidence", [])
        )
    ):
        raise ValueError("ExtraBiblical Verb projection evidence/review drift")

    successor = copy.deepcopy(source)
    successor["manifest_id"] = MANIFEST_ID
    selected = [row for row in successor["semantic_items"] if row["item_id"] == ITEM]
    if len(selected) != 1 or selected[0]["accounting"]["production"] is not None:
        raise ValueError("ExtraBiblical Verb accounting not a new single item")
    selected[0]["accounting"]["production"] = copy.deepcopy(ACCOUNTING)
    validate_coverage_manifest(successor)
    report = coverage_report(successor)
    if (
        report.semantic_items != 136
        or report.denominator_digest != SOURCE_DIGEST
        or report.production_reviewed_items != 8
        or report.production_common_target_items != 8
        or report.production_unreviewed_items != 128
        or report.production_outside_denominator_items != 0
        or report.corpus_wide_completion_claim_eligible
    ):
        raise ValueError(f"ExtraBiblical Verb coverage drifted: {report}")
    return successor


def serialized(value: dict) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = serialized(build_successor())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != output:
            raise SystemExit("I-027B4 packaged successor missing or stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
