"""Pinned SEDRA-derived Peshitta 0.2 text-carrier mappings.

The source transcribes whitespace-delimited Syriac words without splitting
enclitics or providing a lemma. A/B are local witness *labels*, not physical
manuscript or item identifiers. Category joins never assert token identity.
"""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes

SOURCE = "9850f5addade26f681334aa475570bef9b0b440a"
TOKEN = "http://purl.org/olia/olia.owl#Token"
EXPRESSION = "http://iflastandards.info/ns/lrm/lrmoo/F2_Expression"
LRMOO = "http://iflastandards.info/ns/lrm/lrmoo/"


class PeshittaSourceTextMappingsTests(unittest.TestCase):
    def test_actual_pinned_source_counts_and_provenance(self):
        census = json.loads((
            Path(__file__).resolve().parents[2] /
            "docs/research/data/generated/r005/peshitta.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual((census["revision"], census["tf_version"]),
                         (SOURCE, "0.2"))
        self.assertEqual(
            census["node_types"],
            {"book": 65, "chapter": 1269,
             "verse": 31341, "word": 426835},
        )
        word = census["node_features"]["word"]
        self.assertEqual(word["applies_to"], ["word"])
        self.assertEqual(word["nodes_with_value"], 426834)
        self.assertEqual(word["empty_observation_count"], 1)
        self.assertEqual(word["metadata"]["description"],
                         "full form of the word in syriac script")
        transcription = census["node_features"]["word_etcbc"]
        self.assertEqual(transcription["nodes_with_value"], 426834)
        self.assertEqual(transcription["empty_observation_count"], 1)
        self.assertEqual(census["node_features"]["witness"]["applies_to"],
                         ["book", "chapter", "verse"])
        self.assertEqual(census["node_features"]["witness"]["observed_frequencies"],
                         {"A": 1230, "B": 1155})

    def test_only_populated_word_carriers_are_orthographic_tokens(self):
        catalog = MappingCatalog()
        self.assertIn("peshitta", catalog.list_corpora())
        bare, = catalog.map_native(
            "peshitta", kind="node", node="word")
        self.assertEqual((bare.relation, bare.target),
                         ("native-only", None))
        selected, = catalog.map_native(
            "peshitta", kind="node", node="word", feature="word",
            corpus_version="0.2")
        self.assertEqual((selected.relation, selected.target),
                         ("exact", TOKEN))
        self.assertEqual(selected.corpus_version, "0.2")
        self.assertIn(SOURCE, selected.evidence or "")
        self.assertIn(selected, catalog.find_by_target(
            TOKEN, corpus="peshitta", kind="node"))
        # word_etcbc is a second transcription of the same text carriers,
        # not an additional independently aligned 426834-word corpus.
        self.assertEqual(catalog.map_native(
            "peshitta", kind="node", node="word", feature="word_etcbc"), ())
        self.assertEqual(catalog.map_native(
            "peshitta", kind="entity", node="word", feature="word",
            value="ܒܪܫܝܬ"), ())
        for corpus, feature in (("bhsa", "g_word"), ("syrnt", "word"),
                                ("pseudepigrapha", "g_word_utf8")):
            with self.subTest(other=corpus):
                matches = catalog.find_correspondences(
                    "peshitta", corpus, kind="node",
                    node="word", feature="word")
                self.assertIn(
                    (corpus, TOKEN, "exact", "category", feature),
                    {(m.destination.corpus, m.target, m.relation, m.scope,
                      m.destination.feature) for m in matches},
                )

    def test_source_books_are_text_expressions_but_not_items_or_works(self):
        catalog = MappingCatalog()
        book, = catalog.map_native("peshitta", kind="node", node="book")
        self.assertEqual((book.relation, book.target, book.corpus_version),
                         ("exact", EXPRESSION, "0.2"))
        self.assertIn(SOURCE, book.evidence or "")
        self.assertIn("LRMoo 1.1.1", book.note or "")
        self.assertIn(book, catalog.find_by_target(
            EXPRESSION, corpus="peshitta", kind="node"))
        versions = catalog.find_correspondences(
            "peshitta", "pseudepigrapha", kind="node", node="book")
        self.assertEqual(
            {(m.target, m.relation, m.scope, m.destination.node)
             for m in versions},
            {(EXPRESSION, "exact", "category", "book")},
        )
        for type_name in ("chapter", "verse"):
            with self.subTest(node=type_name):
                m, = catalog.map_native("peshitta", kind="node", node=type_name)
                self.assertEqual((m.relation, m.target),
                                 ("native-only", None))
        for cls in ("F1_Work", "F3_Manifestation", "F5_Item"):
            self.assertEqual(catalog.find_by_target(
                LRMOO + cls, corpus="peshitta", kind="node"), ())

    def test_witness_letters_are_native_version_labels_not_manuscripts(self):
        catalog = MappingCatalog()
        rows = [m for m in catalog.load("peshitta")
                if m.kind == "value" and m.feature == "witness"]
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            {(m.node, m.value) for m in rows},
            {(node, letter) for node in ("book", "chapter", "verse")
             for letter in ("A", "B")},
        )
        for node in ("book", "chapter", "verse"):
            for letter in ("A", "B"):
                with self.subTest(node=node, letter=letter):
                    m, = catalog.map_native(
                        "peshitta", kind="value", node=node,
                        feature="witness", value=letter,
                        corpus_version="0.2")
                    self.assertEqual((m.relation, m.target),
                                     ("native-only", None))
                    self.assertIn(SOURCE, m.evidence or "")
                    self.assertEqual(catalog.find_correspondences(
                        "peshitta", "pseudepigrapha", node=node,
                        feature="witness", value=letter,
                        include_approximate=True), ())
                    self.assertEqual(catalog.map_native(
                        "peshitta", kind="entity", node=node,
                        feature="witness", value=letter), ())
        self.assertEqual(catalog.find_by_target(
            LRMOO + "F5_Item", corpus="peshitta", kind="node",
            include_approximate=True), ())

    def test_native_tf_execution_keeps_one_unpopulated_word_out(self):
        catalog = MappingCatalog()
        tok, = catalog.map_native("peshitta", kind="node",
                                  node="word", feature="word")
        expr, = catalog.map_native("peshitta", kind="node", node="book")
        bare, = catalog.map_native("peshitta", kind="node", node="word")
        witness, = catalog.map_native(
            "peshitta", kind="value", node="book",
            feature="witness", value="A")

        class Otype:
            def s(self, node):
                return {"word": (1, 2, 3, 4),
                        "book": (101, 102)}[node]
        class API:
            class F:
                otype = Otype()

            @staticmethod
            def Fs(feature):
                assert feature == "word"
                class Values:
                    @staticmethod
                    def v(node):
                        return {1: "ܒܪܫܝܬ", 2: None,
                                3: "", 4: "ܡܢ"}[node]
                return Values()

        self.assertEqual(resolve_nodes(API(), tok, corpus_version="0.2"),
                         (1, 4))
        self.assertEqual(resolve_nodes(API(), expr, corpus_version="0.2"),
                         (101, 102))
        for row in (bare, witness):
            with self.subTest(row=row.kind):
                with self.assertRaisesRegex(MappingError, "only positive"):
                    resolve_nodes(API(), row, corpus_version="0.2")
        with self.assertRaisesRegex(MappingError, "loaded corpus version"):
            resolve_nodes(API(), tok, corpus_version="2021")


if __name__ == "__main__":
    unittest.main()
