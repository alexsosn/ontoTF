"""Pinned SyrNT demonstrative categories and safe non-exact execution.

Original TF 0.1 sp/prtyp/demcat word features were independently cross-tabulated;
near+far partition exactly the 5,043 demonstrative pronouns (not the entire
109,640-word corpus).  Narrower mappings are discoverable, not executable.
"""
from dataclasses import replace
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#DemonstrativePronoun"
PIN = "dae3eb6ff62b9b272fb503646796c25d248175ce"


class SyrNTDemonstrativeMappingsTests(unittest.TestCase):
    def test_pinned_observed_value_denominators(self):
        inventory = json.loads((
            Path(__file__).resolve().parents[2]
            / "docs/research/data/generated/r005/syrnt.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(inventory["revision"], PIN)
        self.assertEqual(inventory["tf_version"], "0.1")
        self.assertEqual(inventory["node_features"]["prtyp"]["observed_frequencies"], {
            "NA": 99413, "demonstrative": 5043,
            "interrogative": 2011, "personal": 3173,
        })
        self.assertEqual(inventory["node_features"]["demcat"]["observed_frequencies"], {
            "NA": 104597, "far": 3397, "near": 1646,
        })

    def test_reviewed_category_dispositions_and_source_scope(self):
        catalog = MappingCatalog()
        expected = {
            ("prtyp", "demonstrative"): ("exact", OLIA),
            ("prtyp", "interrogative"): (
                "exact", "http://purl.org/olia/olia.owl#InterrogativePronoun"),
            ("prtyp", "personal"): ("narrower", "http://purl.org/olia/olia.owl#Pronoun"),
            ("prtyp", "NA"): ("native-only", None),
            ("demcat", "near"): ("narrower", OLIA),
            ("demcat", "far"): ("narrower", OLIA),
            ("demcat", "NA"): ("native-only", None),
        }
        rows = [r for r in catalog.load("syrnt")
                if r.kind == "value" and r.node == "word"
                and r.feature in {"prtyp", "demcat"}]
        self.assertEqual(len(rows), len(expected))
        self.assertEqual({(r.feature, r.value) for r in rows}, set(expected))
        for (feature, value), decision in expected.items():
            with self.subTest(feature=feature, value=value):
                m, = catalog.map_native("syrnt", node="word", feature=feature,
                                        value=value, corpus_version="0.1")
                self.assertEqual((m.relation, m.target), decision)
                self.assertEqual(m.corpus_version, "0.1")
                self.assertIn(PIN, m.evidence or "")

    def test_exact_and_opt_in_narrower_lookup_are_distinguished(self):
        catalog = MappingCatalog()
        exact = catalog.find_by_target(OLIA, corpus="syrnt")
        self.assertEqual([(x.feature, x.value, x.relation) for x in exact],
                         [("prtyp", "demonstrative", "exact")])
        all_results = catalog.find_by_target(
            OLIA, corpus="syrnt", include_approximate=True)
        self.assertEqual(
            {(x.feature, x.value, x.relation) for x in all_results},
            {("prtyp", "demonstrative", "exact"),
             ("demcat", "near", "narrower"),
             ("demcat", "far", "narrower")},
        )
        for destination in ("bhsa", "extrabiblical"):
            with self.subTest(destination=destination):
                full = catalog.find_correspondences(
                    "syrnt", destination, node="word",
                    feature="prtyp", value="demonstrative")
                # The earlier BHSA lexeme-POS mapping legitimately adds
                # lex.sp=prde as a third category destination, whereas
                # ExtraBiblical has only word nodes. Keep both source paths.
                observed = {
                    (x.destination.node, x.destination.feature,
                     x.destination.value, x.relation, x.scope)
                    for x in full
                }
                required = {
                    ("word", "sp", "prde", "exact", "category"),
                    ("word", "pdp", "prde", "exact", "category"),
                }
                permitted = required | ({
                    ("lex", "sp", "prde", "exact", "category")
                } if destination == "bhsa" else set())
                self.assertTrue(required <= observed)
                self.assertTrue(observed <= permitted)
                for distance in ("near", "far"):
                    self.assertEqual(catalog.find_correspondences(
                        "syrnt", destination, node="word",
                        feature="demcat", value=distance), ())
                    tentative = catalog.find_correspondences(
                        "syrnt", destination, node="word", feature="demcat",
                        value=distance, include_approximate=True)
                    observed_approx = {
                        (x.destination.node, x.destination.feature,
                         x.destination.value, x.relation,
                         x.source.relation, x.scope)
                        for x in tentative
                    }
                    required_approx = {
                        ("word", "sp", "prde", "approximate-via-target",
                         "narrower", "category"),
                        ("word", "pdp", "prde", "approximate-via-target",
                         "narrower", "category"),
                    }
                    permitted_approx = required_approx | ({
                        ("lex", "sp", "prde", "approximate-via-target",
                         "narrower", "category")
                    } if destination == "bhsa" else set())
                    self.assertTrue(required_approx <= observed_approx)
                    self.assertTrue(observed_approx <= permitted_approx)
        # Inverse lookup must retain the same strength/direction; a
        # narrower destination is not silently promoted to exact.
        inverse = catalog.find_correspondences(
            "bhsa", "syrnt", node="word", feature="sp", value="prde")
        self.assertEqual(
            {(x.destination.feature, x.destination.value, x.relation)
             for x in inverse},
            {("prtyp", "demonstrative", "exact")},
        )
        # Contextual BHSA pdp is an additional SOURCE category, not
        # identical to lexical sp or to a particular SyrNT word token.
        contextual_inverse = catalog.find_correspondences(
            "bhsa", "syrnt", node="word", feature="pdp", value="prde")
        self.assertEqual(
            {(x.source.feature, x.destination.feature,
              x.destination.value, x.relation, x.scope)
             for x in contextual_inverse},
            {("pdp", "prtyp", "demonstrative", "exact", "category")},
        )
        inverse_approximate = catalog.find_correspondences(
            "bhsa", "syrnt", node="word", feature="sp", value="prde",
            include_approximate=True)
        self.assertEqual(
            {(x.destination.feature, x.destination.value,
              x.destination.relation, x.relation)
             for x in inverse_approximate},
            {("prtyp", "demonstrative", "exact", "exact"),
             ("demcat", "near", "narrower", "approximate-via-target"),
             ("demcat", "far", "narrower", "approximate-via-target")},
        )
        # The 3,173 observed personal-pronoun occurrences are a subset of
        # Pronoun. They do NOT satisfy unverified OLiA PersonalPronoun
        # irreflexivity or entitle callers to exact equivalence.
        base_pronoun = "http://purl.org/olia/olia.owl#Pronoun"
        self.assertEqual(catalog.find_correspondences(
            "syrnt", "syriac", node="word", feature="prtyp", value="personal"), ())
        limited = catalog.find_correspondences(
            "syrnt", "syriac", node="word", feature="prtyp", value="personal",
            include_approximate=True)
        self.assertEqual(
            {(x.destination.feature, x.destination.value, x.target,
              x.source.relation, x.relation, x.scope) for x in limited},
            {("sp", "pron", base_pronoun, "narrower",
              "approximate-via-target", "category")},
        )
        self.assertEqual(
            catalog.find_by_target(
                "http://purl.org/olia/olia.owl#PersonalPronoun",
                corpus="syrnt", include_approximate=True),
            (),
        )
        self.assertIn(
            ("prtyp", "personal", "narrower"),
            {(x.feature, x.value, x.relation) for x in catalog.find_by_target(
                base_pronoun, corpus="syrnt", include_approximate=True)},
        )
        for feature in ("prtyp", "demcat"):
            self.assertEqual(catalog.find_correspondences(
                "syrnt", "bhsa", node="word", feature=feature, value="NA",
                include_approximate=True), ())

    def test_non_exact_value_mappings_cannot_execute_without_authority(self):
        catalog = MappingCatalog()
        exact, = catalog.map_native(
            "syrnt", node="word", feature="prtyp", value="interrogative")
        class MustNotInspect:
            class F:
                class otype:
                    @staticmethod
                    def s(kind):
                        raise AssertionError("non-exact execution reached TF nodes")
        for relation in ("close", "broader", "narrower", "related"):
            with self.subTest(relation=relation):
                with self.assertRaisesRegex(MappingError, "exact"):
                    resolve_nodes(MustNotInspect(), replace(exact,
                        relation=relation), corpus_version="0.1")
        for value in ("near", "far"):
            narrower, = catalog.map_native(
                "syrnt", node="word", feature="demcat", value=value)
            with self.assertRaisesRegex(MappingError, "exact"):
                resolve_nodes(MustNotInspect(), narrower, corpus_version="0.1")

    def test_exact_demonstrative_selects_loaded_word_feature(self):
        catalog = MappingCatalog()
        exact, = catalog.map_native(
            "syrnt", node="word", feature="prtyp", value="demonstrative")
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(kind):
                        assert kind == "word"
                        return (1, 2, 3, 4, 5)
            @staticmethod
            def Fs(feature):
                assert feature == "prtyp"
                class Values:
                    @staticmethod
                    def v(n):
                        return {1: "demonstrative", 2: "interrogative",
                                3: "demonstrative", 4: "NA",
                                5: "personal"}[n]
                return Values()
        self.assertEqual(resolve_nodes(API(), exact, corpus_version="0.1"),
                         (1, 3))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), exact, corpus_version="0.2")


if __name__ == "__main__":
    unittest.main()
