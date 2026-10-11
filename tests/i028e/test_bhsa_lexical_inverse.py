"""I-028E: reverse source-index lookup never merges identical BHSA lexical strings."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
import unittest

from tfont.bhsa_lexical_preview import (
    BHSA_SOURCE_REVISION,
    LexicalProjectionError,
    project_bhsa_lexical_form,
    resolve_bhsa_lexical_uri,
    find_bhsa_lexical_forms,
)

A = 1437729
B = 1437796
W = 17
WRITTEN = "אַף"  # actual shared vocalized value in the two source lex nodes
SOURCE = BHSA_SOURCE_REVISION


class FakeFeature:
    def __init__(self, data, *, search=None):
        self.data = data
        self.search = search

    def v(self, node):
        return self.data.get(node)

    def s(self, value):
        if self.search is not None:
            return self.search(value)
        return [node for node, got in self.data.items() if got == value]


class FakeTF:
    def __init__(self, *, typed=None, lex=None, vocal=None, languages=None, search=None):
        otype = {A: "lex", B: "lex", W: "word", 1446832: "word"}
        spelled = {A: ">P/", B: ">P"}
        vocalized = {A: WRITTEN, B: WRITTEN, W: WRITTEN}
        lang = {A: "hbo", B: "hbo"}
        for target, override in ((otype, typed), (spelled, lex),
                                 (vocalized, vocal), (lang, languages)):
            if override:
                target.update(override)
        self.F = SimpleNamespace(
            otype=FakeFeature(otype),
            lex=FakeFeature(spelled),
            voc_lex_utf8=FakeFeature(vocalized, search=search),
            languageISO=FakeFeature(lang),
        )


class BHSAInverseContractTests(unittest.TestCase):
    def test_original_vocalization_collision_retains_two_entry_form_identities(self):
        api = FakeTF()
        matches = find_bhsa_lexical_forms(api, WRITTEN, source_revision=SOURCE)
        self.assertIsInstance(matches, tuple)
        self.assertEqual([m.source_node_id for m in matches], [A, B])
        self.assertEqual([m.source_lexeme for m in matches], [">P/", ">P"])
        self.assertEqual([m.written_rep for m in matches], [WRITTEN, WRITTEN])
        self.assertEqual(len({m.entry_iri for m in matches}), 2)
        self.assertEqual(len({m.form_iri for m in matches}), 2)
        self.assertEqual({m.authority for m in matches}, {"unreviewed-derived-preview"})
        self.assertFalse(any(m.source_node_id == W for m in matches))

    def test_inverse_uris_reverify_against_runtime_features(self):
        api = FakeTF()
        for node in (A, B):
            direct = project_bhsa_lexical_form(api, node, source_revision=SOURCE)
            for uri, kind in ((direct.entry_iri, "entry"), (direct.form_iri, "form")):
                with self.subTest(node=node, kind=kind):
                    parsed_kind, resolved = resolve_bhsa_lexical_uri(
                        api, uri, source_revision=SOURCE
                    )
                    self.assertEqual(parsed_kind, kind)
                    self.assertEqual(resolved, direct)
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_lexical_uri(api, direct.form_iri, source_revision="0" * 40)

    def test_index_query_order_is_deterministic_and_empty_result_is_unambiguous(self):
        backwards = lambda query: [B, W, A] if query == WRITTEN else []
        hits = find_bhsa_lexical_forms(FakeTF(search=backwards), WRITTEN, source_revision=SOURCE)
        self.assertEqual([x.source_node_id for x in hits], [A, B])
        self.assertEqual(
            find_bhsa_lexical_forms(FakeTF(search=backwards), "nonexistent", source_revision=SOURCE),
            (),
        )
        self.assertEqual(
            find_bhsa_lexical_forms(FakeTF(search=lambda _: [W]), WRITTEN, source_revision=SOURCE),
            (),
        )

    def test_adversarial_malformed_index_rejected(self):
        cases = (
            ("bad-duplicate", lambda _: [A, A]),
            ("out-of-scope-lex", lambda _: [1446832]),
            ("wrong-feature-value", lambda _: [B]),
            ("index-bool", lambda _: [True]),
            ("index-string", lambda _: [str(A)]),
            ("not-an-index", lambda _: WRITTEN),
        )
        for name, search in cases:
            with self.subTest(name=name):
                api = FakeTF(search=search)
                if name == "out-of-scope-lex":
                    api.F.otype.data[1446832] = "lex"
                if name == "wrong-feature-value":
                    api.F.voc_lex_utf8.data[B] = "different source label"
                with self.assertRaises(LexicalProjectionError):
                    find_bhsa_lexical_forms(api, WRITTEN, source_revision=SOURCE)
        missing_method = FakeTF()
        missing_method.F.voc_lex_utf8.s = None
        with self.assertRaises(LexicalProjectionError):
            find_bhsa_lexical_forms(missing_method, WRITTEN, source_revision=SOURCE)

    def test_valid_scope_with_invalid_source_details_stays_closed(self):
        scenarios = (
            {"lex": {B: None}},
            {"languages": {B: "xx"}},
            {"vocal": {B: None}},
        )
        for delta in scenarios:
            with self.subTest(delta=delta):
                api = FakeTF(**delta, search=lambda _: [A, B])
                with self.assertRaises(LexicalProjectionError):
                    find_bhsa_lexical_forms(api, WRITTEN, source_revision=SOURCE)
        for value in (None, b"x", "", True, 123):
            with self.subTest(value=value):
                with self.assertRaises(LexicalProjectionError):
                    find_bhsa_lexical_forms(FakeTF(), value, source_revision=SOURCE)
        with self.assertRaises(LexicalProjectionError):
            find_bhsa_lexical_forms(FakeTF(), WRITTEN, source_revision="0" * 40)
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_lexical_uri(FakeTF(), "urn:tfont:derived:bhsa:wrong", source_revision=SOURCE)
        forged = project_bhsa_lexical_form(FakeTF(), B, source_revision=SOURCE).form_iri
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_lexical_uri(FakeTF(typed={B: "word"}), forged, source_revision=SOURCE)


if __name__ == "__main__":
    unittest.main()
