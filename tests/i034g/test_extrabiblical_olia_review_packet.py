"""I-034G: deterministic single-cohort ExtraBiblical OLiA review packet.

The original MQL enum and TF frequencies were verified in I-034F; this
review packet has NO mapping publication authority before protected review.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tfont.batch_proposals import compile_candidate_batch
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.review_packets import build_review_packet, serialized, verify_review_packet

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/research/data/batch_review/inputs.json"
PREVIOUS = ROOT / "docs/research/data/batch_review/i034a-inputs.json"
EXPECTED = {"adjv", "advb", "art", "conj", "inrg", "intj", "nega", "prde", "prep", "prin", "prps"}
NO_TARGET = {"inrg", "nega", "prps"}


class ExtraBiblicalReviewedCohortRED(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.ledger = json.loads((ROOT / cls.manifest["ledger"]).read_text(encoding="utf-8"))
        cls.reader = CandidateEvidenceResources(
            cls.ledger, {
                resource: json.loads((ROOT / file).read_text(encoding="utf-8"))
                for resource, file in cls.manifest["evidence_resources"].items()
            },
        )
        cls.compiled = compile_candidate_batch(cls.ledger, resource_loader=cls.reader)
        cls.expected_packet = build_review_packet(cls.ledger, resource_loader=cls.reader)

    def test_old_bhsa_syriac_packet_remains_reproducible(self):
        previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
        self.assertEqual(previous["ledger"], "src/tfont/resources/batch_pilots/i034a-olia-bhsa-syriac-pos-proposals.json")
        self.assertTrue((ROOT / previous["packet"]).is_file())
        self.assertNotEqual(self.manifest["packet"], previous["packet"])

    def test_one_unapproved_eleven_row_extrabiblical_cohort(self):
        self.assertEqual(self.manifest["schema_version"], 2)
        self.assertEqual(
            self.manifest["ledger"],
            "src/tfont/resources/batch_pilots/i034f-extrabiblical-olia-pos.json",
        )
        self.assertEqual(
            self.manifest["evidence_resources"],
            {
                "resources/profiles/extrabiblical/batch-candidates/i034f-word-sp.json":
                "docs/research/data/batch_review/evidence/i034f-extrabiblical-pos.json"
            },
        )
        self.assertEqual(self.compiled["count"], 11)
        self.assertIs(self.compiled["release_authorized"], False)
        packet = self.expected_packet
        self.assertEqual(packet["authority"], "unreviewed-proposal")
        self.assertIs(packet["release_authorized"], False)
        self.assertEqual(packet["count"], 11)
        self.assertEqual(len(packet["rows"]), 11)
        self.assertEqual(
            {r["native_binding"]["value"] for r in packet["rows"]}, EXPECTED,
        )
        self.assertEqual(
            {r["native_binding"]["value"] for r in packet["rows"]
             if r["assessment"] == "native-only"},
            NO_TARGET,
        )
        self.assertEqual(
            sum(r["assessment"] == "exact" for r in packet["rows"]), 8,
        )
        self.assertEqual(len({r["decision_digest"] for r in packet["rows"]}), 11)
        self.assertTrue(all(
            (r["ontology_target"] is not None) == (r["assessment"] == "exact")
            and (r["projection_semantic_digest"] is not None) == (r["assessment"] == "exact")
            for r in packet["rows"]
        ))

    def test_frozen_candidate_packet_recomputed_byte_for_byte(self):
        packet_name = self.manifest["packet"]
        self.assertEqual(
            packet_name,
            "docs/research/data/generated/i033d/i034g-extrabiblical-olia-review-request.json",
        )
        path = ROOT / packet_name
        computed = serialized(self.expected_packet)
        if not path.is_file():
            # One-time RED evidence from CI, not a production mapping or review.
            print("I034G_GENERATED_PACKET_BEGIN", flush=True)
            print(computed, end="", flush=True)
            print("I034G_GENERATED_PACKET_END", flush=True)
        self.assertTrue(path.is_file(), "RED: derived review packet has not yet been frozen")
        self.assertEqual(path.read_text(encoding="utf-8"), computed)
        packet = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(verify_review_packet(packet, self.ledger, resource_loader=self.reader))


if __name__ == "__main__":
    unittest.main()
