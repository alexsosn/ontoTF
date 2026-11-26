"""Progress page counts categories, not declarations or token occurrences."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.pages.build_progress import build_report, render, summarize, ontology
from tfont.xml_mappings import Mapping


class ProgressTrackerTests(unittest.TestCase):
    def row(self, **kw):
        fields = dict(corpus="demo", source="example/demo", corpus_version="1",
                      kind="value", node="word", feature="pos", value="N",
                      relation="exact", target="http://purl.org/olia/olia.owl#Noun")
        fields.update(kw)
        return Mapping(**fields)

    def test_duplicates_scope_versions_and_nonmatching(self):
        rows = [self.row(), self.row(target="http://purl.org/olia/olia.owl#CommonNoun"),
                self.row(node="lex", relation="narrower"),
                self.row(value="V", relation="native-only", target=None),
                self.row(value="A", relation="ambiguous"),
                self.row(corpus_version="0"),
                self.row(kind="node", feature="surface", value=None),
                self.row(kind="edge", node=None, feature="parent", value=None,
                         from_node="word", to_node="lex",
                         target="http://www.cidoc-crm.org/cidoc-crm/P46_is_composed_of")]
        inventory = dict(version="1", node_types=["word", "lex"], node_features=["pos", "surface"],
                         edge_features=["parent"], source="snapshot")
        s = summarize(rows, inventory, "1")
        self.assertEqual(s["declarations"], 8)
        self.assertEqual(s["reviewed"], 7)
        self.assertEqual(s["exact"], 4)
        self.assertEqual(s["qualified"], 1)
        self.assertEqual(s["nonpositive"], 2)
        self.assertEqual(s["ontologies"]["OLiA"]["selectors"], 4)
        self.assertEqual(s["schema_total"], 5)
        self.assertEqual(s["schema_positive"], 3)
        self.assertEqual(s["ontologies"]["OLiA"]["schema"], 2)
        self.assertEqual(s["ontologies"]["CIDOC CRM"]["schema"], 1)
        self.assertIn("feature:surface", s["schema_unmapped"])

    def test_unknown_and_mismatched_inventory(self):
        for inventory in (None, dict(version="0", node_types=["word"],
                                     node_features=["pos"], edge_features=[], source="old")):
            s = summarize([self.row()], inventory, "1")
            self.assertIsNone(s["schema_total"])
            self.assertIsNone(s["schema_positive"])
            self.assertEqual(s["reviewed"], 1)

    def test_ontology_namespace_and_unknown(self):
        self.assertEqual(ontology("http://www.w3.org/2004/02/skos/core#Concept"), "SKOS")
        self.assertEqual(ontology("http://iflastandards.info/ns/lrm/lrmoo/F2_Expression"), "LRMoo")
        self.assertEqual(ontology("https://example.org/olia#Noun"), "Other")

    def test_real_repo_report_and_html(self):
        root = Path(__file__).resolve().parents[1]
        report = build_report(root, "a" * 40)
        by_name = {c["corpus"]: c for c in report["corpora"]}
        self.assertGreaterEqual(len(by_name), 9)
        self.assertGreater(by_name["bhsa"]["ontologies"]["OLiA"]["selectors"], 100)
        self.assertEqual(by_name["cuc"]["schema_total"], 21)
        self.assertEqual(by_name["peshitta"]["schema_total"], 13)
        self.assertEqual(by_name["assyrian-royal-inscriptions"]["schema_total"], 93)
        self.assertEqual(by_name["tlhdig-tf"]["schema_total"], 153)
        self.assertEqual(report["totals"]["reviewed"], sum(c["reviewed"] for c in by_name.values()))
        html = render(report)
        for word in ("Corpus × ontology", "Schema coverage", "native-only", "934",
                     "aaaaaaaaaaaa", "progress.json"):
            self.assertIn(word, html)
        self.assertNotIn("<script", html)
        report["corpora"][0]["corpus"] = "<img src=x onerror=alert(1)>"
        self.assertNotIn("<img src=x", render(report))
