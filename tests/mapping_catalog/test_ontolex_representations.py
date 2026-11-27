"""Lexical representation fields must not become lexical identities or RDF assertions."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes
from scripts.pages.scoped_progress import rule_matches

ROOT = Path(__file__).resolve().parents[2]
ONTOLEX = "http://www.w3.org/ns/lemon/ontolex#"
EXPECTED = {
    "bhsa": ("2021", {
        **{(node, feature): ("writtenRep", 9230 if node == "lex" else 426590)
           for node in ("lex", "word") for feature in ("lex0", "lex_utf8")},
        **{(node, feature): ("canonicalForm", 9230 if node == "lex" else 426590)
           for node in ("lex", "word") for feature in ("voc_lex", "voc_lex_utf8")},
        ("word", "g_lex"): ("writtenRep", 426579),
        ("word", "g_lex_utf8"): ("writtenRep", 420102),
    }),
    "extrabiblical": ("0.2", {
        ("word", "lex_utf8"): ("writtenRep", 38974),
        ("word", "g_lex"): ("writtenRep", 39525),
        ("word", "g_lex_utf8"): ("writtenRep", 39224),
    }),
    "syriac": ("0.92", {
        ("word", "lex"): ("writtenRep", 407319),
        ("word", "g_lex"): ("writtenRep", 406610),
    }),
    "syrnt": ("0.1", {
        (node, feature): ("writtenRep", 3038 if node == "lexeme" else 109640)
        for node in ("lexeme", "word")
        for feature in ("lexeme", "lexeme_etcbc", "lexeme_sedra")
    }),
    "tlhdig-tf": ("0.4.0", {
        ("lex", "lemma"): ("canonicalForm", 15847),
        ("analysis", "lemma"): ("canonicalForm", 1582460),
    }),
    "assyrian-royal-inscriptions": ("1.0.0", {
        ("lex", "cf"): ("canonicalForm", 8025),
        ("word", "cf"): ("canonicalForm", 289205),
        ("word", "norm"): ("writtenRep", 288557),
    }),
}

class OntolexRepresentationTests(unittest.TestCase):
    def test_scoped_representations_and_discovery(self):
        cat = MappingCatalog()
        policy = json.loads((ROOT / "docs/research/data/scoped-applicability.json").read_text())
        for corpus, (version, fields) in EXPECTED.items():
            inv = json.loads((ROOT / "docs/research/data/generated/scoped" / (corpus + ".json")).read_text())
            self.assertEqual(inv["catalog_version"], version)
            rules = policy["corpora"][corpus]["rules"]["OntoLex-Lemon"]
            for (node, feature), (prop, count) in fields.items():
                with self.subTest(corpus=corpus, node=node, feature=feature):
                    self.assertEqual(inv["node_features"][feature]["scopes"][node]["count"], count)
                    row, = [r for r in cat.map_native(corpus, kind="feature", node=node,
                                 feature=feature, corpus_version=version)
                            if r.target == ONTOLEX + prop]
                    self.assertEqual(row.relation, "related")
                    self.assertTrue(row.evidence)
                    self.assertTrue(any(rule_matches(rule, row.selector) for rule in rules))
                    self.assertNotIn(row, cat.find_by_target(row.target, corpus=corpus, kind="feature"))
                    self.assertIn(row, cat.find_by_target(row.target, corpus=corpus,
                                  kind="feature", include_approximate=True))
                    with self.assertRaises(MappingError):
                        resolve_nodes(object(), row, corpus_version=version)

    def test_citation_form_not_token_identity_or_sense(self):
        cat = MappingCatalog()
        for corpus, node, feature, value in (
            ("bhsa", "word", "voc_lex_utf8", "דָּבָר"),
            ("syrnt", "word", "lexeme", "ܟܬܒܐ"),
            ("tlhdig-tf", "analysis", "lemma", "pai-"),
            ("assyrian-royal-inscriptions", "word", "cf", "mātu"),
        ):
            self.assertEqual(cat.map_native(corpus, kind="entity", node=node,
                                            feature=feature, value=value), ())
        for corpus, node, feature in (
            ("bhsa", "lex", "lex"),
            ("bhsa", "lex", "gloss"),
            ("tlhdig-tf", "analysis", "gloss"),
            ("assyrian-royal-inscriptions", "word", "gw"),
            ("assyrian-royal-inscriptions", "word", "sense"),
        ):
            self.assertFalse(any(r.target in {ONTOLEX + "canonicalForm",
                             ONTOLEX + "writtenRep", ONTOLEX + "reference",
                             ONTOLEX + "denotes"} for r in cat.map_native(
                             corpus, kind="feature", node=node, feature=feature)))

if __name__ == "__main__":
    unittest.main()
