"""All observed rela selectors are accounted for on their native node types."""
import json
from pathlib import Path
import unittest

from ontotf.xml_mappings import MappingCatalog, MappingError, resolve_nodes

BASE = "http://purl.org/olia/olia.owl#"
NEW_POSITIVE = {
    ("bhsa", "clause", "PrAd"): ("narrower", "SyntacticAdjunct"),
    ("bhsa", "phrase", "PrAd"): ("related", "SyntacticAdjunct"),
    ("extrabiblical", "phrase", "PrAd"): ("related", "SyntacticAdjunct"),
    ("bhsa", "phrase_atom", "Appo"): ("related", "Apposition"),
    ("extrabiblical", "phrase_atom", "Appo"): ("related", "Apposition"),
}
PINS = {
    "bhsa": ("2021", "4db00e2157915495e1a4d3d57e41223df24775da"),
    "extrabiblical": ("0.2", "9a56288e6777bad6328856acf055c780e65dd5d9"),
}


class CompleteRelationDomainTests(unittest.TestCase):
    def test_scoped_domains_are_complete(self):
        catalog = MappingCatalog()
        for corpus, (version, pin) in PINS.items():
            inventory = json.loads((
                Path(__file__).resolve().parents[2]
                / "docs/research/data/generated/scoped" / f"{corpus}.json"
            ).read_text(encoding="utf-8"))
            self.assertEqual(inventory["revision"], pin)
            self.assertEqual(inventory["catalog_version"], version)
            scopes = inventory["node_features"]["rela"]["scopes"]
            expected = {(node, value) for node, scope in scopes.items()
                        for value in scope["values"]}
            rows = [r for r in catalog.load(corpus)
                    if r.kind == "value" and r.feature == "rela"]
            self.assertEqual(len(rows), len(expected))
            self.assertEqual({(r.node, r.value) for r in rows}, expected)
            for node, scope in scopes.items():
                self.assertEqual(scope["value_domain"], "complete_observed")
                self.assertEqual(sum(scope["values"].values()), scope["count"])
                self.assertEqual(scope["count"], inventory["node_types"][node])
            for row in rows:
                self.assertIn(pin, row.evidence or "")
                self.assertNotEqual(row.relation, "exact")
                if row.value == "NA":
                    self.assertEqual((row.relation, row.target), ("native-only", None))
                if row.node == "phrase_atom" and row.value != "Appo":
                    self.assertEqual((row.relation, row.target), ("native-only", None))
                if row.node == "phrase" and row.value != "PrAd":
                    self.assertEqual((row.relation, row.target), ("native-only", None))
            self.assertEqual(catalog.map_native(
                corpus, node="clause_atom", feature="rela"), ())

    def test_new_positive_paths_are_qualified_only(self):
        catalog = MappingCatalog()
        for (corpus, node, value), (relation, target) in NEW_POSITIVE.items():
            with self.subTest(corpus=corpus, node=node, value=value):
                row, = catalog.map_native(
                    corpus, node=node, feature="rela", value=value)
                iri = BASE + target
                self.assertEqual((row.relation, row.target), (relation, iri))
                self.assertNotIn(row, catalog.find_by_target(iri, corpus=corpus))
                self.assertIn(row, catalog.find_by_target(
                    iri, corpus=corpus, include_approximate=True))
                with self.assertRaisesRegex(MappingError, "exact"):
                    resolve_nodes(object(), row, corpus_version=PINS[corpus][0])
                other = "extrabiblical" if corpus == "bhsa" else "bhsa"
                self.assertEqual(catalog.find_correspondences(
                    corpus, other, node=node, feature="rela", value=value), ())
                self.assertEqual(catalog.map_native(
                    corpus, kind="entity", node=node, feature="rela", value=value), ())
        self.assertEqual(catalog.map_native(
            "extrabiblical", node="clause", feature="rela", value="PrAd"), ())
        self.assertEqual(catalog.map_native(
            "bhsa", node="phrase", feature="rela", value="Appo"), ())
