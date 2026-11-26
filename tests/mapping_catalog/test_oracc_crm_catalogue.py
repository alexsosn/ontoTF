"""ORACC catalogue semantics: field discovery, not individual identity."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

CORPUS = "assyrian-royal-inscriptions"
VERSION = "1.0.0"
CRM = "http://www.cidoc-crm.org/cidoc-crm/"
EXPECTED = {
    "document_key": ("close", "P1_is_identified_by"),
    "text_id": ("close", "P1_is_identified_by"),
    "source_id": ("close", "P1_is_identified_by"),
    "designation": ("close", "P1_is_identified_by"),
    "cdli_id": ("related", "P1_is_identified_by"),
    "material": ("related", "P45_consists_of"),
    "object_type": ("related", "P2_has_type"),
    "genre": ("related", "P2_has_type"),
    "subgenre": ("related", "P2_has_type"),
    "supergenre": ("related", "P2_has_type"),
}


class OraccCrmCatalogueTests(unittest.TestCase):
    def test_scoped_field_candidates_are_present_and_nonexecutable(self):
        root = Path(__file__).resolve().parents[2]
        evidence = json.loads((root / "docs/research/data/generated/scoped" /
                               (CORPUS + ".json")).read_text())
        self.assertEqual(evidence["catalog_version"], VERSION)
        self.assertEqual(evidence["revision"], "60db4b724a687c0f425e78eae924fce89454e106")
        from scripts.pages.scoped_progress import rule_matches
        policy = json.loads((root / "docs/research/data/scoped-applicability.json").read_text())
        rules = policy["corpora"][CORPUS]["rules"]["CIDOC CRM"]
        cat = MappingCatalog()
        for feature, (relation, name) in EXPECTED.items():
            with self.subTest(feature=feature):
                self.assertGreater(evidence["node_features"][feature]["scopes"]["document"]["count"], 0)
                self.assertTrue(any(rule_matches(rule, ("feature", "document", feature, None, None, None))
                                    for rule in rules))
                rows = cat.map_native(CORPUS, kind="feature", node="document",
                                      feature=feature, corpus_version=VERSION)
                matches = [r for r in rows if r.target == CRM + name]
                self.assertEqual(len(matches), 1)
                row, = matches
                self.assertEqual(row.relation, relation)
                self.assertEqual(row.corpus_version, VERSION)
                self.assertTrue(row.evidence)
                self.assertNotIn(row, cat.find_by_target(row.target, corpus=CORPUS,
                                                         kind="feature"))
                self.assertIn(row, cat.find_by_target(row.target, corpus=CORPUS,
                                                      kind="feature", include_approximate=True))
                with self.assertRaises(MappingError):
                    resolve_nodes(object(), row, corpus_version=VERSION)

    def test_identifier_fields_do_not_create_individual_identity_mappings(self):
        cat = MappingCatalog()
        for feature, value in (("text_id", "Q003840"), ("cdli_id", "P466002"),
                               ("document_key", "rinap/rinap5:Q003840")):
            self.assertEqual(cat.map_native(CORPUS, kind="entity", node="document",
                                            feature=feature, value=value,
                                            corpus_version=VERSION), ())
        # document_key is propagated to words but identifies their document,
        # not the word itself. The document selector does not match that scope.
        self.assertFalse(any(row.target == CRM + "P1_is_identified_by"
                             for row in cat.map_native(CORPUS, kind="feature",
                                                       node="word", feature="document_key")))
        # An explicit feature lookup never appears as a default node/value hit.
        self.assertTrue(all(row.kind != "feature" for row in
                            cat.find_by_target(CRM + "P1_is_identified_by",
                                               corpus=CORPUS, include_approximate=True)))


if __name__ == "__main__":
    unittest.main()
