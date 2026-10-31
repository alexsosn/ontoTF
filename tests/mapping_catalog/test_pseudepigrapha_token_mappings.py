"""Pinned Pseudepigrapha source tokens vs TF synthetic slots and textual versions."""
from __future__ import annotations

import unittest
from dataclasses import replace
from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

TOKEN = "http://purl.org/olia/olia.owl#Token"
PIN = "7c4b757bb543a110ae9a252d1281835859136852"
TF_VERSION = "1.0"


class PseudepigraphaObservedMappingsTests(unittest.TestCase):
    def test_variant_word_is_a_source_token_category_only(self):
        catalog = MappingCatalog()
        self.assertIn("pseudepigrapha", catalog.list_corpora())
        rows = catalog.map_native(
            "pseudepigrapha", kind="node", node="variant_word"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            (rows[0].relation, rows[0].target, rows[0].corpus_version),
            ("exact", TOKEN, TF_VERSION),
        )
        self.assertIn(PIN, rows[0].evidence)
        # The reverse category lookup includes both source-backed forms:
        # alternative variant_word tokens and text-bearing primary words.
        found = catalog.find_by_target(
            TOKEN, corpus="pseudepigrapha", kind="node"
        )
        self.assertEqual(
            {(m.node, m.feature, m.relation, m.target) for m in found},
            {
                ("variant_word", None, "exact", TOKEN),
                ("word", "g_word_utf8", "exact", TOKEN),
            },
        )
        self.assertIn(rows[0], found)
        self.assertEqual(
            catalog.map_native("pseudepigrapha", kind="entity",
                               node="variant_word", feature="g_word_utf8",
                               value="same spelling"),
            (),
        )
        with self.assertRaises(MappingError):
            catalog.map_native("pseudepigrapha", kind="node",
                               node="variant_word", corpus_version="0.9")

    def test_gap_anchor_and_nontext_carriers_do_not_become_tokens(self):
        catalog = MappingCatalog()
        for node in ("word", "reading", "manuscript", "book"):
            with self.subTest(node=node):
                rows = catalog.map_native(
                    "pseudepigrapha", kind="node", node=node)
                self.assertEqual(len(rows), 1)
                self.assertEqual((rows[0].relation, rows[0].target),
                                 ("native-only", None))
        rows = catalog.map_native(
            "pseudepigrapha", kind="value", node="word",
            feature="is_gap", value="1"
        )
        self.assertEqual(
            [(r.relation, r.target) for r in rows],
            [("native-only", None)],
        )
        self.assertEqual(
            catalog.find_correspondences(
                "pseudepigrapha", "bhsa",
                kind="node", node="word"
            ), (),
        )

    def test_source_versions_and_source_edges_are_not_expression_identity(self):
        catalog = MappingCatalog()
        for value in ("source", "generated_translation"):
            with self.subTest(version_kind=value):
                rows = catalog.map_native(
                    "pseudepigrapha", node="book",
                    feature="version_kind", value=value)
                self.assertEqual(
                    [(r.relation, r.target) for r in rows],
                    [("native-only", None)]
                )
        for edge, source, target in (
            ("translation_of", "book", "book"),
            ("variant_word_of", "variant_word", "reading"),
        ):
            with self.subTest(edge=edge):
                rows = catalog.map_native(
                    "pseudepigrapha", kind="edge",
                    feature=edge, from_node=source, to_node=target,
                )
                self.assertEqual(
                    [(r.relation, r.target) for r in rows],
                    [("native-only", None)],
                )


    def test_execute_reviewed_node_kind_on_real_tf_api_shape(self):
        catalog = MappingCatalog()

        class Otype:
            def s(self, kind):
                if kind == "variant_word":
                    return (101, 103, 107)
                if kind == "lex":
                    return (400, 401)
                return ()

        class API:
            class F:
                otype = Otype()

            def Fs(self, feature):
                raise AssertionError("node category must not request a feature")

        api = API()
        token = catalog.map_native(
            "pseudepigrapha", kind="node", node="variant_word"
        )[0]
        self.assertEqual(
            resolve_nodes(api, token, corpus_version="1.0"),
            (101, 103, 107),
        )
        entry = catalog.map_native("bhsa", kind="node", node="lex")[0]
        self.assertEqual(resolve_nodes(api, entry), (400, 401))
        # A TF node type is a category, never lexical/token identity.
        with self.assertRaisesRegex(MappingError, "positive"):
            resolve_nodes(
                api, catalog.map_native(
                    "pseudepigrapha", kind="node", node="word"
                )[0],
            )
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(api, token, corpus_version="0.9")

        # Approximate/related category associations cannot silently become
        # executable node-set equivalence without explicit opt-in semantics.
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(api, replace(token, relation="related"))
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(api, replace(token, relation="narrower"))

        class NoOtype:
            class F:
                pass

        with self.assertRaisesRegex(MappingError, "required TF"):
            resolve_nodes(NoOtype(), token)


    def test_surface_bearing_primary_word_nodes_exclude_empty_gaps(self):
        catalog = MappingCatalog()
        positive = catalog.map_native(
            "pseudepigrapha", kind="node",
            node="word", feature="g_word_utf8"
        )
        self.assertEqual(
            [(m.relation, m.target) for m in positive],
            [("exact", TOKEN)],
        )
        self.assertEqual(
            {x.node for x in catalog.find_by_target(
                TOKEN, kind="node", corpus="pseudepigrapha"
            )},
            {"word", "variant_word"},
        )

        class Otype:
            def s(self, kind):
                assert kind == "word"
                return (1, 2, 3, 4)

        class Surface:
            def v(self, n):
                return {1: "λόγος", 2: None, 3: "ܡܠܬܐ", 4: ""}[n]

        class API:
            class F:
                otype = Otype()

            def Fs(self, name):
                assert name == "g_word_utf8"
                return Surface()

        self.assertEqual(resolve_nodes(API(), positive[0], corpus_version="1.0"),
                         (1, 3))
        # The unconditional word kind includes empty source anchors and cannot
        # be promoted without the verified feature-presence precondition.
        self.assertEqual(
            [(m.relation, m.target) for m in catalog.map_native(
                "pseudepigrapha", kind="node", node="word"
            )],
            [("native-only", None)],
        )
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), positive[0], corpus_version="0.9")
        with self.assertRaisesRegex(MappingError, "required TF"):
            class MissingSurface(API):
                def Fs(self, name):
                    raise KeyError(name)
            resolve_nodes(MissingSurface(), positive[0])


if __name__ == "__main__":
    unittest.main()
