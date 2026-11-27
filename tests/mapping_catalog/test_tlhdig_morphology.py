"""Source-observed HFR morphological tags on candidate analysis nodes."""
import unittest
from ontotf.xml_mappings import MappingCatalog, MappingError, resolve_nodes

CORPUS = "tlhdig-tf"
VERSION = "0.4.0"
OLIA = "http://purl.org/olia/olia.owl#"
PIN = "e954600d9f9cc7f16570729813cf6bf3954b8f6d"
# Explicit source tags, not an implicit parser of arbitrary tag strings.
EXACT = {"ADV":"Adverb", "POSP":"Postposition", "CNJ":"Conjunction",
         "QUANcar":"CardinalNumber", "ABL":"AblativeCase",
         "INS":"InstrumentalCase", "ALL":"AllativeCase"}
QUALIFIED = {
    "2SG.IMP": {"Second":"narrower", "Singular":"narrower",
                 "ImperativeVerb":"narrower", "ImperativeMood":"narrower"},
    "3SG.PRS": {"Third":"narrower", "Singular":"narrower", "Present":"close"},
    "3SG.PRS.MP": {"Third":"narrower", "Singular":"narrower", "Present":"close",
                   "MediopassiveVoice":"close"},
    "D/L.SG": {"Singular":"narrower"},
    "ACC.SG.C": {"Accusative":"narrower", "Singular":"narrower", "CommonGender":"close"},
    "PTCP.NOM.SG.C": {"Participle":"narrower", "Nominative":"narrower",
                      "Singular":"narrower", "CommonGender":"close"},
    "GEN.SG": {"GenitiveCase":"narrower", "Singular":"narrower"},
}
NATIVE = ("NEG", "PREV", "STF", "{ a → 3SG.PRS} { b → 2SG.IMP}",
          "{ a → …:ABL} { b → …:INS}",
          "{ a → GEN.SG} { b → GEN.PL} { c → D/L.PL}")

class TLHdigMorphologyTests(unittest.TestCase):
    def setUp(self):
        self.catalog = MappingCatalog()

    def rows(self, value):
        return self.catalog.map_native(CORPUS, node="analysis", feature="morph",
                                       value=value, corpus_version=VERSION)

    def test_exact_single_labels(self):
        for value, cls in EXACT.items():
            with self.subTest(value=value):
                row, = self.rows(value)
                self.assertEqual((row.relation, row.target), ("exact", OLIA + cls))
                self.assertIn(PIN, row.evidence)
                self.assertEqual(row.corpus_version, VERSION)

    def test_compound_annotations_do_not_become_exact_single_categories(self):
        for value, expected in QUALIFIED.items():
            with self.subTest(value=value):
                rows = self.rows(value)
                self.assertEqual({r.target.removeprefix(OLIA): r.relation for r in rows}, expected)
                for row in rows:
                    self.assertIn(PIN, row.evidence)
                    self.assertNotIn(row, self.catalog.find_by_target(row.target))
                    with self.assertRaisesRegex(MappingError, "exact"):
                        resolve_nodes(object(), row, corpus_version=VERSION)

    def test_alternatives_and_syncretism_remain_visible(self):
        for value in NATIVE:
            with self.subTest(value=value):
                row, = self.rows(value)
                self.assertEqual((row.relation, row.target), ("native-only", None))
        self.assertEqual({r.target for r in self.rows("D/L.SG")}, {OLIA + "Singular"})
        self.assertFalse(any(r.target in {OLIA+"MiddleVoice", OLIA+"PassiveVoice"}
                             for r in self.rows("3SG.PRS.MP")))
        self.assertEqual(self.catalog.map_native(CORPUS, node="word",
                         feature="morph", value="ADV", corpus_version=VERSION), ())
        self.assertEqual(self.catalog.map_native(CORPUS, node="analysis",
                         feature="clitic_morph", value="ADV", corpus_version=VERSION), ())
        self.assertEqual(self.rows("9SG.PRS"), ())

    def test_exact_execution_preserves_analysis_carrier(self):
        row, = self.rows("ABL")
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(kind):
                        assert kind == "analysis"
                        return (10, 11, 12)
            @staticmethod
            def Fs(name):
                assert name == "morph"
                class Feature:
                    @staticmethod
                    def v(n):
                        return {10:"ABL", 11:"{ a → …:ABL} { b → …:INS}", 12:"INS"}[n]
                return Feature()
        self.assertEqual(resolve_nodes(API(), row, corpus_version=VERSION), (10,))
        with self.assertRaisesRegex(MappingError, "version"):
            resolve_nodes(API(), row, corpus_version="0.3")

    def test_batch_is_explicit_and_versioned(self):
        expected = ["ADV","POSP","CNJ","QUANcar","ABL","INS","ALL","2SG.IMP","3SG.PRS","3PL.PRS","3SG.PRS.MP","3SG.PST","3PL.PRS.MP","1SG.PRS.MP","3SG.IMP","3PL.PST","1SG.PST","2SG.PRS","2PL.IMP","3SG.PRS.IMPF","1SG.PRS","3SG.IMP.MP","3PL.PRS.IMPF","2SG.PST","3PL.IMP","1PL.PST","1PL.PRS","2PL.PRS","2PL.PST","D/L.SG","ACC.SG.C","PTCP.NOM.SG.C","GEN.SG","PTCP.ACC.SG.C","NOM.PL.C","NOM.SG.C","GEN.PL","ACC.PL.C","D/L.SG.C","D/L.PL","D/L.SG.N","NEG","PREV","STF","{ a → 3SG.PRS} { b → 2SG.IMP}","{ a → …:ABL} { b → …:INS}","{ a → GEN.SG} { b → GEN.PL} { c → D/L.PL}","{ a → NOM.SG(UNM)} { b → ACC.SG(UNM)} { c → NOM.PL(UNM)} { d → ACC.PL(UNM)} { e → GEN.SG(UNM)} { f → GEN.PL(UNM)} { g → D/L.SG(UNM)} { h → D/L.PL(UNM)} { i → ALL(UNM)} { j → ABL(UNM)} { k → INS(UNM)} { l → VOC.SG(UNM)} { m → VOC.PL(UNM)}"]
        rows = [r for r in self.catalog.load(CORPUS) if r.kind == "value"
                and r.node == "analysis" and r.feature == "morph"]
        self.assertEqual({r.value for r in rows if r.value in expected}, set(expected))
        self.assertEqual(len([r for r in rows if r.value in expected]), 121)
        self.assertTrue(all(r.corpus_version == VERSION and PIN in r.evidence for r in rows))
        self.assertEqual(sum(r.relation == "exact" for r in rows), 7)

    def test_second_batch_common_alternative_properties_only(self):
        cases = {
            "{ a → PTCP.NOM.SG.N} { b → PTCP.ACC.SG.N} { c → PTCP.INDCL}": {"Participle": "narrower"},
            "{ a → PTCP.NOM.PL.N} { b → PTCP.ACC.PL.N} { c → PTCP.STF}": {"Participle": "narrower"},
            "{ a → NOM.COLL.C} { b → ACC.COLL.C}": {"CommonGender": "close"},
            "{ a → NOM.PL.C} { b → ACC.PL.C}": {"Plural": "narrower", "CommonGender": "close"},
            "{ a → 2SG.PST} { b → 3SG.PST}": {"Singular": "narrower", "Past": "close"},
            "{ a → 3SG.PRS} { b → 3SG.PST} { c → 3PL.PRS}": {"Third": "narrower"},
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                rows = self.rows(value)
                self.assertEqual({r.target.removeprefix(OLIA): r.relation for r in rows}, expected)
                for row in rows:
                    self.assertIn(PIN, row.evidence)
                    self.assertNotIn(row, self.catalog.find_by_target(row.target))
                    with self.assertRaisesRegex(MappingError, "exact"):
                        resolve_nodes(object(), row, corpus_version=VERSION)
        for value in ("HURR.ESS||HITT.D/L.SG", "{ a → HURR.ABS.SG} { b → STF}",
                      "{ a → ACC.SG.C} { b → GEN.PL}"):
            row, = self.rows(value)
            self.assertEqual((row.relation, row.target), ("ambiguous", None))
