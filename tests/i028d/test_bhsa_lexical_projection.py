"""I-028D: real BHSA TF lexical nodes, rather than string-based entry IDs."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
import unittest

from tfont.bhsa_lexical_preview import (
    BHSA_SOURCE_REVISION, LexicalProjectionError,
    project_bhsa_lexical_form, parse_bhsa_lexical_uri,
)

A, B = 1437649, 1437650
SOURCE = BHSA_SOURCE_REVISION
ENTRY_CLASS = "http://www.w3.org/ns/lemon/ontolex#LexicalEntry"
FORM_CLASS = "http://www.w3.org/ns/lemon/ontolex#Form"
FORM_PRED = "http://www.w3.org/ns/lemon/ontolex#lexicalForm"
WRITTEN = "http://www.w3.org/ns/lemon/ontolex#writtenRep"


class _V:
    def __init__(self, values):
        self.values = values

    def v(self, node):
        return self.values.get(node)


def api_for(a=True, b=True, overrides=None):
    # Values verified against ETCBC/bhsa@4db00e tf/2021/otype.tf and
    # full lex.tf, voc_lex_utf8.tf, languageISO.tf Git blobs.
    data = {
        "otype": {A: "lex", B: "lex", 1: "word"},
        "lex": {A: "DC>[", B: "DC>/"},
        "voc_lex_utf8": {A: "דשא", B: "דֶּשֶׁא"},
        "languageISO": {A: "hbo", B: "hbo"},
    }
    if overrides:
        for feature, values in overrides.items():
            data[feature].update(values)
    return SimpleNamespace(F=SimpleNamespace(**{name: _V(values) for name, values in data.items()}))


class BHSADerivedLexicalFormTests(unittest.TestCase):
    def test_real_distinct_lex_nodes_same_lex0_are_distinct_entries_and_forms(self):
        tf = api_for()
        left = project_bhsa_lexical_form(tf, A, source_revision=SOURCE)
        right = project_bhsa_lexical_form(tf, B, source_revision=SOURCE)
        self.assertEqual(left.source_lexeme, "DC>[")
        self.assertEqual(right.source_lexeme, "DC>/")
        self.assertEqual(left.written_rep, "דשא")
        self.assertEqual(right.written_rep, "דֶּשֶׁא")
        self.assertEqual((left.language_tag, right.language_tag), ("hbo", "hbo"))
        self.assertNotEqual(left.entry_iri, right.entry_iri)
        self.assertNotEqual(left.form_iri, right.form_iri)
        for node, proj in ((A, left), (B, right)):
            with self.subTest(node=node):
                self.assertEqual(proj.authority, "unreviewed-derived-preview")
                self.assertEqual(proj.source_node_id, node)
                self.assertEqual(proj.entry_candidate_class, ENTRY_CLASS)
                self.assertEqual(proj.form_candidate_class, FORM_CLASS)
                self.assertEqual(proj.lexical_form_relation, FORM_PRED)
                self.assertEqual(proj.written_rep_relation, WRITTEN)
                self.assertEqual(proj.source_representation_feature, "voc_lex_utf8")
                self.assertEqual(proj.source_revision, SOURCE)
                self.assertEqual(parse_bhsa_lexical_uri(proj.entry_iri), (node, "entry"))
                self.assertEqual(parse_bhsa_lexical_uri(proj.form_iri), (node, "form"))
                self.assertNotIn("canonicalForm", repr(proj))
                self.assertNotIn("LexicalSense", repr(proj))
        with self.assertRaises(FrozenInstanceError):
            left.written_rep = "invented"

    def test_source_word_and_absent_lexical_data_fail_closed(self):
        for node, revision, overrides in (
            (1, SOURCE, {}),
            (A, "0" * 40, {}),
            (A, SOURCE, {"voc_lex_utf8": {A: ""}}),
            (A, SOURCE, {"voc_lex_utf8": {A: None}}),
            (A, SOURCE, {"languageISO": {A: "unknown"}}),
            (A, SOURCE, {"lex": {A: ""}}),
            (1437601, SOURCE, {}),
            (1446832, SOURCE, {}),
            (True, SOURCE, {}),
        ):
            with self.subTest(node=node, revision=revision, overrides=overrides):
                with self.assertRaises(LexicalProjectionError):
                    project_bhsa_lexical_form(api_for(overrides=overrides), node, source_revision=revision)

    def test_adversarial_identifier_misbindings(self):
        good = project_bhsa_lexical_form(api_for(), A, source_revision=SOURCE)
        for uri in (
            good.entry_iri.replace(SOURCE, "0" * 40),
            good.entry_iri.replace(":bhsa:", ":syriac:"),
            good.entry_iri.replace(":1437649", ":01437649"),
            good.entry_iri.replace(":1437649", ":1"),
            good.form_iri + ":extra",
            good.form_iri.replace(":form:voc_lex_utf8", ":form:lex0"),
            good.entry_iri.replace("urn:tfont:derived", "http://example.org"),
        ):
            with self.subTest(uri=uri):
                with self.assertRaises(LexicalProjectionError):
                    parse_bhsa_lexical_uri(uri)
        with self.assertRaises(LexicalProjectionError):
            parse_bhsa_lexical_uri(123)


if __name__ == "__main__":
    unittest.main()
