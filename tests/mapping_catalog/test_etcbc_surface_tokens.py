"""Source-attested ETCBC word tokens mapped by populated TF surface forms."""
from __future__ import annotations

import unittest
from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

TOKEN = "http://purl.org/olia/olia.owl#Token"
# Frozen R-005 evidence: corpus, TF version, surface feature, source pin,
# observed non-null source-feature values, total native word slots.
CASES = (
    ("bhsa", "2021", "g_word", "4db00e2157915495e1a4d3d57e41223df24775da", 426590, 426590),
    ("extrabiblical", "0.2", "g_word", "9a56288e6777bad6328856acf055c780e65dd5d9", 39560, 39862),
    ("syriac", "0.9", "g_cons_utf8", "bb0eaa7e21b020a26b7566d2e495da9b1f84a919", 359508, 360193),
    ("syrnt", "0.1", "word", "dae3eb6ff62b9b272fb503646796c25d248175ce", 109640, 109640),
)


class EtcSourceTokensTests(unittest.TestCase):
    def test_each_pinned_real_surface_feature_has_one_exact_node_class(self):
        catalog = MappingCatalog()
        for corpus, version, feature, sha, count, total in CASES:
            with self.subTest(corpus=corpus):
                rows = catalog.map_native(
                    corpus, kind="node", node="word", feature=feature,
                    corpus_version=version,
                )
                self.assertEqual(len(rows), 1)
                self.assertEqual(
                    (rows[0].relation, rows[0].target, rows[0].corpus_version),
                    ("exact", TOKEN, version),
                )
                self.assertIn(sha, rows[0].evidence)
                self.assertIn(rows[0], catalog.find_by_target(
                    TOKEN, corpus=corpus, kind="node",
                ))
                # No unconditional category assertion on potentially empty slots.
                self.assertEqual(catalog.map_native(
                    corpus, kind="node", node="word",
                ), ())
                self.assertEqual(catalog.map_native(
                    corpus, kind="entity", node="word",
                    feature=feature, value="same spelling",
                ), ())
                self.assertGreater(count, 0)
                self.assertLessEqual(count, total)

    def test_native_tf_execution_only_selects_populated_carriers(self):
        catalog = MappingCatalog()

        class Otype:
            def s(self, kind):
                assert kind == "word"
                return (1, 2, 3, 4)

        class Surf:
            def v(self, node):
                return {1: "ܡܠܬܐ", 2: None, 3: "", 4: "בָּרָא"}[node]

        class API:
            class F:
                otype = Otype()

            def Fs(self, feature):
                assert feature in {x[2] for x in CASES}
                return Surf()

        api = API()
        for corpus, version, feature, _, _, _ in CASES:
            with self.subTest(corpus=corpus):
                row = catalog.map_native(
                    corpus, kind="node", node="word", feature=feature
                )[0]
                self.assertEqual(
                    resolve_nodes(api, row, corpus_version=version), (1, 4),
                )
                with self.assertRaisesRegex(
                    MappingError, "loaded corpus version"
                ):
                    resolve_nodes(api, row, corpus_version="wrong")

    def test_exact_categories_join_but_do_not_identify_occurrences(self):
        catalog = MappingCatalog()
        for corpus, _, feature, _, _, _ in CASES:
            for destination in ("pseudepigrapha", "bhsa", "syrnt"):
                if destination == corpus:
                    continue
                with self.subTest(corpus=corpus, destination=destination):
                    joins = catalog.find_correspondences(
                        corpus, destination, kind="node",
                        node="word", feature=feature,
                    )
                    self.assertTrue(joins)
                    self.assertEqual({j.target for j in joins}, {TOKEN})
                    self.assertEqual(
                        {(j.relation, j.scope) for j in joins},
                        {("exact", "category")},
                    )


if __name__ == "__main__":
    unittest.main()
