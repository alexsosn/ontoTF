"""Geographic and custody metadata are qualified discovery, not facts about a TF node."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes
from scripts.pages.scoped_progress import rule_matches

CORPUS = "assyrian-royal-inscriptions"
CRM = "http://www.cidoc-crm.org/cidoc-crm/"
VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "provenience": ("P53_has_former_or_current_location", 2075),
    "collection": ("P49_has_former_or_current_keeper", 1784),
    "pleiades_id": ("P1_is_identified_by", 2069),
    "pleiades_coord": ("P168_place_is_defined_by", 2068),
    "period": ("P2_has_type", 2075),
}

class OraccGeographicCatalogueTests(unittest.TestCase):
    def test_scoped_discovery_and_policy(self):
        inv = json.loads((ROOT / "docs/research/data/generated/scoped" / (CORPUS + ".json")).read_text())
        self.assertEqual(inv["catalog_version"], VERSION)
        self.assertEqual(inv["revision"], "60db4b724a687c0f425e78eae924fce89454e106")
        policy = json.loads((ROOT / "docs/research/data/scoped-applicability.json").read_text())
        rules = policy["corpora"][CORPUS]["rules"]["CIDOC CRM"]
        cat = MappingCatalog()
        for feature, (prop, count) in EXPECTED.items():
            with self.subTest(feature=feature):
                self.assertEqual(inv["node_features"][feature]["scopes"]["document"]["count"], count)
                row, = [r for r in cat.map_native(CORPUS, kind="feature", node="document",
                           feature=feature, corpus_version=VERSION) if r.target == CRM + prop]
                self.assertEqual(row.relation, "related")
                self.assertTrue(row.evidence)
                self.assertTrue(any(rule_matches(rule, row.selector) for rule in rules))
                self.assertNotIn(row, cat.find_by_target(row.target, corpus=CORPUS, kind="feature"))
                self.assertIn(row, cat.find_by_target(row.target, corpus=CORPUS,
                              kind="feature", include_approximate=True))
                with self.assertRaises(MappingError):
                    resolve_nodes(object(), row, corpus_version=VERSION)
                self.assertFalse(any(r.target == row.target for r in cat.map_native(
                    CORPUS, kind="feature", node="word", feature=feature)))

    def test_no_automatic_place_identity_or_ownership(self):
        cat = MappingCatalog()
        for feature, value in (("pleiades_id", "874621"), ("collection", "unlocated"),
                               ("period", "Late Middle Assyrian or early Neo-Assyrian")):
            self.assertEqual(cat.map_native(CORPUS, kind="entity", node="document",
                           feature=feature, value=value, corpus_version=VERSION), ())
        forbidden = {"collection": {"P50_has_current_keeper", "P52_has_current_owner",
                                     "P55_has_current_location"},
                     "provenience": {"P55_has_current_location", "P7_took_place_at"},
                     "period": {"P10_falls_within", "P4_has_time-span"}}
        for feature, props in forbidden.items():
            self.assertFalse(any(r.target in {CRM + p for p in props} for r in
                             cat.map_native(CORPUS, kind="feature", node="document", feature=feature)))

if __name__ == "__main__":
    unittest.main()
