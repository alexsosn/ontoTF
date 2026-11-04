"""CUC and ORACC source-token mappings without reading/glyph identity shortcuts."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

TOKEN = "http://purl.org/olia/olia.owl#Token"
CASES = (
    ("cuc", "0.2.8", "g_cons", "ad69400f5446e1c8217af01659c7c10ab00c015b", 27242, 27770),
    ("assyrian-royal-inscriptions", "1.0.0", "form", "60db4b724a687c0f425e78eae924fce89454e106", 320975, 320975),
)


class CUCOraccSourceTokens(unittest.TestCase):
    def test_source_word_surface_selectors_are_exact_and_bounded(self):
        c = MappingCatalog()
        for corpus, version, feature, sha, observed, total in CASES:
            with self.subTest(corpus=corpus):
                m = c.map_native(corpus, kind="node", node="word",
                                 feature=feature, corpus_version=version)
                self.assertEqual(len(m), 1)
                self.assertEqual((m[0].relation, m[0].target, m[0].corpus_version),
                                 ("exact", TOKEN, version))
                self.assertIn(sha, m[0].evidence)
                self.assertIn(m[0], c.find_by_target(TOKEN, corpus=corpus,
                                                      kind="node"))
                self.assertEqual(c.map_native(corpus, kind="node",
                                               node="word"), ())
                self.assertEqual(c.map_native(corpus, kind="entity",
                                               node="word", feature=feature,
                                               value="x"), ())
                self.assertGreater(observed, 0)
                self.assertLessEqual(observed, total)

    def test_cuc_frozen_source_census_and_oracc_source_word_count(self):
        repo = Path(__file__).resolve().parents[2]
        cuc = json.loads((repo / "docs" / "research" / "data" / "generated"
                          / "r005" / "cuc.json").read_text(encoding="utf-8"))
        self.assertEqual(cuc["revision"], CASES[0][3])
        self.assertEqual(cuc["tf_version"], CASES[0][1])
        self.assertEqual(cuc["node_types"]["word"], CASES[0][5])
        self.assertEqual(cuc["node_features"]["g_cons"]["nodes_with_value"], CASES[0][4])
        # ORACC 1.0.0 is not locally bundled: its pinned primary
        # docs/reference/words-and-lexemes.md and
        # docs/reference/features/word/form.md independently report
        # 320975 word nodes and 320975 form values. That source check
        # belongs to adversarial review, not a tautological local assertion.

    def test_real_tf_node_execution_does_not_promote_empty_surfaces(self):
        class Otype:
            def s(self, kind):
                assert kind == "word"
                return (1, 2, 3, 4)
        class Surface:
            def v(self, n):
                return {1: "x", 2: None, 3: "u₃", 4: ""}[n]
        class API:
            class F:
                otype = Otype()
            def Fs(self, feature):
                assert feature in {"form", "g_cons"}
                return Surface()
        c = MappingCatalog()
        for corpus, version, feature, _, _, _ in CASES:
            with self.subTest(corpus=corpus):
                m = c.map_native(corpus, kind="node", node="word",
                                 feature=feature)[0]
                self.assertEqual(resolve_nodes(API(), m,
                                               corpus_version=version), (1, 3))
                with self.assertRaisesRegex(MappingError, "loaded corpus version"):
                    resolve_nodes(API(), m, corpus_version="wrong")

    def test_cross_corpus_category_join_has_no_word_identity_claim(self):
        c = MappingCatalog()
        for corpus, _, feature, _, _, _ in CASES:
            found = c.find_correspondences(corpus, "pseudepigrapha",
                kind="node", node="word", feature=feature)
            self.assertTrue(found)
            self.assertEqual({(m.target, m.scope, m.relation) for m in found},
                             {(TOKEN, "category", "exact")})


if __name__ == "__main__":
    unittest.main()
