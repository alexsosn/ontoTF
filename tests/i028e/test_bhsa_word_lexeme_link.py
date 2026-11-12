"""BHSA word->lex source-edge resolution, not a gloss/string-based word match.

Real ETCBC/bhsa@4db00e2 programs/lexicon.py resolves L.u(w, otype="lex")
and builds lex-node oslots from (language, disambiguated lex) identities.
The small test graph below is SYNTHETIC; A/B are real pinned lex records,
but no claim is made that word 17/18 actually belongs to these lexemes.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
import unittest

from tfont import BHSAWordLexemeLink, resolve_bhsa_word_lexeme
from tfont.bhsa_lexical_preview import (
    BHSA_SOURCE_REVISION, LexicalProjectionError,
)

A, B = 1437729, 1437796  # different real source lexemes, same pointed rep
W1, W2 = 17, 18  # artificial word->lex graph, NOT a real BHSA occurrence link
SOURCE = BHSA_SOURCE_REVISION
WRITTEN = "אַף"


class Feature:
    def __init__(self, entries):
        self.entries = entries

    def v(self, node):
        return self.entries.get(node)

    def s(self, value):
        raise AssertionError("source lexical link must not scan feature strings")


class NativeLevels:
    def __init__(self, edges):
        self.edges = edges
        self.calls = []

    def u(self, node, *, otype):
        self.calls.append((node, otype))
        if otype != "lex":
            raise AssertionError("wrong source object kind")
        value = self.edges.get(node, ())
        if isinstance(value, Exception):
            raise value
        return value


def tf_for(*, edges=None, types=None, lex=None, languages=None, forms=None):
    data = {
        "otype": {A: "lex", B: "lex", W1: "word", W2: "word"},
        "lex": {A: ">P/", B: ">P", W1: ">P/", W2: ">P"},
        "languageISO": {A: "hbo", B: "hbo", W1: "hbo", W2: "hbo"},
        "voc_lex_utf8": {A: WRITTEN, B: WRITTEN},
    }
    for key, overrides in (
        ("otype", types), ("lex", lex),
        ("languageISO", languages), ("voc_lex_utf8", forms)
    ):
        data[key].update(overrides or {})
    api = SimpleNamespace(
        F=SimpleNamespace(**{k: Feature(v) for k, v in data.items()}),
        L=NativeLevels({W1: (A,), W2: (B,)} if edges is None else edges),
    )
    return api


class BHSAWordToLexemeLinkTests(unittest.TestCase):
    def test_source_edge_yields_distinct_entry_and_form_for_homographs(self):
        api = tf_for()
        left = resolve_bhsa_word_lexeme(api, W1, source_revision=SOURCE)
        right = resolve_bhsa_word_lexeme(api, W2, source_revision=SOURCE)
        self.assertIsInstance(left, BHSAWordLexemeLink)
        self.assertEqual((left.word_node_id, left.lex_node_id), (W1, A))
        self.assertEqual((right.word_node_id, right.lex_node_id), (W2, B))
        self.assertEqual(api.L.calls, [(W1, "lex"), (W2, "lex")])
        self.assertEqual(left.source_edge_feature, "oslots")
        self.assertEqual(left.source_revision, SOURCE)
        self.assertEqual(left.lexical_form.source_node_id, A)
        self.assertEqual(right.lexical_form.source_node_id, B)
        self.assertEqual(left.lexical_form.written_rep, WRITTEN)
        self.assertEqual(right.lexical_form.written_rep, WRITTEN)
        self.assertNotEqual(left.lexical_form.entry_iri, right.lexical_form.entry_iri)
        self.assertNotEqual(left.lexical_form.form_iri, right.lexical_form.form_iri)
        self.assertEqual(left.lexical_form.entry_candidate_class,
                         "http://www.w3.org/ns/lemon/ontolex#LexicalEntry")
        self.assertEqual(left.lexical_form.form_candidate_class,
                         "http://www.w3.org/ns/lemon/ontolex#Form")
        self.assertEqual(left.lexical_form.authority, "unreviewed-derived-preview")
        with self.assertRaises(FrozenInstanceError):
            left.word_node_id = 42

    def test_missing_ambiguous_and_invalid_native_edges_fail_closed(self):
        for edges in (
            {W1: ()},
            {W1: (A, B)},
            {W1: (A, A)},
            {W1: ("not-a-node",)},
            {W1: (True,)},
            {W1: (1,)},
            {W1: (1446832,)},
            {W1: None},
            {W1: KeyError("source edge unavailable")},
        ):
            with self.subTest(edges=edges):
                with self.assertRaises(LexicalProjectionError):
                    resolve_bhsa_word_lexeme(
                        tf_for(edges=edges), W1, source_revision=SOURCE
                    )

    def test_word_identity_and_pinned_version_guard_before_lookup(self):
        for word in (0, -1, 426591, A, "17", True, None):
            with self.subTest(word=word):
                api = tf_for()
                with self.assertRaises(LexicalProjectionError):
                    resolve_bhsa_word_lexeme(api, word, source_revision=SOURCE)
                self.assertEqual(api.L.calls, [])
        api = tf_for()
        with self.assertRaisesRegex(LexicalProjectionError, "revision"):
            resolve_bhsa_word_lexeme(api, W1, source_revision="0" * 40)
        self.assertEqual(api.L.calls, [])
        api = tf_for(types={W1: "lex"})
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_word_lexeme(api, W1, source_revision=SOURCE)
        self.assertEqual(api.L.calls, [])

    def test_mismatch_of_word_and_lex_entry_features_must_not_rebind(self):
        for opts in (
            {"lex": {W1: ">P"}},
            {"lex": {W1: ""}},
            {"lex": {W1: None}},
            {"languages": {W1: "arc"}},
            {"languages": {W1: None}},
            {"types": {A: "word"}},
            {"forms": {A: ""}},
        ):
            with self.subTest(opts=opts):
                with self.assertRaises(LexicalProjectionError):
                    resolve_bhsa_word_lexeme(
                        tf_for(**opts), W1, source_revision=SOURCE
                    )
        # A fabricated lexical match based on identical WRITTEN FORM still
        # cannot override the true source edge (B != A).
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_word_lexeme(
                tf_for(edges={W1: (B,)}), W1, source_revision=SOURCE
            )

    def test_missing_tf_levels_are_errors_not_silent_null_results(self):
        api = tf_for()
        del api.L
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_word_lexeme(api, W1, source_revision=SOURCE)
        api = tf_for()
        del api.F.languageISO
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_word_lexeme(api, W1, source_revision=SOURCE)


if __name__ == "__main__":
    unittest.main()
