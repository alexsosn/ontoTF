#!/usr/bin/env python3
"""Build immutable BHSA 0.3.0 OLiA Verb coverage successor.

Does not mutate the I-027A input manifest or create ontology authority.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from tfont.coverage import coverage_report, load_coverage_manifest, validate_coverage_manifest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/tfont/resources/coverage/p004-i027a-bhsa-stems-v1/bhsa.json"
OUTPUT = ROOT / "src/tfont/resources/coverage/p004-i027b1-bhsa-verb-v1/bhsa.json"
MAPPING = ROOT / "src/tfont/resources/profiles/bhsa/0.3.0/mappings/verb.json"
ITEM_ID = 'node_value:sp="verb"'
MAPPING_ID = "mapping:bhsa:olia-verb"
MANIFEST_ID = "coverage:p004-i027b1-bhsa-verb-v1:bhsa"
SOURCE_DIGEST = "sha256:0b260e21a1ebdb771f3d9975cb3e7b2560261dd99d9bd14d0eeabbb566852a03"
SOURCE_REVISION = "4db00e2157915495e1a4d3d57e41223df24775da"
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
        source["corpus_id"] != "bhsa"
        or source["repository"] != "ETCBC/bhsa"
        or source["tf_version"] != "2021"
        or source["denominator_source_revision"] != SOURCE_REVISION
        or source["target_corpus_revision"] != SOURCE_REVISION
        or source["denominator_digest"] != SOURCE_DIGEST
        or source["manifest_id"] != "coverage:p004-i027a-bhsa-stems-v1:bhsa"
    ):
        raise ValueError("source coverage identity drifted")

    mapping_source = json.loads(MAPPING.read_text(encoding="utf-8"))
    mappings = mapping_source["mappings"]
    if len(mappings) != 1 or mappings[0].get("mapping_id") != MAPPING_ID:
        raise ValueError("positive mapping identity drifted")
    mapping = mappings[0]
    if (
        mapping.get("native_binding")
        != {
            "component_id": "bhsa-tf",
            "execution_shape": "value-predicate",
            "feature": "sp",
            "node_type": "word",
            "value": "verb",
        }
        or len(mapping.get("projections", [])) != 1
        or mapping["projections"][0].get("target") != "http://purl.org/olia/olia.owl#Verb"
        or mapping["projections"][0].get("assessment") != "exact"
        or mapping["projections"][0].get("review", {}).get("status") != "reviewed"
        or mapping.get("review", {}).get("status") != "reviewed"
    ):
        raise ValueError("Verb mapping is not independently reviewed and exact")

    successor = copy.deepcopy(source)
    successor["manifest_id"] = MANIFEST_ID
    selected = [row for row in successor["semantic_items"] if row["item_id"] == ITEM_ID]
    if len(selected) != 1 or selected[0]["accounting"]["production"] is not None:
        raise ValueError("expected one unreviewed bounded Verb value")
    selected[0]["accounting"]["production"] = copy.deepcopy(ACCOUNTING)
    validate_coverage_manifest(successor)

    report = coverage_report(successor)
    if (
        report.semantic_items != 219
        or report.denominator_digest != SOURCE_DIGEST
        or report.production_reviewed_items != 35
        or report.production_common_target_items != 8
        or report.production_unreviewed_items != 184
        or report.production_outside_denominator_items != 0
        or report.corpus_wide_completion_claim_eligible
    ):
        raise ValueError(f"coverage drift: {report}")
    return successor


def serialized(doc: dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = serialized(build_successor())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != result:
            raise SystemExit("I-027B1 BHSA coverage successor missing or stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
