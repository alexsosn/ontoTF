"""Native subphrase relations are not general dependency edges or phrase types."""
import json
from pathlib import Path
import unittest

from ontotf.xml_mappings import MappingCatalog, MappingError, resolve_nodes

BASE = "http://purl.org/olia/olia.owl#"
TARGETS = {
    "adj": ("close", "SyntacticAdjunct"),
    "mod": ("close", "Modifier"),
    "atr": ("related", "AdnominalConstituent"),
    "dem": ("related", "DemonstrativeModifier"),
}
PINS = {
    "bhsa": ("2021", "4db00e2157915495e1a4d3d57e41223df24775da",
             {"adj": 4138, "mod": 941, "atr": 3064, "dem": 1847,
              "par": 11946, "rec": 34989}),
    "extrabiblical": ("0.2", "9a56288e6777bad6328856acf055c780e65dd5d9",
                     {"adj": 568, "mod": 39, "atr": 313, "dem": 44,
                      "par": 762, "rec": 5947, "NA": 7678}),
}


class SubphraseRelationsTests(unittest.TestCase):
    def test_scoped_dispositions_and_discovery(self):
        catalog = MappingCatalog()
        for corpus, (version, pin, counts) in PINS.items():
            other = "extrabiblical" if corpus == "bhsa" else "bhsa"
            inventory = json.loads((
                Path(__file__).resolve().parents[2]
                / "docs/research/data/generated/r005" / f"{corpus}.json"
            ).read_text(encoding="utf-8"))
            self.assertEqual(inventory["revision"], pin)
            freq = inventory["node_features"]["rela"]["observed_frequencies"]
            for value, count in counts.items():
                if value != "NA":
                    self.assertEqual(freq[value], count)
                with self.subTest(corpus=corpus, value=value):
                    row, = catalog.map_native(
                        corpus, node="subphrase", feature="rela",
                        value=value, corpus_version=version)
                    relation, target = TARGETS.get(value, ("native-only", None))
                    self.assertEqual((row.relation, row.target),
                                     (relation, BASE + target if target else None))
                    self.assertIn(pin, row.evidence or "")
                    self.assertEqual(catalog.find_correspondences(
                        corpus, other, node="subphrase", feature="rela",
                        value=value), ())
                    hits = catalog.find_correspondences(
                        corpus, other, node="subphrase", feature="rela",
                        value=value, include_approximate=True)
                    if target:
                        self.assertTrue(any(
                            h.destination.node == "subphrase"
                            and h.destination.feature == "rela"
                            and h.destination.value == value
                            and h.relation == "approximate-via-target"
                            and h.scope == "category" for h in hits))
                        self.assertNotIn(row, catalog.find_by_target(
                            BASE + target, corpus=corpus))
                        self.assertIn(row, catalog.find_by_target(
                            BASE + target, corpus=corpus, include_approximate=True))
                        with self.assertRaisesRegex(MappingError, "exact"):
                            resolve_nodes(object(), row, corpus_version=version)
                    else:
                        self.assertEqual(hits, ())
                    self.assertEqual(catalog.map_native(
                        corpus, kind="entity", node="subphrase",
                        feature="rela", value=value), ())
                    if value != "NA":
                        for node in ("clause", "clause_atom", "phrase", "phrase_atom"):
                            self.assertEqual(catalog.map_native(
                                corpus, node=node, feature="rela", value=value), ())
            self.assertFalse(any(
                r.kind == "edge" and r.feature == "mother"
                for r in catalog.load(corpus)))

    def test_extrabiblical_complete_subphrase_domain(self):
        catalog = MappingCatalog()
        rows = [r for r in catalog.load("extrabiblical")
                if r.kind == "value" and r.node == "subphrase" and r.feature == "rela"]
        expected = PINS["extrabiblical"][2]
        self.assertEqual(len(rows), len(expected))
        self.assertEqual({r.value for r in rows}, set(expected))
        self.assertEqual(sum(expected.values()), 15351)
        # Missing BHSA node-scoped NA count is not inferred from global NA.
        self.assertEqual(catalog.map_native(
            "bhsa", node="subphrase", feature="rela", value="NA"), ())
