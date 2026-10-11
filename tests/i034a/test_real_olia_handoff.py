"""I-034A: protected OWL class evidence must survive signed handoff verification.

The observation is a test fixture, never independently authenticated GitHub approval.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import canonical_json_bytes
from tfont.overlay_handoff import build_overlay_handoff, verify_overlay_handoff_integrity
from tfont.review_packets import build_review_packet
from tests.i033e.test_overlay_handoff import cohort


ROOT = Path(__file__).resolve().parents[2]
LOCK_ROOT = "resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/"


def pin_digest(pack):
    pack["content_digest"] = "sha256:" + hashlib.sha256(canonical_json_bytes({
        k: v for k, v in pack.items() if k != "content_digest"
    })).hexdigest()


def real_pack():
    ledger = json.loads((ROOT / "src/tfont/resources/batch_pilots/"
                              "i034a-olia-bhsa-syriac-pos-proposals.json").read_text())
    src = json.loads((ROOT/"docs/research/data/batch_review/evidence/"
                           "i033e3-bhsa-word-sp.json").read_text())
    syr = json.loads((ROOT/"docs/research/data/batch_review/evidence/"
                           "i034a-syriac-word-sp.json").read_text())
    resource_loader = CandidateEvidenceResources(ledger, {
        ledger["source_registry"]["bhsa"]["evidence_resource"]: src,
        ledger["source_registry"]["syriac"]["evidence_resource"]: syr,
    })
    packet = build_review_packet(ledger, resource_loader=resource_loader)
    _, _, _, observation = cohort()
    observation = copy.deepcopy(observation)
    observation.update({
        "packet_id": packet["packet_id"],
        "batch_digest": packet["batch_digest"],
        "rows": [{
            "mapping_id": row["mapping_id"],
            "decision_digest": row["decision_digest"],
            "disposition": "accept" if row["assessment"] == "exact"
                           else "needs-evidence",
        } for row in packet["rows"]],
        "counts": {"accept": 12, "reject": 0, "needs-evidence": 3},
        "provenance": "UNAUTHENTICATED-FIXTURE-ONLY-NOT-GITHUB",
    })
    return build_overlay_handoff(packet, ledger, observation, resource_loader=resource_loader)


class ProtectedOLiAClassEvidenceTDD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = real_pack()

    def test_actual_twelve_positive_mappings_have_original_protected_olia_evidence(self):
        self.assertEqual(self.pack["counts"], {"exact": 12, "native-only": 0})
        added_ontology = [
            entry for corpus in self.pack["corpora"]
            for entry in corpus["added_evidence"]
            if entry["resource"].startswith(LOCK_ROOT)
        ]
        self.assertGreaterEqual(len(added_ontology), 9)
        for entry in added_ontology:
            self.assertEqual(entry["record"]["kind"], "ontology-definition")
            self.assertEqual(entry["record"]["source_revision"],
                             "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6")
        self.assertIsNone(verify_overlay_handoff_integrity(self.pack))
        self.assertFalse(self.pack["release_authorized"])

    def test_ontology_path_outside_protected_lock_is_rejected_even_if_rehashed(self):
        for forged in (
            "resources/ontologies/olia/0000000000000000000000000000000000000000/fake.json",
            "resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/../fake.json",
            "resources/ontologies/other/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/fake.json",
            "resources/profiles/bhsa/candidate\\ontology.json",
        ):
            clone = copy.deepcopy(self.pack)
            found = next(c for c in clone["corpora"] if
                         any(e["resource"].startswith(LOCK_ROOT)
                             for e in c["added_evidence"]))
            entry = next(e for e in found["added_evidence"]
                         if e["resource"].startswith(LOCK_ROOT))
            entry["resource"] = forged
            pin_digest(clone)
            with self.subTest(path=forged), self.assertRaises(ValueError):
                verify_overlay_handoff_integrity(clone)


    def test_ontology_evidence_cannot_masquerade_as_corpus_source(self):
        clone = copy.deepcopy(self.pack)
        corpus = next(c for c in clone["corpora"] if c["corpus_id"] == "bhsa")
        entry = next(e for e in corpus["added_evidence"]
                     if e["resource"].startswith(LOCK_ROOT))
        entry["resource"] = "resources/profiles/bhsa/fake-class-evidence.json"
        pin_digest(clone)
        with self.assertRaises(ValueError):
            verify_overlay_handoff_integrity(clone)

    def test_ontology_record_replacement_under_protected_path_fails_closed(self):
        clone = copy.deepcopy(self.pack)
        corpus = next(c for c in clone["corpora"]
                      if any(e["resource"].startswith(LOCK_ROOT)
                             for e in c["added_evidence"]))
        entry = next(e for e in corpus["added_evidence"]
                     if e["resource"].startswith(LOCK_ROOT))
        entry["record"]["reviewed_content"]["target"] = (
            "http://purl.org/olia/olia.owl#ForgedClass"
        )
        from tfont.digests import evidence_record_digest
        entry["record"]["content_digest"] = evidence_record_digest(entry["record"])
        pin_digest(clone)
        with self.assertRaises(ValueError):
            verify_overlay_handoff_integrity(clone)


if __name__ == "__main__":
    unittest.main()
