"""I-034F RED: exact original ExtraBiblical MQL anchor for candidate POS facts.

The installed 0.3.0 ExtraBiblical source provenance is a corpus-source-enumeration,
not a BHSA/Syriac corpus-feature-definition. Never synthesize source authority.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tfont.batch_proposals import BatchProposalError, packaged_resource
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import evidence_record_digest


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "src/tfont/resources/batch_pilots/i034f-extrabiblical-olia-pos.json"
REV = "9a56288e6777bad6328856acf055c780e65dd5d9"
PINNED_VERB = "resources/profiles/extrabiblical/0.3.0/evidence/native-verb-pos.json"


class PinnedOriginalMQLCandidateEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.name = cls.ledger["source_registry"]["extrabiblical"]["evidence_resource"]
        cls.original = packaged_resource(PINNED_VERB)

    def source(self):
        base = self.original
        record = {
            "evidence_id": "evidence:extrabiblical:word-sp-i034f",
            "kind": "corpus-feature-definition",
            "source_uri": base["source_uri"],
            "source_revision": REV,
            "content_mode": "normalized-record",
            "reviewed_content": {
                "feature": "sp",
                "feature_semantics": "part-of-speech",
                "production_node_type": "word",
                "documented_node_types": ["word"],
                "target_tf_revision": REV,
                "original_mql_blob": base["reviewed_content"]["source_blob_sha"],
                "decompressed_sha256": base["reviewed_content"]["source_decompressed_sha256"],
                "source_definitions": {
                    "verb": {"gloss": "verb", "line": 165, "enum_code": 1},
                },
            },
        }
        record["content_digest"] = evidence_record_digest(record)
        return record

    def test_genuine_pinned_original_source_is_valid_candidate_not_auto_release(self):
        reader = CandidateEvidenceResources(self.ledger, {self.name: self.source()})
        record = reader(self.name)
        self.assertEqual(record["source_uri"], self.original["source_uri"])
        self.assertEqual(record["source_revision"], REV)
        self.assertEqual(record["reviewed_content"]["original_mql_blob"],
                         self.original["reviewed_content"]["source_blob_sha"])
        self.assertNotIn("reviewer_login", record)
        self.assertNotIn("release_authorized", record)

    def test_rejects_changed_real_source_revision_blob_feature_node_or_tf_target(self):
        mutations = [
            ("source_uri", "https://example.org/untrusted"),
            ("source_revision", "f"*40),
            ("kind", "corpus-provenance"),
        ]
        for key, value in mutations:
            changed = self.source()
            changed[key] = value
            changed["content_digest"] = evidence_record_digest(changed)
            with self.subTest(key=key), self.assertRaises(BatchProposalError):
                CandidateEvidenceResources(self.ledger, {self.name: changed})
        for key, value in (
            ("feature", "pdp"),
            ("feature_semantics", "invented"),
            ("production_node_type", "verse"),
            ("documented_node_types", ["verse"]),
            ("target_tf_revision", "f"*40),
            ("original_mql_blob", "f"*40),
            ("decompressed_sha256", "f"*64),
        ):
            changed = self.source()
            changed["reviewed_content"][key] = value
            changed["content_digest"] = evidence_record_digest(changed)
            with self.subTest(key=key), self.assertRaises(BatchProposalError):
                CandidateEvidenceResources(self.ledger, {self.name: changed})


if __name__ == "__main__":
    unittest.main()
