from __future__ import annotations

import importlib
import unittest

from tfont.production_bundles import load_production_noun_bundles
from tfont.semantic_execution import LoadedComponentContext, LoadedCorpusContext
from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle

RESOLVER = importlib.import_module("tfont.semantic_resolver")
EXECUTION = importlib.import_module("tfont.semantic_execution")
HAS_CONJUNCTION = hasattr(RESOLVER, "SemanticConjunctionRequest") and hasattr(
    EXECUTION, "execute_exact_conjunction"
)

BASE = "http://purl.org/olia/olia.owl#"


def key(target: str) -> SemanticKey:
    return SemanticKey(
        profile_id="linguistic",
        capability_id=(
            "linguistic.part-of-speech"
            if target in {"Noun", "ProperNoun"}
            else "linguistic.morphology"
        ),
        target=BASE + target,
        formal_kind="class",
        semantic_role="annotation-value",
    )


class _Feature:
    def __init__(self, values):
        self.values = dict(values)

    def v(self, node):
        return self.values.get(node)

    def s(self, value):
        return tuple(node for node, observed in self.values.items() if observed == value)


class _Otype(_Feature):
    pass


class _API:
    def __init__(self, corpus_id: str):
        types = {node: "word" for node in range(1, 7)}
        if corpus_id == "syriac":
            sp = {1: "subs", 2: "subs", 3: "subs", 4: "subs", 5: "verb", 6: "subs"}
            ls = {3: "prop", 4: "prop", 6: "prop"}
        else:
            sp = {1: "subs", 2: "subs", 3: "nmpr", 4: "nmpr", 5: "verb", 6: "nmpr"}
            ls = {}
        gn = {1: "m", 2: "f", 3: "f", 4: "m", 5: "m", 6: "f"}
        nu = {1: "sg", 2: "pl", 3: "sg", 4: "pl", 5: "pl", 6: "du"}
        self.F = type(
            "Features",
            (),
            {
                "otype": _Otype(types),
                "sp": _Feature(sp),
                "ls": _Feature(ls),
                "gn": _Feature(gn),
                "nu": _Feature(nu),
            },
        )()

    def Fall(self):
        return ("otype", "sp", "ls", "gn", "nu")


def compiled_and_contexts():
    bundles = load_production_noun_bundles()
    validated = tuple(validate_semantic_bundle(bundle) for bundle in bundles)
    ir = compile_semantic_ir(validated)
    contexts = []
    for bundle in bundles:
        corpus_id = bundle.mappings.data["mappings"][0]["corpus_id"]
        component = bundle.expected_parent_manifest.data["components"][0]
        contexts.append(
            LoadedCorpusContext(
                corpus_id=corpus_id,
                parent_manifest_digest=next(
                    row.key.expected_parent_manifest_digest
                    for row in ir.variants
                    if row.key.corpus_id == corpus_id
                ),
                components=(
                    LoadedComponentContext(
                        component_id=component["component_id"],
                        content_digest=component["content_digest"],
                        api=_API(corpus_id),
                    ),
                ),
            )
        )
    return ir, tuple(contexts)


@unittest.skipUnless(HAS_CONJUNCTION, "RED sentinel owns conjunction API absence")
class I015ExactConjunctionBehaviorTests(unittest.TestCase):
    def request(self, *names, corpora=("bhsa", "syriac", "extrabiblical")):
        return RESOLVER.SemanticConjunctionRequest(
            keys=tuple(key(name) for name in names),
            corpora=tuple(corpora),
        )

    def execute(self, *names):
        ir, contexts = compiled_and_contexts()
        return EXECUTION.execute_exact_conjunction(ir, self.request(*names), contexts)

    def test_noun_and_plural_intersects_nodes_in_all_three_corpora(self):
        result = self.execute("Noun", "Plural")
        self.assertEqual(
            [(row.corpus_id, row.nodes) for row in result.corpora],
            [
                ("bhsa", (2, 4)),
                ("extrabiblical", (2, 4)),
                ("syriac", (2, 4)),
            ],
        )

    def test_proper_noun_and_feminine_uses_corpus_specific_proper_encoding(self):
        result = self.execute("ProperNoun", "Feminine")
        self.assertEqual(
            [(row.corpus_id, row.nodes) for row in result.corpora],
            [
                ("bhsa", (3, 6)),
                ("extrabiblical", (3, 6)),
                ("syriac", (3, 6)),
            ],
        )
        syriac = next(row for row in result.corpora if row.corpus_id == "syriac")
        bindings = {plan.semantic_key.target: plan.native_execution_binding for plan in syriac.plans}
        self.assertEqual(bindings[BASE + "ProperNoun"].feature, "ls")
        self.assertEqual(bindings[BASE + "ProperNoun"].value, "prop")

    def test_empty_exact_intersection_is_valid(self):
        result = self.execute("Dual", "Masculine")
        self.assertTrue(all(row.nodes == () for row in result.corpora))

    def test_key_order_does_not_change_resolution_or_execution(self):
        ir, contexts = compiled_and_contexts()
        forward = EXECUTION.execute_exact_conjunction(
            ir, self.request("Noun", "Plural"), contexts
        )
        reverse = EXECUTION.execute_exact_conjunction(
            ir, self.request("Plural", "Noun"), contexts
        )
        self.assertEqual(forward, reverse)

    def test_constituent_provenance_is_retained(self):
        result = self.execute("Noun", "Plural")
        for corpus in result.corpora:
            self.assertEqual(len(corpus.plans), 2)
            for plan in corpus.plans:
                self.assertEqual(plan.mapping_review.status, "reviewed")
                self.assertEqual(plan.projection_review.status, "reviewed")
                self.assertTrue(plan.mapping_evidence)
                self.assertTrue(plan.projection_evidence)
                self.assertTrue(plan.plan_fingerprint)


if __name__ == "__main__":
    unittest.main()
