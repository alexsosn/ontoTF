"""TLHdig 0.4.0 normalized word-transliteration category without glyph identity."""
from __future__ import annotations

import unittest
from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

PIN = "e954600d9f9cc7f16570729813cf6bf3954b8f6d"
TOKEN = "http://purl.org/olia/olia.owl#Token"
CORPUS = "tlhdig-tf"
VERSION = "0.4.0"


class TLHdigNormalizedSourceTokens(unittest.TestCase):
    def test_only_reviewed_trans_word_nodes_map_to_olia_token(self):
        c = MappingCatalog()
        rows = c.map_native(
            CORPUS, kind="node", node="word", feature="trans",
            corpus_version=VERSION,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            (rows[0].relation, rows[0].target, rows[0].corpus_version),
            ("exact", TOKEN, VERSION),
        )
        self.assertIn(PIN, rows[0].evidence)
        self.assertIn(rows[0], c.find_by_target(
            TOKEN, corpus=CORPUS, kind="node",
        ))
        self.assertEqual(c.map_native(CORPUS, kind="node", node="word"), ())
        self.assertEqual(c.map_native(
            CORPUS, kind="entity", node="word",
            feature="trans", value="murši-DINGIR-LIMiš",
        ), ())
        with self.assertRaisesRegex(MappingError, "not verified"):
            c.map_native(CORPUS, kind="node", node="word",
                         feature="trans", corpus_version="0.3.0")

    def test_loaded_tf_feature_presence_excludes_unknown_transcriptions(self):
        class Otype:
            def s(self, node):
                assert node == "word"
                return (10, 11, 12, 13, 14)

        class Trans:
            def v(self, n):
                return {
                    10: "murši-DINGIR-LIMiš",
                    11: None,
                    12: "nuza",
                    13: "",
                    14: "ḫuantalait",
                }[n]

        class API:
            class F:
                otype = Otype()
            def Fs(self, feature):
                assert feature == "trans"
                return Trans()

        c = MappingCatalog()
        row = c.map_native(
            CORPUS, kind="node", node="word", feature="trans"
        )[0]
        self.assertEqual(
            resolve_nodes(API(), row, corpus_version=VERSION), (10, 12, 14),
        )
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), row, corpus_version="0.3.0")
        with self.assertRaisesRegex(MappingError, "required TF"):
            class Missing(API):
                def Fs(self, feature):
                    raise KeyError(feature)
            resolve_nodes(Missing(), row)

    def test_token_category_corresponds_to_corpus_without_word_identity(self):
        c = MappingCatalog()
        joins = c.find_correspondences(
            CORPUS, "pseudepigrapha", kind="node",
            node="word", feature="trans",
        )
        self.assertEqual(
            {(j.target, j.scope, j.relation) for j in joins},
            {(TOKEN, "category", "exact")},
        )
        self.assertEqual(
            {j.destination.node for j in joins},
            {"word", "variant_word"},
        )


if __name__ == "__main__":
    unittest.main()
