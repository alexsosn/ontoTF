"""ORACC-TF 1.0.0 word→lex edges, including compound multi-analysis words.

Source evidence: alexsosn/ORACC-TF@60db4b7 docs/reference/words-and-lexemes.md,
features/edge/word_lex.md, and features/lex/lexeme.md. The 289,205
linked words have 289,824 edges (288,591 degree-one, 609 degree-two,
five degree-three). 31,770 other source words lack a lexical analysis.
The small API double below is synthetic, not a downloaded full corpus.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from types import SimpleNamespace
import unittest

from tfont import ORACCWordLexemeLink, resolve_oracc_word_lexemes
from tfont.oracc_lexical_preview import (
    ORACC_SOURCE_REVISION, ORACCLexicalResolutionError,
)

W, A, B, C = 101, 901, 902, 903
SOURCE = ORACC_SOURCE_REVISION
# A/B deliberately reuse a real source citation form but have distinct real
# lexical keys. Their synthetic edge membership below is NOT source attested.
KEYS = {
    A: ("akk", "Abi-Baʾal", "king of Samsimurruna", "RN"),
    B: ("akk", "Abi-Baʾal", "son of Yakin-Lu", "RN"),
    C: ("akk", "mātu", "land", "N"),
}


class Feature:
    def __init__(self, values):
        self.values = values

    def v(self, node):
        return self.values.get(node)

    def s(self, value):
        raise AssertionError("identity joins and feature scans are forbidden")


class Edge:
    def __init__(self, links):
        self.links = links
        self.calls = []

    def f(self, node):
        self.calls.append(node)
        value = self.links.get(node, ())
        if isinstance(value, Exception):
            raise value
        return value


def api_for(*, links=None, features=None):
    data = {
        "otype": {W: "word", A: "lex", B: "lex", C: "lex"},
        "lexeme": {n: json.dumps(key, ensure_ascii=False)
                   for n, key in KEYS.items()},
        "lang": {n: key[0] for n, key in KEYS.items()},
        "cf": {n: key[1] for n, key in KEYS.items()},
        "gw": {n: key[2] for n, key in KEYS.items()},
        "pos": {n: key[3] for n, key in KEYS.items()},
    }
    for key, overrides in (features or {}).items():
        data[key].update(overrides)
    return SimpleNamespace(
        F=SimpleNamespace(**{k: Feature(v) for k, v in data.items()}),
        E=SimpleNamespace(word_lex=Edge({W: (A, B, C)} if links is None
                                        else links)),
    )


class ORACCWordLexemeTests(unittest.TestCase):
    def resolve(self, api):
        return resolve_oracc_word_lexemes(api, W, source_revision=SOURCE)

    def test_three_analyses_preserved_as_three_distinct_native_lex_nodes(self):
        api = api_for()
        hits = self.resolve(api)
        self.assertEqual(api.E.word_lex.calls, [W])
        self.assertEqual(len(hits), 3)
        self.assertTrue(all(isinstance(h, ORACCWordLexemeLink) for h in hits))
        self.assertEqual(tuple(h.lex_node_id for h in hits), (A, B, C))
        self.assertEqual(tuple(h.lexical_key for h in hits),
                         tuple(KEYS.values()))
        self.assertEqual(tuple(h.word_node_id for h in hits), (W, W, W))
        self.assertTrue(all(h.source_edge_feature == "word_lex"
                            and h.source_revision == SOURCE for h in hits))
        self.assertTrue(all(
            h.entry_candidate_class
            == "http://www.w3.org/ns/lemon/ontolex#LexicalEntry"
            for h in hits))
        self.assertEqual(hits[0].lexical_key[1], hits[1].lexical_key[1])
        self.assertNotEqual(hits[0].lex_node_id, hits[1].lex_node_id)
        self.assertNotEqual(hits[0].lexical_key, hits[1].lexical_key)
        with self.assertRaises(FrozenInstanceError):
            hits[0].lex_node_id = C

    def test_unlemmatized_word_is_valid_and_not_fabricated(self):
        api = api_for(links={W: ()})
        self.assertEqual(self.resolve(api), ())
        self.assertEqual(api.E.word_lex.calls, [W])
        self.assertEqual(tuple(x.lex_node_id for x in self.resolve(
            api_for(links={W: (A,)}))), (A,))
        self.assertEqual(tuple(x.lex_node_id for x in self.resolve(
            api_for(links={W: (A, B)}))), (A, B))

    def test_invalid_edges_are_rejected_not_silently_deduplicated(self):
        for links in (
            {W: (A, A)}, {W: (A, B, C, A)},
            {W: (True,)}, {W: ("901",)}, {W: (0,)}, {W: (-1,)},
            {W: (W,)}, {W: (9999,)}, {W: None},
            {W: ValueError("edge unavailable")},
        ):
            with self.subTest(links=links):
                with self.assertRaises(ORACCLexicalResolutionError):
                    self.resolve(api_for(links=links))

    def test_key_must_be_original_canonical_lexeme_tuple(self):
        for changes in (
            {"lexeme": {A: None}},
            {"lexeme": {A: "not-json"}},
            {"lexeme": {A: "[]"}},
            {"lexeme": {A: '{"lang":"akk"}'}},
            {"lexeme": {A: '["akk","cf",null,"RN"]'}},
            {"lexeme": {A: '["akk","cf","gw","RN","extra"]'}},
            {"lang": {A: "sux"}},
            {"cf": {A: "Abi-Baʾal?"}},
            {"gw": {A: "king"}},
            {"pos": {A: "PN"}},
            {"otype": {A: "word"}},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(ORACCLexicalResolutionError):
                    self.resolve(api_for(features=changes, links={W: (A,)}))

    def test_wrong_word_or_revision_fails_before_graph_query(self):
        api = api_for()
        for node in (0, -1, True, None, "101", A):
            with self.subTest(node=node):
                with self.assertRaises(ORACCLexicalResolutionError):
                    resolve_oracc_word_lexemes(
                        api, node, source_revision=SOURCE)
        with self.assertRaisesRegex(ORACCLexicalResolutionError, "revision"):
            resolve_oracc_word_lexemes(
                api, W, source_revision="not-pinned")
        self.assertEqual(api.E.word_lex.calls, [])
        api = api_for(features={"otype": {W: "lex"}})
        with self.assertRaises(ORACCLexicalResolutionError):
            self.resolve(api)

    def test_missing_native_tf_api_and_features_fail_closed(self):
        api = api_for()
        del api.E.word_lex
        with self.assertRaises(ORACCLexicalResolutionError):
            self.resolve(api)
        api = api_for()
        del api.F.gw
        with self.assertRaises(ORACCLexicalResolutionError):
            self.resolve(api)

    def test_oracc_lex_nodes_are_ontolex_entries_without_sense_forgery(self):
        from tfont.xml_mappings import MappingCatalog
        catalog = MappingCatalog()
        rows = catalog.map_native(
            "assyrian-royal-inscriptions", kind="node", node="lex")
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            (rows[0].target, rows[0].relation),
            ("http://www.w3.org/ns/lemon/ontolex#LexicalEntry", "exact"))
        self.assertEqual(
            catalog.map_native("assyrian-royal-inscriptions",
                               kind="entity", node="lex",
                               feature="lexeme", value="mātu"), ())


if __name__ == "__main__":
    unittest.main()
