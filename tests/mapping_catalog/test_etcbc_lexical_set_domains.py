"""Source-observed ETCBC Syriac and ExtraBiblical lexical-set domain accounting.

The pinned R-005 real-corpus inventories are the authoritative observed
feature/value denominators; this module deliberately does not infer identities
or finer part-of-speech classes from shared abbreviations or gloss strings.
"""
import unittest

from ontotf.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#"

OBSERVED = {
    "syriac": frozenset({
        "card", "cjad", "demo", "focp", "gntl", "nmex", "ordn", "pcon",
        "pers", "pinr", "pint", "ppre", "prin", "prop", "quot", "sffx", "vbex",
    }),
    "extrabiblical": frozenset({
        "afad", "card", "focp", "gntl", "mult", "nmcp", "nmdi", "none",
        "ordn", "padv", "ppre", "ques", "quot", "sffx", "vbcp",
    }),
}
EXACT = {
    "syriac": {
        "card": "CardinalNumber",
        "ordn": "OrdinalNumber",
        "prop": "ProperNoun",
    },
    "extrabiblical": {
        "card": "CardinalNumber",
        "ordn": "OrdinalNumber",
        "ques": "InterrogativeParticle",
    },
}
PIN = {
    "syriac": "bb0eaa7e21b020a26b7566d2e495da9b1f84a919",
    "extrabiblical": "9a56288e6777bad6328856acf055c780e65dd5d9",
}
QUALIFIED = {
    "extrabiblical": {
        "nmdi": "Noun", "nmcp": "Noun", "mult": "Noun",
        "vbcp": "Verb", "quot": "Verb", "afad": "Adverb",
        "gntl": "Adjective",
    },
    "syriac": {
        "cjad": "Adverb", "gntl": "Adjective", "vbex": "Verb",
        "quot": "Verb", "demo": "Pronoun", "pers": "PersReflPronoun",
        "prin": "Pronoun", "pinr": "Adverb",
    },
}


class ETCBCObservedLexicalSetsTests(unittest.TestCase):
    def test_complete_pinned_observed_domain_with_source_specific_semantics(self):
        catalog = MappingCatalog()
        for corpus in ("syriac", "extrabiblical"):
            version = "0.9" if corpus == "syriac" else "0.2"
            rows = [r for r in catalog.load(corpus)
                    if r.kind == "value" and r.node == "word"
                    and r.feature == "ls" and r.corpus_version == version]
            self.assertEqual(len(rows), len(OBSERVED[corpus]))
            self.assertEqual({r.value for r in rows}, OBSERVED[corpus])
            for value in OBSERVED[corpus]:
                with self.subTest(corpus=corpus, code=value):
                    m = catalog.map_native(
                        corpus, node="word", feature="ls", value=value, corpus_version=version
                    )
                    self.assertEqual(len(m), 1)
                    self.assertIn(PIN[corpus], m[0].evidence)
                    cls = EXACT[corpus].get(value)
                    parent = QUALIFIED.get(corpus, {}).get(value)
                    expected = (("exact", OLIA + cls) if cls
                                else ("narrower", OLIA + parent) if parent
                                else ("native-only", None))
                    self.assertEqual((m[0].relation, m[0].target), expected)

    def test_positive_cross_language_category_not_word_identity(self):
        catalog = MappingCatalog()
        for code, cls in (("card", "CardinalNumber"),
                          ("ordn", "OrdinalNumber")):
            with self.subTest(code=code):
                matching = catalog.find_correspondences(
                    "syriac", "extrabiblical",
                    node="word", feature="ls", value=code,
                    source_version="0.9",
                )
                self.assertEqual(len(matching), 1)
                m = matching[0]
                self.assertEqual(m.target, OLIA + cls)
                self.assertEqual(
                    (m.destination.feature, m.destination.value),
                    ("ls", code),
                )
                self.assertEqual(m.scope, "category")
                self.assertEqual(m.relation, "exact")
        self.assertEqual(
            catalog.map_native("syriac", corpus_version="0.9", kind="entity",
                               node="word", feature="ls", value="card"),
            (),
        )

    def test_source_observed_qualified_subtypes_stay_out_of_exact_queries(self):
        catalog = MappingCatalog()
        for corpus in ("syriac", "extrabiblical"):
            version = "0.9" if corpus == "syriac" else "0.2"
            codes = (QUALIFIED[corpus] if corpus == "syriac"
                     else {"gntl": "Adjective"})
            for code, target in codes.items():
                with self.subTest(corpus=corpus, code=code):
                    row, = catalog.map_native(
                        corpus, node="word", feature="ls", value=code,
                        corpus_version=version,
                    )
                    self.assertEqual(
                        (row.relation, row.target), ("narrower", OLIA + target),
                    )
                    self.assertNotIn(row, catalog.find_by_target(OLIA + target))
                    self.assertIn(row, catalog.find_by_target(
                        OLIA + target, include_approximate=True,
                    ))
                    self.assertEqual(catalog.find_correspondences(
                        corpus, "bhsa", node="word", feature="ls", value=code, source_version=version,
                    ), ())
                    with self.assertRaisesRegex(MappingError, "exact"):
                        resolve_nodes(object(), row, corpus_version=version)
        # 'demo' includes XDD> 'each other' (9 occurrences); never pretend
        # all 3,575 native demo annotations are demonstrative pronouns.
        row, = catalog.map_native(
            "syriac", corpus_version="0.9", node="word", feature="ls", value="demo",
        )
        self.assertNotEqual(row.target, OLIA + "DemonstrativePronoun")
        # OLiA explicitly distinguishes the broad personal/reflexive
        # category from its narrower irreflexive PersonalPronoun.
        pers, = catalog.map_native(
            "syriac", corpus_version="0.9", node="word", feature="ls", value="pers",
        )
        self.assertNotEqual(pers.target, OLIA + "PersonalPronoun")

    def test_unverified_subtypes_and_multitude_do_not_forge_matches(self):
        catalog = MappingCatalog()
        for code in ("pint", "pcon", "focp", "sffx", "nmex", "ppre"):
            with self.subTest(corpus="syriac", code=code):
                self.assertEqual(
                    catalog.find_correspondences(
                        "syriac", "syrnt", node="word",
                        feature="ls", value=code,
                        include_approximate=True, source_version="0.9"),
                    (),
                )
        for code in ("mult", "padv", "ppre", "focp", "sffx"):
            with self.subTest(corpus="extrabiblical", code=code):
                self.assertEqual(
                    catalog.find_correspondences(
                        "extrabiblical", "tlhdig-tf",
                        node="word", feature="ls", value=code,
                        include_approximate=True,
                    ),
                    (),
                )


if __name__ == "__main__":
    unittest.main()
