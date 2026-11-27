"""Complete observed ORACC POS/EPOS coverage, preserving scope and granularity."""
import json
from pathlib import Path
import unittest

from ontotf.xml_mappings import MappingCatalog, MappingError, resolve_nodes

CORPUS = "assyrian-royal-inscriptions"
VERSION = "1.0.0"
BASE = "http://purl.org/olia/olia.owl#"
TARGETS = {
    "DP": ("exact", "DemonstrativePronoun"),
    "QP": ("exact", "InterrogativePronoun"),
    "XP": ("exact", "IndefinitePronoun"),
    "J": ("exact", "Interjection"),
    "RP": ("narrower", "PersReflPronoun"),
    "SBJ": ("close", "SubordinatingConjunction"),
    "V/i": ("narrower", "Verb"),
    "V/t": ("narrower", "Verb"),
    "X": ("native-only", None),
}
for name in ("CN", "LN", "MN", "ON", "QN", "WN"):
    TARGETS[name] = ("narrower", "ProperNoun")

class OraccCompletePosTests(unittest.TestCase):
    def test_actual_observed_domains_have_one_disposition_each(self):
        root = Path(__file__).resolve().parents[2]
        data = json.loads((root / "docs/research/data/generated/scoped" / (CORPUS + ".json")).read_text())
        self.assertEqual(data["catalog_version"], VERSION)
        self.assertEqual(data["tf_version"], "0.4.0")
        self.assertEqual(data["revision"], "60db4b724a687c0f425e78eae924fce89454e106")
        catalog = MappingCatalog()
        for feature in ("pos", "epos"):
            for node, scope in data["node_features"][feature]["scopes"].items():
                with self.subTest(node=node, feature=feature):
                    self.assertEqual(scope["value_domain"], "complete_observed")
                    rows = [r for r in catalog.load(CORPUS) if r.kind == "value"
                            and r.node == node and r.feature == feature]
                    self.assertEqual(len(rows), len(scope["values"]))
                    self.assertEqual({r.value for r in rows}, set(scope["values"]))
                    for row in rows:
                        if row.value not in TARGETS:
                            continue
                        relation, target = TARGETS[row.value]
                        self.assertEqual((row.relation, row.target),
                                         (relation, BASE + target if target else None))
                        self.assertTrue(row.evidence)
                        if relation != "exact":
                            with self.assertRaises(MappingError):
                                resolve_nodes(object(), row, corpus_version=VERSION)
                            self.assertEqual(catalog.find_correspondences(
                                CORPUS, "bhsa", node=node, feature=feature, value=row.value), ())
                    self.assertEqual(catalog.map_native(CORPUS, node=node,
                                     feature=feature, value="AN"), ())
        self.assertEqual(catalog.map_native(CORPUS, node="lex", feature="epos", value="DP"), ())
        self.assertEqual(catalog.map_native(CORPUS, kind="entity", node="word",
                                         feature="pos", value="CN"), ())

    def test_qualified_verb_and_pronoun_do_not_claim_specific_valency_or_reflexivity(self):
        catalog = MappingCatalog()
        for node, feature in (("word", "pos"), ("word", "epos"), ("lex", "pos")):
            for tag in ("V/i", "V/t", "RP", "SBJ"):
                row, = catalog.map_native(CORPUS, node=node, feature=feature, value=tag)
                self.assertNotEqual(row.relation, "exact")
                self.assertNotIn(row, catalog.find_by_target(row.target, corpus=CORPUS))
                self.assertIn(row, catalog.find_by_target(row.target, corpus=CORPUS, include_approximate=True))

if __name__ == "__main__":
    unittest.main()
