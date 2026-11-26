"""Scoped accounting is evidence-based and never claims complete eligibility."""
import unittest
from pathlib import Path

from scripts.pages.scoped_progress import scoped_progress, eligible_progress
from scripts.pages.build_progress import build_report, render
from tfont.xml_mappings import Mapping


def row(**kw):
    d = dict(corpus="demo", source="owner/demo", corpus_version="1",
             kind="value", node="word", feature="pos", value="N",
             relation="exact", target="http://purl.org/olia/olia.owl#Noun")
    d.update(kw)
    return Mapping(**d)


def inventory():
    return dict(schema_version=2, evidence_kind="loaded_tf_scoped_artifact",
                corpus_id="demo", repository="owner/demo", catalog_version="1",
                tf_version="1", revision="a"*40, tf_files_sha256="b"*64,
                node_types={"word": 4, "lex": 2},
                node_features={
                    "pos": {"categorical_values_requested": True, "scopes": {
                        "word": {"count": 4, "value_domain": "complete_observed", "values": {"N": 3, "V": 1}},
                        "lex": {"count": 2, "value_domain": "complete_observed", "values": {"N": 2}}}},
                    "form": {"scopes": {"word": {"count": 3}}},
                    "large": {"categorical_values_requested": True, "scopes": {
                        "word": {"count": 4, "value_domain": "overflow", "distinct_values_at_least": 3}}}},
                edge_features={
                    "parent": {"valued": False, "pairs": [
                        {"from": "word", "to": "lex", "count": 3},
                        {"from": "lex", "to": "word", "count": 2}]},
                    "choice": {"valued": True, "pairs": [
                        {"from": "word", "to": "lex", "count": 2, "value_domain": "complete_observed", "values": {"yes": 2}}]},
                    "omap@old-new": {"scope_status": "cross_version", "edge_count": 8}})


class ScopedProgressTests(unittest.TestCase):
    def test_scoped_values_and_frequency_not_multiplied(self):
        rows = [row(), row(target="http://purl.org/olia/olia.owl#CommonNoun"),
                row(value="V", relation="native-only", target=None),
                row(node="lex", corpus_version="0"), row(value="A"),
                row(feature="large", value="x")]
        s = scoped_progress(rows, inventory(), "owner/demo", "1")
        self.assertEqual(s["node_values"]["total"], 3)
        self.assertEqual(s["node_values"]["positive"], 1)
        self.assertEqual(s["node_values"]["reviewed"], 2)
        self.assertEqual(s["node_values"]["occurrences"], 6)
        self.assertEqual(s["node_values"]["positive_occurrences"], 3)
        self.assertEqual(s["node_values"]["reviewed_occurrences"], 4)
        self.assertEqual(s["outside_values"], [["word", "pos", "A"]])
        self.assertEqual(s["unmeasured_values"], [["word", "large", "x"]])
        self.assertEqual(s["overflow_domains"], [["word", "large"]])

    def test_guard_does_not_cover_type_and_edge_direction_is_preserved(self):
        rows = [row(kind="node", feature="form", value=None),
                row(kind="feature", node=None, value=None, feature="pos"),
                row(kind="edge", node=None, feature="parent", value=None, from_node="word", to_node="lex")]
        s = scoped_progress(rows, inventory(), "owner/demo", "1")
        self.assertEqual(s["node_types"]["positive"], 0)
        self.assertEqual(s["guarded_nodes"][0]["observations"], 3)
        self.assertEqual(s["guarded_nodes"][0]["node_count"], 4)
        self.assertEqual(s["node_features"]["positive"], 2)
        self.assertEqual(s["edge_pairs"]["positive"], 1)
        self.assertEqual(s["edge_pairs"]["total"], 3)
        self.assertEqual(s["edge_values"]["total"], 1)
        self.assertEqual(s["edge_values"]["positive"], 0)
        self.assertEqual(s["cross_version_edges"], ["omap@old-new"])

    def test_incompatible_source_revision_or_version_is_unknown(self):
        for source, version in (("other/demo", "1"), ("owner/demo", "2"),
                                ("owner/demo@" + "c"*40 + ":demo", "1"), ("owner/demo@unverified-tag", "1")):
            self.assertIsNone(scoped_progress([row()], inventory(), source, version))

    def test_eligibility_subset_and_ontology_specific_targets(self):
        rows = [row(), row(node="lex", target="http://www.w3.org/ns/lemon/ontolex#LexicalEntry"),
                row(value="V", relation="native-only", target=None)]
        policy = {"OLiA": [{"kind": "value", "features": ["pos"]}],
                  "OntoLex-Lemon": [{"kind": "value", "features": ["pos"], "nodes": ["lex"]}]}
        s = eligible_progress(rows, inventory(), policy, "1")
        self.assertEqual(s["OLiA"]["eligible"], 3)
        self.assertEqual(s["OLiA"]["exact"], 1)
        self.assertEqual(s["OLiA"]["global_nonpositive"], 1)
        self.assertEqual(s["OLiA"]["other_target"], 1)
        self.assertEqual(s["OntoLex-Lemon"]["eligible"], 1)
        self.assertEqual(s["OntoLex-Lemon"]["exact"], 1)
        self.assertNotIn("CRMtex", s)

    def test_partially_missing_rule_is_visible(self):
        s = eligible_progress([], inventory(),
                              {"OLiA": [{"kind": "value", "features": ["pos", "absent", "large"]}]},
                              "1")
        self.assertEqual(s["OLiA"]["eligible"], 3)
        self.assertEqual(s["OLiA"]["unmatched_rules"][0]["unobserved_features"], ["absent", "large"])

    def test_applicability_research_distinguishes_sign_flags_and_catalogue_metadata(self):
        import json
        root = Path(__file__).resolve().parents[2]
        policy = json.loads((root / "docs/research/data/scoped-applicability.json").read_text())
        from scripts.pages.scoped_progress import rule_matches
        def routed(corpus, ontology, key):
            return any(rule_matches(r, key) for r in policy["corpora"][corpus]["rules"].get(ontology, []))
        def node(kind, scope, feature=None, value=None):
            return (kind, scope, feature, value, None, None)
        def edge(kind, feature, source, target, value=None):
            return (kind, None, feature, value, source, target)
        self.assertTrue(routed("tlhdig-tf", "CRMtex", node("value", "sign", "agr", "1")))
        self.assertFalse(routed("tlhdig-tf", "OLiA", node("value", "sign", "agr", "1")))
        self.assertTrue(routed("tlhdig-tf", "OLiA", node("value", "analysis", "pos", "ADV")))
        self.assertTrue(routed("tlhdig-tf", "CRMinf", edge("edge_value", "witness_resolution", "line", "fragment", "ambiguous")))
        self.assertFalse(routed("tlhdig-tf", "LRMoo", edge("edge_value", "joined", "fragment", "fragment", "direct")))
        self.assertTrue(routed("assyrian-royal-inscriptions", "CIDOC CRM", node("feature", "document", "material")))
        self.assertFalse(routed("assyrian-royal-inscriptions", "CIDOC CRM", node("value", "document", "material", "clay")))
        self.assertTrue(routed("assyrian-royal-inscriptions", "SKOS", node("feature", "document", "genre")))
        self.assertTrue(routed("pseudepigrapha", "LRMoo", node("node", "chapter")))
        self.assertTrue(routed("pseudepigrapha", "SKOS", node("feature", "document_metadata", "historical_genres_json")))
        for model in policy["ontology_evidence"]:
            self.assertFalse(routed("pseudepigrapha", model, node("feature", "book", "source_sha256")))
            self.assertFalse(routed("tlhdig-tf", model, node("feature", "sign", "anchor")))

    def test_real_snapshots_and_report(self):
        root = Path(__file__).resolve().parents[2]
        report = build_report(root, "a"*40)
        self.assertEqual(report["totals"]["scoped_corpora"], 9)
        self.assertEqual(report["totals"]["scoped"]["node_values"]["total"], 1317)
        self.assertEqual(report["totals"]["scoped"]["edge_values"]["total"], 4)
        self.assertEqual(report["totals"]["scoped"]["node_features"]["total"], 739)
        self.assertEqual(report["totals"]["scoped"]["edge_pairs"]["total"], 73)
        c = {x["corpus"]: x for x in report["corpora"]}
        self.assertEqual(c["bhsa"]["scoped"]["node_values"]["total"], 459)
        self.assertEqual(c["tlhdig-tf"]["scoped"]["edge_values"]["total"], 4)
        self.assertEqual(c["assyrian-royal-inscriptions"]["scoped"]["tf_version"], "0.4.0")
        self.assertEqual(c["tlhdig-tf"]["applicability"]["classification"]["node_features"]["excluded"], 2)
        self.assertEqual(c["pseudepigrapha"]["applicability"]["classification"]["node_features"]["excluded"], 2)
        self.assertEqual(c["assyrian-royal-inscriptions"]["applicability"]["classification"]["node_features"]["excluded"], 1)
        for corpus in c.values():
            for kind, stat in corpus["applicability"]["classification"].items():
                self.assertEqual(stat["candidates"], stat["routed"] + stat["excluded"] + stat["unclassified"], (corpus["corpus"], kind))
            for model, stat in corpus["applicability"]["ontologies"].items():
                self.assertFalse(stat["unmatched_rules"], (corpus["corpus"], model))
                self.assertEqual(stat["eligible"], sum(stat[k] for k in ("exact", "qualified", "global_nonpositive", "ambiguous", "other_target", "unreviewed")))
        html = render(report)
        self.assertIn("Observed scoped coverage", html)
        self.assertIn("Ontology applicability review", html)
        self.assertIn("Incomplete", html)
