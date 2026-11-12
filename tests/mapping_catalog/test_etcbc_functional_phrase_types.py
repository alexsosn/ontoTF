"""ETCBC functional phrases versus distributional phrase atoms (pinned TF).

The ETCBC otype codebook defines phrase/clauses as functional, potentially
discontinuous entities. Their atoms are maximal *continuous parts*, not
independently attested full phrases or clauses. Only the functional entities
receive generic syntax class mappings and qualified phrase-type categories.
"""
from pathlib import Path
import json
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#"
PINS = {
    "bhsa": ("2021", "4db00e2157915495e1a4d3d57e41223df24775da",
             253203, 267532, 88131, 90704),
    "extrabiblical": ("0.2", "9a56288e6777bad6328856acf055c780e65dd5d9",
                     22770, 23370, 8908, 9160),
}
EXACT = {
    "VP": "VerbPhrase", "PP": "PrepositionalPhrase",
    "AdjP": "AdjectivePhrase",
}
QUALIFIED = {
    "NP": "NounPhrase", "PrNP": "NounPhrase",
    "PPrP": "NounPhrase", "DPrP": "NounPhrase",
    "IPrP": "NounPhrase",
}
NATIVE = {"AdvP", "CP", "InjP", "NegP", "InrP"}
SOURCE_PHRASE_CODES = set(EXACT) | set(QUALIFIED) | NATIVE


class ETCBCFunctionalPhraseTypeMappingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = MappingCatalog()

    def test_original_pinned_typ_domains_and_disjoint_node_type_ranges(self):
        for corpus, (version, pin, phrases, atoms, clauses, clause_atoms) in PINS.items():
            with self.subTest(corpus=corpus):
                source = json.loads((
                    Path(__file__).resolve().parents[2]
                    / "docs/research/data/generated/r005"
                    / f"{corpus}.json"
                ).read_text(encoding="utf-8"))
                self.assertEqual((source["tf_version"], source["revision"]),
                                 (version, pin))
                self.assertEqual(
                    tuple(source["node_types"][k] for k in
                          ("phrase", "phrase_atom", "clause", "clause_atom")),
                    (phrases, atoms, clauses, clause_atoms),
                )
                feature = source["node_features"]["typ"]
                self.assertEqual(set(feature["applies_to"]),
                                 {"phrase", "phrase_atom", "clause", "clause_atom"})
                self.assertEqual(
                    sum(feature["observed_frequencies"][v]
                        for v in SOURCE_PHRASE_CODES),
                    phrases + atoms,
                )
                self.assertEqual(
                    set(feature["observed_values"]) & SOURCE_PHRASE_CODES,
                    SOURCE_PHRASE_CODES,
                )
                # A corpus-wide typ histogram sums four DIFFERENT node kinds.
                # Do not pretend that all source phrase+atom values belong to
                # independent full phrases.

    def test_functional_phrase_and_clause_nodes_only_are_positive(self):
        c = self.catalog
        for corpus, (version, pin, _, _, _, _) in PINS.items():
            for native, target in (("phrase", "Phrase"), ("clause", "Clause"),
                                   ("phrase_atom", None), ("clause_atom", None)):
                with self.subTest(corpus=corpus, native=native):
                    m, = c.map_native(
                        corpus, kind="node", node=native,
                        corpus_version=version)
                    self.assertEqual(
                        (m.relation, m.target),
                        ("exact", OLIA + target) if target
                        else ("native-only", None),
                    )
                    self.assertEqual(m.corpus_version, version)
                    self.assertIn(pin, m.evidence or "")
                    self.assertEqual(
                        c.map_native(corpus, kind="entity", node=native,
                                     feature="typ", value="VP"), ())
        for node in ("phrase", "clause"):
            with self.subTest(node=node):
                mapped = c.find_correspondences(
                    "bhsa", "extrabiblical", kind="node", node=node)
                self.assertEqual(
                    {(x.destination.node, x.target, x.relation, x.scope)
                     for x in mapped},
                    {(node, OLIA + ("Phrase" if node == "phrase" else "Clause"),
                      "exact", "category")},
                )
        self.assertEqual(
            c.find_correspondences(
                "bhsa", "extrabiblical", kind="node", node="phrase_atom"),
            (),
        )

    def test_all_phrase_and_atom_type_values_have_explicit_dispositions(self):
        c = self.catalog
        for corpus, (version, pin, _, _, _, _) in PINS.items():
            rows = [x for x in c.load(corpus) if x.kind == "value"
                    and x.feature == "typ"
                    and x.node in ("phrase", "phrase_atom")]
            self.assertEqual(len(rows), 26)
            self.assertEqual(
                {(x.node, x.value) for x in rows},
                {(node, v) for node in ("phrase", "phrase_atom")
                 for v in SOURCE_PHRASE_CODES},
            )
            for code in SOURCE_PHRASE_CODES:
                for node in ("phrase", "phrase_atom"):
                    with self.subTest(corpus=corpus, code=code, node=node):
                        m, = c.map_native(
                            corpus, node=node, feature="typ", value=code,
                            corpus_version=version)
                        if node == "phrase" and code in EXACT:
                            expected = ("exact", OLIA + EXACT[code])
                        elif node == "phrase" and code in QUALIFIED:
                            expected = ("narrower", OLIA + QUALIFIED[code])
                        else:
                            expected = ("native-only", None)
                        self.assertEqual((m.relation, m.target), expected)
                        self.assertEqual(m.corpus_version, version)
                        self.assertIn(pin, m.evidence or "")

    def test_direct_phrase_class_matches_are_exact_and_bidirectional(self):
        c = self.catalog
        for code, target in EXACT.items():
            with self.subTest(code=code):
                matches = c.find_correspondences(
                    "bhsa", "extrabiblical",
                    node="phrase", feature="typ", value=code)
                self.assertEqual(
                    {(x.destination.node, x.destination.feature,
                      x.destination.value, x.target, x.relation, x.scope)
                     for x in matches},
                    {("phrase", "typ", code, OLIA + target,
                      "exact", "category")},
                )
                inverse = c.find_correspondences(
                    "extrabiblical", "bhsa",
                    node="phrase", feature="typ", value=code)
                self.assertEqual(
                    {(x.destination.node, x.destination.value, x.relation,
                      x.scope) for x in inverse},
                    {("phrase", code, "exact", "category")},
                )
                self.assertEqual(
                    c.find_correspondences(
                        "bhsa", "extrabiblical",
                        node="phrase_atom", feature="typ", value=code,
                        include_approximate=True), (),
                )

    def test_nominal_and_pronominal_phrases_retain_subtype_qualifiers(self):
        c = self.catalog
        for value in QUALIFIED:
            with self.subTest(code=value):
                self.assertEqual(c.find_correspondences(
                    "bhsa", "extrabiblical", node="phrase",
                    feature="typ", value=value), ())
                matches = c.find_correspondences(
                    "bhsa", "extrabiblical", node="phrase", feature="typ",
                    value=value, include_approximate=True)
                self.assertEqual(
                    {(x.destination.node, x.destination.feature,
                      x.destination.value, x.target,
                      x.source.relation, x.destination.relation,
                      x.relation, x.scope) for x in matches},
                    {("phrase", "typ", other, OLIA + "NounPhrase",
                      "narrower", "narrower",
                      "approximate-via-target", "category")
                     for other in QUALIFIED},
                )
                # Both OLiA and the source distinguish a broad noun phrase
                # from pronoun/proper-name subtypes. No word/lexeme identity.
        self.assertEqual(
            c.find_by_target(OLIA + "NounPhrase", corpus="bhsa"),
            (),
        )
        self.assertEqual(
            {(x.value, x.relation) for x in c.find_by_target(
                OLIA + "NounPhrase", corpus="extrabiblical",
                include_approximate=True)},
            {(v, "narrower") for v in QUALIFIED},
        )

    def test_source_adverbial_and_conjunctive_are_not_false_olia_classes(self):
        c = self.catalog
        for corpus in PINS:
            for value in NATIVE:
                with self.subTest(corpus=corpus, code=value):
                    row, = c.map_native(
                        corpus, node="phrase", feature="typ", value=value)
                    self.assertEqual((row.relation, row.target),
                                     ("native-only", None))
                    other = "extrabiblical" if corpus == "bhsa" else "bhsa"
                    self.assertEqual(
                        c.find_correspondences(
                            corpus, other, node="phrase", feature="typ",
                            value=value, include_approximate=True),
                        (),
                    )

    def test_real_tf_shaped_phrase_selection_and_atom_fail_closed(self):
        c = self.catalog
        phrase, = c.map_native("extrabiblical", kind="node", node="phrase")
        verb, = c.map_native(
            "extrabiblical", node="phrase", feature="typ", value="VP")
        noun, = c.map_native(
            "extrabiblical", node="phrase", feature="typ", value="NP")
        atom, = c.map_native(
            "extrabiblical", kind="node", node="phrase_atom")
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(node):
                        return {"phrase": (1, 2, 3, 4),
                                "phrase_atom": (11, 12)}[node]
            @staticmethod
            def Fs(feature):
                assert feature == "typ"
                class Feature:
                    @staticmethod
                    def v(n):
                        return {1: "VP", 2: "PP", 3: "NP", 4: "VP"}[n]
                return Feature()
        self.assertEqual(resolve_nodes(API(), phrase,
                                       corpus_version="0.2"), (1, 2, 3, 4))
        self.assertEqual(resolve_nodes(API(), verb,
                                       corpus_version="0.2"), (1, 4))
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(API(), noun, corpus_version="0.2")
        with self.assertRaisesRegex(MappingError, "only positive"):
            resolve_nodes(API(), atom, corpus_version="0.2")
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), verb, corpus_version="2021")


if __name__ == "__main__":
    unittest.main()
