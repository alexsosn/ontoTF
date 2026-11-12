"""Pinned ETCBC syntactic phrase functions; do not confuse roles with POS.

The original BHSA codebook calls these phrase *functions*. The locked OLiA
syntax vocabulary distinguishes SyntacticSubject/Object/Complement/Predicate
from SyntacticAdjunct and Modifier, which OLiA declares equivalent. We do
not promote the source's distinct adjunct/modifier tags to exact equivalence.
"""
from pathlib import Path
import json
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

BASE = "http://purl.org/olia/olia.owl#"
PINS = {
    "bhsa": ("2021", "4db00e2157915495e1a4d3d57e41223df24775da", 253203),
    "extrabiblical": ("0.2", "9a56288e6777bad6328856acf055c780e65dd5d9", 22770),
}
EXACT = {
    "Subj": "SyntacticSubject",
    "Objc": "SyntacticObject",
    "Cmpl": "SyntacticComplement",
    "Pred": "Predicate",
}
NARROW = {
    "Adju": "SyntacticAdjunct",
    "Modi": "Modifier",
    "PreC": "SyntacticComplement",
    "PrAd": "SyntacticAdjunct",
    "PreO": "Predicate",
    "PreS": "Predicate",
    "ModS": "Modifier",
    "PrcS": "SyntacticComplement",
}
POSITIVE = {**EXACT, **NARROW}
POSITIVE_OBSERVATIONS = {
    "bhsa": (141753, 39190),
    "extrabiblical": (10538, 6080),
}


class PhraseFunctionMappingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = MappingCatalog()

    def test_pinned_real_phrase_function_domains_and_denominators(self):
        for corpus, (version, revision, phrase_count) in PINS.items():
            with self.subTest(corpus=corpus):
                path = (Path(__file__).resolve().parents[2]
                        / "docs/research/data/generated/r005"
                        / f"{corpus}.json")
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual((data["tf_version"], data["revision"]),
                                 (version, revision))
                function = data["node_features"]["function"]
                self.assertEqual(function["applies_to"], ["phrase"])
                self.assertEqual(data["node_types"]["phrase"], phrase_count)
                self.assertEqual(function["nodes_with_value"], phrase_count)
                self.assertEqual(function["observation_count"], phrase_count)
                self.assertEqual(sum(function["observed_frequencies"].values()),
                                 phrase_count)
                self.assertEqual(function["observed_unique_count"],
                                 29 if corpus == "bhsa" else 21)
                self.assertTrue(set(EXACT) <= set(function["observed_values"]))
                narrower = set(NARROW) & set(function["observed_values"])
                freq = function["observed_frequencies"]
                self.assertEqual(
                    (sum(freq[x] for x in EXACT),
                     sum(freq[x] for x in narrower)),
                    POSITIVE_OBSERVATIONS[corpus],
                )
                if corpus == "extrabiblical":
                    self.assertEqual(freq["Unkn"], 23)

    def test_all_source_values_have_one_conservative_disposition(self):
        for corpus, (version, revision, _) in PINS.items():
            path = (Path(__file__).resolve().parents[2]
                    / "docs/research/data/generated/r005"
                    / f"{corpus}.json")
            values = json.loads(path.read_text(encoding="utf-8"))[
                "node_features"]["function"]["observed_values"]
            rows = [r for r in self.catalog.load(corpus)
                    if r.kind == "value" and r.node == "phrase"
                    and r.feature == "function"]
            self.assertEqual(len(rows), len(values))
            self.assertEqual({r.value for r in rows}, set(values))
            for value in values:
                with self.subTest(corpus=corpus, code=value):
                    found = self.catalog.map_native(
                        corpus, node="phrase", feature="function", value=value,
                        corpus_version=version)
                    self.assertEqual(len(found), 1)
                    row = found[0]
                    relation = ("exact" if value in EXACT else
                                "narrower" if value in NARROW else
                                "native-only")
                    expected = POSITIVE.get(value)
                    self.assertEqual(
                        (row.relation, row.target),
                        (relation, BASE + expected if expected else None),
                    )
                    self.assertIn(revision, row.evidence or "")
                    self.assertEqual(row.corpus_version, version)
            self.assertEqual(self.catalog.map_native(
                corpus, kind="entity", node="phrase",
                feature="function", value="Subj"), ())

    def test_four_common_phrase_roles_crosswalk_exactly(self):
        for code, target in EXACT.items():
            with self.subTest(code=code):
                result = self.catalog.find_correspondences(
                    "bhsa", "extrabiblical",
                    node="phrase", feature="function", value=code)
                self.assertEqual(
                    {(x.source.node, x.destination.node,
                      x.source.feature, x.destination.feature,
                      x.destination.value, x.relation, x.scope, x.target)
                     for x in result},
                    {("phrase", "phrase", "function", "function",
                      code, "exact", "category", BASE + target)},
                )
                inverse = self.catalog.find_correspondences(
                    "extrabiblical", "bhsa",
                    node="phrase", feature="function", value=code)
                self.assertEqual(
                    {(x.destination.value, x.relation, x.scope)
                     for x in inverse},
                    {(code, "exact", "category")},
                )

    def test_specialized_and_nearby_roles_require_opt_in(self):
        for code, target in NARROW.items():
            if code not in ("Adju", "Modi", "PreC", "PrAd"):
                continue  # BHSA-only subtype: tested via its native disposition
            with self.subTest(code=code):
                self.assertEqual(
                    self.catalog.find_correspondences(
                        "bhsa", "extrabiblical", node="phrase",
                        feature="function", value=code), (),
                )
                links = self.catalog.find_correspondences(
                    "bhsa", "extrabiblical", node="phrase",
                    feature="function", value=code,
                    include_approximate=True)
                self.assertEqual(
                    {(x.destination.value, x.target, x.relation, x.scope,
                      x.source.relation, x.destination.relation)
                     for x in links},
                    {(code, BASE + target, "approximate-via-target",
                      "category", "narrower", "narrower")},
                )
        # OLiA itself equates Modifier with SyntacticAdjunct. Its ontology
        # equivalence must NOT silently erase the source's native contrast.
        self.assertEqual(
            self.catalog.find_correspondences(
                "bhsa", "extrabiblical", node="phrase",
                feature="function", value="Adju"), (),
        )
        self.assertNotEqual(
            self.catalog.map_native(
                "bhsa", node="phrase", feature="function",
                value="Adju")[0].target,
            self.catalog.map_native(
                "bhsa", node="phrase", feature="function",
                value="Modi")[0].target,
        )

    def test_no_forged_pos_or_question_sentence_correspondence(self):
        for corpus in PINS:
            for code in ("Conj", "Intj", "Nega", "Ques", "Voct", "Rela"):
                with self.subTest(corpus=corpus, code=code):
                    row, = self.catalog.map_native(
                        corpus, node="phrase", feature="function", value=code)
                    self.assertEqual((row.relation, row.target),
                                     ("native-only", None))
                    other = "extrabiblical" if corpus == "bhsa" else "bhsa"
                    self.assertEqual(
                        self.catalog.find_correspondences(
                            corpus, other, node="phrase",
                            feature="function", value=code,
                            include_approximate=True), (),
                    )

    def test_exact_phrase_nodes_execute_and_qualified_nodes_fail_closed(self):
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(node):
                        assert node == "phrase"
                        return (11, 12, 13, 14, 15)
            @staticmethod
            def Fs(feature):
                assert feature == "function"
                class Feature:
                    @staticmethod
                    def v(node):
                        return {11: "Subj", 12: "Modi", 13: "Objc",
                                14: "Subj", 15: "Unkn"}[node]
                return Feature()
        exact, = self.catalog.map_native(
            "extrabiblical", node="phrase", feature="function",
            value="Subj")
        self.assertEqual(resolve_nodes(API(), exact, corpus_version="0.2"),
                         (11, 14))
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), exact, corpus_version="2021")
        narrower, = self.catalog.map_native(
            "extrabiblical", node="phrase", feature="function",
            value="Modi")
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(API(), narrower, corpus_version="0.2")
        unresolved, = self.catalog.map_native(
            "extrabiblical", node="phrase", feature="function",
            value="Unkn")
        with self.assertRaisesRegex(MappingError, "only positive"):
            resolve_nodes(API(), unresolved, corpus_version="0.2")


if __name__ == "__main__":
    unittest.main()
