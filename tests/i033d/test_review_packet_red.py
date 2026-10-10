"""I-033D batch review requests are not approval receipts."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from tfont.batch_proposals import compile_candidate_batch, load_ledger
from tfont.digests import canonical_json_bytes
from tfont.review_packets import build_review_packet, verify_review_packet, serialized

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/research/data/generated/i033d/adj-adv-review-request.json"


class BatchReviewPacketTests(unittest.TestCase):
    def test_four_candidate_packet_is_review_request_only(self):
        ledger = load_ledger()
        packet = build_review_packet(ledger)
        candidates = compile_candidate_batch(ledger)["candidates"]
        self.assertEqual(packet["schema_version"], 1)
        self.assertEqual(packet["batch_id"], ledger["batch_id"])
        self.assertEqual(packet["authority"], "unreviewed-proposal")
        self.assertFalse(packet["release_authorized"])
        self.assertEqual(packet["count"], 4)
        self.assertEqual(
            [x["mapping_id"] for x in packet["rows"]],
            sorted(x["mapping_id"] for x in candidates),
        )
        self.assertEqual(
            {x["coverage_item_ids"][0] for x in packet["rows"]},
            {'node_value:sp="adjv"', 'node_value:sp="advb"'},
        )
        self.assertTrue(all(x["rationale"] for x in packet["rows"]))
        self.assertTrue(all(x["assessment"] == "exact" for x in packet["rows"]))
        self.assertTrue(all(len(x["evidence"]) == 2 for x in packet["rows"]))
        self.assertTrue(all("review" not in x for x in packet["rows"]))
        self.assertTrue(verify_review_packet(packet, ledger))

    def test_freeze_byte_identical_review_packet(self):
        self.assertTrue(OUTPUT.is_file(), "RED: frozen review packet absent")
        self.assertEqual(
            OUTPUT.read_text(encoding="utf-8"),
            serialized(build_review_packet(load_ledger())),
        )

    def test_full_candidate_and_rationale_are_digest_bound(self):
        ledger = load_ledger()
        original = build_review_packet(ledger)
        changed = copy.deepcopy(ledger)
        changed["decisions"][0]["rationale"] += " New scholarly caveat."
        revised = build_review_packet(changed)
        initial_mappings = {
            m["mapping_id"]: m for m in compile_candidate_batch(ledger)["candidates"]
        }
        revised_mappings = {
            m["mapping_id"]: m for m in compile_candidate_batch(changed)["candidates"]
        }
        ident = "mapping:bhsa:olia-adjective"
        # Runtime semantic digest legitimately excludes audit-only rationale.
        self.assertEqual(
            initial_mappings[ident]["mapping_semantic_digest"],
            revised_mappings[ident]["mapping_semantic_digest"],
        )
        old_row = next(x for x in original["rows"] if x["mapping_id"] == ident)
        new_row = next(x for x in revised["rows"] if x["mapping_id"] == ident)
        self.assertNotEqual(old_row["decision_digest"], new_row["decision_digest"])
        self.assertNotEqual(original["batch_digest"], revised["batch_digest"])

    def test_independently_recomputed_jcs_batch_digest(self):
        packet = build_review_packet(load_ledger())
        body = {k: v for k, v in packet.items() if k != "batch_digest"}
        digest = "sha256:" + hashlib.sha256(canonical_json_bytes(body)).hexdigest()
        self.assertEqual(packet["batch_digest"], digest)


if __name__ == "__main__":
    unittest.main()
