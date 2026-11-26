"""Editorial evidence is qualified discovery, not reconstructed inference."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes
from scripts.pages.scoped_progress import rule_matches

CRM = "http://www.cidoc-crm.org/cidoc-crm/"
INF = "http://www.cidoc-crm.org/extensions/crminf/"
ROOT = Path(__file__).resolve().parents[2]

class EditorialEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = MappingCatalog()
        self.policy = json.loads((ROOT / "docs/research/data/scoped-applicability.json").read_text())

    def inventory(self, name):
        return json.loads((ROOT / "docs/research/data/generated/scoped" / (name + ".json")).read_text())

    def check_candidate(self, corpus, model, target, relation, version, **selector):
        rows = self.catalog.map_native(corpus, corpus_version=version, **selector)
        row, = [r for r in rows if r.target == target]
        self.assertEqual(row.relation, relation)
        self.assertTrue(row.evidence)
        self.assertEqual(row.corpus_version, version)
        self.assertTrue(any(rule_matches(rule, row.selector) for rule in
                            self.policy["corpora"][corpus]["rules"][model]))
        self.assertNotIn(row, self.catalog.find_by_target(target, corpus=corpus, kind=row.kind))
        self.assertIn(row, self.catalog.find_by_target(target, corpus=corpus,
                                                       kind=row.kind, include_approximate=True))
        with self.assertRaises(MappingError):
            resolve_nodes(object(), row, corpus_version=version)

    def test_cuc_certainty_is_not_proposition_truth(self):
        data = self.inventory("cuc")
        scope = data["node_features"]["cert"]["scopes"]["sign"]
        self.assertEqual(data["catalog_version"], "0.2.8")
        self.assertEqual(scope["values"], {"False": 23551, "True": 53664})
        self.assertEqual(data["node_features"]["cert"]["empty_records"], 68802)
        for value in scope["values"]:
            self.check_candidate("cuc", "CRMinf", INF + "I6_Belief_Value", "related", "0.2.8",
                                 kind="value", node="sign", feature="cert", value=value)
        self.assertEqual(self.catalog.map_native("cuc", node="sign", feature="cert",
                                                 value="", corpus_version="0.2.8"), ())
        self.assertFalse(any(r.target == INF + "I6_Belief_Value"
                             for r in self.catalog.map_native("cuc", node="sign",
                                    feature="emen", value="restored", corpus_version="0.2.8")))

    def test_editorial_history_properties_do_not_claim_actor_identity(self):
        corpus = "tlhdig-tf"
        data = self.inventory(corpus)
        self.assertEqual(data["catalog_version"], "0.4.0")
        self.assertEqual(data["node_types"]["edit"], 170955)
        self.check_candidate(corpus, "CIDOC CRM", CRM + "E7_Activity", "related", "0.4.0",
                             kind="node", node="edit")
        for feature, count, prop in (("editor", 75388, "P14_carried_out_by"),
                                     ("date", 121938, "P4_has_time-span"),
                                     ("src", 7029, "P16_used_specific_object")):
            self.assertEqual(data["node_features"][feature]["scopes"]["edit"]["count"], count)
            self.check_candidate(corpus, "CIDOC CRM", CRM + prop, "related", "0.4.0",
                                 kind="feature", node="edit", feature=feature)
        self.assertFalse(any(r.target == CRM + "P14_carried_out_by"
                             for r in self.catalog.map_native(corpus, kind="feature", node="edit",
                                                             feature="author")))
        self.assertFalse(any(r.kind == "entity" and r.node == "edit" for r in self.catalog.load(corpus)))

if __name__ == "__main__":
    unittest.main()
