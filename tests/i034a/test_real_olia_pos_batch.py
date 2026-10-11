"""I-034A RED: 15 real BHSA/Syriac POS category decisions, nine OLiA classes.

Proposals are NOT approved GitHub reviews or published ontology mappings.
"""
from __future__ import annotations

import copy
import hashlib
import json
from importlib.resources import files
from pathlib import Path
import unittest

from tfont.batch_proposals import compile_candidate_batch, packaged_resource
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import evidence_record_digest
from tfont.source_validation import validate_source


ROOT = Path(__file__).resolve().parents[2]
REV = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
BASE = f"resources/ontologies/olia/{REV}"
LOCK = BASE + "/lock-linguistic-i034a-pos.json"
LEDGER = "src/tfont/resources/batch_pilots/i034a-olia-bhsa-syriac-pos-proposals.json"

TARGET_LINES = {
    "article": ("Article", 1682),
    "preposition": ("Preposition", 525),
    "conjunction": ("Conjunction", 356),
    "demonstrativepronoun": ("DemonstrativePronoun", 1935),
    "interrogativepronoun": ("InterrogativePronoun", 2135),
    "interjection": ("Interjection", 307),
    "negativeparticle": ("NegativeParticle", 3684),
    "interrogativeparticle": ("InterrogativeParticle", 3812),
    "pronoun": ("Pronoun", 1860),
}
EXPECTED = {
    ("bhsa", "art"): "Article",
    ("bhsa", "prep"): "Preposition",
    ("bhsa", "conj"): "Conjunction",
    ("bhsa", "prps"): None,
    ("bhsa", "prde"): "DemonstrativePronoun",
    ("bhsa", "prin"): "InterrogativePronoun",
    ("bhsa", "intj"): "Interjection",
    ("bhsa", "nega"): "NegativeParticle",
    ("bhsa", "inrg"): "InterrogativeParticle",
    ("syriac", "conj"): "Conjunction",
    ("syriac", "inrg"): None,
    ("syriac", "intj"): "Interjection",
    ("syriac", "nega"): None,
    ("syriac", "prep"): "Preposition",
    ("syriac", "pron"): "Pronoun",
}


class RealOLiAPOSBatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((ROOT / LEDGER).read_text(encoding="utf-8"))
        cls.ontology_lock = packaged_resource(LOCK)
        cls.old_lock = packaged_resource(BASE + "/lock-linguistic-0.4.0.json")
        old_inputs = json.loads(
            (ROOT / "docs/research/data/batch_review/inputs.json").read_text()
        )
        evidence = {
            key: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for key, name in old_inputs["evidence_resources"].items()
        }
        cls.resource_loader = CandidateEvidenceResources(cls.ledger, evidence)
        cls.compiled = compile_candidate_batch(
            cls.ledger, resource_loader=cls.resource_loader
        )

    def test_exact_source_snapshot_declares_nine_new_olia_classes(self):
        validate_source(self.ontology_lock, "ontology-lock")
        self.assertEqual(self.ledger["ontology_lock_resource"], LOCK)
        self.assertEqual(self.ontology_lock["source_revision"], REV)
        self.assertEqual(self.ontology_lock["content_digest"],
                         self.old_lock["content_digest"])
        self.assertNotEqual(self.ontology_lock["lock_id"], self.old_lock["lock_id"])
        self.assertEqual(
            set(self.ontology_lock["terms_used"]),
            set(self.old_lock["terms_used"]) | {
                "http://purl.org/olia/olia.owl#" + term for term, _ in TARGET_LINES.values()
            },
        )
        artifact = files("tfont").joinpath(
            *self.ontology_lock["snapshot_artifact"].split("/")
        ).read_bytes()
        self.assertEqual(
            "sha256:" + hashlib.sha256(artifact).hexdigest(),
            self.ontology_lock["content_digest"],
        )
        lines = artifact.decode("utf-8").splitlines()
        expected_blob = "5c5e8bda93eaeab2940472a167ff8d3107be8d43"
        for key, (label, line) in TARGET_LINES.items():
            with self.subTest(class_name=label):
                name = self.ledger["ontology_evidence_resources"][key]
                record = packaged_resource(name)
                self.assertEqual(record["kind"], "ontology-definition")
                self.assertEqual(record["source_revision"], REV)
                self.assertEqual(record["content_digest"], evidence_record_digest(record))
                self.assertEqual(record["reviewed_content"]["original_source_blob"], expected_blob)
                self.assertEqual(record["reviewed_content"]["snapshot_digest"],
                                 self.ontology_lock["content_digest"])
                self.assertEqual(record["reviewed_content"]["target"],
                                 "http://purl.org/olia/olia.owl#" + label)
                self.assertEqual(record["reviewed_content"]["declaration_line"], line)
                self.assertEqual(
                    lines[line - 1].strip(),
                    f'<owl:Class rdf:about="http://purl.org/olia/olia.owl#{label}">',
                )

    def test_fifteen_decisions_include_twelve_real_olia_projections(self):
        self.assertEqual(self.ledger["schema_version"], 2)
        self.assertEqual(self.ledger["mode"], "proposal-only")
        self.assertEqual(self.compiled["count"], 15)
        self.assertIs(self.compiled["release_authorized"], False)
        observed = {}
        for candidate in self.compiled["candidates"]:
            native = candidate["native_binding"]
            key = (candidate["corpus_id"], native["value"])
            self.assertNotIn(key, observed)
            observed[key] = candidate
            self.assertEqual(native["feature"], "sp")
            self.assertEqual(native["node_type"], "word")
            self.assertEqual(native["execution_shape"], "value-predicate")
            self.assertEqual(candidate["profiles"], ["linguistic"])
            self.assertEqual(candidate["capabilities"], ["linguistic.part-of-speech"])
            self.assertTrue(candidate["rationale"])
            self.assertTrue(candidate["mapping_semantic_digest"].startswith("sha256:"))
            target = EXPECTED[key]
            if target is None:
                self.assertEqual(candidate["native_state"], "native-only")
                self.assertEqual(candidate["projections"], [])
                self.assertEqual(len(candidate["evidence"]), 1)
            else:
                self.assertEqual(candidate["native_state"], "positive")
                self.assertEqual(len(candidate["evidence"]), 2)
                self.assertEqual(len(candidate["projections"]), 1)
                projection = candidate["projections"][0]
                self.assertEqual(projection["assessment"], "exact")
                self.assertEqual(projection["target"], "http://purl.org/olia/olia.owl#" + target)
                self.assertEqual(projection["ontology_lock"], self.ontology_lock["lock_id"])
                self.assertEqual(projection["evidence"], candidate["evidence"])
                self.assertEqual(projection["native_execution_binding"], native)
                self.assertTrue(projection["projection_semantic_digest"].startswith("sha256:"))
        self.assertEqual(set(observed), set(EXPECTED))
        self.assertEqual(sum(c["native_state"] == "positive" for c in observed.values()), 12)
        self.assertEqual(sum(c["native_state"] == "native-only" for c in observed.values()), 3)

    def test_no_overclaim_about_syrian_particle_or_bhsa_personal_pronoun(self):
        entries = {(d["corpus_id"], d["value"]): d for d in self.ledger["decisions"]}
        self.assertEqual(
            {key for key, row in entries.items() if row["assessment"] == "native-only"},
            {("bhsa", "prps"), ("syriac", "inrg"), ("syriac", "nega")},
        )
        self.assertNotIn("personalpronoun", self.ledger["ontology_evidence_resources"])
        for key in (("bhsa", "prps"), ("syriac", "inrg"), ("syriac", "nega")):
            self.assertNotIn("term_key", entries[key])
            self.assertGreater(len(entries[key]["rationale"]), 95)
        pron = next(m for m in self.compiled["candidates"]
                    if m["corpus_id"] == "syriac" and m["native_binding"]["value"] == "pron")
        self.assertEqual(
            pron["projections"][0]["target"], "http://purl.org/olia/olia.owl#Pronoun"
        )
        self.assertFalse(any(
            "PersonalPronoun" in p["target"]
            for m in self.compiled["candidates"] for p in m["projections"]
        ))

    def test_source_records_preserve_original_provenance_and_are_not_installed(self):
        self.assertEqual(set(self.ledger["source_registry"]), {"bhsa", "syriac"})
        for corpus, spec in self.ledger["source_registry"].items():
            source = self.resource_loader(spec["evidence_resource"])
            self.assertEqual(source["source_revision"], spec["source_revision"])
            self.assertEqual(
                source["reviewed_content"]["target_tf_revision"],
                spec["target_corpus_revision"],
            )
            self.assertEqual(source["content_digest"], evidence_record_digest(source))
        unchanged = copy.deepcopy(self.old_lock)
        self.assertEqual(packaged_resource(BASE + "/lock-linguistic-0.4.0.json"), unchanged)


if __name__ == "__main__":
    unittest.main()
