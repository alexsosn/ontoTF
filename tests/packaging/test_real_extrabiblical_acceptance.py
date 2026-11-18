"""Researcher acceptance contract for the pinned full ETCBC ExtraBiblical TF 0.2 source.

The small offline API exercises the exact same acceptance logic as the
fresh-installed-wheel/real-Text-Fabric CI smoke. It never stands in for
the real upstream corpus: the CI gate supplies real pinned TF files.
"""
from __future__ import annotations

import unittest

from scripts.acceptance.real_extrabiblical import audit_loaded_api, verify_source_counts


class _Feature:
    def __init__(self, values):
        self.values = values

    def v(self, node):
        return self.values.get(node)


class _Type:
    def s(self, kind):
        if kind != "word":
            raise AssertionError(f"unexpected node type: {kind}")
        return (1, 2, 3, 4, 5, 6)


class _API:
    class F:
        otype = _Type()

    def Fs(self, name):
        features = {
            "g_word": {1: "ABC", 2: "", 3: None, 4: "DEF", 5: "GHI", 6: "JKL"},
            "sp": {1: "subs", 2: "subs", 3: "verb", 4: "subs",
                   5: "nmpr", 6: "nmpr"},
        }
        return _Feature(features[name])


class ExtraBiblicalInstalledWheelAcceptanceTests(unittest.TestCase):
    def test_native_selectors_preserve_gaps_and_cross_corpus_category_scope(self):
        observed = audit_loaded_api(_API())
        self.assertEqual(observed["word_slots"], 6)
        self.assertEqual(observed["surface_tokens"], 4)
        self.assertEqual(observed["empty_slots"], 2)
        self.assertEqual(observed["nouns_subs"], 3)
        self.assertEqual(observed["proper_nouns_nmpr"], 2)
        self.assertGreater(observed["shared_noun_category_matches"], 0)

    def test_frozen_real_source_counts_are_not_replaced_with_synthetic_counts(self):
        expected = {
            "word_slots": 39862,
            "surface_tokens": 39560,
            "empty_slots": 302,
            "nouns_subs": 12225,
            "proper_nouns_nmpr": 723,
        }
        verify_source_counts({**expected, "shared_noun_category_matches": 2})
        with self.assertRaisesRegex(ValueError, "surface_tokens"):
            verify_source_counts({**expected, "surface_tokens": 39862})
        with self.assertRaisesRegex(ValueError, "nouns_subs"):
            verify_source_counts({**expected, "nouns_subs": 12226})
        with self.assertRaisesRegex(ValueError, "missing"):
            verify_source_counts({"word_slots": 39862})


if __name__ == "__main__":
    unittest.main()
