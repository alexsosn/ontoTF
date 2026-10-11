"""I-034C: source-verified BHSA morphology → OLiA value-class proposals.

This checks 29 *observed* TF feature-value identities against frozen source
docs, the real installed OLiA XML snapshot, and the immutable BHSA denominator.
It does not release mappings or authorize an ontology review.
"""
from __future__ import annotations

import copy
import hashlib
import json
from importlib.resources import files
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "docs/research/data/i034c/bhsa-morphology-olia.json"
DENOMINATOR = ROOT / "src/tfont/resources/coverage/p004-i027c2-bhsa-adj-adv-v1/bhsa.json"
BHSA_SHA = "4db00e2157915495e1a4d3d57e41223df24775da"
OLIA_SHA = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
OLIA_DIGEST = "sha256:5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd"
OLIA_BASE = f"resources/ontologies/olia/{OLIA_SHA}/olia.owl"

ORIGINAL_SOURCE = {
    "ps": [("p1", "first person", 14), ("p2", "second person", 15),
           ("p3", "third person", 16), ("NA", "not applicable", 17),
           ("unknown", "unknown", 18)],
    "prs_ps": [("p1", "first person", 15), ("p2", "second person", 16),
               ("p3", "third person", 17), ("NA", "not applicable", 18)],
    "prs_gn": [("m", "masculine", 12), ("f", "feminine", 13),
               ("NA", "not applicable", 14), ("unknown", "unknown", 15)],
    "prs_nu": [("sg", "singular", 15), ("pl", "plural", 17),
               ("NA", "not applicable", 18)],
    "st": [("a", "absolute", 17), ("c", "construct", 18),
           ("e", "emphatic", 19), ("NA", "not applicable", 21)],
    "vt": [("NA", "not applicable", 14), ("perf", "perfect", 20),
           ("impf", "imperfect", 21), ("wayq", "wayyiqtol", 22),
           ("impv", "imperative", 23),
           ("infa", "infinitive (absolute)", 24),
           ("infc", "infinitive (construct)", 25),
           ("ptca", "participle", 26),
           ("ptcp", "participle (passive)", 27)],
}
EXACT = {
    ("ps", "p1"): ("First", 4986),
    ("ps", "p2"): ("Second", 4976),
    ("ps", "p3"): ("Third", 4963),
    ("prs_ps", "p1"): ("First", 4986),
    ("prs_ps", "p2"): ("Second", 4976),
    ("prs_ps", "p3"): ("Third", 4963),
    ("prs_gn", "f"): ("Feminine", 5123),
    ("prs_gn", "m"): ("Masculine", 5151),
    ("prs_nu", "sg"): ("Singular", 4183),
    ("prs_nu", "pl"): ("Plural", 4157),
    ("st", "c"): ("StatusConstructus", 6712),
    ("vt", "impv"): ("ImperativeVerb", 1373),
}


def assert_batch(source: dict, denominator: dict, xml: str):
    if set(source) != {
        "schema_version", "batch_id", "authority", "source_registry",
        "ontology_evidence", "denominator", "rows",
    }:
        raise ValueError("unknown/missing batch fields")
    if source["schema_version"] != 1 or source["batch_id"] != "i034c-bhsa-olia-morphology":
        raise ValueError("schema/batch identity drift")
    if source["authority"] != "unreviewed-semantic-proposals":
        raise ValueError("forged review or publication authority")
    if source["denominator"] != {
        "corpus_id": "bhsa", "resource_set": "p004-i027c2-bhsa-adj-adv-v1",
        "denominator_digest": denominator["denominator_digest"],
        "source_revision": BHSA_SHA,
    }:
        raise ValueError("installed denominator drift")
    if source["ontology_evidence"] != {
        "ontology_id": "olia", "source_revision": OLIA_SHA,
        "snapshot_digest": OLIA_DIGEST,
        "snapshot_artifact": OLIA_BASE,
        "release_authorized": False,
    }:
        raise ValueError("ontology lock/review authority forged")
    if set(source["source_registry"]) != set(ORIGINAL_SOURCE):
        raise ValueError("missing corpus source definitions")
    for feat in ORIGINAL_SOURCE:
        if source["source_registry"][feat] != {
            "uri": f"https://raw.githubusercontent.com/ETCBC/bhsa/{BHSA_SHA}/docs/features/{feat}.md",
            "revision": BHSA_SHA,
        }:
            raise ValueError(f"{feat} not pinned to real BHSA feature definition")
    actual = {
        row["item_id"] for row in denominator["semantic_items"]
        if row["item_id"].startswith("node_value:") and
        row["item_id"].split(":", 1)[1].split("=", 1)[0] in ORIGINAL_SOURCE
    }
    expected = {
        f'node_value:{feat}="{value}"'
        for feat, defs in ORIGINAL_SOURCE.items() for value, _, _ in defs
    }
    if actual != expected or len(expected) != 29:
        raise ValueError("pinned R-005 BHSA observed feature/value inventory drift")
    rows = source["rows"]
    if not isinstance(rows, list) or len(rows) != 29:
        raise ValueError("expected 29 individual source-backed decisions")
    ids = [row.get("item_id") for row in rows]
    if len(set(ids)) != 29 or set(ids) != expected:
        raise ValueError("duplicate, missing or phantom source selector")
    source_defs = {
        (feat, val): (gloss, line)
        for feat, defs in ORIGINAL_SOURCE.items()
        for val, gloss, line in defs
    }
    xml_lines = xml.splitlines()
    positives = 0
    for row in rows:
        if set(row) != {
            "feature", "value", "item_id", "source_line", "source_gloss",
            "native_subject", "assessment", "ontology_target",
            "ontology_line", "rationale",
        }:
            raise ValueError("unknown/missing row field")
        key = (row["feature"], row["value"])
        if key not in source_defs or row["item_id"] != f'node_value:{key[0]}="{key[1]}"':
            raise ValueError("source selector is not a real original feature/value")
        gloss, lineno = source_defs[key]
        if (row["source_gloss"], row["source_line"]) != (gloss, lineno):
            raise ValueError("original corpus meaning or line mismatch")
        subject = "pronominal-suffix" if key[0].startswith("prs_") else "word-morphology"
        if row["native_subject"] != subject:
            raise ValueError("suffix and host morphology conflated")
        if not isinstance(row["rationale"], str) or len(row["rationale"].strip()) < 85:
            raise ValueError("missing individual semantic decision justification")
        if key in EXACT:
            term, line = EXACT[key]
            positives += 1
            if (row["assessment"], row["ontology_target"], row["ontology_line"]) != (
                "exact", "http://purl.org/olia/olia.owl#" + term, line
            ):
                raise ValueError("exact class alignment is unsupported or absent")
            declaration = xml_lines[line - 1].strip()
            expected_declaration = (
                '<owl:Class rdf:ID="StatusConstructus">' if term == "StatusConstructus"
                else f'<owl:Class rdf:about="http://purl.org/olia/olia.owl#{term}">'
            )
            if declaration != expected_declaration:
                raise ValueError("ontology class not declared at pinned original XML line")
        elif (row["assessment"], row["ontology_target"], row["ontology_line"]) != (
            "native-only", None, None
        ):
            raise ValueError("unverified morphology/tense equivalence projected as exact")
    if positives != 12:
        raise ValueError("incorrect positive OLiA alignment count")


class BHSARealMorphologySemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))
        cls.denom = json.loads(DENOMINATOR.read_text(encoding="utf-8"))
        artifact = files("tfont").joinpath(*OLIA_BASE.split("/")).read_bytes()
        cls.xml = artifact.decode("utf-8")
        assert "sha256:" + hashlib.sha256(artifact).hexdigest() == OLIA_DIGEST

    def test_all_29_source_values_have_one_semantic_decision(self):
        assert_batch(self.data, self.denom, self.xml)
        self.assertEqual(len(self.data["rows"]), 29)
        self.assertEqual(sum(r["assessment"] == "exact" for r in self.data["rows"]), 12)
        self.assertEqual(sum(r["assessment"] == "native-only" for r in self.data["rows"]), 17)

    def test_no_invented_published_or_existing_production_mapping(self):
        for row in self.data["rows"]:
            self.assertFalse(next(x for x in self.denom["semantic_items"]
                                  if x["item_id"] == row["item_id"])["accounting"]["production"])
        raw = json.dumps(self.data)
        for forged in ('"reviewer_login"', '"review_id"', '"publish_handoff"',
                       '"installed_profile"', '"release_receipt"'):
            self.assertNotIn(forged, raw)

    def test_source_identity_and_olia_semantic_scope(self):
        rows = {(r["feature"], r["value"]): r for r in self.data["rows"]}
        for f in ("prs_ps", "prs_gn", "prs_nu"):
            self.assertTrue(all(x["native_subject"] == "pronominal-suffix"
                                for k, x in rows.items() if k[0] == f))
        self.assertEqual(rows["st", "c"]["ontology_target"],
                         "http://purl.org/olia/olia.owl#StatusConstructus")
        self.assertEqual(rows["vt", "impv"]["ontology_target"],
                         "http://purl.org/olia/olia.owl#ImperativeVerb")
        for f, v in (("vt", "perf"), ("vt", "impf"), ("st", "e"),
                     ("vt", "infa"), ("vt", "infc"), ("vt", "wayq")):
            with self.subTest(feature=f, value=v):
                self.assertEqual(rows[f, v]["assessment"], "native-only")
                self.assertIsNone(rows[f, v]["ontology_target"])
        # No reviewed source occurrence of a pronominal-suffix dual.
        self.assertNotIn(("prs_nu", "du"), rows)

    def test_adversarial_mutations_fail_without_changing_locked_resources(self):
        for case in ("missing", "duplicate", "phantom", "wrong-source",
                     "fake-target", "swap-subject", "assume-perfect-past",
                     "assume-emphatic-emphasis", "forged-release"):
            value = copy.deepcopy(self.data)
            rows = value["rows"]
            if case == "missing":
                rows.pop()
            elif case == "duplicate":
                rows[-1] = copy.deepcopy(rows[0])
            elif case == "phantom":
                rows[-1]["value"] = "impossible"
            elif case == "wrong-source":
                value["source_registry"]["ps"]["revision"] = "0" * 40
            elif case == "fake-target":
                rows[0]["ontology_target"] = "http://purl.org/olia/olia.owl#Fake"
            elif case == "swap-subject":
                next(r for r in rows if r["feature"] == "prs_ps")["native_subject"] = "word-morphology"
            elif case == "assume-perfect-past":
                target = next(r for r in rows if r["feature"] == "vt" and r["value"] == "perf")
                target.update(assessment="exact", ontology_target="http://purl.org/olia/olia.owl#Perfect",
                              ontology_line=5292)
            elif case == "assume-emphatic-emphasis":
                target = next(r for r in rows if r["feature"] == "st" and r["value"] == "e")
                target.update(assessment="exact", ontology_target="http://purl.org/olia/olia.owl#Emphatic",
                              ontology_line=4951)
            else:
                value["authority"] = "approved"
            with self.subTest(case=case), self.assertRaises(ValueError):
                assert_batch(value, self.denom, self.xml)


if __name__ == "__main__":
    unittest.main()
