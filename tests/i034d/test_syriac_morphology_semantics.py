"""I-034D RED: real Syriac grammar + R005 observed values → nine OLiA classes.

The proposed rows have NO GitHub review, RDF publication or release authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from importlib.resources import files
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/research/data/i034d/syriac-morphology-olia.json"
DENOM = ROOT / "src/tfont/resources/coverage/p004-i027c2-syriac-adj-adv-v1/syriac.json"
SYRIAC = "bb0eaa7e21b020a26b7566d2e495da9b1f84a919"
GRAMMAR = "3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6"
OLIA = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
SNAPSHOT = f"resources/ontologies/olia/{OLIA}/olia.owl"
DIGEST = "sha256:5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd"
NS = "http://purl.org/olia/olia.owl#"

SOURCE = {
    "ps": [("first", "first", 61), ("second", "second", 61),
           ("third", "third", 61), ("unknown", None, None)],
    "st": [("abs", "absolute", 95), ("c", None, None),
           ("cst", "construct", 95), ("emph", "emphatic", 95),
           ("unknown", None, None)],
    "vo": [("act", "active", 97), ("pas", "passive", 97)],
    "vpm": [("d", None, None), ("dp", None, None),
            ("p", "vowel pattern", 50)],
    "vs": [("af", "afel", 99), ("pa", "pael", 99), ("pe", "peal", 99)],
    "vt": [("imp", "imperative", 101), ("inf", "infinitive", 102),
           ("ipf", "imperfect", 101), ("pf", "perfect", 101),
           ("ptc", "participle", 102)],
}
EXACT = {
    ("ps", "first"): ("First", 4986),
    ("ps", "second"): ("Second", 4976),
    ("ps", "third"): ("Third", 4963),
    ("st", "cst"): ("StatusConstructus", 6712),
    ("vo", "act"): ("ActiveVoice", 9254),
    ("vo", "pas"): ("PassiveVoice", 9272),
    ("vt", "imp"): ("ImperativeVerb", 1373),
    ("vt", "inf"): ("Infinitive", 1013),
    ("vt", "ptc"): ("Participle", 1072),
}


def check(data, manifest, xml):
    if set(data) != {
        "schema_version", "batch_id", "authority", "corpus", "grammar",
        "ontology_evidence", "denominator", "rows",
    }:
        raise ValueError("batch shape changed")
    if (data["schema_version"], data["batch_id"], data["authority"]) != (
        1, "i034d-syriac-olia-morphology", "unreviewed-semantic-proposals"
    ):
        raise ValueError("semantic batch identity or authority forged")
    if data["corpus"] != {"id": "syriac", "source_revision": SYRIAC}:
        raise ValueError("target corpus identity mismatch")
    if data["grammar"] != {
        "uri": f"https://raw.githubusercontent.com/ETCBC/linksyr/{GRAMMAR}/data/lib/syriac/word_grammar",
        "revision": GRAMMAR,
    }:
        raise ValueError("grammar evidence revision or source drift")
    if data["ontology_evidence"] != {
        "source_revision": OLIA, "snapshot_artifact": SNAPSHOT,
        "snapshot_digest": DIGEST, "release_authorized": False,
    }:
        raise ValueError("unreviewed OntoLex/OLiA authority drift")
    if data["denominator"] != {
        "resource_set": "p004-i027c2-syriac-adj-adv-v1",
        "denominator_digest": manifest["denominator_digest"],
        "source_revision": SYRIAC,
    }:
        raise ValueError("source denominator altered")
    source_values = {
        (f, v): (gloss, line)
        for f, triples in SOURCE.items() for v, gloss, line in triples
    }
    inventory = {
        row["item_id"] for row in manifest["semantic_items"]
        if row["item_id"].startswith("node_value:") and
        row["item_id"].split(":", 1)[1].split("=", 1)[0] in SOURCE
    }
    expected = {f'node_value:{f}="{v}"' for f, v in source_values}
    if inventory != expected or len(inventory) != 22:
        raise ValueError("R-005 real observed Syriac morphology inventory changed")
    rows = data["rows"]
    if not isinstance(rows, list) or len(rows) != 22:
        raise ValueError("require 22 individually justified source values")
    ids = [r["item_id"] for r in rows]
    if len(set(ids)) != 22 or set(ids) != inventory:
        raise ValueError("duplicate, invented or missing Syriac observed code")
    positives = 0
    lines = xml.splitlines()
    for row in rows:
        if set(row) != {
            "feature", "value", "item_id", "source_gloss", "source_line",
            "evidence_kind", "assessment", "ontology_target",
            "ontology_line", "rationale",
        }:
            raise ValueError("semantic row schema altered")
        key = (row["feature"], row["value"])
        if key not in source_values or row["item_id"] != f'node_value:{key[0]}="{key[1]}"':
            raise ValueError("candidate not in original source corpus")
        if (row["source_gloss"], row["source_line"]) != source_values[key]:
            raise ValueError("invented pinned grammar definition or original source line")
        expected_kind = "grammar-defined" if row["source_line"] is not None else "R005-observed-only"
        if row["evidence_kind"] != expected_kind:
            raise ValueError("unexplained R005-only source value treated as grammar-defined")
        if not isinstance(row["rationale"], str) or len(row["rationale"].strip()) < 88:
            raise ValueError("no individual skeptical semantic reason")
        if key in EXACT:
            term, lineno = EXACT[key]
            positives += 1
            if (row["assessment"], row["ontology_target"], row["ontology_line"]) != (
                "exact", NS + term, lineno
            ):
                raise ValueError("unverified shared morphology concept")
            decl = lines[lineno - 1].strip()
            exp = ('<owl:Class rdf:ID="StatusConstructus">' if term == "StatusConstructus"
                   else f'<owl:Class rdf:about="{NS}{term}">')
            if decl != exp:
                raise ValueError("no declared target OWL class at pinned original line")
        elif (row["assessment"], row["ontology_target"], row["ontology_line"]) != (
            "native-only", None, None
        ):
            raise ValueError("fabricated exact semantic equivalence")
        original = next(r for r in manifest["semantic_items"]
                        if r["item_id"] == row["item_id"])
        if original["accounting"]["production"] is not None:
            raise ValueError("already-published selector being counted again")
    if positives != 9:
        raise ValueError("unexpected candidate exact count")


class RealSyriacOLiAMorphology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.manifest = json.loads(DENOM.read_text(encoding="utf-8"))
        blob = files("tfont").joinpath(*SNAPSHOT.split("/")).read_bytes()
        cls.xml = blob.decode("utf-8")
        assert "sha256:" + hashlib.sha256(blob).hexdigest() == DIGEST

    def test_all_observed_values_and_original_ontology_classes(self):
        check(self.data, self.manifest, self.xml)
        self.assertEqual(sum(x["assessment"] == "exact" for x in self.data["rows"]), 9)
        self.assertEqual(sum(x["assessment"] == "native-only" for x in self.data["rows"]), 13)

    def test_unlisted_grammar_values_are_not_invented_semantics(self):
        rows = {(r["feature"], r["value"]):r for r in self.data["rows"]}
        for key in (("st", "c"), ("st", "unknown"), ("ps", "unknown"),
                    ("vpm", "d"), ("vpm", "dp")):
            self.assertIsNone(rows[key]["source_line"])
            self.assertEqual(rows[key]["assessment"], "native-only")
        self.assertEqual(rows["st", "cst"]["ontology_target"], NS + "StatusConstructus")
        self.assertEqual(rows["vo", "act"]["ontology_target"], NS + "ActiveVoice")
        self.assertEqual(rows["vo", "pas"]["ontology_target"], NS + "PassiveVoice")
        for value in ("pf", "ipf"):
            self.assertEqual(rows["vt", value]["assessment"], "native-only")

    def test_forged_semantics_and_authority_are_rejected(self):
        for case in ("drop", "duplicate", "new-value", "pretend-alias",
                     "invent-pattern", "perfect-is-past", "emphatic-is-emphasis",
                     "fake-ontology", "fake-authority"):
            data = copy.deepcopy(self.data)
            rows = data["rows"]
            if case == "drop": rows.pop()
            elif case == "duplicate": rows[-1] = copy.deepcopy(rows[0])
            elif case == "new-value": rows[-1]["value"] = "invented"
            elif case == "pretend-alias":
                next(r for r in rows if r["feature"] == "st" and r["value"] == "c")["source_gloss"] = "construct"
            elif case == "invent-pattern":
                next(r for r in rows if r["feature"] == "vpm" and r["value"] == "dp")["source_line"] = 50
            elif case == "perfect-is-past":
                row = next(r for r in rows if r["feature"] == "vt" and r["value"] == "pf")
                row.update(assessment="exact", ontology_target=NS+"Perfect", ontology_line=5292)
            elif case == "emphatic-is-emphasis":
                row = next(r for r in rows if r["feature"] == "st" and r["value"] == "emph")
                row.update(assessment="exact", ontology_target=NS+"Emphatic", ontology_line=4951)
            elif case == "fake-ontology":
                data["ontology_evidence"]["snapshot_digest"] = "sha256:" + "0"*64
            else: data["authority"] = "approved"
            with self.subTest(case=case), self.assertRaises(ValueError):
                check(data, self.manifest, self.xml)


if __name__ == "__main__":
    unittest.main()
