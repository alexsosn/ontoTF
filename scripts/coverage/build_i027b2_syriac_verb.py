#!/usr/bin/env python3
"""Reproduce the immutable Syriac 0.3.0 OLiA Verb coverage successor.

All source and ontology authorities are version-pinned, and the existing
Syriac ls="prop" outside-denominator gap is deliberately preserved.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from tfont.coverage import coverage_report, load_coverage_manifest, validate_coverage_manifest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/tfont/resources/coverage/p004-r011-baseline-v1/syriac.json"
OUTPUT = ROOT / "src/tfont/resources/coverage/p004-i027b2-syriac-verb-v1/syriac.json"
MAPPING = ROOT / "src/tfont/resources/profiles/syriac/0.3.0/mappings/verb.json"
ITEM_ID = 'node_value:sp="verb"'
MAPPING_ID = "mapping:syriac:olia-verb"
MANIFEST_ID = "coverage:p004-i027b2-syriac-verb-v1:syriac"
SOURCE_DIGEST = "sha256:33ea9d6ce7b44dbdf7ed12e11971e229321efb3b422dbfd9cf0bc9131d5972f8"
SOURCE_REVISION = "bb0eaa7e21b020a26b7566d2e495da9b1f84a919"
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
        source["manifest_id"] != "coverage:p004-r011-baseline-v1:syriac"
        or source["corpus_id"] != "syriac"
        or source["repository"] != "ETCBC/syriac"
        or source["tf_version"] != "0.9"
        or source["denominator_source_revision"] != SOURCE_REVISION
        or source["target_corpus_revision"] != SOURCE_REVISION
        or source["denominator_digest"] != SOURCE_DIGEST
    ):
        raise ValueError("Syriac source coverage corpus/denominator drift")
    expected_gap = {
        "assessments": ["exact"],
        "authority": "production",
        "capabilities": ["linguistic.part-of-speech"],
        "common_target": True,
        "item_id": 'node_value:ls="prop"',
        "kind": "node_value",
        "profiles": ["linguistic"],
        "reason": "outside-denominator",
        "source_ids": ["mapping:syriac:olia-proper-noun"],
    }
    if source["accounting_gaps"] != [expected_gap]:
        raise ValueError("Syriac ls=prop accounting gap drifted")

    data = json.loads(MAPPING.read_text(encoding="utf-8"))
    mappings = data["mappings"]
    if len(mappings) != 1 or mappings[0].get("mapping_id") != MAPPING_ID:
        raise ValueError("Syriac positive mapping identity drifted")
    mapping = mappings[0]
    if (
        mapping.get("native_binding")
        != {
            "component_id": "syriac-tf",
            "execution_shape": "value-predicate",
            "feature": "sp",
            "node_type": "word",
            "value": "verb",
        }
        or len(mapping.get("projections", [])) != 1
        or mapping["projections"][0].get("target") != "http://purl.org/olia/olia.owl#Verb"
        or mapping["projections"][0].get("assessment") != "exact"
        or mapping.get("review", {}).get("status") != "reviewed"
        or mapping["projections"][0].get("review", {}).get("status") != "reviewed"
    ):
        raise ValueError("Syriac Verb mapping not reviewed/exact")

    successor = copy.deepcopy(source)
    successor["manifest_id"] = MANIFEST_ID
    selected = [x for x in successor["semantic_items"] if x["item_id"] == ITEM_ID]
    if len(selected) != 1 or selected[0]["accounting"]["production"] is not None:
        raise ValueError("Syriac Verb denominator item absent or already reviewed")
    selected[0]["accounting"]["production"] = copy.deepcopy(ACCOUNTING)
    validate_coverage_manifest(successor)
    report = coverage_report(successor)
    if (
        report.semantic_items != 74
        or report.denominator_digest != SOURCE_DIGEST
        or report.production_reviewed_items != 7
        or report.production_common_target_items != 7
        or report.production_unreviewed_items != 67
        or report.production_outside_denominator_items != 1
        or report.corpus_wide_completion_claim_eligible
    ):
        raise ValueError(f"Syriac coverage state drifted: {report}")
    return successor


def serialized(data: dict) -> str:
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = serialized(build_successor())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != result:
            raise SystemExit("I-027B2 Syriac Verb coverage successor missing or stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
