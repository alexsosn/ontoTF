from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tfont.xml_mappings import (
    MappingCatalog, MappingError, find_correspondences, list_corpora,
    map_native, resolve_nodes,
)

NOUN = "http://purl.org/olia/olia.owl#Noun"


def file(root: Path, corpus: str, rows: str) -> None:
    (root / f"{corpus}.xml").write_text(
        f'<mappings corpus="{corpus}" source="test">{rows}</mappings>',
        encoding="utf-8",
    )


class XMLMappingContractTests(unittest.TestCase):
    def test_real_reviewed_bhsa_syriac_extrabiblical_equivalences(self):
        self.assertTrue({"bhsa", "syriac", "extrabiblical"} <= set(list_corpora()))
        forward = find_correspondences(
            "bhsa", "syriac", node="word", feature="sp", value="subs")
        self.assertEqual({(r.target, r.destination.value, r.relation, r.scope)
                          for r in forward}, {(NOUN, "subs", "exact", "category")})
        inverse = find_correspondences(
            "syriac", "bhsa", node="word", feature="sp", value="subs")
        self.assertEqual({r.destination.value for r in inverse}, {"subs", "nmpr"})
        third = find_correspondences(
            "bhsa", "extrabiblical", node="word", feature="sp", value="verb")
        self.assertEqual({r.destination.value for r in third}, {"verb"})
        proper = find_correspondences(
            "bhsa", "syriac", node="word", feature="sp", value="nmpr")
        self.assertTrue(any(r.target.endswith("#Noun") for r in proper))
        self.assertTrue(any(r.target.endswith("#ProperNoun")
                            and r.destination.feature == "ls"
                            and r.destination.value == "prop" for r in proper))
        self.assertEqual(map_native("syriac", node="word", feature="sp", value="inrg")[0].relation, "native-only")
        self.assertFalse(find_correspondences("syriac", "bhsa", node="word", feature="sp", value="inrg"))
        construct = find_correspondences(
            "bhsa", "syriac", node="word", feature="st", value="c")
        self.assertEqual({r.destination.value for r in construct}, {"cst"})
        self.assertEqual(
            find_correspondences("syriac", "bhsa", node="word", feature="st", value="c"), ())
        first = find_correspondences(
            "bhsa", "syriac", node="word", feature="ps", value="p1")
        self.assertEqual({r.destination.value for r in first}, {"first"})
        self.assertEqual(
            find_correspondences("bhsa", "syriac", node="word", feature="prs_ps", value="p1"), ())
        self.assertEqual(
            find_correspondences("syriac", "bhsa", node="word", feature="vt", value="pf"), ())


    def test_all_corpora_mapping_joins_different_native_node_kinds(self):
        from tfont import find_across_corpora

        # TLHdig has analysis-level POS; BHSA/Syriac/ExtraBiblical have
        # word-level POS. The join is about class, never token identity.
        hits = find_across_corpora(
            "tlhdig-tf", node="analysis", feature="pos", value="ADV"
        )
        observed = {(x.destination.corpus, x.destination.node,
                     x.destination.feature, x.destination.value)
                    for x in hits}
        self.assertTrue({
            ("bhsa", "word", "sp", "advb"),
            ("syriac", "word", "sp", "advb"),
            ("extrabiblical", "word", "sp", "advb"),
            ("syrnt", "word", "sp", "adverb"),
        } <= observed)
        self.assertTrue(all(x.source.corpus == "tlhdig-tf"
                            and x.destination.corpus != "tlhdig-tf"
                            and x.target.endswith("#Adverb")
                            and x.scope == "category" for x in hits))
        self.assertEqual(
            find_across_corpora(
                "tlhdig-tf", node="analysis", feature="pos", value="PREV"
            ), ()
        )
        with self.assertRaisesRegex(MappingError, "not verified"):
            find_across_corpora(
                "tlhdig-tf", node="analysis", feature="pos",
                value="ADV", source_version="wrong",
            )

    def test_all_corpora_lookup_without_source_target_false_identity(self):
        from tfont.xml_mappings import MappingCatalog

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file(root, "a", f'<map kind="value" node="token" feature="p" value="N" relation="exact" target="{NOUN}"/>')
            file(root, "b", f'<map kind="value" node="word" feature="sp" value="n" relation="exact" target="{NOUN}"/>')
            file(root, "c", '<map kind="value" node="analysis" feature="pos" value="N" relation="native-only"/>')
            cat = MappingCatalog(root)
            got = cat.find_across_corpora("a", node="token", feature="p", value="N")
            self.assertEqual([(x.source.corpus, x.destination.corpus, x.scope)
                              for x in got], [("a", "b", "category")])
            self.assertEqual(cat.find_across_corpora("c", node="analysis",
                                                     feature="pos", value="N"), ())

    def test_reverse_ontology_lookup_discovers_all_corpora(self):
        from tfont import find_by_target

        rows = find_by_target(NOUN)
        self.assertTrue({"bhsa", "syriac", "extrabiblical", "syrnt"}
                        <= {row.corpus for row in rows})
        self.assertTrue(all(row.target == NOUN and row.relation == "exact"
                            and row.kind == "value" for row in rows))
        self.assertEqual(
            {(row.feature, row.value) for row in find_by_target(NOUN, corpus="syriac")},
            {("sp", "subs")},
        )
        self.assertEqual(find_by_target("urn:unmapped:unknown-class"), ())
        with self.assertRaisesRegex(MappingError, "absolute"):
            find_by_target("not-an-ontology-IRI")

    def test_reverse_lookup_excludes_ambiguous_and_opt_in_approximate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file(root, "a", (
                f'<map kind="value" node="word" feature="sp" value="close" relation="close" target="{NOUN}"/>'
                f'<map kind="value" node="word" feature="sp" value="guess" relation="ambiguous" target="{NOUN}"/>'
                '<map kind="value" node="word" feature="sp" value="native" relation="native-only"/>'
            ))
            file(root, "b", (
                f'<map kind="value" node="word" feature="pos" value="N" relation="exact" target="{NOUN}"/>'
            ))
            cat = MappingCatalog(root)
            self.assertEqual([(r.corpus, r.value) for r in cat.find_by_target(NOUN)], [("b", "N")])
            self.assertEqual(
                [(r.corpus, r.value, r.relation)
                 for r in cat.find_by_target(NOUN, include_approximate=True)],
                [("a", "close", "close"), ("b", "N", "exact")],
            )
            self.assertEqual(
                [(r.corpus, r.value) for r in cat.find_by_target(NOUN, corpus="a",
                                                                  include_approximate=True)],
                [("a", "close")],
            )

    def test_single_file_new_corpus_and_lazy_corruption_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file(root, "newcorpus", f'<map kind="value" relation="exact" node="word" feature="pos" value="N" target="{NOUN}"/>')
            file(root, "other", f'<map kind="value" relation="exact" node="token" feature="cat" value="noun" target="{NOUN}"/>')
            catalog = MappingCatalog(root)
            self.assertEqual(catalog.list_corpora(), ("newcorpus", "other"))
            matches = catalog.find_correspondences("newcorpus", "other", node="word", feature="pos", value="N")
            self.assertEqual((matches[0].destination.node, matches[0].destination.feature), ("token", "cat"))
            (root / "broken.xml").write_text("<mappings", encoding="utf-8")
            self.assertEqual(len(catalog.find_correspondences("newcorpus", "other", node="word", feature="pos", value="N")), 1)
            with self.assertRaisesRegex(MappingError, "broken.xml: malformed XML"):
                catalog.load("broken")

    def test_negative_dispositions_and_approximate_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file(root, "a", f'<map kind="value" node="word" feature="sp" value="x" relation="close" target="{NOUN}"/>'
                            f'<map kind="value" node="word" feature="sp" value="bad" relation="ambiguous" target="{NOUN}"/>')
            file(root, "b", f'<map kind="value" node="word" feature="sp" value="y" relation="exact" target="{NOUN}"/>')
            cat = MappingCatalog(root)
            query = dict(node="word", feature="sp", value="x")
            self.assertEqual(cat.find_correspondences("a", "b", **query), ())
            found = cat.find_correspondences("a", "b", include_approximate=True, **query)
            self.assertEqual(found[0].relation, "approximate-via-target")
            self.assertEqual(cat.find_correspondences("a", "b", node="word", feature="sp", value="bad", include_approximate=True), ())

    def test_bad_selectors_duplicates_versions_and_entity_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file(root, "wrong", '<map kind="value" relation="exact" feature="sp" value="x" target="urn:o:Noun"/>')
            with self.assertRaisesRegex(MappingError, "map #1: invalid value selector"):
                MappingCatalog(root).load("wrong")
            file(root, "wrong", '<map kind="value" node="word" feature="sp" value="x" relation="exact" target="urn:o:Noun"/>'
                                '<map kind="value" node="word" feature="sp" value="x" relation="exact" target="urn:o:Noun"/>')
            with self.assertRaisesRegex(MappingError, "duplicate mapping"):
                MappingCatalog(root).load("wrong")
            file(root, "wrong", '<map kind="entity" node="word" feature="id" value="42" relation="exact" target="urn:thing:42"/>')
            file(root, "other", '<map kind="entity" node="lexeme" feature="id" value="11" relation="exact" target="urn:thing:42"/>')
            cat = MappingCatalog(root)
            rows = cat.find_correspondences("wrong", "other", kind="entity", node="word", feature="id", value="42")
            self.assertEqual(rows[0].scope, "entity-candidate")
            self.assertEqual(rows[0].relation, "unverified")
            self.assertEqual(cat.find_correspondences("wrong", "other", node="word", feature="id", value="42"), ())

    def test_loaded_tf_execution_and_version_mismatch(self):
        mapping = map_native("syriac", node="word", feature="sp", value="subs")[0]

        class Feature:
            def v(self, n):
                return {1: "subs", 2: "verb", 3: "subs"}.get(n)

        class Otype:
            def s(self, node_type):
                assert node_type == "word"
                return [1, 2, 3]

        class API:
            class F:
                otype = Otype()

            def Fs(self, feature):
                assert feature == "sp"
                return Feature()

        self.assertEqual(resolve_nodes(API(), mapping, corpus_version="0.9"), (1, 3))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), mapping, corpus_version="unknown")
        with self.assertRaisesRegex(MappingError, "not verified"):
            map_native("syriac", node="word", feature="sp", value="subs", corpus_version="wrong")


if __name__ == "__main__":
    unittest.main()
