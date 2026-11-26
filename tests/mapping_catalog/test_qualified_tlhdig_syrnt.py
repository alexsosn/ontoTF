"""Source-grounded conservative categories in TLHdig and SyrNT.

Primary source pins verified independently:
TLHdig-TF@e954600, tf/0.4.0/pos.tf: 2,961 INDadv and 2,292 INDCL
analyses; these are *candidate analyses*, not selected word tokens.
ETCBC/syrnt@dae3eb6, tf/0.1/gn.tf: 7,327 gn=c words, across
noun/pronoun/verb categories; source docs call this common gender.
OLiA core is the vendored d3bd4f1a snapshot. Its Clitic class is
deprecated; use CliticElement instead. Its CommonGender definition is
EAGLES-specific, hence a close rather than exact correspondence.
"""
from __future__ import annotations

import unittest

from ontotf.xml_mappings import (
    MappingCatalog, MappingError, find_across_corpora,
    find_by_target, resolve_nodes,
)

OLIA = "http://purl.org/olia/olia.owl#"


class QualifiedSourceCategoryTests(unittest.TestCase):
    def test_hittite_indefinite_adverb_is_a_narrower_adverb_category(self):
        catalog = MappingCatalog()
        row, = catalog.map_native(
            "tlhdig-tf", node="analysis", feature="pos", value="INDadv",
            corpus_version="0.4.0",
        )
        self.assertEqual((row.relation, row.target),
                         ("narrower", OLIA + "Adverb"))
        self.assertIn("tf/0.4.0/pos.tf", row.evidence)
        self.assertEqual(row.corpus_version, "0.4.0")
        # The default exact-only lookup must not launder qualified mappings.
        self.assertNotIn(row, find_by_target(OLIA + "Adverb"))
        self.assertIn(row, find_by_target(
            OLIA + "Adverb", include_approximate=True,
        ))
        self.assertEqual(find_across_corpora(
            "tlhdig-tf", node="analysis", feature="pos", value="INDadv",
        ), ())
        hits = find_across_corpora(
            "tlhdig-tf", node="analysis", feature="pos", value="INDadv",
            include_approximate=True, source_version="0.4.0",
        )
        self.assertTrue(any(
            x.destination.corpus == "bhsa"
            and x.destination.node == "word"
            and x.destination.feature == "sp"
            and x.destination.value == "advb"
            for x in hits
        ))
        self.assertTrue(all(
            x.scope == "category"
            and x.relation == "approximate-via-target"
            for x in hits
        ))
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(object(), row, corpus_version="0.4.0")

    def test_hittite_indefinite_clitic_uses_non_deprecated_olia_class(self):
        catalog = MappingCatalog()
        row, = catalog.map_native(
            "tlhdig-tf", node="analysis", feature="pos", value="INDCL",
            corpus_version="0.4.0",
        )
        self.assertEqual((row.relation, row.target),
                         ("narrower", OLIA + "CliticElement"))
        self.assertIn("tf/0.4.0/pos.tf", row.evidence)
        self.assertNotIn(row, find_by_target(OLIA + "CliticElement"))
        self.assertIn(row, find_by_target(
            OLIA + "CliticElement", include_approximate=True,
        ))
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(object(), row, corpus_version="0.4.0")
        with self.assertRaisesRegex(MappingError, "not verified"):
            catalog.map_native(
                "tlhdig-tf", node="analysis", feature="pos", value="INDCL",
                corpus_version="0.3",
            )

    def test_syrnt_common_gender_is_close_not_exact_eagles_equivalence(self):
        catalog = MappingCatalog()
        row, = catalog.map_native(
            "syrnt", node="word", feature="gn", value="c",
            corpus_version="0.1",
        )
        self.assertEqual((row.relation, row.target),
                         ("close", OLIA + "CommonGender"))
        self.assertIn("tf/0.1/gn.tf", row.evidence)
        self.assertNotIn(row, find_by_target(OLIA + "CommonGender"))
        self.assertIn(row, find_by_target(
            OLIA + "CommonGender", include_approximate=True,
        ))
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(object(), row, corpus_version="0.1")

    def test_unsafe_negative_and_underdetermined_categories_remain_native(self):
        catalog = MappingCatalog()
        for corpus, node, feature, value in (
            ("tlhdig-tf", "analysis", "pos", "NEG"),
            ("tlhdig-tf", "analysis", "pos", "PREV"),
            ("tlhdig-tf", "analysis", "pos", "ADV POSP PREV"),
            ("syrnt", "word", "gn", "NA"),
            ("syrnt", "word", "sfgn", "NA"),
            ("syrnt", "word", "sp", "particle"),
        ):
            with self.subTest(corpus=corpus, value=value):
                row, = catalog.map_native(
                    corpus, node=node, feature=feature, value=value,
                )
                self.assertEqual((row.relation, row.target),
                                 ("native-only", None))


if __name__ == "__main__":
    unittest.main()
