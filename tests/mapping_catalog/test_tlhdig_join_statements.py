"""Manuscript apparatus statements and references are not proven physical joins."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes, resolve_edges
from scripts.pages.scoped_progress import rule_matches

CORPUS = "tlhdig-tf"
VERSION = "0.4.0"
CRM = "http://www.cidoc-crm.org/cidoc-crm/"
INF = "http://www.cidoc-crm.org/extensions/crminf/"
ROOT = Path(__file__).resolve().parents[2]

class TlhdigJoinStatementTests(unittest.TestCase):
    def setUp(self):
        self.cat = MappingCatalog()
        self.data = json.loads((ROOT / "docs/research/data/generated/scoped" / (CORPUS + ".json")).read_text())
        self.policy = json.loads((ROOT / "docs/research/data/scoped-applicability.json").read_text())["corpora"][CORPUS]

    def test_statement_and_reference_discovery(self):
        self.assertEqual(self.data["node_types"]["joinstmt"], 3603)
        row, = [r for r in self.cat.map_native(CORPUS, kind="node", node="joinstmt",
                        corpus_version=VERSION) if r.target == INF + "I4_Proposition_Set"]
        self.assertEqual(row.relation, "related")
        self.assertNotIn(row, self.cat.find_by_target(row.target, corpus=CORPUS))
        self.assertIn(row, self.cat.find_by_target(row.target, corpus=CORPUS, include_approximate=True))
        with self.assertRaises(MappingError):
            resolve_nodes(object(), row, corpus_version=VERSION)
        for feature, to, target, count, model in (
            ("joinLeft", "fragment", INF + "J28_contains_entity_reference", 3581, "CRMinf"),
            ("joinRight", "fragment", INF + "J28_contains_entity_reference", 3580, "CRMinf"),
            ("joinDocument", "document", CRM + "P106i_forms_part_of", 3603, "CIDOC CRM")):
            with self.subTest(feature=feature):
                self.assertIn({"from": "joinstmt", "to": to, "count": count},
                              self.data["edge_features"][feature]["pairs"])
                row, = [r for r in self.cat.map_native(CORPUS, kind="edge", feature=feature,
                         from_node="joinstmt", to_node=to, corpus_version=VERSION) if r.target == target]
                self.assertEqual(row.relation, "related")
                self.assertTrue(row.evidence)
                self.assertTrue(any(rule_matches(rule, row.selector) for rule in self.policy["rules"][model]))
                self.assertNotIn(row, self.cat.find_by_target(target, corpus=CORPUS, kind="edge"))
                self.assertIn(row, self.cat.find_by_target(target, corpus=CORPUS, kind="edge", include_approximate=True))
                self.assertFalse(any(r.target == target for r in self.cat.map_native(
                    CORPUS, kind="edge", feature=feature, from_node=to, to_node="joinstmt")))
                with self.assertRaises(MappingError):
                    resolve_edges(object(), row, corpus_version=VERSION)

    def test_native_statement_status_is_not_belief_truth(self):
        expected = {"join_kind": {"direct": 2902, "indirect": 691, "direct-multi": 2,
                                  "indirect-multi": 1, "malformed": 7},
                    "join_resolved": {"0": 30, "1": 3573}}
        for feature, values in expected.items():
            self.assertEqual(self.data["node_features"][feature]["scopes"]["joinstmt"]["values"], values)
            for value in values:
                rows = self.cat.map_native(CORPUS, node="joinstmt", feature=feature,
                                           value=value, corpus_version=VERSION)
                self.assertTrue(any(r.relation == "native-only" and r.target is None for r in rows))
        for value in ("uncertain", "unknown"):
            self.assertEqual(self.cat.map_native(CORPUS, node="joinstmt", feature="join_kind",
                                                 value=value, corpus_version=VERSION), ())

if __name__ == "__main__":
    unittest.main()
