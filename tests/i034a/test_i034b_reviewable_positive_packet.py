"""I-034B reviewable, source-pinned 15-row OLiA packet: twelve exact class targets."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tfont.batch_proposals import compile_candidate_batch
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.review_packets import build_review_packet, serialized, verify_review_packet

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"docs/research/data/batch_review/i034a-inputs.json"

class SourcePinnedOLiAPacket(unittest.TestCase):
    def test_fifteen_recomputed_decisions_and_twelve_exact_projections(self):
        meta=json.loads(MANIFEST.read_text(encoding="utf-8"))
        ledger=json.loads((ROOT/meta["ledger"]).read_text(encoding="utf-8"))
        reader=CandidateEvidenceResources(ledger,{
            k:json.loads((ROOT/path).read_text(encoding="utf-8"))
            for k,path in meta["evidence_resources"].items()
        })
        packet=json.loads((ROOT/meta["packet"]).read_text(encoding="utf-8"))
        self.assertTrue(verify_review_packet(packet,ledger,resource_loader=reader))
        self.assertEqual((ROOT/meta["packet"]).read_text(encoding="utf-8"),
                         serialized(build_review_packet(ledger,resource_loader=reader)))
        compiled=compile_candidate_batch(ledger,resource_loader=reader)
        self.assertEqual(compiled["count"],15)
        self.assertIs(compiled["release_authorized"],False)
        self.assertEqual(packet["authority"],"unreviewed-proposal")
        self.assertIs(packet["release_authorized"],False)
        self.assertEqual(sum(r["assessment"]=="exact" for r in packet["rows"]),12)
        self.assertEqual(sum(r["assessment"]=="native-only" for r in packet["rows"]),3)
        self.assertEqual(len({r["decision_digest"] for r in packet["rows"]}),15)
        self.assertTrue(all((r["ontology_target"] is not None)==(r["assessment"]=="exact")
                            for r in packet["rows"]))
        self.assertTrue(all((r["projection_semantic_digest"] is not None)==(r["assessment"]=="exact")
                            for r in packet["rows"]))

if __name__=="__main__":
    unittest.main()
