"""Pinned LRMoo F2/R76 scope against real Pseudepigrapha source versions.

No Work, Manifestation, Item or physical witness instance is manufactured.
"""
import unittest

from tfont.xml_mappings import MappingCatalog, resolve_nodes, MappingError

LRMOO = "http://iflastandards.info/ns/lrm/lrmoo/"
UPSTREAM = "7c4b757bb543a110ae9a252d1281835859136852"


class PseudepigraphaExpressionMappingsTests(unittest.TestCase):
    def test_text_bearing_source_version_is_expression_category(self):
        c = MappingCatalog()
        m = c.map_native("pseudepigrapha", kind="node", node="book")
        self.assertEqual(len(m), 1)
        self.assertEqual(
            (m[0].relation, m[0].target, m[0].corpus_version),
            ("exact", LRMOO + "F2_Expression", "1.0"),
        )
        self.assertIn(UPSTREAM, m[0].evidence)
        self.assertIn("LRMoo 1.1.1", m[0].note)
        self.assertIn(
            m[0], c.find_by_target(LRMOO + "F2_Expression",
                                   corpus="pseudepigrapha", kind="node")
        )

        class Otype:
            def s(self, kind):
                if kind != "book":
                    raise AssertionError("not a text-version type")
                return (101, 104, 110)

        class API:
            class F:
                otype = Otype()

            def Fs(self, feature):
                raise AssertionError("F2 should not be defined by a word feature")

        self.assertEqual(resolve_nodes(API(), m[0], corpus_version="1.0"),
                         (101, 104, 110))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), m[0], corpus_version="0.9")

    def test_source_pinned_translation_points_derivative_to_source_expression(self):
        c = MappingCatalog()
        r = c.map_native(
            "pseudepigrapha", kind="edge",
            feature="translation_of", from_node="book", to_node="book",
        )
        self.assertEqual(len(r), 1)
        self.assertEqual(
            (r[0].relation, r[0].target),
            ("exact", LRMOO + "R76_is_derivative_of"),
        )
        self.assertIn(UPSTREAM, r[0].evidence)
        self.assertIn("LRMoo 1.1.1", r[0].note)
        self.assertIn(
            r[0], c.find_by_target(LRMOO + "R76_is_derivative_of",
                                   corpus="pseudepigrapha", kind="edge"),
        )
        # Pseudepigrapha's converter explicitly records translation -> source;
        # the inverse relation or a Work derivation must not be inferred.
        self.assertEqual(c.map_native(
            "pseudepigrapha", kind="edge",
            feature="translation_of", from_node="reading", to_node="book"
        ), ())

    def test_witnesses_and_other_lrmoo_objects_remain_unasserted(self):
        c = MappingCatalog()
        for kind in ("manuscript", "reading", "word"):
            with self.subTest(kind=kind):
                self.assertEqual(
                    [(m.relation, m.target) for m in c.map_native(
                        "pseudepigrapha", kind="node", node=kind
                    )],
                    [("native-only", None)],
                )
        for uri in ("F1_Work", "F3_Manifestation", "F5_Item",
                    "R2_is_derivative_of", "R76i_has_derivative"):
            self.assertEqual(
                c.find_by_target(LRMOO + uri, corpus="pseudepigrapha",
                                 kind="edge" if uri.startswith("R") else "node"),
                (),
            )


if __name__ == "__main__":
    unittest.main()
