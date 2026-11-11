"""Phrase-dependent POS is an attested word-context annotation, not lexeme POS.

Both ETCBC BHSA and BHSA-family ExtraBiblical use the same pinned pdp
codebook. The source word.sp and word.pdp values can differ, and the two
native selectors must remain distinguishable in ontology queries.
"""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#"
PINS = {
    "bhsa": ("4db00e2157915495e1a4d3d57e41223df24775da", "2021", 426590),
    "extrabiblical": ("9a56288e6777bad6328856acf055c780e65dd5d9", "0.2", 39862),
}
POS = {
    "adjv": {"Adjective"}, "advb": {"Adverb"}, "art": {"Article"},
    "conj": {"Conjunction"}, "inrg": {"InterrogativeParticle"},
    "intj": {"Interjection"}, "nega": {"NegativeParticle"},
    "nmpr": {"Noun", "ProperNoun"},
    "prde": {"DemonstrativePronoun"}, "prep": {"Preposition"},
    "prin": {"InterrogativePronoun"}, "subs": {"Noun"}, "verb": {"Verb"},
}
NATIVE_VALUES = set(POS) | {"prps"}


class PhraseDependentPartOfSpeechMappingsTests(unittest.TestCase):
    def test_pinned_contextual_pos_is_on_words_and_full_codebook_matches(self):
        for corpus, (revision, version, denominator) in PINS.items():
            with self.subTest(corpus=corpus):
                census = json.loads((
                    Path(__file__).resolve().parents[2]
                    / f"docs/research/data/generated/r005/{corpus}.json"
                ).read_text(encoding="utf-8"))
                self.assertEqual((census["revision"], census["tf_version"]),
                                 (revision, version))
                native = census["node_features"]["pdp"]
                self.assertEqual(native["applies_to"], ["word"])
                self.assertEqual(native["observation_count"], denominator)
                self.assertEqual(set(native["observed_values"]), NATIVE_VALUES)
                self.assertEqual(sum(native["observed_frequencies"].values()),
                                 denominator)
                self.assertEqual(native["observed_unique_count"], 14)
                self.assertEqual(native["observed_frequencies"]["prps"],
                                 4508 if corpus == "bhsa" else 4368)
                self.assertEqual(native["observed_frequencies"]["subs"],
                                 125457 if corpus == "bhsa" else 12560)

    def test_every_contextual_pos_value_has_the_pinned_reviewed_ontology(self):
        catalog = MappingCatalog()
        for corpus, (revision, version, denominator) in PINS.items():
            with self.subTest(corpus=corpus):
                rows = [m for m in catalog.load(corpus)
                        if m.kind == "value" and m.node == "word"
                        and m.feature == "pdp"]
                self.assertEqual(len(rows), 15)
                self.assertEqual({r.value for r in rows}, NATIVE_VALUES)
                conservative = ({"prps", "nega", "inrg"} if
                                corpus == "extrabiblical" else {"prps"})
                self.assertEqual(
                    {r.value for r in rows if r.relation != "exact"},
                    conservative)
                for value in NATIVE_VALUES:
                    matches = catalog.map_native(
                        corpus, node="word", feature="pdp", value=value,
                        corpus_version=version)
                    if corpus == "extrabiblical" and value in {"nega", "inrg"}:
                        expected = {("native-only", None)}
                    elif value == "prps":
                        expected = {("narrower", OLIA + "Pronoun")}
                    else:
                        expected = {("exact", OLIA + cls)
                                    for cls in POS[value]}
                    self.assertEqual(
                        {(m.relation, m.target) for m in matches}, expected)
                    self.assertTrue(all(
                        m.corpus_version == version
                        and revision in (m.evidence or "")
                        for m in matches
                    ))
                self.assertEqual(
                    catalog.map_native(corpus, kind="value", node="lex",
                                       feature="pdp", value="verb"), ())

    def test_contextual_and_lexical_pos_remain_distinguishable(self):
        catalog = MappingCatalog()
        source, = catalog.map_native(
            "bhsa", node="word", feature="pdp", value="adjv")
        self.assertEqual((source.relation, source.target),
                         ("exact", OLIA + "Adjective"))
        matches = catalog.find_correspondences(
            "bhsa", "extrabiblical", node="word",
            feature="pdp", value="adjv")
        self.assertEqual(
            {(m.destination.node, m.destination.feature, m.destination.value,
              m.relation, m.scope) for m in matches},
            {("word", "sp", "adjv", "exact", "category"),
             ("word", "pdp", "adjv", "exact", "category")},
        )
        # The same ontology class can be reported from both native features;
        # source provenance is preserved, no rule rewrites sp to pdp.
        self.assertTrue(all(m.source.feature == "pdp" for m in matches))
        self.assertEqual(catalog.map_native(
            "bhsa", kind="entity", node="word", feature="pdp", value="adjv"), ())
        other = catalog.find_correspondences(
            "bhsa", "syrnt", node="word", feature="pdp", value="verb")
        self.assertIn(
            ("sp", "verb", "exact", "category"),
            {(m.destination.feature, m.destination.value, m.relation, m.scope)
             for m in other},
        )

    def test_personal_pronoun_remains_a_qualified_general_category(self):
        catalog = MappingCatalog()
        for corpus in PINS:
            with self.subTest(corpus=corpus):
                m, = catalog.map_native(
                    corpus, node="word", feature="pdp", value="prps")
                self.assertEqual((m.relation, m.target),
                                 ("narrower", OLIA + "Pronoun"))
                self.assertNotIn(
                    m, catalog.find_by_target(OLIA + "Pronoun", corpus=corpus))
                self.assertIn(
                    m, catalog.find_by_target(
                        OLIA + "Pronoun", corpus=corpus,
                        include_approximate=True))
                self.assertEqual(catalog.find_by_target(
                    OLIA + "PersonalPronoun", corpus=corpus,
                    include_approximate=True), ())
        self.assertEqual(catalog.find_correspondences(
            "bhsa", "syrnt", node="word", feature="pdp",
            value="prps"), ())
        mapped = catalog.find_correspondences(
            "bhsa", "syrnt", node="word", feature="pdp",
            value="prps", include_approximate=True)
        self.assertTrue(any(
            r.target == OLIA + "Pronoun"
            and r.destination.feature == "sp"
            and r.destination.value == "pronoun"
            and r.relation == "approximate-via-target"
            and r.scope == "category"
            for r in mapped
        ))

    def test_extra_contextual_negation_and_interrogative_particle_stay_native_only(self):
        catalog = MappingCatalog()
        for value in ("nega", "inrg"):
            with self.subTest(value=value):
                self.assertEqual(catalog.find_correspondences(
                    "extrabiblical", "bhsa", node="word", feature="pdp",
                    value=value, include_approximate=True), ())
                self.assertEqual(catalog.map_native(
                    "extrabiblical", kind="entity", node="word",
                    feature="pdp", value=value), ())

    def test_exact_contextual_selector_selects_words_not_lexemes(self):
        m, = MappingCatalog().map_native(
            "extrabiblical", node="word", feature="pdp", value="subs")
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(kind):
                        assert kind == "word"
                        return (1, 2, 3, 4, 5)
            @staticmethod
            def Fs(feature):
                assert feature == "pdp"
                class Values:
                    @staticmethod
                    def v(n):
                        return {1: "subs", 2: "verb", 3: "subs",
                                4: "adjv", 5: "prps"}[n]
                return Values()
        self.assertEqual(resolve_nodes(API(), m, corpus_version="0.2"),
                         (1, 3))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), m, corpus_version="2021")
        qualified, = MappingCatalog().map_native(
            "extrabiblical", node="word", feature="pdp", value="prps")
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(API(), qualified, corpus_version="0.2")


if __name__ == "__main__":
    unittest.main()
