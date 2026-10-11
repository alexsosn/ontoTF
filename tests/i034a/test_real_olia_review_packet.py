"""I-034A: genuine 15-row proposal packet, NOT an approval or installed release."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.mappings.build_candidate_review_packet import build_packet
from tfont.batch_proposals import compile_candidate_batch
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.review_packets import verify_review_packet, BatchReviewPacketError


ROOT = Path(__file__).resolve().parents[2]
META = ROOT / "docs/research/data/batch_review/inputs.json"


class FirstRealOLiAReviewPacketTDD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads(META.read_text(encoding="utf-8"))
        cls.ledger = json.loads((ROOT / cls.meta["ledger"]).read_text(encoding="utf-8"))
        evidence = {
            name: json.loads((ROOT / path).read_text(encoding="utf-8"))
            for name, path in cls.meta["evidence_resources"].items()
        }
        cls.reader = CandidateEvidenceResources(cls.ledger, evidence)
        cls.packet = json.loads((ROOT / cls.meta["packet"]).read_text(encoding="utf-8"))

    def test_real_fifteen_rows_twelve_positive_three_unresolved(self):
        self.assertEqual(self.meta["schema_version"], 2)
        self.assertEqual(self.ledger["batch_id"], "i034a-bhsa-syriac-olia-full-pos")
        self.assertEqual(len(self.meta["evidence_resources"]), 2)
        self.assertEqual(len(self.packet["rows"]), 15)
        self.assertEqual(self.packet["count"], 15)
        self.assertEqual(self.packet["authority"], "unreviewed-proposal")
        self.assertIs(self.packet["release_authorized"], False)
        self.assertEqual(self.packet["schema_version"], 2)
        positives = [r for r in self.packet["rows"] if r["assessment"] == "exact"]
        native = [r for r in self.packet["rows"] if r["assessment"] == "native-only"]
        self.assertEqual(len(positives), 12)
        self.assertEqual(len(native), 3)
        self.assertEqual(
            {(r["corpus_id"], r["native_binding"]["value"]) for r in native},
            {("bhsa", "prps"), ("syriac", "inrg"), ("syriac", "nega")},
        )
        targets = {r["ontology_target"] for r in positives}
        self.assertEqual(targets, {
            "http://purl.org/olia/olia.owl#" + name
            for name in ("Article", "Preposition", "Conjunction",
                         "DemonstrativePronoun", "InterrogativePronoun",
                         "Interjection", "NegativeParticle",
                         "InterrogativeParticle", "Pronoun")
        })
        self.assertTrue(all(r["ontology_target"] is None
                            and r["projection_semantic_digest"] is None
                            for r in native))
        self.assertEqual(len({r["mapping_id"] for r in self.packet["rows"]}), 15)
        self.assertEqual(len({r["decision_digest"] for r in self.packet["rows"]}), 15)

    def test_packet_exactly_recompiles_and_can_never_self_approve(self):
        self.assertTrue(verify_review_packet(
            self.packet, self.ledger, resource_loader=self.reader
        ))
        encoded = build_packet(ROOT, mode="check")
        self.assertEqual(encoded, (ROOT / self.meta["packet"]).read_text(encoding="utf-8"))
        compiled = compile_candidate_batch(self.ledger, resource_loader=self.reader)
        self.assertIs(compiled["release_authorized"], False)
        self.assertEqual(sum(bool(c["projections"]) for c in compiled["candidates"]), 12)
        self.assertEqual(len(compiled["candidates"]), 15)
        for row in self.packet["rows"]:
            corpus = row["corpus_id"]
            spec = self.ledger["source_registry"][corpus]
            self.assertEqual(row["source_pin"], spec)
            self.assertEqual(row["native_binding"]["feature"], "sp")
            self.assertEqual(row["coverage_item_ids"],
                             [f'node_value:sp="{row["native_binding"]["value"]}"'])
            self.assertTrue(row["decision_digest"].startswith("sha256:"))
            self.assertNotIn("review", row)

    def test_packet_digest_cannot_approve_wrong_target_or_source(self):
        for mutate in (
            lambda x: x["rows"][0].update(assessment="exact"),
            lambda x: x["rows"][-1].update(ontology_target="http://example.org/Forged"),
            lambda x: x["rows"][-1]["source_pin"].update(source_revision="0"*40),
            lambda x: x.update(release_authorized=True),
            lambda x: x["rows"].pop(),
        ):
            wrong = copy.deepcopy(self.packet)
            mutate(wrong)
            with self.assertRaises(BatchReviewPacketError):
                verify_review_packet(wrong, self.ledger, resource_loader=self.reader)


if __name__ == "__main__":
    unittest.main()
