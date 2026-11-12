"""Phrase determination is source morphology, not automatic semantic definiteness.

BHSA's codebook distinguishes determined / undetermined / NA on functional
phrases and their continuous atoms. OLiA Definite/Indefinite, however, are
semantic definiteness classes defined in terms of hearer familiarity. These
are defensibly related categories only, never exact/one-way subtype claims.
"""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

OLIA = "http://purl.org/olia/olia.owl#"
PINS = {
    "bhsa": ("2021", "4db00e2157915495e1a4d3d57e41223df24775da",
             253203, 267532, {"NA": 280219, "det": 178601, "und": 61915}),
    "extrabiblical": ("0.2", "9a56288e6777bad6328856acf055c780e65dd5d9",
                     22770, 23370, {"NA": 25061, "det": 12314, "und": 8765}),
}
VALUES = {"NA", "det", "und"}
QUALIFIED = {"det": "Definite", "und": "Indefinite"}


class PhraseDeterminationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = MappingCatalog()

    def test_real_source_counts_are_pinned_but_union_not_phrase_only(self):
        for corpus, (version, pin, phrases, atoms, counts) in PINS.items():
            with self.subTest(corpus=corpus):
                src = json.loads((
                    Path(__file__).resolve().parents[2]
                    / f"docs/research/data/generated/r005/{corpus}.json"
                ).read_text(encoding="utf-8"))
                self.assertEqual((src["tf_version"], src["revision"]),
                                 (version, pin))
                self.assertEqual(
                    (src["node_types"]["phrase"],
                     src["node_types"]["phrase_atom"]), (phrases, atoms))
                feature = src["node_features"]["det"]
                self.assertEqual(set(feature["applies_to"]),
                                 {"phrase", "phrase_atom"})
                self.assertEqual(feature["observed_frequencies"], counts)
                self.assertEqual(feature["observation_count"], phrases+atoms)
                self.assertEqual(set(feature["observed_values"]), VALUES)

    def test_pinned_source_values_have_all_twelve_safe_decisions(self):
        for corpus, (version, pin, _, _, _) in PINS.items():
            rows = [m for m in self.cat.load(corpus)
                    if m.kind == "value" and m.feature == "det"
                    and m.node in ("phrase", "phrase_atom")]
            self.assertEqual(len(rows), 6)
            self.assertEqual({(m.node, m.value) for m in rows},
                             {(n, v) for n in ("phrase", "phrase_atom")
                              for v in VALUES})
            for node in ("phrase", "phrase_atom"):
                for value in VALUES:
                    with self.subTest(corpus=corpus, node=node, value=value):
                        m, = self.cat.map_native(
                            corpus, node=node, feature="det", value=value,
                            corpus_version=version)
                        if node == "phrase" and value in QUALIFIED:
                            expected = ("related", OLIA + QUALIFIED[value])
                        else:
                            expected = ("native-only", None)
                        self.assertEqual((m.relation, m.target), expected)
                        self.assertIn(pin, m.evidence or "")
                        self.assertEqual(m.corpus_version, version)
                        self.assertEqual(self.cat.map_native(
                            corpus, kind="entity", node=node, feature="det",
                            value=value), ())

    def test_opt_in_discovery_preserves_related_not_exact_or_narrower(self):
        for code, target in QUALIFIED.items():
            with self.subTest(code=code):
                self.assertEqual(self.cat.find_correspondences(
                    "bhsa", "extrabiblical", node="phrase", feature="det",
                    value=code), ())
                result = self.cat.find_correspondences(
                    "bhsa", "extrabiblical", node="phrase", feature="det",
                    value=code, include_approximate=True)
                self.assertEqual(
                    {(x.destination.node, x.destination.feature,
                      x.destination.value, x.target, x.source.relation,
                      x.destination.relation, x.relation, x.scope)
                     for x in result},
                    {("phrase", "det", code, OLIA+target, "related",
                      "related", "approximate-via-target", "category")},
                )
                self.assertEqual(self.cat.find_by_target(
                    OLIA + target, corpus="bhsa"), ())
                qualified = self.cat.find_by_target(
                    OLIA + target, corpus="bhsa",
                    include_approximate=True)
                self.assertIn(self.cat.map_native(
                    "bhsa", node="phrase", feature="det", value=code)[0],
                    qualified)
                self.assertNotIn("exact", {x.relation for x in qualified})

    def test_source_atom_and_na_are_not_semantically_promoted(self):
        c = self.cat
        for corpus in PINS:
            other = "extrabiblical" if corpus == "bhsa" else "bhsa"
            for node in ("phrase", "phrase_atom"):
                for value in VALUES:
                    if node == "phrase" and value != "NA":
                        continue
                    with self.subTest(corpus=corpus,node=node,value=value):
                        self.assertEqual(c.find_correspondences(
                            corpus, other, node=node, feature="det",
                            value=value, include_approximate=True), ())

    def test_related_determination_cannot_run_as_exact_tf_selection(self):
        c = self.cat
        class API:
            class F:
                class otype:
                    @staticmethod
                    def s(node):
                        assert node == "phrase"
                        return (1, 2, 3)
            @staticmethod
            def Fs(name):
                assert name == "det"
                class Feature:
                    @staticmethod
                    def v(n):
                        return {1: "det", 2: "NA", 3: "und"}[n]
                return Feature()
        related, = c.map_native(
            "extrabiblical", node="phrase", feature="det", value="det")
        with self.assertRaisesRegex(MappingError, "exact"):
            resolve_nodes(API(), related, corpus_version="0.2")
        unresolved, = c.map_native(
            "extrabiblical", node="phrase", feature="det", value="NA")
        with self.assertRaisesRegex(MappingError, "only positive"):
            resolve_nodes(API(), unresolved, corpus_version="0.2")
        with self.assertRaisesRegex(MappingError, "version"):
            c.map_native("extrabiblical", node="phrase", feature="det",
                         value="det", corpus_version="2021")


if __name__ == "__main__":
    unittest.main()
