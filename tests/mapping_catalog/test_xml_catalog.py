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
    def test_every_packaged_corpus_xml_is_validated_without_per_corpus_tests(self):
        # Every XML added by a contributor participates automatically in CI.
        catalog = MappingCatalog()
        for corpus in catalog.list_corpora():
            with self.subTest(corpus=corpus):
                catalog.load(corpus)

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
        # Suffix person and host-word person share the OLiA category, but
        # the returned selectors retain their different grammatical carriers.
        suffix_person = find_correspondences(
            "bhsa", "syriac", node="word", feature="prs_ps", value="p1")
        self.assertEqual(
            {(r.source.feature, r.destination.feature, r.target, r.scope)
             for r in suffix_person},
            {("prs_ps", "ps", "http://purl.org/olia/olia.owl#First", "category")})
        self.assertTrue(all(r.source.node == r.destination.node == "word"
                            and r.relation == "exact" for r in suffix_person))
        # No equivalence of an individual pronoun or word token is inferred.
        self.assertEqual(
            find_correspondences("bhsa", "syriac", kind="entity",
                                 node="word", feature="prs_ps", value="p1"), ())
        self.assertEqual(
            find_correspondences("syriac", "bhsa", node="word", feature="vt", value="pf"), ())


    def test_bhsa_nonfinite_verbal_forms_share_only_general_olia_categories(self):
        # ETCBC/bhsa@4db00e2 docs/features/vt.md calls infa/infc
        # infinitives and ptca/ptcp participles. The subtype survives in
        # the returned native selector; no subtype/tense/voice is fabricated.
        target_base = "http://purl.org/olia/olia.owl#"
        source_forms = {
            "infa": "Infinitive", "infc": "Infinitive",
            "ptca": "Participle", "ptcp": "Participle",
        }
        for value, concept in source_forms.items():
            with self.subTest(value=value):
                rows = map_native("bhsa", node="word", feature="vt", value=value)
                self.assertEqual(
                    [(row.relation, row.target) for row in rows],
                    [("exact", target_base + concept)],
                )
                matches = find_correspondences(
                    "bhsa", "syriac", node="word", feature="vt", value=value
                )
                self.assertEqual(
                    {(row.destination.feature, row.destination.value,
                      row.target, row.scope) for row in matches},
                    {("vt", "inf" if concept == "Infinitive" else "ptc",
                      target_base + concept, "category")},
                )
        # SyrNT uses lexical verbal-form names; no word token is equated.
        for native, label in (("infa", "infinitive"), ("ptcp", "participle")):
            cross = find_correspondences(
                "bhsa", "syrnt", node="word", feature="vt", value=native
            )
            self.assertEqual(
                {(row.destination.feature, row.destination.value,
                  row.scope) for row in cross},
                {("vt", label, "category")},
            )
        # No reinterpretation of Biblical Hebrew finite forms as modern
        # tense or aspect categories.
        for native in ("perf", "impf", "wayq"):
            self.assertEqual(
                [(row.relation, row.target) for row in
                 map_native("bhsa", node="word", feature="vt", value=native)],
                [("native-only", None)],
            )
            self.assertEqual(
                find_correspondences(
                    "bhsa", "syriac", node="word", feature="vt", value=native
                ), (),
            )

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

    def test_reject_conflicting_conservative_and_exact_same_selector(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exact = f'<map kind="value" node="word" feature="sp" value="x" relation="exact" target="{NOUN}"/>'
            for disposition in ("native-only", "unsupported", "ambiguous"):
                negative = (f'<map kind="value" node="word" feature="sp" value="x" '
                            f'relation="{disposition}"/>')
                for content in (negative + exact, exact + negative):
                    file(root, "a", content)
                    with self.subTest(relation=disposition, negative_first=content.startswith(negative)):
                        with self.assertRaisesRegex(MappingError, "conflicting.*dispositions"):
                            MappingCatalog(root).load("a")

    def test_multiple_ambiguous_candidates_do_not_create_a_positive_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proper = "http://purl.org/olia/olia.owl#ProperNoun"
            file(root, "a", (
                f'<map kind="value" node="word" feature="sp" value="x" relation="ambiguous" target="{NOUN}"/>'
                f'<map kind="value" node="word" feature="sp" value="x" relation="ambiguous" target="{proper}"/>'
            ))
            file(root, "b", f'<map kind="value" node="word" feature="sp" value="y" relation="exact" target="{NOUN}"/>')
            catalog = MappingCatalog(root)
            self.assertEqual(len(catalog.load("a")), 2)
            self.assertEqual(catalog.find_correspondences(
                "a", "b", node="word", feature="sp", value="x",
                include_approximate=True), ())

    def test_one_file_edit_promotes_native_only_and_multitarget_is_valid(self):
        proper = "http://purl.org/olia/olia.owl#ProperNoun"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file(root, "a", '<map kind="value" node="word" feature="sp" value="nmpr" relation="native-only"/>')
            file(root, "b", f'<map kind="value" node="word" feature="pos" value="noun" relation="exact" target="{NOUN}"/>')
            first = MappingCatalog(root)
            self.assertEqual(first.find_correspondences(
                "a", "b", node="word", feature="sp", value="nmpr"), ())
            # Author changes ONE XML file; Git history is the revision record.
            file(root, "a", (
                f'<map kind="value" node="word" feature="sp" value="nmpr" relation="exact" target="{NOUN}"/>'
                f'<map kind="value" node="word" feature="sp" value="nmpr" relation="exact" target="{proper}"/>'
            ))
            updated = MappingCatalog(root)
            rows = updated.map_native("a", node="word", feature="sp", value="nmpr")
            self.assertEqual({r.target for r in rows}, {NOUN, proper})
            self.assertEqual(len(updated.find_correspondences(
                "a", "b", node="word", feature="sp", value="nmpr")), 1)

    def test_unversioned_disposition_conflicts_with_specific_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wildcard = '<map kind="value" node="word" feature="sp" value="x" relation="native-only"/>'
            pinned = f'<map kind="value" node="word" feature="sp" value="x" relation="exact" corpusVersion="2" target="{NOUN}"/>'
            for xml in (wildcard + pinned, pinned + wildcard):
                file(root, "a", xml)
                with self.subTest(wildcard_first=xml.startswith(wildcard)):
                    with self.assertRaisesRegex(MappingError, "conflicting.*dispositions"):
                        MappingCatalog(root).load("a")

    def test_version_scopes_are_not_conflicting_dispositions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file(root, "a", (
                '<map kind="value" node="word" feature="sp" value="x" relation="native-only" corpusVersion="1"/>'
                f'<map kind="value" node="word" feature="sp" value="x" relation="exact" corpusVersion="2" target="{NOUN}"/>'
            ))
            file(root, "b", f'<map kind="value" node="word" feature="sp" value="y" relation="exact" target="{NOUN}"/>')
            catalog = MappingCatalog(root)
            self.assertEqual(len(catalog.load("a")), 2)
            with self.assertRaisesRegex(MappingError, "multiple source versions"):
                catalog.map_native("a", node="word", feature="sp", value="x")
            with self.assertRaisesRegex(MappingError, "multiple source versions"):
                catalog.find_correspondences(
                    "a", "b", node="word", feature="sp", value="x")
            self.assertEqual([row.relation for row in catalog.map_native(
                "a", node="word", feature="sp", value="x", corpus_version="1")],
                ["native-only"])
            self.assertEqual([row.relation for row in catalog.map_native(
                "a", node="word", feature="sp", value="x", corpus_version="2")],
                ["exact"])
            self.assertEqual(catalog.find_correspondences(
                "a", "b", node="word", feature="sp", value="x", source_version="1"), ())
            self.assertEqual(len(catalog.find_correspondences(
                "a", "b", node="word", feature="sp", value="x", source_version="2")), 1)

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


    def test_real_oracc_syrnt_ontolex_lexical_entry_node_correspondence(self):
        from tfont.xml_mappings import MappingCatalog

        catalog = MappingCatalog()
        iri = "http://www.w3.org/ns/lemon/ontolex#LexicalEntry"
        oracc = catalog.map_native(
            "assyrian-royal-inscriptions", kind="node", node="lex"
        )
        syrnt = catalog.map_native("syrnt", kind="node", node="lexeme")
        self.assertEqual(len(oracc), 1)
        self.assertEqual(len(syrnt), 1)
        self.assertEqual((oracc[0].relation, oracc[0].target), ("exact", iri))
        self.assertEqual((syrnt[0].relation, syrnt[0].target), ("exact", iri))
        forward = catalog.find_correspondences(
            "assyrian-royal-inscriptions", "syrnt", kind="node", node="lex"
        )
        self.assertEqual(len(forward), 1)
        self.assertEqual(forward[0].destination.node, "lexeme")
        self.assertEqual(forward[0].target, iri)
        self.assertEqual((forward[0].scope, forward[0].relation), ("category", "exact"))
        # A shared lexical-entry CLASS is not an identity alignment, translation,
        # linked lexical sense, or assertion about the form of any occurrence.
        self.assertEqual(
            catalog.find_correspondences(
                "assyrian-royal-inscriptions", "syrnt",
                kind="entity", node="word", feature="pos", value="N"
            ),
            (),
        )

    def test_tlhdig_lexical_entry_nodes_are_category_only(self):
        from tfont.xml_mappings import MappingCatalog

        catalog = MappingCatalog()
        target = "http://www.w3.org/ns/lemon/ontolex#LexicalEntry"
        native = catalog.map_native("tlhdig-tf", kind="node", node="lex")
        self.assertEqual(len(native), 1)
        self.assertEqual((native[0].relation, native[0].target),
                         ("exact", target))
        matches = catalog.find_across_corpora(
            "tlhdig-tf", kind="node", node="lex"
        )
        self.assertEqual(
            {(m.destination.corpus, m.destination.node,
              m.target, m.scope, m.relation) for m in matches},
            {
                ("assyrian-royal-inscriptions", "lex", target,
                 "category", "exact"),
                ("syrnt", "lexeme", target, "category", "exact"),
                ("bhsa", "lex", target, "category", "exact"),
            },
        )
        # A lexeme grouping is not a selected word's morphology, a shared
        # lexical sense, a citation-form export or an individual identity.
        self.assertEqual(
            catalog.find_across_corpora(
                "tlhdig-tf", kind="entity", node="lex",
                feature="lemma", value="unknown"
            ),
            (),
        )


    def test_bhsa_lexeme_node_is_ontolex_category_not_lex0_identity(self):
        catalog = MappingCatalog()
        target = "http://www.w3.org/ns/lemon/ontolex#LexicalEntry"
        native = catalog.map_native("bhsa", kind="node", node="lex")
        self.assertEqual(
            [(r.relation, r.target) for r in native],
            [("exact", target)]
        )
        matches = catalog.find_across_corpora(
            "bhsa", kind="node", node="lex"
        )
        self.assertEqual(
            {(r.destination.corpus, r.destination.node, r.scope,
              r.relation, r.target) for r in matches},
            {
                ("assyrian-royal-inscriptions", "lex", "category", "exact", target),
                ("tlhdig-tf", "lex", "category", "exact", target),
                ("syrnt", "lexeme", "category", "exact", target),
            },
        )
        # BHSA lex0 without final disambiguators is NOT a lexeme ID;
        # class discovery never aligns individual lexemes across corpora.
        self.assertEqual(
            catalog.find_across_corpora(
                "bhsa", kind="entity", node="lex", feature="lex0",
                value="ABC"
            ),
            (),
        )
        self.assertEqual(
            catalog.map_native("bhsa", kind="node", node="word"),
            (),
        )


if __name__ == "__main__":
    unittest.main()
