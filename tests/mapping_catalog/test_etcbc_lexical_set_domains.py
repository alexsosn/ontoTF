"""Source-observed ETCBC Syriac and ExtraBiblical lexical-set domain accounting.

The pinned R-005 real-corpus inventories are the authoritative observed
feature/value denominators; this module deliberately does not infer identities
or finer part-of-speech classes from shared abbreviations or gloss strings.
"""
import unittest

from tfont.xml_mappings import MappingCatalog

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


class ETCBCObservedLexicalSetsTests(unittest.TestCase):
    def test_complete_pinned_observed_domain_with_source_specific_semantics(self):
        catalog = MappingCatalog()
        for corpus in ("syriac", "extrabiblical"):
            rows = [r for r in catalog.load(corpus)
                    if r.kind == "value" and r.node == "word"
                    and r.feature == "ls"]
            self.assertEqual(len(rows), len(OBSERVED[corpus]))
            self.assertEqual({r.value for r in rows}, OBSERVED[corpus])
            for value in OBSERVED[corpus]:
                with self.subTest(corpus=corpus, code=value):
                    m = catalog.map_native(
                        corpus, node="word", feature="ls", value=value
                    )
                    self.assertEqual(len(m), 1)
                    self.assertIn(PIN[corpus], m[0].evidence)
                    cls = EXACT[corpus].get(value)
                    self.assertEqual(
                        (m[0].relation, m[0].target),
                        ("exact", OLIA + cls) if cls else ("native-only", None),
                    )

    def test_positive_cross_language_category_not_word_identity(self):
        catalog = MappingCatalog()
        for code, cls in (("card", "CardinalNumber"),
                          ("ordn", "OrdinalNumber")):
            with self.subTest(code=code):
                matching = catalog.find_correspondences(
                    "syriac", "extrabiblical",
                    node="word", feature="ls", value=code
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
            catalog.map_native("syriac", kind="entity",
                               node="word", feature="ls", value="card"),
            (),
        )

    def test_unverified_subtypes_and_multitude_do_not_forge_matches(self):
        catalog = MappingCatalog()
        for code in ("demo", "pers", "pinr", "pint", "pcon", "focp", "sffx"):
            with self.subTest(corpus="syriac", code=code):
                self.assertEqual(
                    catalog.find_correspondences(
                        "syriac", "syrnt", node="word",
                        feature="ls", value=code,
                        include_approximate=True,
                    ),
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
