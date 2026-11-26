"""LRMoo F2 textual expression categories, not identities or physical objects."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes, resolve_edges

LRMOO = "http://iflastandards.info/ns/lrm/lrmoo/"
F2 = LRMOO + "F2_Expression"
R5I = LRMOO + "R5i_is_component_of"
CASES = (
    ("bhsa", "2021", "4db00e2157915495e1a4d3d57e41223df24775da", 39, "exact"),
    ("syrnt", "0.1", "dae3eb6ff62b9b272fb503646796c25d248175ce", 27, "exact"),
    ("syriac", "0.9", "bb0eaa7e21b020a26b7566d2e495da9b1f84a919", 29, "close"),
    ("extrabiblical", "0.2", "9a56288e6777bad6328856acf055c780e65dd5d9", 13, "related"),
)


class LrmooSourceBookTests(unittest.TestCase):
    def test_book_categories_follow_source_scope(self):
        c = MappingCatalog()
        root = Path(__file__).resolve().parents[2]
        for corpus, version, revision, count, relation in CASES:
            with self.subTest(corpus=corpus):
                d = json.loads((root / "docs/research/data/generated/scoped" / (corpus+".json")).read_text())
                self.assertEqual(d["revision"], revision)
                self.assertEqual(d["node_types"]["book"], count)
                self.assertEqual(d["node_features"]["book"]["scopes"]["book"]["count"], count)
                row, = (m for m in c.map_native(corpus, kind="node", node="book",
                                                  corpus_version=version) if m.target == F2)
                self.assertEqual(row.relation, relation)
                self.assertIn(revision, row.evidence)
                self.assertIn(row, c.find_by_target(F2, corpus=corpus, include_approximate=True))
                hits = c.find_correspondences(corpus, "peshitta", kind="node", node="book")
                if relation == "exact":
                    self.assertTrue(any(x.target == F2 and x.scope == "category" and x.relation == "exact" for x in hits))
                    class API:
                        class F:
                            class otype:
                                @staticmethod
                                def s(node):
                                    assert node == "book"
                                    return (1, 2)
                    self.assertEqual(resolve_nodes(API(), row, corpus_version=version), (1, 2))
                else:
                    self.assertFalse(any(x.target == F2 for x in hits))
                    self.assertNotIn(row, c.find_by_target(F2, corpus=corpus))
                    with self.assertRaisesRegex(MappingError, "exact"):
                        resolve_nodes(object(), row, corpus_version=version)
                self.assertEqual(c.map_native(corpus, kind="entity", node="book",
                                              feature="book", value="Genesis"), ())
                for target in ("F1_Work", "F3_Manifestation", "F5_Item"):
                    self.assertFalse(c.find_by_target(LRMOO+target, corpus=corpus,
                                                      include_approximate=True))

    def test_apparatus_structure_not_expression_derivation_or_identity(self):
        c = MappingCatalog()
        root = Path(__file__).resolve().parents[2]
        d = json.loads((root / "docs/research/data/generated/scoped/pseudepigrapha.json").read_text())
        expected = {"div": 42742, "unit": 81275, "ellipsis": 1, "orphan_reading": 9}
        self.assertEqual({p["from"]: p["count"] for p in d["edge_features"]["parent"]["pairs"]}, expected)
        for node in expected:
            row, = c.map_native("pseudepigrapha", kind="edge", feature="parent",
                                from_node=node, to_node="div")
            self.assertEqual((row.relation, row.target),
                             ("related", R5I) if node == "div" else ("native-only", None))
            with self.assertRaises(MappingError):
                resolve_edges(object(), row, corpus_version="1.0")
        self.assertEqual(c.map_native("pseudepigrapha", kind="edge", feature="parent",
                                     from_node="div", to_node="unit"), ())
        self.assertEqual(d["edge_features"]["translation_unit_of"]["pairs"][0]["count"], 54143)
        row, = c.map_native("pseudepigrapha", kind="edge", feature="translation_unit_of",
                            from_node="unit", to_node="unit")
        self.assertEqual((row.relation, row.target), ("native-only", None))
        exact, = c.map_native("pseudepigrapha", kind="edge", feature="translation_of",
                              from_node="book", to_node="book")
        self.assertEqual((exact.relation, exact.target), ("exact", LRMOO+"R76_is_derivative_of"))
        self.assertEqual(c.find_by_target(R5I, kind="edge", corpus="pseudepigrapha"), ())


if __name__ == "__main__":
    unittest.main()
