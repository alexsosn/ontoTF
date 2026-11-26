"""CUC 0.2.8 observed sign vocabulary: transliteration letters vs editorial marks."""
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError

PIN = "ad69400f5446e1c8217af01659c7c10ab00c015b"
LETTER = "http://purl.org/olia/olia.owl#Letter"
OCCURRENCE = "http://www.cidoc-crm.org/extensions/crmtex/TX11_Grapheme_Occurrence"

# Pinned CUC r005/cuc.json sign-feature observed values (TF 0.2.8).
LETTERS = frozenset({
    "a", "b", "d", "g", "h", "i", "k", "l", "m", "n",
    "p", "q", "r", "s", "t", "u", "w", "y", "z", "ġ",
    "ś", "š", "ʿ", "ḏ", "ḥ", "ḫ", "ṣ", "ṭ", "ṯ", "ẓ",
})
CONSERVATIVE = frozenset({"-", "?", "x", "Ṯ", "…"})
DIVIDER = "."
SEPARATOR = "http://purl.org/olia/olia.owl#GraphicalSeparator"
# XML selector validation excludes whitespace-only attributes, correctly
# leaving textual layout slots unmapped rather than manufacturing a Letter.
TECHNICAL = frozenset({" ", "\u00a0"})


class CUCObservedSignVocabularyTests(unittest.TestCase):
    def test_pinned_source_sign_values_and_orthographic_letter_categories(self):
        c = MappingCatalog()
        self.assertIn("cuc", c.list_corpora())
        expected = LETTERS | CONSERVATIVE | {DIVIDER}
        rows = [r for r in c.load("cuc")
                if r.kind == "value" and r.node == "sign"
                and r.feature == "sign"]
        self.assertEqual({r.value for r in rows}, expected)
        self.assertEqual(len(rows), len(expected) + len(LETTERS))
        for value in LETTERS:
            with self.subTest(letter=value):
                m = c.map_native("cuc", node="sign",
                                 feature="sign", value=value)
                self.assertEqual({(r.relation, r.target) for r in m},
                                 {("exact", LETTER), ("close", OCCURRENCE)})
                self.assertEqual(len(m), 2)
                for row in m:
                    self.assertEqual(row.corpus_version, "0.2.8")
                    self.assertIn(PIN, row.evidence)
        for value in CONSERVATIVE:
            with self.subTest(editorial_or_unverified=value):
                m = c.map_native("cuc", node="sign",
                                 feature="sign", value=value)
                self.assertEqual(
                    [(r.relation, r.target) for r in m],
                    [("native-only", None)],
                )
        divider, = c.map_native("cuc", node="sign", feature="sign",
                                value=DIVIDER, corpus_version="0.2.8")
        self.assertEqual((divider.relation, divider.target),
                         ("narrower", SEPARATOR))
        self.assertIn(PIN, divider.evidence)
        for value in TECHNICAL:
            with self.subTest(technical_layout=value):
                self.assertEqual(c.map_native(
                    "cuc", node="sign", feature="sign", value=value), ())

    def test_no_physical_glyph_token_identity_or_forged_language_category(self):
        c = MappingCatalog()
        self.assertEqual(
            [(r.relation, r.target) for r in c.map_native(
                "cuc", node="word", feature="language", value="Ugaritic")],
            [("native-only", None)],
        )
        self.assertEqual(c.map_native("cuc", kind="node", node="sign"), ())
        self.assertEqual(c.map_native(
            "cuc", kind="entity", node="sign", feature="sign", value="a"), ())
        self.assertEqual(c.find_correspondences(
            "cuc", "syriac", node="sign", feature="sign", value="a"), ())
        with self.assertRaises(MappingError):
            c.map_native("cuc", node="sign", feature="sign",
                         value="a", corpus_version="0.2.7")


if __name__ == "__main__":
    unittest.main()
