"""ORACC named-entity POS/EPOS categories are qualified OLiA ProperNoun subtypes.

Pinned ORACC-TF 1.0.0 provides 320,975 words and 8,025 lexical nodes.
The full observed scoped POS/EPOS domains now determine named-entity rows.
Its source epos codebook and primary ORACC QPN docs classify DN/GN/SN/RN/
EN/PN/TN/WN as *name* types, not identified named-entity individuals.
A narrower class-level correspondence cannot authorize exact TF selection.
"""
from __future__ import annotations

import unittest

from ontotf.xml_mappings import MappingCatalog, MappingError, resolve_nodes

ORACC = "assyrian-royal-inscriptions"
VERSION = "1.0.0"
PROPER = "http://purl.org/olia/olia.owl#ProperNoun"
CODES = ("DN", "GN", "SN", "RN", "EN", "PN", "TN", "WN", "CN", "LN", "MN", "ON", "QN")
SCOPES = (("word", "pos"), ("word", "epos"), ("lex", "pos"))


def existing_codes(feature):
    return CODES


class OraccProperNameSubtypesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = MappingCatalog()

    def test_each_source_name_tag_has_one_narrower_proper_noun_disposition(self):
        for node, feature in SCOPES:
            for code in existing_codes(feature):
                with self.subTest(node=node, feature=feature, code=code):
                    rows = self.catalog.map_native(
                        ORACC, node=node, feature=feature, value=code,
                        corpus_version=VERSION,
                    )
                    self.assertEqual(len(rows), 1)
                    mapping, = rows
                    self.assertEqual((mapping.relation, mapping.target),
                                     ("narrower", PROPER))
                    self.assertIn(
                        "oracc.museum.upenn.edu/doc/help/languages/propernouns",
                        mapping.evidence or "",
                    )
                    self.assertEqual(mapping.corpus_version, VERSION)
                    self.assertEqual(mapping.kind, "value")
        matches = self.catalog.find_by_target(
            PROPER, corpus=ORACC, include_approximate=True
        )
        self.assertEqual(
            {(row.node, row.feature, row.value) for row in matches},
            {(node, feature, code) for node, feature in SCOPES
             for code in existing_codes(feature)},
        )
        self.assertEqual(
            self.catalog.find_by_target(PROPER, corpus=ORACC), ()
        )
        # No unobserved QPN code is fabricated from the vocabulary alone.
        for node, feature in SCOPES:
            self.assertEqual(self.catalog.map_native(
                ORACC, node=node, feature=feature, value="AN"), ())

    def test_cross_corpus_name_class_discovery_requires_opt_in(self):
        for node, feature in SCOPES:
            with self.subTest(scope=(node, feature)):
                plain = self.catalog.find_correspondences(
                    ORACC, "bhsa", node=node, feature=feature, value="DN")
                self.assertEqual(plain, ())
                qualified = self.catalog.find_correspondences(
                    ORACC, "bhsa", node=node, feature=feature,
                    value="DN", include_approximate=True,
                    source_version=VERSION, target_version="2021")
                self.assertTrue(qualified)
                self.assertTrue(any(
                    hit.destination.node == "word"
                    and hit.destination.feature == "sp"
                    and hit.destination.value == "nmpr"
                    for hit in qualified
                ))
                self.assertTrue(all(
                    hit.target == PROPER
                    and hit.source.relation == "narrower"
                    and hit.destination.relation == "exact"
                    and hit.scope == "category"
                    and hit.relation == "approximate-via-target"
                    for hit in qualified
                ))
        reverse = self.catalog.find_correspondences(
            "syriac", ORACC, node="word", feature="ls",
            value="prop", include_approximate=True, source_version="0.9")
        self.assertTrue(any(
            match.destination.feature == "epos"
            and match.destination.value == "DN" for match in reverse
        ))
        self.assertEqual(
            self.catalog.find_correspondences(
                "syriac", ORACC, node="word", feature="ls",
                value="prop", source_version="0.9"), (),
        )

    def test_name_tags_never_turn_into_exact_token_selection_or_identity(self):
        row, = self.catalog.map_native(
            ORACC, node="word", feature="epos", value="DN")
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(object(), row, corpus_version=VERSION)
        self.assertEqual(self.catalog.map_native(
            ORACC, kind="entity", node="word", feature="epos",
            value="DN"), ())
        self.assertEqual(self.catalog.find_correspondences(
            ORACC, "bhsa", kind="entity", node="word",
            feature="epos", value="DN", include_approximate=True), ())

    def test_other_unresolved_and_unlemmatised_tags_remain_unmapped(self):
        for node, feature in SCOPES:
            for code in ("DET", "MOD"):
                with self.subTest(scope=(node, feature), value=code):
                    row, = self.catalog.map_native(
                        ORACC, node=node, feature=feature, value=code)
                    self.assertEqual((row.relation, row.target),
                                     ("native-only", None))
                    self.assertEqual(self.catalog.find_correspondences(
                        ORACC, "bhsa", node=node, feature=feature,
                        value=code, include_approximate=True), ())
        for code in ("u", "n"):
            row, = self.catalog.map_native(
                ORACC, node="word", feature="pos", value=code)
            self.assertEqual((row.relation, row.target),
                             ("native-only", None))

    def test_independent_anaphoric_pronoun_is_qualified(self):
        target = "http://purl.org/olia/olia.owl#Pronoun"
        expected = {(node, feature, "IP") for node, feature in SCOPES}
        for node, feature in SCOPES:
            with self.subTest(node=node, feature=feature):
                row, = self.catalog.map_native(
                    ORACC, node=node, feature=feature, value="IP",
                    corpus_version=VERSION)
                self.assertEqual((row.relation, row.target), ("narrower", target))
                self.assertEqual(self.catalog.find_correspondences(
                    ORACC, "bhsa", node=node, feature=feature, value="IP"), ())
                hits = self.catalog.find_correspondences(
                    ORACC, "bhsa", node=node, feature=feature, value="IP",
                    include_approximate=True)
                self.assertTrue(hits)
                self.assertTrue(all(hit.scope == "category" and
                                    hit.relation == "approximate-via-target"
                                    for hit in hits))
                with self.assertRaisesRegex(MappingError, "exact"):
                    resolve_nodes(object(), row, corpus_version=VERSION)
                self.assertEqual(self.catalog.map_native(
                    ORACC, kind="entity", node=node, feature=feature, value="IP"), ())
        self.assertEqual({(row.node, row.feature, row.value)
                          for row in self.catalog.find_by_target(
                              target, corpus=ORACC, include_approximate=True)},
                         expected)
        self.assertEqual(self.catalog.find_by_target(target, corpus=ORACC), ())


if __name__ == "__main__":
    unittest.main()
