"""ETCBC ExtraBiblical word-person categories against the pinned source TF domain.

These are grammatical person categories, not cross-corpus word/entity identities.
"""
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError

OLIA = "http://purl.org/olia/olia.owl#"
PIN = "9a56288e6777bad6328856acf055c780e65dd5d9"
CASES = {"p1": "First", "p2": "Second", "p3": "Third"}
MISSING = ("NA", "unknown")


class ExtraBiblicalPersonMappingsTests(unittest.TestCase):
    def test_all_five_pinned_source_values_are_disposed(self):
        catalog = MappingCatalog()
        rows = [m for m in catalog.load("extrabiblical")
                if m.kind == "value" and m.node == "word" and m.feature == "ps"]
        self.assertEqual(len(rows), 5)
        self.assertEqual({m.value for m in rows}, set(CASES) | set(MISSING))
        for code in (*CASES, *MISSING):
            with self.subTest(code=code):
                found = catalog.map_native(
                    "extrabiblical", kind="value", node="word",
                    feature="ps", value=code, corpus_version="0.2",
                )
                self.assertEqual(len(found), 1)
                m, = found
                self.assertEqual(m.corpus_version, "0.2")
                self.assertIn(PIN, m.evidence)
                expected = ("exact", OLIA + CASES[code]) if code in CASES else (
                    "native-only", None)
                self.assertEqual((m.relation, m.target), expected)

    def test_cross_corpus_person_categories_without_word_identity(self):
        catalog = MappingCatalog()
        for code, target in CASES.items():
            for other, other_code in (("bhsa", code), ("syriac", {
                "p1": "first", "p2": "second", "p3": "third"}[code])):
                with self.subTest(code=code, other=other):
                    matches = catalog.find_correspondences(
                        "extrabiblical", other,
                        kind="value", node="word", feature="ps", value=code,
                    )
                    # BHSA has both word person (ps) and the distinct
                    # pronominal-suffix person (prs_ps) category. A shared
                    # ontology class must not erase this native distinction.
                    expected_destinations = {("ps", other_code)}
                    if other == "bhsa":
                        expected_destinations.add(("prs_ps", code))
                    self.assertEqual(
                        {(m.destination.feature, m.destination.value)
                         for m in matches},
                        expected_destinations,
                    )
                    for match in matches:
                        self.assertEqual(match.target, OLIA + target)
                        self.assertEqual((match.scope, match.relation),
                                         ("category", "exact"))
        self.assertEqual(
            catalog.map_native("extrabiblical", kind="entity",
                               node="word", feature="ps", value="p1"), (),
        )

    def test_not_applicable_and_unknown_cannot_be_promoted(self):
        catalog = MappingCatalog()
        for code in MISSING:
            for dest in ("bhsa", "syriac"):
                with self.subTest(code=code, dest=dest):
                    self.assertEqual(
                        catalog.find_correspondences(
                            "extrabiblical", dest, kind="value",
                            node="word", feature="ps", value=code,
                            include_approximate=True,
                        ), (),
                    )
        with self.assertRaisesRegex(MappingError, "version"):
            catalog.map_native("extrabiblical", kind="value", node="word",
                               feature="ps", value="p1", corpus_version="2021")


if __name__ == "__main__":
    unittest.main()
