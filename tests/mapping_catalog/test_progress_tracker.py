"""Progress page counts categories, not declarations or token occurrences."""
import unittest
from pathlib import Path

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
        self.assertEqual(ontology("http://www.cidoc-crm.org/extensions/crmtex/TX1_Written_Text"), "CRMtex")
        self.assertEqual(ontology("http://www.cidoc-crm.org/extensions/crminf/I1_Argumentation"), "CRMinf")
        self.assertEqual(ontology("https://example.org/olia#Noun"), "Other")
        self.assertEqual(ontology("http://www.cidoc-crm.org/crmtex/TX1_Written_Text"), "Other")

    def test_explicit_revision_mismatch_and_individual_candidates(self):
        inv = dict(version="1", revision="a"*40, node_types=["word"],
                   node_features=["pos"], edge_features=[], source="snapshot")
        s = summarize([self.row(), self.row(kind="entity", target="https://example.org/id/1")],
                      inv, "1", source_revision="b"*40)
        self.assertEqual(s["declarations"], 2)
        self.assertEqual(s["individual_declarations"], 1)
        self.assertEqual(s["reviewed"], 1)
        self.assertEqual(s["positive"], 1)
        self.assertIsNone(s["schema_total"])
        self.assertEqual(s["ontologies"]["Other"]["selectors"], 0)

    def test_observed_value_domains_do_not_multiply_scopes_or_claim_open_domains(self):
        inv = dict(version="1", node_types=["word", "lex"], node_features=["pos"], edge_features=[],
                   source="snapshot", value_domains={"pos": {"values": ["N", "V", "A"],
                                                              "scopes": ["word", "lex"]}})
        rows = [self.row(), self.row(node="lex"), self.row(value="V", relation="native-only", target=None),
                self.row(value="X"), self.row(value="A", corpus_version="0")]
        s = summarize(rows, inv, "1")
        self.assertEqual(s["schema_breakdown"]["feature"], {"total": 1, "reviewed": 1, "positive": 1})
        domain, = s["value_domains"]
        self.assertEqual(domain["total"], 3)
        self.assertEqual(domain["positive"], 1)
        self.assertEqual(domain["reviewed"], 2)
        self.assertEqual(domain["unreviewed"], ["A"])
        self.assertEqual(domain["outside_inventory"], ["X"])
        self.assertEqual(domain["scopes"], ["word", "lex"])
        self.assertEqual(domain["ontologies"]["OLiA"], 1)
        self.assertEqual(summarize(rows, None, "1")["value_domains"], [])

    def test_real_repo_report_and_html(self):
        root = Path(__file__).resolve().parents[2]
        report = build_report(root, "a" * 40)
        by_name = {c["corpus"]: c for c in report["corpora"]}
        self.assertGreaterEqual(len(by_name), 9)
        self.assertGreater(by_name["bhsa"]["ontologies"]["OLiA"]["selectors"], 100)
        self.assertEqual(by_name["cuc"]["schema_total"], 21)
        self.assertEqual(by_name["peshitta"]["schema_total"], 13)
        self.assertEqual(by_name["assyrian-royal-inscriptions"]["schema_total"], 93)
        self.assertEqual(by_name["assyrian-royal-inscriptions"]["version"], "1.0.0")
        self.assertEqual(by_name["assyrian-royal-inscriptions"]["inventory"]["tf_version"], "0.4.0")
        self.assertEqual(by_name["tlhdig-tf"]["schema_total"], 153)
        self.assertEqual(report["totals"]["reviewed"], sum(c["reviewed"] for c in by_name.values()))
        html = render(report)
        for word in ("Coverage by corpus", "Ontology coverage", "Annotation coverage",
                     "Applicability research", "aaaaaaaaaaaa", "progress.json"):
            self.assertIn(word, html)
        self.assertNotIn("<script", html)
        self.assertNotIn(".xml", html)
        self.assertNotIn("Historical semantic work plan", html)
        self.assertNotIn("TFont", html)
        self.assertIn("<details>", html)
        self.assertIn('aria-hidden="true"', html)
        report["corpora"][0]["corpus"] = "<img src=x onerror=alert(1)>"
        self.assertNotIn("<img src=x", render(report))

    def test_dashboard_distinguishes_missing_empty_and_zero(self):
        from scripts.pages.dashboard import coverage_bar, ontology_cell
        self.assertIn("Unknown", coverage_bar(None))
        self.assertIn("No observed items", coverage_bar(dict(total=0)))
        self.assertIn("0.0%", coverage_bar(dict(total=10, exact=0, qualified=0,
                                                nonpositive=0, unreviewed=10)))
        self.assertIn("Not assessed", ontology_cell(None))
        empty = dict(eligible=0, exact=0, qualified=0, global_nonpositive=0,
                     ambiguous=0, other_target=0, unreviewed=0, unmatched_rules=[])
        self.assertIn("Empty scope", ontology_cell(empty))
        self.assertIn("0.0%", ontology_cell(dict(empty, eligible=5, other_target=5)))
        self.assertIn("5 other ontology", ontology_cell(dict(empty, eligible=5, other_target=5)))

    def test_dashboard_bar_has_distinct_review_and_mapping_segments(self):
        from scripts.pages.dashboard import coverage_bar
        html = coverage_bar(dict(total=10, exact=2, qualified=1, nonpositive=3, unreviewed=4))
        for expected in ("30.0%", "3 / 10", "2 exact", "1 qualified",
                         "3 without positive match", "4 unreviewed"):
            self.assertIn(expected, html)
        self.assertIn('width:20%', html)
        self.assertIn('width:40%', html)
        self.assertNotIn("60.0% mapped", html)
