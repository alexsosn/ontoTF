"""I-034C TDD RED: protected class evidence may accompany real exact POS mappings.

Fixtures model a candidate HANDOFF, not a GitHub-attested installed release.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from tests.i033e.test_overlay_handoff import cohort
from tfont.batch_proposals import packaged_resource
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import canonical_json_bytes, evidence_record_digest
from tfont.overlay_handoff import (
    build_overlay_handoff, verify_overlay_handoff_integrity,
)
from tfont.review_packets import build_review_packet


ROOT = Path(__file__).resolve().parents[2]
LEDGER = "resources/batch_pilots/i034a-olia-bhsa-syriac-pos-proposals.json"


def _rehash(pack):
    pack["content_digest"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes({k: v for k, v in pack.items()
                              if k != "content_digest"})
    ).hexdigest()
    return pack


class PositiveProtectedOntologyEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = packaged_resource(LEDGER)
        names = cls.ledger["source_registry"]
        evidence = {
            names["bhsa"]["evidence_resource"]: json.loads(
                (ROOT / "docs/research/data/batch_review/evidence/"
                        "i033e3-bhsa-word-sp.json").read_text()),
            names["syriac"]["evidence_resource"]: json.loads(
                (ROOT / "docs/research/data/batch_review/evidence/"
                        "i034a-syriac-word-sp.json").read_text()),
        }
        cls.reader = CandidateEvidenceResources(cls.ledger, evidence)
        cls.packet = build_review_packet(cls.ledger, resource_loader=cls.reader)
        _old_ledger, _old_reader, _old_packet, mock = cohort()
        mock = copy.deepcopy(mock)
        mock["packet_id"] = cls.packet["packet_id"]
        mock["batch_digest"] = cls.packet["batch_digest"]
        mock["rows"] = [
            {"mapping_id": row["mapping_id"],
             "decision_digest": row["decision_digest"],
             "disposition": "accept"} for row in cls.packet["rows"]
        ]
        mock["counts"] = {"accept": 15, "reject": 0, "needs-evidence": 0}
        mock["provenance"] = "UNAUTHENTICATED-TEST-ONLY-NOT-GITHUB"
        cls.pack = build_overlay_handoff(
            cls.packet, cls.ledger, mock, resource_loader=cls.reader
        )

    def test_real_fifteen_row_positive_pack_uses_preinstalled_exact_olia_evidence(self):
        self.assertEqual(self.pack["counts"], {"exact": 12, "native-only": 3})
        self.assertEqual(sum(len(c["mappings"]) for c in self.pack["corpora"]), 15)
        base = ("resources/ontologies/olia/" +
                self.ledger["ontology_revision"] + "/")
        found = []
        for corpus in self.pack["corpora"]:
            self.assertTrue(any(
                e["record"]["kind"] == "ontology-definition"
                for e in corpus["added_evidence"]
            ))
            for item in corpus["added_evidence"]:
                if item["record"]["kind"] == "ontology-definition":
                    self.assertTrue(item["resource"].startswith(base))
                    self.assertEqual(item["record"], packaged_resource(item["resource"]))
                    found.append(item)
        self.assertGreaterEqual(len(found), 9)
        self.assertIsNone(verify_overlay_handoff_integrity(self.pack))
        self.assertFalse(self.pack["release_authorized"])

    def test_foreign_ontology_path_or_modified_class_record_fails_after_rehash(self):
        source = next(e for c in self.pack["corpora"]
                      for e in c["added_evidence"]
                      if e["record"]["kind"] == "ontology-definition")
        mutations = []
        wrong_path = copy.deepcopy(self.pack)
        for c in wrong_path["corpora"]:
            for e in c["added_evidence"]:
                if e["record"]["evidence_id"] == source["record"]["evidence_id"]:
                    e["resource"] = "resources/ontologies/olia/other-revision/class.json"
        mutations.append(wrong_path)
        wrong_record = copy.deepcopy(self.pack)
        for c in wrong_record["corpora"]:
            for e in c["added_evidence"]:
                if e["record"]["evidence_id"] == source["record"]["evidence_id"]:
                    e["record"]["source_uri"] = "https://invalid.example/forged.owl"
                    e["record"]["content_digest"] = evidence_record_digest(e["record"])
        mutations.append(wrong_record)
        disguised = copy.deepcopy(self.pack)
        for c in disguised["corpora"]:
            for e in c["added_evidence"]:
                if e["record"]["evidence_id"] == source["record"]["evidence_id"]:
                    e["resource"] = f"resources/profiles/{c['corpus_id']}/candidate-forged-olia.json"
        mutations.append(disguised)
        for i,changed in enumerate(mutations):
            with self.subTest(mutant=i), self.assertRaises(ValueError):
                verify_overlay_handoff_integrity(_rehash(changed))

    def test_native_only_old_source_handoff_still_verifies(self):
        from tests.i033e.test_overlay_handoff import assemble
        ledger, reader, packet, mock = cohort()
        pack = assemble(ledger, reader, packet, mock)
        self.assertIsNone(verify_overlay_handoff_integrity(pack))


if __name__ == "__main__":
    unittest.main()
