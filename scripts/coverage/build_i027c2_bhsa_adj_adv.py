#!/usr/bin/env python3
"""Rebuild the exact source-reviewed I-027C2 bhsa POS successor."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from tfont.coverage import (
    coverage_denominator_digest, coverage_report, load_coverage_manifest,
    validate_coverage_manifest,
)
from tfont.digests import evidence_record_digest
from tfont.semantic_digest_v2 import (
    mapping_semantic_digest_v2, projection_semantic_digest_v1,
)

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"src/tfont/resources/coverage/p004-i027b1-bhsa-verb-v1/bhsa.json"
OUTPUT=ROOT/"src/tfont/resources/coverage/p004-i027c2-bhsa-adj-adv-v1/bhsa.json"
MAPPING=ROOT/"src/tfont/resources/profiles/bhsa/0.4.0/mappings/adj-adv.json"
EVIDENCE=ROOT/"src/tfont/resources/profiles/bhsa/0.4.0/evidence/native-adj-adv-pos.json"
EXPECTED_CORPUS="bhsa"
SOURCE_MANIFEST="coverage:p004-i027b1-bhsa-verb-v1:bhsa"
MANIFEST_ID="coverage:p004-i027c2-bhsa-adj-adv-v1:bhsa"
DELTA={"adjv":("adjective","Adjective"),"advb":("adverb","Adverb")}
EXPECTED_COUNT=37
EXPECTED_COMMON=10
EXPECTED_NATIVE=27


def build_successor()->dict:
    original=load_coverage_manifest(SOURCE)
    if original["manifest_id"]!=SOURCE_MANIFEST or original["corpus_id"]!=EXPECTED_CORPUS:
        raise ValueError("I-027C2 predecessor identity drift")
    if original["denominator_source_revision"]!=original["target_corpus_revision"]:
        raise ValueError("I-027C2 source corpus revision drift")
    if coverage_denominator_digest(original)!=original["denominator_digest"]:
        raise ValueError("I-027C2 predecessor denominator digest drift")
    evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if (
        evidence["evidence_id"]!="evidence:bhsa:word-sp-adj-adv-source"
        or evidence["content_digest"]!=evidence_record_digest(evidence)
        or evidence["reviewed_content"]["production_node_type"]!="word"
        or evidence["reviewed_content"]["feature"]!="sp"
        or evidence["reviewed_content"]["target_tf_revision"]!=original["target_corpus_revision"]
        or set(evidence["reviewed_content"]["source_definitions"])!=set(DELTA)
    ):
        raise ValueError("I-027C2 original native source evidence drift")
    mappings=json.loads(MAPPING.read_text(encoding="utf-8"))["mappings"]
    if len(mappings)!=2:
        raise ValueError("I-027C2 expected precisely two POS mappings")
    for code,(name,target) in DELTA.items():
        candidates=[m for m in mappings if m.get("mapping_id")==f"mapping:bhsa:olia-{name}"]
        if len(candidates)!=1:
            raise ValueError("I-027C2 mapping identity mismatch")
        m=candidates[0]
        binding={"component_id":"bhsa-tf","execution_shape":"value-predicate",
                 "feature":"sp","node_type":"word","value":code}
        if (
            m.get("native_binding")!=binding
            or m.get("native_dependencies")!=[f"dep:bhsa:word-sp:{code}"]
            or m.get("mapping_semantic_digest")!=mapping_semantic_digest_v2(m)
            or m.get("review",{}).get("reviewed_mapping_digest")!=m.get("mapping_semantic_digest")
            or m.get("review",{}).get("status")!="reviewed"
            or len(m.get("projections",[]))!=1
        ):
            raise ValueError("I-027C2 mapping validation/review drift")
        projection=m["projections"][0]
        if (
            projection.get("native_execution_binding")!=binding
            or projection.get("target")!=f"http://purl.org/olia/olia.owl#{target}"
            or projection.get("assessment")!="exact"
            or projection.get("projection_semantic_digest")!=projection_semantic_digest_v1(projection)
            or projection.get("review",{}).get("reviewed_mapping_digest")!=projection.get("projection_semantic_digest")
            or projection.get("review",{}).get("status")!="reviewed"
            or not any(e.get("evidence_id")==evidence["evidence_id"] and e.get("content_digest")==evidence["content_digest"] for e in m["evidence"])
        ):
            raise ValueError("I-027C2 ontology or reviewed evidence drift")
    successor=copy.deepcopy(original)
    successor["manifest_id"]=MANIFEST_ID
    for code,(name,_) in DELTA.items():
        selected=[r for r in successor["semantic_items"] if r["item_id"]==f'node_value:sp="{code}"']
        if len(selected)!=1 or selected[0]["accounting"]["production"] is not None:
            raise ValueError("I-027C2 POS item absent or previously reviewed")
        selected[0]["accounting"]["production"]={
            "assessments":["exact"],"capabilities":["linguistic.part-of-speech"],
            "common_target":True,"profiles":["linguistic"],
            "source_ids":[f"mapping:bhsa:olia-{name}"],
        }
    validate_coverage_manifest(successor)
    state=coverage_report(successor)
    if (
        state.production_reviewed_items!=EXPECTED_COUNT
        or state.production_common_target_items!=EXPECTED_COMMON
        or dict(state.production_assessment_counts).get("native-only",0)!=EXPECTED_NATIVE
        or state.production_outside_denominator_items!=(
            0 if EXPECTED_CORPUS=="bhsa" else 1
        )
        or state.corpus_wide_completion_claim_eligible
    ):
        raise ValueError(f"I-027C2 production coverage drift: {state}")
    return successor


def serialized(data:dict)->str:
    return json.dumps(data,sort_keys=True,indent=2,ensure_ascii=False)+"\n"


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    result=serialized(build_successor())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8")!=result:
            raise SystemExit("I-027C2 immutable successor stale or absent")
    else:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        OUTPUT.write_text(result,encoding="utf-8")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
