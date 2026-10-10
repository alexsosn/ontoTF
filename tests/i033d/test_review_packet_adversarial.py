"""I-033D skeptical mutation tests for source, digest and review authority."""
from __future__ import annotations

import copy
import unittest

from tfont.batch_proposals import BatchProposalError, load_ledger
from tfont.review_packets import (
    BatchReviewPacketError, build_review_packet, verify_review_packet
)


class BatchReviewPacketAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.ledger = load_ledger()
        self.packet = build_review_packet(self.ledger)

    def test_candidate_order_does_not_change_packet_hash(self):
        changed = copy.deepcopy(self.ledger)
        changed["decisions"].reverse()
        self.assertEqual(build_review_packet(changed), self.packet)

    def test_batch_id_and_source_pins_are_bound(self):
        changed = copy.deepcopy(self.ledger)
        changed["batch_id"] = "different-proposed-batch"
        other = build_review_packet(changed)
        self.assertNotEqual(self.packet["batch_digest"], other["batch_digest"])
        self.assertNotEqual(self.packet["rows"][0]["decision_digest"],
                            other["rows"][0]["decision_digest"])
        invalid = copy.deepcopy(self.ledger)
        invalid["source_registry"]["bhsa"]["source_revision"] = "0" * 40
        with self.assertRaises((BatchReviewPacketError, BatchProposalError)):
            build_review_packet(invalid)

    def test_packet_cannot_forge_successful_review(self):
        for field, value in (
            ("review", {"status": "reviewed"}),
            ("approved_by", "author"),
            ("release_authorized", True),
        ):
            packet = copy.deepcopy(self.packet)
            packet[field] = value
            with self.subTest(field=field), self.assertRaises(BatchReviewPacketError):
                verify_review_packet(packet, self.ledger)

    def test_forged_row_rationale_and_hash_cannot_be_accepted(self):
        for change in ("rationale", "decision_digest", "mapping_semantic_digest", "ontology_target", "evidence"):
            packet = copy.deepcopy(self.packet)
            row = packet["rows"][0]
            if change == "rationale":
                row["rationale"] += " an unreviewed change"
            elif change == "evidence":
                row["evidence"][0]["content_digest"] = "sha256:" + "a" * 64
            else:
                row[change] = "sha256:" + "b" * 64 if "digest" in change else "not-a-class"
            with self.subTest(change=change), self.assertRaises(BatchReviewPacketError):
                verify_review_packet(packet, self.ledger)

    def test_recomputed_batch_checksum_does_not_approve_forged_content(self):
        from tfont.digests import canonical_json_bytes
        import hashlib
        packet = copy.deepcopy(self.packet)
        packet["rows"][0]["rationale"] = "unreviewed substituted claim"
        packet["batch_digest"] = "sha256:" + hashlib.sha256(
            canonical_json_bytes({k:v for k,v in packet.items() if k!="batch_digest"})
        ).hexdigest()
        with self.assertRaises(BatchReviewPacketError):
            verify_review_packet(packet, self.ledger)

    def test_python_bool_numeric_equality_cannot_bypass_review_gate(self):
        # A plain dict equality check incorrectly accepts all these values:
        # False == 0, True == 1, and 4 == 4.0.
        for key, forged in (
            ("release_authorized", 0),
            ("schema_version", True),
            ("count", 4.0),
        ):
            altered = copy.deepcopy(self.packet)
            altered[key] = forged
            with self.subTest(key=key), self.assertRaises(BatchReviewPacketError):
                verify_review_packet(altered, self.ledger)

    def test_source_binding_and_coverage_intent_cannot_be_replaced(self):
        for key in ("source_pin", "coverage_item_ids"):
            altered = copy.deepcopy(self.packet)
            row = altered["rows"][0]
            if key == "source_pin":
                row[key]["target_corpus_revision"] = "0" * 40
            else:
                row[key] = ['node_value:sp="verb"']
            with self.subTest(key=key), self.assertRaises(BatchReviewPacketError):
                verify_review_packet(altered, self.ledger)

    def test_self_declared_approval_in_source_ledger_fails(self):
        changed = copy.deepcopy(self.ledger)
        changed["decisions"][0]["review"] = {"status":"reviewed"}
        with self.assertRaises((BatchProposalError, BatchReviewPacketError)):
            build_review_packet(changed)

    def test_duplicate_decisions_fail_closed(self):
        changed = copy.deepcopy(self.ledger)
        changed["decisions"].append(copy.deepcopy(changed["decisions"][0]))
        with self.assertRaises((BatchProposalError, BatchReviewPacketError)):
            build_review_packet(changed)


if __name__ == "__main__":
    unittest.main()
