"""Contract tests: 30 real reviewed decisions, generated in one batch."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tfont.batch_compiler import (
    BatchCompilerError, ROOT, compile_pilot, load_pilot, parity_report, serialized
)
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1

REPORT=ROOT/"docs/research/data/generated/i033a/pos-pilot-summary.json"


class BatchPilotContractTests(unittest.TestCase):
    def test_real_30_decision_batch_does_not_create_new_semantic_authority(self):
        pilot=load_pilot()
        produced=compile_pilot(pilot)
        self.assertEqual(len(produced["mappings"]),3)
        self.assertEqual(len(produced["native_only"]),27)
        self.assertEqual({x["corpus_id"] for x in produced["mappings"]},
                         {"bhsa","syriac","extrabiblical"})
        for mapping in produced["mappings"]:
            self.assertEqual(mapping_semantic_digest_v2(mapping),
                             mapping["mapping_semantic_digest"])
            self.assertEqual(mapping["review"]["reviewed_mapping_digest"],
                             mapping["mapping_semantic_digest"])
            self.assertEqual(len(mapping["projections"]),1)
            projection=mapping["projections"][0]
            self.assertEqual(projection_semantic_digest_v1(projection),
                             projection["projection_semantic_digest"])
            self.assertEqual(projection["review"]["reviewed_mapping_digest"],
                             projection["projection_semantic_digest"])
            self.assertEqual(mapping["native_binding"]["node_type"],"word")
            self.assertEqual(mapping["native_binding"]["feature"],"sp")
            self.assertEqual(mapping["native_binding"]["value"],"verb")
            self.assertEqual(projection["target"],
                             "http://purl.org/olia/olia.owl#Verb")
        self.assertTrue(all(x["assessment"]=="native-only" and
                            x["common_target"] is False and
                            "target" not in x for x in produced["native_only"]))
        self.assertTrue(all(x["item_id"].startswith(("node_feature:vs","node_value:vs="))
                            for x in produced["native_only"]))
        report=parity_report(pilot)
        self.assertEqual(report["counts"],{
            "positive_exact":3,"reviewed_native_only":27,"total_decisions":30
        })
        self.assertFalse(report["authorizes_new_mappings"])

    def test_compiled_positive_semantics_are_byte_equivalent_to_reviewed_release(self):
        pilot=load_pilot()
        produced=compile_pilot(pilot)
        for mapping in produced["mappings"]:
            original_rel=f"src/tfont/resources/profiles/{mapping['corpus_id']}/0.3.0/mappings/verb.json"
            import json
            published=json.loads((ROOT/original_rel).read_text(encoding="utf-8"))
            self.assertEqual(published["mappings"],[mapping])

    def test_report_is_small_reproducible_not_a_second_coverage_manifest(self):
        self.assertEqual(REPORT.read_text(encoding="utf-8"),
                         serialized(parity_report(load_pilot())))
        self.assertLess(REPORT.stat().st_size,8000)
        self.assertNotIn("semantic_items",REPORT.read_text(encoding="utf-8"))


class BatchPilotAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.ledger=load_pilot()

    def test_forged_native_selector_is_rejected(self):
        for key,bad in (("node_type","lex"),("feature","vs"),("value","subs")):
            mutated=copy.deepcopy(self.ledger)
            mutated["positive_pos"][0]["native"][key]=bad
            with self.subTest(key=key), self.assertRaises(BatchCompilerError):
                compile_pilot(mutated)

    def test_forged_ontology_term_or_evidence_is_rejected(self):
        for field,value in (
            ("target","http://purl.org/olia/olia.owl#Noun"),
            ("ontology_evidence_digest","sha256:"+"0"*64),
            ("corpus_evidence_digest","sha256:"+"f"*64)
        ):
            mutated=copy.deepcopy(self.ledger)
            mutated["positive_pos"][1][field]=value
            with self.subTest(field=field),self.assertRaises(BatchCompilerError):
                compile_pilot(mutated)

    def test_wrong_reviewed_source_revision_is_rejected(self):
        mutated=copy.deepcopy(self.ledger)
        mutated["positive_pos"][0]["source_revision"]="not-the-source-revision"
        with self.assertRaises(BatchCompilerError):
            compile_pilot(mutated)

    def test_review_status_is_not_a_client_authorized_field(self):
        mutated=copy.deepcopy(self.ledger)
        mutated["positive_pos"][0]["review"]={"status":"reviewed"}
        with self.assertRaises(BatchCompilerError):
            compile_pilot(mutated)

    def test_replacing_or_omitting_native_only_member_is_rejected(self):
        for how in ("remove","replace","append"):
            mutated=copy.deepcopy(self.ledger)
            ids=mutated["native_only"]["item_ids"]
            if how=="remove": ids.pop()
            elif how=="replace": ids[2]='node_value:vs="invented"'
            else: ids.append(ids[0])
            with self.subTest(how=how),self.assertRaises(BatchCompilerError):
                compile_pilot(mutated)

    def test_native_only_cannot_inherit_shared_target(self):
        mutated=copy.deepcopy(self.ledger)
        mutated["native_only"]["target"]="http://purl.org/olia/olia.owl#Verb"
        with self.assertRaises(BatchCompilerError):
            compile_pilot(mutated)

    def test_duplicate_positive_or_unknown_schema_version_rejected(self):
        mutated=copy.deepcopy(self.ledger)
        mutated["positive_pos"].append(copy.deepcopy(mutated["positive_pos"][0]))
        with self.assertRaises(BatchCompilerError):
            compile_pilot(mutated)
        mutated=copy.deepcopy(self.ledger)
        mutated["schema_version"]=2
        with self.assertRaises(BatchCompilerError):
            compile_pilot(mutated)


if __name__=="__main__":
    unittest.main()
