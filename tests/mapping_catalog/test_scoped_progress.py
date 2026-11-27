"""Scoped accounting is evidence-based and never claims complete eligibility."""
import unittest
from pathlib import Path

from scripts.pages.scoped_progress import scoped_progress, eligible_progress
from scripts.pages.build_progress import build_report, render
from ontotf.xml_mappings import Mapping


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

    def test_etcbc_granularity_distinguishes_labels_counts_and_morphemes(self):
        import json
        from scripts.pages.scoped_progress import rule_matches
        root = Path(__file__).resolve().parents[2]
        policy = json.loads((root / "docs/research/data/scoped-applicability.json").read_text())
        def routed(corpus, model, key):
            return any(rule_matches(r, key) for r in policy["corpora"][corpus]["rules"].get(model, []))
        def excluded(corpus, key):
            return any(rule_matches(r, key) for r in policy["corpora"][corpus].get("exclusions", []))
        def key(kind, node, feature=None, value=None):
            return (kind, node, feature, value, None, None)
        self.assertTrue(routed("bhsa", "LRMoo", key("feature", "book", "book@he")))
        self.assertFalse(routed("bhsa", "SKOS", key("feature", "book", "book@he")))
        self.assertTrue(excluded("bhsa", key("feature", "lex", "freq_lex")))
        self.assertFalse(routed("bhsa", "OntoLex-Lemon", key("feature", "lex", "freq_lex")))
        self.assertTrue(excluded("bhsa", key("feature", "word", "freq_occ")))
        self.assertTrue(excluded("bhsa", key("feature", "word", "rank_occ")))
        self.assertTrue(excluded("bhsa", key("value", "word", "language", "Hebrew")))
        self.assertTrue(routed("bhsa", "OLiA", key("feature", "lex", "language")))
        self.assertTrue(routed("bhsa", "OLiA", key("value", "clause_atom", "is_root", "true")))
        self.assertTrue(excluded("bhsa", key("value", "clause", "dist_unit", "words")))
        self.assertTrue(routed("syriac", "OLiA", key("feature", "word", "g_emf")))
        self.assertTrue(routed("syrnt", "CRMtex", key("feature", "word", "word_sedra")))
        self.assertTrue(routed("cuc", "CRMtex", key("value", "sign", "cont", "continued")))
        self.assertTrue(routed("peshitta", "OLiA", key("node", "word")))
        # Independent direct blob comparison established byte-identical
        # data payloads at the pinned versions; do not require a second
        # mapping of those duplicate native annotations.
        for corpus in ("bhsa", "extrabiblical"):
            for name in ("suffix_gender", "suffix_number", "suffix_person"):
                self.assertTrue(excluded(corpus, key("feature", "word", name)))
                self.assertTrue(excluded(corpus, key("value", "word", name, "NA")))
        self.assertTrue(excluded("bhsa", key("value", "word", "suffix_gender", "m")))
        self.assertFalse(routed("bhsa", "OLiA", key("value", "word", "suffix_gender", "m")))
        self.assertTrue(routed("bhsa", "OLiA", key("value", "word", "prs_gn", "m")))

    def test_converter_granularity_preserves_editorial_and_source_identity_distinctions(self):
        import json
        from scripts.pages.scoped_progress import rule_matches
        root = Path(__file__).resolve().parents[2]
        policy = json.loads((root / "docs/research/data/scoped-applicability.json").read_text())
        def routed(corpus, model, key):
            return any(rule_matches(r, key) for r in policy["corpora"][corpus]["rules"].get(model, []))
        def excluded(corpus, key):
            return any(rule_matches(r, key) for r in policy["corpora"][corpus].get("exclusions", []))
        def key(kind, node, feature=None, value=None):
            return (kind, node, feature, value, None, None)

        # ORACC source identifiers and rights, source section vs synthetic anchor.
        o = "assyrian-royal-inscriptions"
        self.assertTrue(routed(o, "CIDOC CRM", key("feature", "document", "document_key")))
        self.assertTrue(routed(o, "CIDOC CRM", key("feature", "translation_unit", "translation_source_license")))
        self.assertTrue(routed(o, "CRMtex", key("value", "chunk", "implicit", "yes")))
        self.assertTrue(excluded(o, key("value", "sign", "synthetic", "1")))
        self.assertTrue(excluded(o, key("value", "word", "lang", "qcu-949")))
        self.assertTrue(excluded(o, key("feature", "sign", "readingu")))
        self.assertTrue(routed(o, "LRMoo", key("feature", "translation_unit", "translation_sref")))

        # OCP generated empty anchors are not lacunae; witness-list serialization
        # and ordinal indices do not create extra semantic mapping obligations.
        p = "pseudepigrapha"
        self.assertTrue(excluded(p, key("value", "word", "is_gap", "1")))
        self.assertFalse(routed(p, "CRMtex", key("value", "word", "is_gap", "1")))
        self.assertTrue(excluded(p, key("feature", "reading", "mss")))
        self.assertTrue(routed(p, "LRMoo", key("feature", "book", "generated_language")))
        self.assertTrue(routed(p, "SKOS", key("feature", "document_metadata", "intro_themes_json")))
        self.assertTrue(routed(p, "CRMinf", key("feature", "document_metadata", "intro_corrections_json")))

        # TLHdig parser status is distinct from a philological uncertainty.
        t = "tlhdig-tf"
        self.assertTrue(excluded(t, key("value", "analysis", "parse_ok", "0")))
        self.assertTrue(routed(t, "CRMinf", key("value", "cluster", "from_open_marker", "0")))
        self.assertTrue(routed(t, "CRMtex", key("value", "cluster", "crossesline", "1")))
        self.assertTrue(routed(t, "CIDOC CRM", key("value", "fragment", "fragment_kind", "invnr")))
        self.assertFalse(routed(t, "OLiA", key("value", "word", "sel_group", "sg")))
        self.assertFalse(excluded(t, key("value", "word", "sel_group", "sg")))
        self.assertTrue(excluded(t, key("feature", "document", "docid_raw")))
        self.assertTrue(routed(t, "CRMtex", key("feature", "cluster", "width")))
        self.assertFalse(routed(t, "OLiA", key("value", "word", "mrpsel_kind", "DEL")))
        self.assertTrue(routed(t, "CRMinf", key("value", "word", "mrpsel_kind", "DEL")))

    def test_real_snapshots_and_report(self):
        root = Path(__file__).resolve().parents[2]
        report = build_report(root, "a"*40)
        self.assertEqual(report["totals"]["scoped_corpora"], 9)
        self.assertEqual(report["totals"]["scoped"]["node_values"]["total"], 5898)
        self.assertEqual(report["totals"]["scoped"]["edge_values"]["total"], 4)
        self.assertEqual(report["totals"]["scoped"]["node_features"]["total"], 740)
        self.assertEqual(report["totals"]["scoped"]["edge_pairs"]["total"], 73)
        c = {x["corpus"]: x for x in report["corpora"]}
        self.assertEqual(c["bhsa"]["scoped"]["node_values"]["total"], 459)
        self.assertEqual(c["tlhdig-tf"]["scoped"]["edge_values"]["total"], 4)
        tlh = c["tlhdig-tf"]
        morph = next(d for d in tlh["scoped"]["domains"]
                     if d["node"] == "analysis" and d["feature"] == "morph")
        self.assertEqual((morph["total"], morph["occurrences"]), (4581, 1357004))
        self.assertEqual((morph["positive"], morph["reviewed"]), (47, 57))
        self.assertEqual((morph["positive_occurrences"], morph["reviewed_occurrences"]),
                         (413526, 728190))
        self.assertEqual(morph["unreviewed"], 4524)
        self.assertEqual(len(morph["unreviewed_values"]), 4524)
        self.assertEqual(len(morph["top_unreviewed_values"]), 8)
        self.assertFalse(any(row[:2] == ["analysis", "morph"]
                             for row in tlh["scoped"]["unmeasured_values"]))
        self.assertFalse(any(key[:3] == ["value", "analysis", "morph"]
                             for key in tlh["applicability"]["unclassified_items"]))
        self.assertEqual(c["assyrian-royal-inscriptions"]["scoped"]["tf_version"], "0.4.0")
        for name in ("tlhdig-tf", "pseudepigrapha", "assyrian-royal-inscriptions"):
            self.assertGreater(c[name]["applicability"]["classification"]["node_features"]["excluded"], 0)
        self.assertEqual(c["tlhdig-tf"]["scoped"]["edge_values"]["reviewed"], 4)
        for corpus in c.values():
            for kind, stat in corpus["applicability"]["classification"].items():
                self.assertEqual(stat["candidates"], stat["routed"] + stat["excluded"] + stat["unclassified"], (corpus["corpus"], kind))
            for model, stat in corpus["applicability"]["ontologies"].items():
                self.assertFalse(stat["unmatched_rules"], (corpus["corpus"], model))
                self.assertEqual(stat["eligible"], sum(stat[k] for k in ("exact", "qualified", "global_nonpositive", "ambiguous", "other_target", "unreviewed")))
        html = render(report)
        self.assertIn("Coverage by annotation type", html)
        self.assertIn("Ontology coverage", html)
        self.assertIn("All applicability research is partial", html)
        self.assertIn("Morphological analysis tags", html)
        self.assertIn("413,526 / 1,357,004", html)
        self.assertIn("candidate analyses", html)

    def test_large_measured_domain_ranks_gaps_without_rendering_every_raw_tag(self):
        from scripts.pages.dashboard import domain_gaps
        data = inventory()
        values = {f"raw-{i:04d}": i + 1 for i in range(600)}
        data["node_features"]["morph"] = {"scopes": {"word": {
            "count": sum(values.values()), "value_domain": "complete_observed",
            "values": values}}}
        rows = [row(feature="morph", value="raw-0599"),
                row(feature="morph", value="raw-0598", relation="ambiguous", target=None)]
        result = scoped_progress(rows, data, "owner/demo", "1")
        domain = next(d for d in result["domains"] if d["feature"] == "morph")
        self.assertEqual(domain["total"], 600)
        self.assertEqual(domain["positive_occurrences"], 600)
        self.assertEqual(domain["unreviewed"], 598)
        self.assertEqual(len(domain["unreviewed_values"]), 598)
        self.assertEqual(domain["top_unreviewed_values"][0], ["raw-0597", 598])
        self.assertEqual(len(domain["top_unreviewed_values"]), 8)
        html = domain_gaps(result)
        self.assertIn("raw-0597", html)
        self.assertIn("598", html)
        self.assertNotIn("raw-0000", html)
        self.assertIn("download", html.lower())

    def test_long_native_values_are_compact_in_html_but_complete_in_report(self):
        from scripts.pages.dashboard import domain_gaps
        data = inventory()
        value = "{ a → <rare> } " + "X" * 250 + " { z → final }"
        data["node_features"]["morph"] = {"scopes": {"word": {
            "count": 12345, "value_domain": "complete_observed",
            "values": {value: 12345}}}}
        result = scoped_progress([], data, "owner/demo", "1")
        domain = next(d for d in result["domains"] if d["feature"] == "morph")
        self.assertIn(value, domain["unreviewed_values"])
        self.assertEqual(domain["top_unreviewed_values"], [[value, 12345]])
        html = domain_gaps(result)
        self.assertIn("…", html)
        self.assertIn("12,345", html)
        self.assertIn("&lt;rare&gt;", html)
        self.assertIn("final", html)
        self.assertNotIn("X" * 100, html)
        self.assertIn('href="progress.json"', html)
        self.assertIn('class="gap-preview"', html)
