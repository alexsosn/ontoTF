from __future__ import annotations

import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from importlib.resources import files
from pathlib import Path

from tfont.production_bundles import load_production_adj_adv_bundle
from tfont.digests import evidence_record_digest

ROOT=Path(__file__).resolve().parents[2]
MATRIX=ROOT/"docs/research/data/generated/i027c1/native-pos-matrix.json"
OLIA_REVISION="d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
OLIA_BLOB="5c5e8bda93eaeab2940472a167ff8d3107be8d43"
OWL="http://www.w3.org/2002/07/owl#"
RDF="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
BASE="http://purl.org/olia/olia.owl#"


class OriginalPOSReviewEvidence(unittest.TestCase):
    def test_each_native_gloss_and_pin_agrees_with_original_source_matrix(self):
        source=json.loads(MATRIX.read_text(encoding="utf-8"))
        rows={(r["corpus_id"],r["native_code"]):r for r in source["semantic_rows"]}
        for corpus in ("bhsa","syriac"):
            b=load_production_adj_adv_bundle(corpus)
            evidence=next(x.data for x in b.evidences
                if x.data["evidence_id"]==f"evidence:{corpus}:word-sp-adj-adv-source")
            self.assertEqual(evidence["content_digest"],evidence_record_digest(evidence))
            self.assertEqual(evidence["reviewed_content"]["production_node_type"],"word")
            for code,expected in (("adjv","adjective"),("advb","adverb")):
                row=rows[(corpus,code)]
                value=evidence["reviewed_content"]["source_definitions"][code]
                self.assertEqual(row["source_definition_kind"],"explicit-gloss")
                self.assertEqual(row["source_gloss"],expected)
                self.assertEqual(value["gloss"],row["source_gloss"])
                self.assertEqual(value["line"],row["source_line"])
                self.assertEqual(value["featureObservations"],row["observed_feature_records"])
                self.assertEqual(evidence["source_revision"],row["source_revision"])
                self.assertEqual(evidence["reviewed_content"]["target_tf_revision"],
                                 row["target_corpus_revision"])
        self.assertEqual(rows[("bhsa","adjv")]["source_revision"],
                         "4db00e2157915495e1a4d3d57e41223df24775da")

    def test_olia_classes_exist_as_real_rdf_owl_class_declarations(self):
        root=files("tfont").joinpath(
            "resources","ontologies","olia",OLIA_REVISION,"olia.owl"
        )
        raw=root.read_bytes()
        expected_blob=hashlib.sha1(
            b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw
        ).hexdigest()
        self.assertEqual(expected_blob,OLIA_BLOB)
        xml=ET.fromstring(raw)
        for label in ("Adjective","Adverb"):
            matches=xml.findall(f".//{{{OWL}}}Class[@{{{RDF}}}about='{BASE+label}']")
            self.assertTrue(matches, f"pinned OLiA source lacks {label} class declaration")
        for corpus in ("bhsa","syriac"):
            b=load_production_adj_adv_bundle(corpus)
            lock=b.ontology_locks[0].data
            self.assertEqual(lock["source_revision"],OLIA_REVISION)
            for label in ("Adjective","Adverb"):
                self.assertIn(BASE+label,lock["terms_used"])

    def test_extrabiblical_enum_remains_unreviewed_for_this_mapping(self):
        rows=json.loads(MATRIX.read_text(encoding="utf-8"))["semantic_rows"]
        extra=[x for x in rows if x["corpus_id"]=="extrabiblical"
               and x["native_code"] in ("adjv","advb")]
        self.assertEqual(len(extra),2)
        self.assertTrue(all(x["source_definition_kind"]=="enum-only"
                            and x["source_gloss"] is None
                            and x["ontology_mapping_authorized"] is False for x in extra))


if __name__=="__main__":
    unittest.main()
