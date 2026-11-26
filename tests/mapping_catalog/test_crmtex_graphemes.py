"""CRMtex 2.0 abstract text occurrence mappings must remain qualified."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

PIN = "ad69400f5446e1c8217af01659c7c10ab00c015b"
CRM = "http://www.cidoc-crm.org/extensions/crmtex/"
OCCURRENCE = CRM + "TX11_Grapheme_Occurrence"
SEQUENCE = CRM + "TX12_Grapheme_Sequence"
LETTER = "http://purl.org/olia/olia.owl#Letter"
LATIN = set("abdghiklmnpqrstuwyzġśšʿḏḥḫṣṭṯẓ")
UGARITIC = {chr(i) for i in range(0x10380, 0x1039e)}


class CrmtexCucTests(unittest.TestCase):
    def test_scoped_letter_occurrences_and_exclusions(self):
        c = MappingCatalog()
        root = Path(__file__).resolve().parents[2]
        data = json.loads((root / "docs/research/data/generated/scoped/cuc.json").read_text())
        self.assertEqual(data["revision"], PIN)
        self.assertEqual(data["node_types"]["sign"], 146017)
        from scripts.pages.scoped_progress import eligible_progress
        policy = json.loads((root / "docs/research/data/scoped-applicability.json").read_text())
        rules = policy["corpora"]["cuc"]["rules"]
        status = eligible_progress(c.load("cuc"), data, rules, "0.2.8")["CRMtex"]
        self.assertEqual(status["qualified"], 60)
        self.assertEqual(status["exact"], 0)
        actual = {(m.feature, m.value) for m in c.find_by_target(
            OCCURRENCE, corpus="cuc", include_approximate=True)}
        self.assertEqual(actual, {("sign", v) for v in LATIN}
                         | {("usign", v) for v in UGARITIC})
        self.assertEqual(c.find_by_target(OCCURRENCE, corpus="cuc"), ())
        for feature, letters in (("sign", LATIN), ("usign", UGARITIC)):
            values = data["node_features"][feature]["scopes"]["sign"]["values"]
            self.assertEqual(sum(values[v] for v in letters), 70872)
            for value in values:
                rows = c.map_native("cuc", node="sign", feature=feature,
                                    value=value, corpus_version="0.2.8")
                if value in letters:
                    row, = (m for m in rows if m.target == OCCURRENCE)
                    self.assertEqual(row.relation, "close")
                    self.assertIn(PIN, row.evidence)
                    self.assertTrue(any(m.target == LETTER and m.relation == "exact" for m in rows))
                    with self.assertRaisesRegex(MappingError, "exact"):
                        resolve_nodes(object(), row, corpus_version="0.2.8")
                else:
                    self.assertFalse(any(m.target and m.target.startswith(CRM) for m in rows))
        self.assertFalse(any(m.target in {CRM+"TX8_Grapheme", CRM+"TX9_Glyph",
                                         CRM+"TX1_Written_Text", CRM+"TX7_Written_Text_Fragment"}
                             for m in c.load("cuc")))
        self.assertEqual(c.map_native("cuc", kind="entity", node="sign",
                                      feature="usign", value="𐎀"), ())

    def test_guarded_text_sequence_views_are_not_exact_physical_or_token_identity(self):
        c = MappingCatalog()
        for corpus, feature, version in (
                ("cuc", "g_cons", "0.2.8"),
                ("tlhdig-tf", "trans", "0.4.0"),
                ("assyrian-royal-inscriptions", "form", "1.0.0")):
            rows = c.map_native(corpus, kind="node", node="word", feature=feature,
                                corpus_version=version)
            mapping, = (m for m in rows if m.target == SEQUENCE)
            self.assertEqual(mapping.relation, "close")
            self.assertFalse(any(m.target == SEQUENCE for m in c.map_native(
                corpus, kind="node", node="word")))
            with self.assertRaisesRegex(MappingError, "exact"):
                resolve_nodes(object(), mapping, corpus_version=version)
        hits = c.find_correspondences("cuc", "tlhdig-tf", kind="node",
                                      node="word", feature="g_cons",
                                      include_approximate=True)
        self.assertTrue(any(m.target == SEQUENCE and m.scope == "category"
                            and m.relation == "approximate-via-target" for m in hits))
        self.assertFalse(any(m.target == SEQUENCE for m in c.find_correspondences(
            "cuc", "tlhdig-tf", kind="node", node="word", feature="g_cons")))


if __name__ == "__main__":
    unittest.main()
