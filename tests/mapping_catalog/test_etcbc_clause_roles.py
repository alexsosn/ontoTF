"""Clause constituent relations are roles, not phrase types or edges."""
import unittest

from ontotf.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#"
ROLES = {
    "Adju": "SyntacticAdjunct",
    "Cmpl": "SyntacticComplement",
    "Objc": "SyntacticObject",
    "PreC": "SyntacticComplement",
    "Subj": "SyntacticSubject",
}
SPECS = {
    "bhsa": ("2021", "4db00e2157915495e1a4d3d57e41223df24775da"),
    "extrabiblical": ("0.2", "9a56288e6777bad6328856acf055c780e65dd5d9"),
}
EXTRA_OTHER = {"NA", "Attr", "Coor", "ReVo", "Resu", "RgRc", "Spec"}


class ClauseRoleTests(unittest.TestCase):
    def test_qualified_role_discovery_and_execution_boundary(self):
        catalog = MappingCatalog()
        for corpus, (version, pin) in SPECS.items():
            other = "extrabiblical" if corpus == "bhsa" else "bhsa"
            for code, role in ROLES.items():
                with self.subTest(corpus=corpus, code=code):
                    row, = catalog.map_native(
                        corpus, node="clause", feature="rela", value=code,
                        corpus_version=version)
                    self.assertEqual((row.relation, row.target), ("narrower", OLIA + role))
                    self.assertIn(pin, row.evidence)
                    self.assertNotIn(row, catalog.find_by_target(OLIA + role, corpus=corpus))
                    self.assertIn(row, catalog.find_by_target(
                        OLIA + role, corpus=corpus, include_approximate=True))
                    self.assertEqual(catalog.find_correspondences(
                        corpus, other, node="clause", feature="rela", value=code), ())
                    hits = catalog.find_correspondences(
                        corpus, other, node="clause", feature="rela", value=code,
                        include_approximate=True)
                    self.assertTrue(any(h.destination.node == "clause"
                                        and h.destination.feature == "rela"
                                        and h.destination.value == code
                                        and h.scope == "category"
                                        and h.relation == "approximate-via-target"
                                        for h in hits))
                    with self.assertRaisesRegex(MappingError, "exact"):
                        resolve_nodes(object(), row, corpus_version=version)
                    for node in ("clause_atom", "phrase_atom", "subphrase", "phrase"):
                        self.assertEqual(catalog.map_native(
                            corpus, node=node, feature="rela", value=code), ())
            self.assertFalse(any(r.kind == "edge" and r.feature == "mother"
                                 for r in catalog.load(corpus)))

    def test_extrabiblical_observed_clause_domain(self):
        catalog = MappingCatalog()
        rows = [r for r in catalog.load("extrabiblical")
                if r.kind == "value" and r.node == "clause" and r.feature == "rela"]
        self.assertEqual(len(rows), len(ROLES) + len(EXTRA_OTHER))
        self.assertEqual({r.value for r in rows}, set(ROLES) | EXTRA_OTHER)
        for row in rows:
            if row.value in EXTRA_OTHER:
                self.assertEqual((row.relation, row.target), ("native-only", None))
        self.assertEqual(catalog.map_native(
            "extrabiblical", node="clause", feature="rela", value="PrAd"), ())


if __name__ == "__main__":
    unittest.main()
