"""I-034F RED: eleven previously unmapped ExtraBiblical word.sp source categories.

Real pinned TF inventory and original MQL enum, not copied BHSA token counts.
Candidates have NO GitHub review authority and are NOT installed mappings.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tfont.batch_proposals import compile_candidate_batch, packaged_resource
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import evidence_record_digest
from tfont.release_registry import load_profile


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "src/tfont/resources/batch_pilots/i034f-extrabiblical-olia-pos.json"
SOURCE = ROOT / "docs/research/data/batch_review/evidence/i034f-extrabiblical-pos.json"
FROZEN = ROOT / "docs/research/data/i034f/extrabiblical-mql-pos-enum.json"
INVENTORY = ROOT / "docs/research/data/generated/r005/extrabiblical.json"
REV = "9a56288e6777bad6328856acf055c780e65dd5d9"
BLOB = "4ba717b1716b747bb94d0359b950a55d8624b109"
MQL_SHA256 = "62540c8b4682121dd002f4c234c693259fb494c439ddfc06574537e5e398790e"
LOCK = "resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/lock-linguistic-i034a-pos.json"

EXPECTED = {
    "adjv": "Adjective",
    "advb": "Adverb",
    "art": "Article",
    "conj": "Conjunction",
    "inrg": None,
    "intj": "Interjection",
    "nega": None,
    "prde": "DemonstrativePronoun",
    "prep": "Preposition",
    "prin": "InterrogativePronoun",
    "prps": None,
}
EXISTING = {"nmpr", "subs", "verb"}


class ExtraBiblicalRealPOSBatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        name = cls.ledger["source_registry"]["extrabiblical"]["evidence_resource"]
        cls.loader = CandidateEvidenceResources(cls.ledger, {name: cls.source})
        cls.compiled = compile_candidate_batch(cls.ledger, resource_loader=cls.loader)

    def test_original_enum_complete_and_measured_against_real_tf(self):
        self.assertEqual(self.inventory["revision"], REV)
        feature = self.inventory["node_features"]["sp"]
        self.assertEqual(feature["applies_to"], ["word"])
        self.assertEqual(feature["observation_count"], 39862)
        self.assertEqual(len(feature["observed_values"]), 14)
        enum = self.frozen["part_of_speech_enum"]
        self.assertEqual(len(enum["values"]), 14)
        self.assertEqual(self.frozen["source_revision"], REV)
        self.assertEqual(self.frozen["git_blob_sha"], BLOB)
        self.assertEqual(self.frozen["decompressed_sha256"], MQL_SHA256)
        self.assertEqual(enum["enum_declaration_line"], 163)
        self.assertEqual(enum["feature_type_line"], 501)
        by_value = {row["value"]: row for row in enum["values"]}
        self.assertEqual(len(by_value), 14)
        self.assertEqual(set(by_value), set(feature["observed_values"]))
        self.assertEqual(by_value["art"]["line"], 164)
        self.assertEqual(by_value["art"]["code"], 0)
        self.assertEqual(by_value["verb"]["line"], 165)
        self.assertEqual(by_value["verb"]["code"], 1)
        self.assertEqual(by_value["subs"]["code"], 2)
        self.assertEqual(by_value["nmpr"]["code"], 3)
        self.assertTrue(all(type(item["code"]) is int and item["code"] >= 0
                            and type(item["line"]) is int and item["line"] > 163
                            for item in by_value.values()))

    def test_original_extrabiblical_source_is_digest_bound(self):
        self.assertEqual(self.source["source_revision"], REV)
        self.assertEqual(self.source["reviewed_content"]["target_tf_revision"], REV)
        self.assertEqual(self.source["content_digest"], evidence_record_digest(self.source))
        self.assertEqual(self.source["reviewed_content"]["original_mql_blob"], BLOB)
        self.assertEqual(self.source["reviewed_content"]["decompressed_sha256"], MQL_SHA256)
        self.assertEqual(self.source["reviewed_content"]["feature"], "sp")
        self.assertEqual(self.source["reviewed_content"]["production_node_type"], "word")
        defs = self.source["reviewed_content"]["source_definitions"]
        actual = {row["value"]: row for row in self.frozen["part_of_speech_enum"]["values"]}
        self.assertEqual(set(defs), set(actual))
        for value, row in defs.items():
            with self.subTest(value=value):
                self.assertEqual(row["line"], actual[value]["line"])
                self.assertEqual(row["enum_code"], actual[value]["code"])
                self.assertTrue(row["gloss"].strip())
                self.assertNotIn("featureObservations", row)
        self.assertTrue(all(
            feature["observed_frequencies"][v] > 0 for v in EXPECTED
        ))

    def test_fifteen_corpus_classes_include_only_eleven_new_candidates(self):
        self.assertEqual(self.ledger["schema_version"], 2)
        self.assertEqual(self.ledger["mode"], "proposal-only")
        self.assertEqual(self.compiled["count"], 11)
        self.assertIs(self.compiled["release_authorized"], False)
        self.assertEqual(
            {x["value"] for x in self.ledger["decisions"]}, set(EXPECTED)
        )
        old = load_profile("extrabiblical", release_id="0.3.0")
        active = {m["native_binding"]["value"] for m in old.mappings.data["mappings"]
                  if m["native_binding"]["feature"] == "sp"}
        self.assertTrue(EXISTING.issubset(active))
        self.assertTrue(set(EXPECTED).isdisjoint(active))
        lock = packaged_resource(LOCK)
        self.assertEqual(self.ledger["ontology_lock_resource"], LOCK)
        self.assertEqual(len(self.compiled["candidates"]), 11)
        for mapping in self.compiled["candidates"]:
            value = mapping["native_binding"]["value"]
            target = EXPECTED[value]
            self.assertEqual(mapping["corpus_id"], "extrabiblical")
            self.assertEqual(mapping["native_binding"]["node_type"], "word")
            self.assertEqual(mapping["native_binding"]["feature"], "sp")
            self.assertEqual(mapping["profiles"], ["linguistic"])
            if target is None:
                self.assertEqual(mapping["native_state"], "native-only")
                self.assertEqual(mapping["projections"], [])
                self.assertEqual(len(mapping["evidence"]), 1)
            else:
                self.assertEqual(mapping["native_state"], "positive")
                self.assertEqual(len(mapping["projections"]), 1)
                self.assertEqual(mapping["projections"][0]["assessment"], "exact")
                self.assertEqual(
                    mapping["projections"][0]["target"],
                    "http://purl.org/olia/olia.owl#" + target
                )
                self.assertIn(mapping["projections"][0]["target"], lock["terms_used"])
                self.assertEqual(len(mapping["evidence"]), 2)
        self.assertEqual(sum(m["native_state"] == "positive"
                             for m in self.compiled["candidates"]), 8)
        self.assertEqual(sum(m["native_state"] == "native-only"
                             for m in self.compiled["candidates"]), 3)

    def test_no_unreviewed_exact_particle_or_irreflexive_pronoun_claim(self):
        for decision in self.ledger["decisions"]:
            self.assertGreater(len(decision["rationale"]), 100)
            if decision["value"] in ("inrg", "nega", "prps"):
                self.assertEqual(decision["assessment"], "native-only")
                self.assertNotIn("term_key", decision)
        self.assertNotIn("personalpronoun",
                         self.ledger["ontology_evidence_resources"])


if __name__ == "__main__":
    unittest.main()
