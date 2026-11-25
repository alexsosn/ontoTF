"""Source-pinned ETCBC functional clause type mappings.

Full TF typ/otype/kind joins separate functional clauses from atoms and
verify that the finite-form codes are verbal clauses in the pinned releases.
"""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#"
FINITE = {
    "Way0", "WayX", "WIm0", "WImX", "WQt0", "WQtX",
    "WxI0", "WXIm", "WxQ0", "WXQt", "WxQX",
    "WxY0", "WXYq", "WxYX", "WYq0", "WYqX",
    "xIm0", "XImp", "xImX", "xQt0", "XQtl", "xQtX",
    "xYq0", "XYqt", "xYqX", "ZIm0", "ZImX", "ZQt0",
    "ZQtX", "ZYq0", "ZYqX",
}
NONFINITE_OR_OTHER = {
    "AjCl", "NmCl", "InfA", "InfC", "Ptcp", "CPen",
    "Ellp", "MSyn", "Voct", "XPos",
}
SPECS = {
    "bhsa": ("2021", "4db00e2157915495e1a4d3d57e41223df24775da",
             FINITE, NONFINITE_OR_OTHER | {"Reop"}, 88131, 90704),
    "extrabiblical": ("0.2", "9a56288e6777bad6328856acf055c780e65dd5d9",
                      FINITE - {"WXIm", "XImp", "xImX"},
                      NONFINITE_OR_OTHER | {"Unkn"}, 8908, 9160),
}


class EtcBcClauseTypeTests(unittest.TestCase):
    def test_functional_clause_domain_and_qualified_targets(self):
        catalog = MappingCatalog()
        for corpus, (version, pin, finite, other, count, atoms) in SPECS.items():
            with self.subTest(corpus=corpus):
                inventory = json.loads((
                    Path(__file__).resolve().parents[2] /
                    "docs/research/data/generated/r005" / (corpus + ".json")
                ).read_text(encoding="utf-8"))
                self.assertEqual(inventory["revision"], pin)
                self.assertEqual(inventory["tf_version"], version)
                self.assertEqual(inventory["node_types"]["clause"], count)
                self.assertEqual(inventory["node_types"]["clause_atom"], atoms)
                observed = inventory["node_features"]["typ"]["observed_frequencies"]
                self.assertTrue((finite | other | {"Defc"}) <= observed.keys())
                rows = [r for r in catalog.load(corpus)
                        if r.kind == "value" and r.node == "clause" and r.feature == "typ"]
                self.assertEqual(len(rows), len(finite | other))
                self.assertEqual({r.value for r in rows}, finite | other)
                for row in rows:
                    self.assertEqual(row.corpus_version, version)
                    self.assertIn(pin, row.evidence)
                    if row.value in finite:
                        self.assertEqual((row.relation, row.target),
                                         ("narrower", OLIA + "FiniteClause"))
                        self.assertNotIn(row, catalog.find_by_target(OLIA + "FiniteClause", corpus=corpus))
                        self.assertIn(row, catalog.find_by_target(OLIA + "FiniteClause", corpus=corpus,
                                                                  include_approximate=True))
                        with self.assertRaisesRegex(MappingError, "exact"):
                            resolve_nodes(object(), row, corpus_version=version)
                    else:
                        self.assertEqual((row.relation, row.target), ("native-only", None))
                self.assertFalse(any(r.kind == "value" and r.node == "clause_atom"
                                     and r.feature == "typ" and r.target
                                     for r in catalog.load(corpus)))
                self.assertEqual(catalog.map_native(corpus, node="clause",
                                                     feature="typ", value="Defc"), ())

    def test_cross_corpus_discovery_is_not_equivalence_or_atom_selection(self):
        catalog = MappingCatalog()
        for source, destination in (("bhsa", "extrabiblical"), ("extrabiblical", "bhsa")):
            self.assertEqual(catalog.find_correspondences(
                source, destination, node="clause", feature="typ", value="Way0"), ())
            matches = catalog.find_correspondences(
                source, destination, node="clause", feature="typ", value="Way0",
                include_approximate=True)
            self.assertEqual({(m.destination.node, m.destination.feature, m.destination.value,
                               m.target, m.source.relation, m.destination.relation,
                               m.relation, m.scope) for m in matches},
                             {("clause", "typ", code, OLIA + "FiniteClause", "narrower",
                               "narrower", "approximate-via-target", "category")
                              for code in SPECS[destination][2]})
            for code in ("InfA", "InfC", "Ptcp", "NmCl", "Ellp"):
                self.assertEqual(catalog.find_correspondences(
                    source, destination, node="clause", feature="typ", value=code,
                    include_approximate=True), ())
            self.assertEqual(catalog.find_correspondences(
                source, destination, node="clause_atom", feature="typ", value="Way0",
                include_approximate=True), ())


if __name__ == "__main__":
    unittest.main()
