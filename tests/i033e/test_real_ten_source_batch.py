"""I-033E3: real proposed 10-item source-pinned batch is reviewable, NEVER approved."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tfont.batch_proposals import compile_candidate_batch
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import evidence_record_digest
from tfont.review_packets import build_review_packet, serialized, verify_review_packet


ROOT = Path(__file__).resolve().parents[2]
LEGACY_MANIFEST = {
    # A frozen historical cohort, not the mutable ACTIVE review manifest.
    "schema_version": 2,
    "ledger": "src/tfont/resources/batch_pilots/i033e3-ten-native-sp-candidates.json",
    "packet": "docs/research/data/generated/i033d/i033e3-ten-native-sp-review-request.json",
    "evidence_resources": {
        "resources/profiles/bhsa/batch-candidates/i033e3-word-sp-source.json":
            "docs/research/data/batch_review/evidence/i033e3-bhsa-word-sp.json",
        "resources/profiles/syriac/batch-candidates/i033e3-word-sp-source.json":
            "docs/research/data/batch_review/evidence/i033e3-syriac-word-sp.json",
    },
}
SOURCE_LINES = {
    "bhsa": {
        "art": ("article", 17),
        "prep": ("preposition", 22),
        "conj": ("conjunction", 23),
        "prps": ("personal pronoun", 24),
        "prde": ("demonstrative pronoun", 25),
        "prin": ("interrogative pronoun", 26),
        "intj": ("interjection", 27),
        "nega": ("negative particle", 28),
        "inrg": ("interrogative particle", 29),
    },
    "syriac": {"pron": ("pronoun", 91)},
}
SOURCES = {
    "bhsa": ("4db00e2157915495e1a4d3d57e41223df24775da",
             "https://raw.githubusercontent.com/ETCBC/bhsa/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/sp.md"),
    "syriac": ("3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6",
               "https://raw.githubusercontent.com/ETCBC/linksyr/3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6/data/lib/syriac/word_grammar"),
}


class TenSourcePOSReviewCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = LEGACY_MANIFEST
        cls.ledger = json.loads((ROOT / cls.meta["ledger"]).read_text(encoding="utf-8"))
        cls.evidence = {
            name: json.loads((ROOT / path).read_text(encoding="utf-8"))
            for name, path in cls.meta["evidence_resources"].items()
        }
        cls.loader = CandidateEvidenceResources(cls.ledger, cls.evidence)

    def test_manifest_and_batch_are_bounded_and_proposal_only(self):
        self.assertEqual(self.meta["schema_version"], 2)
        self.assertEqual(len(self.meta["evidence_resources"]), 2)
        self.assertEqual(self.ledger["schema_version"], 2)
        self.assertEqual(self.ledger["mode"], "proposal-only")
        self.assertEqual(len(self.ledger["decisions"]), 10)
        self.assertEqual(self.ledger["batch_id"], "i033e3-olia-bhsa-syriac-native-sp-review")
        pairs = [(d["corpus_id"], d["value"]) for d in self.ledger["decisions"]]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(set(pairs), {
            (corpus, value) for corpus, values in SOURCE_LINES.items() for value in values
        })
        for decision in self.ledger["decisions"]:
            with self.subTest(decision=decision):
                self.assertEqual(decision["assessment"], "native-only")
                self.assertNotIn("term_key", decision)
                self.assertTrue(len(decision["rationale"]) > 80)

    def test_supplemental_evidence_is_pinned_and_nonshadowing(self):
        for corpus, glossary in SOURCE_LINES.items():
            with self.subTest(corpus=corpus):
                spec = self.ledger["source_registry"][corpus]
                evidence = self.loader(spec["evidence_resource"])
                source_revision, source_uri = SOURCES[corpus]
                self.assertEqual(evidence["source_revision"], source_revision)
                self.assertEqual(evidence["source_uri"], source_uri)
                self.assertEqual(evidence["content_digest"], evidence_record_digest(evidence))
                definitions = evidence["reviewed_content"]["source_definitions"]
                for key, (gloss, line) in glossary.items():
                    self.assertEqual(definitions[key]["gloss"], gloss)
                    self.assertEqual(definitions[key]["line"], line)
                    self.assertNotIn("featureObservations", definitions[key])

    def test_ten_source_candidates_are_not_runtime_mappings(self):
        compiled = compile_candidate_batch(self.ledger, resource_loader=self.loader)
        self.assertEqual(compiled["count"], 10)
        self.assertIs(compiled["release_authorized"], False)
        for row in compiled["candidates"]:
            self.assertEqual(row["native_state"], "native-only")
            self.assertFalse(row["projections"])
            self.assertNotIn("review", row)

    def test_generated_packet_recomputes_exactly_and_cannot_authorize(self):
        encoded = serialized(build_review_packet(self.ledger, resource_loader=self.loader))
        self.assertEqual(encoded, (ROOT / self.meta["packet"]).read_text(encoding="utf-8"))
        packet = json.loads(encoded)
        self.assertEqual(packet["count"], 10)
        self.assertEqual(packet["authority"], "unreviewed-proposal")
        self.assertIs(packet["release_authorized"], False)
        self.assertTrue(verify_review_packet(
            packet, self.ledger, resource_loader=self.loader
        ))
        self.assertEqual({r["mapping_id"] for r in packet["rows"]}, {
            f"mapping:{corpus}:native-sp-{value}"
            for corpus, values in SOURCE_LINES.items() for value in values
        })
        self.assertEqual(len({r["decision_digest"] for r in packet["rows"]}), 10)


if __name__ == "__main__":
    unittest.main()
