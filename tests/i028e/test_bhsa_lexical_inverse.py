"""I-028E: actual lexical collisions and a reusable lex-only TF lookup index."""
from __future__ import annotations

from types import SimpleNamespace
import unittest

from tfont.bhsa_lexical_preview import (
    BHSA_SOURCE_REVISION, LexicalProjectionError,
    project_bhsa_lexical_form,
    resolve_bhsa_lexical_uri,
    build_bhsa_lexical_form_index,
    find_bhsa_lexical_forms,
)

A, B, W = 1437729, 1437796, 17
FIRST, LAST = 1437602, 1446831
WRITTEN = "אַף"  # two distinct lex nodes in original ETCBC BHSA
SOURCE = BHSA_SOURCE_REVISION


class FakeFeature:
    def __init__(self, fallback, overrides=None):
        self.fallback = fallback
        self.overrides = dict(overrides or {})
        self.calls = []

    def v(self, node):
        self.calls.append(node)
        return self.overrides.get(node, self.fallback(node))

    def s(self, _value):
        raise AssertionError("TF NodeFeature.s performs a 435820-entry linear scan")


class FakeTF:
    """Full 9,230-node contract stub; only named collision values are source copies."""

    def __init__(self, *, type_overrides=None, lexical=None, vocal=None, languages=None):
        def otype(n):
            return "lex" if FIRST <= n <= LAST else "word"
        self.F = SimpleNamespace(
            otype=FakeFeature(otype, type_overrides),
            lex=FakeFeature(lambda n: f"L{n}/", {A: ">P/", B: ">P", **(lexical or {})}),
            voc_lex_utf8=FakeFeature(lambda n: f"source-form-{n}",
                                    {A: WRITTEN, B: WRITTEN, W: WRITTEN, **(vocal or {})}),
            languageISO=FakeFeature(lambda n: "hbo", languages),
        )


class BHSAInverseContractTests(unittest.TestCase):
    def test_real_duplicate_vocalization_stays_two_distinct_source_identities(self):
        api = FakeTF()
        index = build_bhsa_lexical_form_index(api, source_revision=SOURCE)
        hits = index.lookup(WRITTEN)
        self.assertEqual([x.source_node_id for x in hits], [A, B])
        self.assertEqual([x.source_lexeme for x in hits], [">P/", ">P"])
        self.assertEqual([x.written_rep for x in hits], [WRITTEN, WRITTEN])
        self.assertEqual(len({x.entry_iri for x in hits}), 2)
        self.assertEqual(len({x.form_iri for x in hits}), 2)
        self.assertEqual({x.authority for x in hits}, {"unreviewed-derived-preview"})
        self.assertEqual(index.source_revision, SOURCE)
        self.assertEqual(index.lexeme_count, 9230)
        self.assertEqual(index.lookup("nonexistent"), ())
        self.assertEqual(
            [m.source_node_id for m in find_bhsa_lexical_forms(api, WRITTEN, source_revision=SOURCE)],
            [A, B],
        )

    def test_index_only_inspects_source_lexeme_nodes_and_supports_fast_reuse(self):
        api = FakeTF()
        index = build_bhsa_lexical_form_index(api, source_revision=SOURCE)
        for f in (api.F.otype, api.F.lex, api.F.voc_lex_utf8, api.F.languageISO):
            self.assertEqual(len(f.calls), 9230)
            self.assertEqual(f.calls[0], FIRST)
            self.assertEqual(f.calls[-1], LAST)
            self.assertNotIn(W, f.calls)  # word-scoped TF data are never scanned
        old_calls = len(api.F.voc_lex_utf8.calls)
        for _ in range(100):
            self.assertEqual(len(index.lookup(WRITTEN)), 2)
        self.assertEqual(len(api.F.voc_lex_utf8.calls), old_calls)
        self.assertEqual(index.lookup("source-form-1437602")[0].source_node_id, FIRST)
        # A snapshot must be rebuilt after corpus data changes, not silently cached globally.
        with self.assertRaises(TypeError):
            index.by_written_rep[WRITTEN] = ()

    def test_inverse_uris_revalidate_actual_tf_source_not_only_urn_syntax(self):
        api = FakeTF()
        for node in (A, B):
            actual = project_bhsa_lexical_form(api, node, source_revision=SOURCE)
            for uri, want in ((actual.entry_iri, "entry"), (actual.form_iri, "form")):
                with self.subTest(node=node, kind=want):
                    kind, result = resolve_bhsa_lexical_uri(api, uri, source_revision=SOURCE)
                    self.assertEqual(kind, want)
                    self.assertEqual(result, actual)
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_lexical_uri(api, actual.form_iri, source_revision="0" * 40)
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_lexical_uri(FakeTF(type_overrides={B: "word"}), actual.form_iri,
                                    source_revision=SOURCE)

    def test_full_index_fails_closed_on_corrupted_source_or_wrong_pinned_revision(self):
        for name, overrides in (
            ("missing-lex-node", {"type_overrides": {B: "word"}}),
            ("missing-lexical-value", {"lexical": {B: ""}}),
            ("missing-vocal", {"vocal": {B: None}}),
            ("invalid-language", {"languages": {B: "xx"}}),
        ):
            with self.subTest(name=name):
                with self.assertRaises(LexicalProjectionError):
                    build_bhsa_lexical_form_index(FakeTF(**overrides), source_revision=SOURCE)
        with self.assertRaises(LexicalProjectionError):
            build_bhsa_lexical_form_index(FakeTF(), source_revision="0" * 40)
        for value in (None, b"x", "", True, 123):
            with self.subTest(value=value):
                with self.assertRaises(LexicalProjectionError):
                    find_bhsa_lexical_forms(FakeTF(), value, source_revision=SOURCE)
        with self.assertRaises(LexicalProjectionError):
            resolve_bhsa_lexical_uri(FakeTF(), "urn:tfont:derived:bhsa:wrong",
                                    source_revision=SOURCE)


if __name__ == "__main__":
    unittest.main()
