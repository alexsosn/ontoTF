"""Pinned ETCBC ExtraBiblical nominal-state categories with no forged state classes."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#StatusConstructus"
PIN = "9a56288e6777bad6328856acf055c780e65dd5d9"
EXPECTED = {"a": ("native-only", None), "c": ("exact", OLIA),
            "e": ("native-only", None), "NA": ("native-only", None)}


class ExtraBiblicalConstructStateTests(unittest.TestCase):
    def test_pinned_real_tf_vocabulary_and_counts(self):
        inventory = json.loads((
            Path(__file__).resolve().parents[2]
            / "docs/research/data/generated/r005/extrabiblical.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(inventory["revision"], PIN)
        self.assertEqual(inventory["tf_version"], "0.2")
        state = inventory["node_features"]["st"]
        self.assertEqual(state["applies_to"], ["word"])
        self.assertEqual(state["observed_frequencies"],
                         {"NA": 22964, "a": 9970, "c": 6919, "e": 9})
        self.assertEqual(state["observation_count"], 39862)

    def test_full_source_state_domain_with_conservative_unmapped_values(self):
        catalog = MappingCatalog()
        rows = [r for r in catalog.load("extrabiblical")
                if r.kind == "value" and r.node == "word" and r.feature == "st"]
        self.assertEqual(len(rows), 4)
        self.assertEqual({r.value for r in rows}, set(EXPECTED))
        for value, decision in EXPECTED.items():
            with self.subTest(value=value):
                row, = catalog.map_native(
                    "extrabiblical", node="word", feature="st", value=value,
                    corpus_version="0.2")
                self.assertEqual((row.relation, row.target), decision)
                self.assertEqual(row.corpus_version, "0.2")
                self.assertIn(PIN, row.evidence or "")

    def test_exact_reversible_word_category_joins_in_three_corpora(self):
        cat = MappingCatalog()
        source, = cat.map_native(
            "extrabiblical", node="word", feature="st", value="c")
        self.assertIn(source, cat.find_by_target(OLIA, corpus="extrabiblical"))
        for corpus, code in (("bhsa", "c"), ("syriac", "cst"),
                             ("syrnt", "construct")):
            with self.subTest(corpus=corpus):
                forward = cat.find_correspondences(
                    "extrabiblical", corpus, node="word", feature="st", value="c")
                self.assertEqual(
                    {(x.destination.node, x.destination.feature,
                      x.destination.value, x.relation, x.scope) for x in forward},
                    {("word", "st", code, "exact", "category")})
                backward = cat.find_correspondences(
                    corpus, "extrabiblical", node="word", feature="st", value=code)
                self.assertEqual(
                    {(x.destination.feature, x.destination.value, x.relation)
                     for x in backward},
                    {("st", "c", "exact")})
        self.assertEqual(cat.map_native(
            "extrabiblical", kind="entity", node="word", feature="st",
            value="c"), ())

    def test_unknown_absolute_and_emphatic_do_not_forge_equivalences(self):
        cat = MappingCatalog()
        for value in ("NA", "a", "e"):
            with self.subTest(value=value):
                self.assertEqual(cat.find_correspondences(
                    "extrabiblical", "bhsa", node="word", feature="st",
                    value=value, include_approximate=True), ())
                self.assertEqual(cat.find_correspondences(
                    "extrabiblical", "syriac", node="word", feature="st",
                    value=value, include_approximate=True), ())

    def test_execute_exact_native_selector_with_version_guard(self):
        cat = MappingCatalog()
        m, = cat.map_native("extrabiblical", node="word", feature="st", value="c")
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(node_type):
                        assert node_type == "word"
                        return (7, 8, 9, 10, 11)
            @staticmethod
            def Fs(feature):
                assert feature == "st"
                class State:
                    @staticmethod
                    def v(node):
                        return {7: "a", 8: "c", 9: "NA",
                                10: "c", 11: "e"}[node]
                return State()
        self.assertEqual(resolve_nodes(API(), m, corpus_version="0.2"),
                         (8, 10))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), m, corpus_version="2021")


if __name__ == "__main__":
    unittest.main()
