"""ETCBC BHSA lexeme POS and conservatively qualified personal pronouns.

Grounding: ETCBC/bhsa@4db00e2 docs/features/sp.md explicitly declares
sp on BOTH word and lex (part-of-speech a word, or rather lexeme, belongs to).
R-005 is a pinned union-domain census; it does NOT provide POS counts per lex.
"""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#"
BHSA_PIN = "4db00e2157915495e1a4d3d57e41223df24775da"
EXTRA_PIN = "9a56288e6777bad6328856acf055c780e65dd5d9"

# Codebook interpretation independently taken from pinned ETCBC sp.md and
# reviewed existing word.sp maps. nmpr is both Noun and ProperNoun; prps
# is a strict pronoun SUBTYPE, not an exact OLiA PersonalPronoun.
EXACT = {
    "adjv": {"Adjective"}, "advb": {"Adverb"}, "art": {"Article"},
    "conj": {"Conjunction"}, "inrg": {"InterrogativeParticle"},
    "intj": {"Interjection"}, "nega": {"NegativeParticle"},
    "nmpr": {"Noun", "ProperNoun"},
    "prde": {"DemonstrativePronoun"}, "prep": {"Preposition"},
    "prin": {"InterrogativePronoun"}, "subs": {"Noun"},
    "verb": {"Verb"},
}
VALUES = set(EXACT) | {"prps"}


class BHSALexemePartOfSpeechTests(unittest.TestCase):
    def test_pinned_feature_exists_on_both_source_node_types(self):
        census = json.loads((
            Path(__file__).resolve().parents[2]
            / "docs/research/data/generated/r005/bhsa.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual((census["revision"], census["tf_version"]),
                         (BHSA_PIN, "2021"))
        self.assertEqual((census["node_types"]["lex"],
                          census["node_types"]["word"]), (9230, 426590))
        source = census["node_features"]["sp"]
        self.assertEqual(source["applies_to"], ["lex", "word"])
        self.assertEqual(source["observation_count"], 435820)
        self.assertEqual(set(source["observed_values"]), VALUES)
        self.assertEqual(source["metadata"]["provenance"],
                         "from additional lexicon file provided by the ETCBC")

    def test_every_pinned_lexeme_pos_code_has_reviewer_selected_disposition(self):
        catalog = MappingCatalog()
        rows = [r for r in catalog.load("bhsa")
                if r.kind == "value" and r.node == "lex" and r.feature == "sp"]
        self.assertEqual(len(rows), 15)
        self.assertEqual({r.value for r in rows}, VALUES)
        for value in VALUES:
            with self.subTest(code=value):
                mappings = catalog.map_native(
                    "bhsa", node="lex", feature="sp", value=value,
                    corpus_version="2021")
                expected = ({("exact", OLIA + name) for name in EXACT[value]}
                            if value in EXACT else
                            {("narrower", OLIA + "Pronoun")})
                self.assertEqual({(r.relation, r.target) for r in mappings},
                                 expected)
                self.assertTrue(all(r.corpus_version == "2021"
                                    and BHSA_PIN in (r.evidence or "")
                                    for r in mappings))
        self.assertEqual(
            catalog.map_native("bhsa", kind="entity",
                               node="lex", feature="sp", value="nmpr"), ())

    def test_lexeme_pos_correspondences_retain_source_and_target_types(self):
        catalog = MappingCatalog()
        for other, other_value in (("syriac", "verb"),
                                   ("extrabiblical", "verb"),
                                   ("syrnt", "verb")):
            with self.subTest(other=other):
                rows = catalog.find_correspondences(
                    "bhsa", other, node="lex", feature="sp", value="verb")
                got = {
                    (x.source.node, x.destination.node,
                     x.destination.feature, x.destination.value,
                     x.relation, x.scope) for x in rows
                }
                self.assertIn(
                    ("lex", "word", "sp", other_value, "exact", "category"),
                    got,
                )
                # Contextual pdp, if independently mapped later, may
                # legitimately provide a second word POS selector. Do not
                # force one native feature per ontology category.
                self.assertTrue(all(
                    x.source.node == "lex"
                    and x.destination.node == "word"
                    and x.target == OLIA + "Verb"
                    and x.relation == "exact" and x.scope == "category"
                    for x in rows
                ))
        proper = catalog.map_native(
            "bhsa", node="lex", feature="sp", value="nmpr")
        self.assertEqual(
            {x.target for x in proper},
            {OLIA + "Noun", OLIA + "ProperNoun"},
        )
        for other in ("syriac", "extrabiblical"):
            matches = catalog.find_correspondences(
                "bhsa", other, node="lex", feature="sp", value="nmpr")
            self.assertTrue(matches)
            self.assertEqual({x.target for x in matches},
                             {OLIA + "Noun", OLIA + "ProperNoun"})
            self.assertTrue(all(x.scope == "category" and x.relation == "exact"
                                for x in matches))

    def test_personal_pronouns_are_subset_of_general_pronoun_not_exact_subtype(self):
        catalog = MappingCatalog()
        for corpus, kind in (("bhsa", "lex"), ("bhsa", "word"),
                             ("extrabiblical", "word")):
            with self.subTest(corpus=corpus, node=kind):
                row, = catalog.map_native(
                    corpus, node=kind, feature="sp", value="prps")
                self.assertEqual((row.relation, row.target),
                                 ("narrower", OLIA + "Pronoun"))
                self.assertIn(BHSA_PIN if corpus == "bhsa" else EXTRA_PIN,
                              row.evidence or "")
                self.assertNotIn(row, catalog.find_by_target(
                    OLIA + "Pronoun", corpus=corpus))
                self.assertIn(row, catalog.find_by_target(
                    OLIA + "Pronoun", corpus=corpus,
                    include_approximate=True))
        for corpus in ("bhsa", "extrabiblical"):
            self.assertEqual(catalog.find_by_target(
                OLIA + "PersonalPronoun", corpus=corpus,
                include_approximate=True), ())
        self.assertEqual(catalog.find_correspondences(
            "bhsa", "syrnt", node="lex", feature="sp", value="prps"), ())
        qualified = catalog.find_correspondences(
            "bhsa", "syrnt", node="lex", feature="sp", value="prps",
            include_approximate=True)
        self.assertIn(
            ("word", "sp", "pronoun", "approximate-via-target", "category"),
            {(r.destination.node, r.destination.feature, r.destination.value,
              r.relation, r.scope) for r in qualified},
        )
        # Same target at word and lex type does not imply same individual.
        self.assertEqual(catalog.find_correspondences(
            "bhsa", "extrabiblical", kind="entity",
            node="lex", feature="sp", value="prps",
            include_approximate=True), ())

    def test_exact_lexical_pos_can_select_tf_lexeme_nodes(self):
        catalog = MappingCatalog()
        exact, = catalog.map_native(
            "bhsa", node="lex", feature="sp", value="verb")
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(kind):
                        assert kind == "lex"
                        return (20, 21, 22, 23)
            @staticmethod
            def Fs(feature):
                assert feature == "sp"
                class Values:
                    @staticmethod
                    def v(n):
                        return {20: "verb", 21: "subs",
                                22: "verb", 23: "prps"}[n]
                return Values()
        self.assertEqual(resolve_nodes(API(), exact,
                                       corpus_version="2021"), (20, 22))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), exact, corpus_version="2025")
        # Qualified crosswalk discovery never silently executes as exact.
        personal, = catalog.map_native(
            "bhsa", node="lex", feature="sp", value="prps")
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(API(), personal, corpus_version="2021")


if __name__ == "__main__":
    unittest.main()
