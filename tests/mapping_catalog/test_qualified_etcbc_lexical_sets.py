"""Scoped qualified lexical-set mapping backed by the ETCBC source codebook.

ETCBC/bhsa@4db00e2 docs/features/ls.md explicitly calls these subclasses
nouns, verbs and adverbs, not numeral or generic particle categories.
ETCBC/extrabiblical@9a56288 tf/0.2/{ls,sp}.tf contains all six codes:
nmdi 1028 subs, nmcp 332 subs, mult 4 subs, vbcp 303 verb,
quot 839 verb and afad 92 advb. These are source word counts.
"""
from __future__ import annotations

import unittest

from ontotf.xml_mappings import (
    MappingCatalog, MappingError, find_correspondences, map_native,
    resolve_nodes,
)

OLIA = "http://purl.org/olia/olia.owl#"
CODE_TO_PARENT = {
    "nmdi": "Noun",    # distributive noun, not distributive numeral
    "nmcp": "Noun",    # copulative noun
    "mult": "Noun",    # noun of multitude, NOT MultipleNumeral
    "vbcp": "Verb",    # copulative verb
    "quot": "Verb",    # quotation verb
    "afad": "Adverb",  # anaphoric adverb
}


class QualifiedETCBCLexicalSetTests(unittest.TestCase):
    def test_reviewed_parent_classes_preserve_native_subtypes_across_scopes(self):
        for corpus, nodes, version in (
            ("bhsa", ("word", "lex"), "2021"),
            ("extrabiblical", ("word",), "0.2"),
        ):
            for node in nodes:
                for code, parent in CODE_TO_PARENT.items():
                    with self.subTest(corpus=corpus, node=node, code=code):
                        row, = map_native(
                            corpus, node=node, feature="ls", value=code,
                            corpus_version=version,
                        )
                        self.assertEqual((row.relation, row.target),
                                         ("narrower", OLIA + parent))
                        self.assertEqual(row.corpus_version, version)
                        self.assertIn("https://github.com/", row.evidence)
                        with self.assertRaisesRegex(MappingError, "exact"):
                            resolve_nodes(object(), row, corpus_version=version)
        # These are NOT equivalent lexical items or individual word tokens.
        self.assertEqual(
            map_native("bhsa", kind="entity", node="word", feature="ls",
                       value="afad"), (),
        )

    def test_opt_in_only_cross_corpus_qualified_correspondences(self):
        for code, parent in CODE_TO_PARENT.items():
            with self.subTest(code=code):
                self.assertEqual(
                    find_correspondences(
                        "bhsa", "extrabiblical",
                        node="word", feature="ls", value=code,
                    ), (),
                )
                matches = find_correspondences(
                    "bhsa", "extrabiblical",
                    node="word", feature="ls", value=code,
                    source_version="2021", target_version="0.2",
                    include_approximate=True,
                )
                self.assertTrue(any(
                    m.destination.node == "word"
                    and m.destination.feature == "ls"
                    and m.destination.value == code
                    and m.target == OLIA + parent
                    for m in matches
                ))
                self.assertTrue(all(
                    m.relation == "approximate-via-target"
                    and m.scope == "category" for m in matches
                ))

    def test_numeral_false_friend_and_unverified_potential_forms_remain_safe(self):
        catalog = MappingCatalog()
        for corpus in ("bhsa", "extrabiblical"):
            with self.subTest(corpus=corpus):
                rows = catalog.map_native(
                    corpus, node="word", feature="ls", value="mult")
                self.assertEqual(rows[0].target, OLIA + "Noun")
                self.assertNotEqual(rows[0].target, OLIA + "MultipleNumeral")
                for source_value in ("padv", "ppre", "focp"):
                    native, = catalog.map_native(
                        corpus, node="word", feature="ls",
                        value=source_value,
                    )
                    self.assertEqual((native.relation, native.target),
                                     ("native-only", None))
                with self.assertRaisesRegex(MappingError, "not verified"):
                    catalog.map_native(
                        corpus, node="word", feature="ls", value="nmdi",
                        corpus_version="wrong",
                    )


if __name__ == "__main__":
    unittest.main()
