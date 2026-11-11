"""Pinned CUC Ugaritic Unicode character-class mappings.

Maps Unicode Ugaritic LETTER values, not physical incisions, individual
sign identities or Latin transliteration equivalence. The word divider,
editorial placeholders and whitespace are NOT letters.
"""
import json
from pathlib import Path
import unicodedata
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

PIN = "ad69400f5446e1c8217af01659c7c10ab00c015b"
VERSION = "0.2.8"
OLIA_LETTER = "http://purl.org/olia/olia.owl#Letter"
LETTERS = tuple(chr(codepoint) for codepoint in range(0x10380, 0x1039E))
WORD_DIVIDER = "\U0001039f"
NONLETTERS = ("-", "?", "x", "…", WORD_DIVIDER)
SPACE = " "


class CUCUgariticUnicodeLetterTests(unittest.TestCase):
    def test_pinned_source_domain_and_counts_are_exhaustive(self):
        source = json.loads((
            Path(__file__).resolve().parents[2]
            / "docs/research/data/generated/r005/cuc.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual((source["revision"], source["tf_version"]),
                         (PIN, VERSION))
        usign = source["node_features"]["usign"]
        self.assertEqual(usign["applies_to"], ["sign"])
        self.assertEqual(usign["observation_count"], 146017)
        self.assertEqual(usign["observed_unique_count"], 36)
        self.assertEqual(set(usign["observed_values"]),
                         set(LETTERS) | set(NONLETTERS) | {SPACE})
        counts = usign["observed_frequencies"]
        self.assertEqual(sum(counts.values()), 146017)
        self.assertEqual(sum(counts[letter] for letter in LETTERS), 70872)
        self.assertEqual(counts[SPACE], 68256)
        self.assertEqual(counts[WORD_DIVIDER], 517)
        self.assertEqual(counts["x"], 6342)

    def test_unicode_characters_are_letters_but_word_divider_is_punctuation(self):
        self.assertEqual(len(LETTERS), 30)
        for letter in LETTERS:
            with self.subTest(letter=letter):
                self.assertEqual(unicodedata.category(letter), "Lo")
                self.assertTrue(unicodedata.name(letter).startswith(
                    "UGARITIC LETTER "))
        self.assertEqual(unicodedata.category(WORD_DIVIDER), "Po")
        self.assertEqual(unicodedata.name(WORD_DIVIDER),
                         "UGARITIC WORD DIVIDER")

    def test_every_source_character_has_an_explicit_safe_disposition(self):
        catalog = MappingCatalog()
        rows = [r for r in catalog.load("cuc")
                if r.kind == "value" and r.node == "sign"
                and r.feature == "usign"]
        # One source whitespace value is intentionally absent because the
        # XML selector validator forbids whitespace-only native values.
        self.assertEqual(len(rows), 35)
        self.assertEqual({r.value for r in rows},
                         set(LETTERS) | set(NONLETTERS))
        for value in LETTERS:
            with self.subTest(letter=value):
                row, = catalog.map_native(
                    "cuc", node="sign", feature="usign", value=value,
                    corpus_version=VERSION)
                self.assertEqual((row.relation, row.target),
                                 ("exact", OLIA_LETTER))
                self.assertEqual(row.corpus_version, VERSION)
                self.assertIn(PIN, row.evidence or "")
        for value in NONLETTERS:
            with self.subTest(nonletter=value):
                row, = catalog.map_native(
                    "cuc", node="sign", feature="usign", value=value,
                    corpus_version=VERSION)
                self.assertEqual((row.relation, row.target),
                                 ("native-only", None))
                self.assertIn(PIN, row.evidence or "")
        self.assertEqual(catalog.map_native(
            "cuc", node="sign", feature="usign", value=SPACE), ())

    def test_both_scripts_are_orthographic_categories_not_sign_identities(self):
        catalog = MappingCatalog()
        grouped = catalog.find_by_target(
            OLIA_LETTER, corpus="cuc", kind="value")
        self.assertEqual(len(grouped), 60)
        self.assertEqual(
            {feature: sum(row.feature == feature for row in grouped)
             for feature in ("sign", "usign")},
            {"sign": 30, "usign": 30},
        )
        self.assertTrue(all(row.node == "sign" and row.relation == "exact"
                            for row in grouped))
        self.assertEqual(catalog.map_native(
            "cuc", kind="entity", node="sign", feature="usign",
            value=LETTERS[0]), ())
        self.assertEqual(catalog.find_correspondences(
            "cuc", "bhsa", node="sign", feature="usign",
            value=LETTERS[0]), ())

    def test_exact_unicode_letter_selects_sign_nodes_only(self):
        mapping, = MappingCatalog().map_native(
            "cuc", node="sign", feature="usign", value=LETTERS[0])
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(kind):
                        assert kind == "sign"
                        return (1, 2, 3, 4, 5)
            @staticmethod
            def Fs(feature):
                assert feature == "usign"
                class Values:
                    @staticmethod
                    def v(n):
                        return {1: LETTERS[0], 2: WORD_DIVIDER,
                                3: LETTERS[1], 4: LETTERS[0],
                                5: "x"}[n]
                return Values()
        self.assertEqual(resolve_nodes(API(), mapping,
                                       corpus_version=VERSION), (1, 4))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), mapping, corpus_version="0.2.7")
        negative, = MappingCatalog().map_native(
            "cuc", node="sign", feature="usign", value=WORD_DIVIDER)
        with self.assertRaisesRegex(MappingError, "only positive"):
            resolve_nodes(API(), negative, corpus_version=VERSION)


if __name__ == "__main__":
    unittest.main()
