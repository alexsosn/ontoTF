"""BHSA pinned 2021 lexical-set category coverage, with no lexical identity inference."""
import unittest

from tfont.xml_mappings import MappingCatalog

OLIA = "http://purl.org/olia/olia.owl#"
PIN = "4db00e2157915495e1a4d3d57e41223df24775da"

# Exact observed domain from r005/bhsa.json for ETCBC/bhsa@PIN (ls feature).
OBSERVED = frozenset({
    "afad", "card", "cjad", "focp", "gntl", "mult", "nmcp",
    "nmdi", "none", "ordn", "padv", "ppre", "ques", "quot", "vbcp",
})
SHARED = {
    "card": "CardinalNumber",
    "ordn": "OrdinalNumber",
    "ques": "InterrogativeParticle",
}


class BHSAObservedLexicalSetTests(unittest.TestCase):
    def test_every_observed_source_code_on_both_documented_node_kinds(self):
        c = MappingCatalog()
        for node in ("word", "lex"):
            for code in OBSERVED:
                with self.subTest(node=node, value=code):
                    m = c.map_native("bhsa", node=node, feature="ls", value=code)
                    self.assertEqual(len(m), 1)
                    row = m[0]
                    self.assertIn(PIN, row.evidence)
                    if code in SHARED:
                        self.assertEqual(
                            (row.relation, row.target),
                            ("exact", OLIA + SHARED[code]),
                        )
                    else:
                        self.assertEqual((row.relation, row.target),
                                         ("native-only", None))
        ls_rows = [r for r in c.load("bhsa")
                   if r.kind == "value" and r.feature == "ls"]
        self.assertEqual(
            {(r.node, r.value) for r in ls_rows},
            {(node, code) for node in ("word", "lex") for code in OBSERVED},
        )

    def test_categories_join_without_inventing_finer_semantics(self):
        c = MappingCatalog()
        for node in ("word", "lex"):
            match = c.find_correspondences(
                "bhsa", "syrnt", node=node, feature="ls", value="card"
            )
            self.assertIn(
                ("nmtyp", "cardinal", "category", "exact"),
                {(r.destination.feature, r.destination.value, r.scope,
                  r.relation) for r in match},
            )
            # Source 'mult' is noun of multitude, NOT a multiplicative numeral.
            self.assertEqual(
                c.find_correspondences(
                    "bhsa", "tlhdig-tf", node=node,
                    feature="ls", value="mult", include_approximate=True
                ), ()
            )
            # Potential adverb must not be promoted to a concrete Adverb.
            self.assertEqual(
                c.find_correspondences(
                    "bhsa", "tlhdig-tf", node=node,
                    feature="ls", value="padv", include_approximate=True
                ), ()
            )
            self.assertEqual(c.map_native(
                "bhsa", kind="entity", node=node, feature="ls", value="card"
            ), ())


if __name__ == "__main__":
    unittest.main()
