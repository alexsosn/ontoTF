"""HFR enclitic tags retain their own analysis scope and qualified semantics."""
import unittest
from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

PIN = "e954600d9f9cc7f16570729813cf6bf3954b8f6d"
OLIA = "http://purl.org/olia/olia.owl#"
CASES = {
    "CNJadd": {
        "Conjunction": "close"
    },
    "CNJctr": {
        "Conjunction": "close"
    },
    "PPRO.3SG.C.ACC": {
        "Pronoun": "narrower",
        "Third": "narrower",
        "Singular": "narrower",
        "CommonGender": "close",
        "Accusative": "narrower"
    },
    "PPRO.3PL.C.ACC": {
        "Pronoun": "narrower",
        "Third": "narrower",
        "Plural": "narrower",
        "CommonGender": "close",
        "Accusative": "narrower"
    },
    "PPRO.3SG.D/L": {
        "Pronoun": "narrower",
        "Third": "narrower",
        "Singular": "narrower"
    },
    "PPRO.3PL.D/L": {
        "Pronoun": "narrower",
        "Third": "narrower",
        "Plural": "narrower"
    },
    "{ R → PPRO.3SG.C.NOM} { S → PPRO.3PL.C.ACC}": {
        "Pronoun": "narrower",
        "Third": "narrower",
        "CommonGender": "close"
    },
    "{ R → PPRO.3SG.N.NOM} { S → PPRO.3SG.N.ACC} { T → PPRO.3PL.C.NOM} { U → PPRO.3PL.N.NOM} { V → PPRO.3PL.N.ACC}": {
        "Pronoun": "narrower",
        "Third": "narrower"
    },
    "POSS.3SG.ALL.SG": {
        "PossessivePronoun": "related"
    },
    "REFL": {},
    "OBPk": {},
    "OBPs": {},
    "OBPst": {},
    "FOC": {},
    "QUOT": {}
}

class TLHdigCliticTests(unittest.TestCase):
    def test_explicit_scope_and_qualified_dispositions(self):
        c = MappingCatalog()
        for value, expected in CASES.items():
            with self.subTest(value=value):
                rows = c.map_native("tlhdig-tf", node="analysis", feature="clitic_morph",
                                    value=value, corpus_version="0.4.0")
                self.assertTrue(rows)
                self.assertTrue(all(PIN in r.evidence and r.corpus_version == "0.4.0"
                                    for r in rows))
                if expected:
                    self.assertEqual({r.target.removeprefix(OLIA): r.relation for r in rows},
                                     expected)
                else:
                    row, = rows
                    self.assertEqual((row.relation, row.target), ("native-only", None))
                for row in rows:
                    self.assertNotEqual(row.relation, "exact")
                    with self.assertRaises(MappingError):
                        resolve_nodes(object(), row, corpus_version="0.4.0")
                self.assertEqual(c.map_native("tlhdig-tf", node="word", feature="clitic_morph",
                                              value=value, corpus_version="0.4.0"), ())

    def test_chain_and_host_not_inferred(self):
        c = MappingCatalog()
        for value in ("CNJctr=REFL", "CNJadd=PPRO.3SG.C.ACC"):
            self.assertEqual(c.map_native("tlhdig-tf", node="analysis", feature="clitic_morph",
                                          value=value, corpus_version="0.4.0"), ())
        self.assertEqual(c.map_native("tlhdig-tf", node="analysis", feature="morph",
                                      value="PPRO.3SG.C.ACC", corpus_version="0.4.0"), ())
