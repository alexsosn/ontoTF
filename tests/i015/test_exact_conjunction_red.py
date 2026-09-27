from __future__ import annotations

import importlib
import unittest

from tfont.semantic_ir import SemanticKey

RESOLVER = importlib.import_module("tfont.semantic_resolver")
EXECUTION = importlib.import_module("tfont.semantic_execution")

BASE = "http://purl.org/olia/olia.owl#"


def noun_key():
    return SemanticKey(
        profile_id="linguistic",
        capability_id="linguistic.part-of-speech",
        target=BASE + "Noun",
        formal_kind="class",
        semantic_role="annotation-value",
    )


def plural_key():
    return SemanticKey(
        profile_id="linguistic",
        capability_id="linguistic.morphology",
        target=BASE + "Plural",
        formal_kind="class",
        semantic_role="annotation-value",
    )


HAS_CONJUNCTION = all(
    hasattr(RESOLVER, name)
    for name in (
        "SemanticConjunctionRequest",
        "SemanticConjunctionResolutionResult",
        "semantic_resolve_conjunction",
        "EXACT_CONJUNCTION_RESOLVER_CONTRACT",
    )
) and all(
    hasattr(EXECUTION, name)
    for name in (
        "ExactConjunctionCorpusExecution",
        "ExactConjunctionExecutionResult",
        "execute_exact_conjunction",
        "EXACT_CONJUNCTION_EXECUTION_CONTRACT",
    )
)


class I015ExactConjunctionRedTests(unittest.TestCase):
    def test_exact_conjunction_api_exists(self):
        self.assertTrue(HAS_CONJUNCTION, "RED: exact conjunction runtime is absent")

    @unittest.skipUnless(HAS_CONJUNCTION, "RED sentinel owns API absence")
    def test_request_requires_two_distinct_semantic_keys(self):
        request_type = RESOLVER.SemanticConjunctionRequest
        with self.assertRaises(RESOLVER.SemanticResolutionError) as raised:
            RESOLVER.semantic_resolve_conjunction(
                None,
                request_type(keys=(noun_key(),), corpora=("bhsa",)),
                (),
            )
        self.assertEqual(raised.exception.problem.category, "invalid_semantic_conjunction")

    @unittest.skipUnless(HAS_CONJUNCTION, "RED sentinel owns API absence")
    def test_duplicate_semantic_keys_are_invalid(self):
        request_type = RESOLVER.SemanticConjunctionRequest
        with self.assertRaises(RESOLVER.SemanticResolutionError) as raised:
            RESOLVER.semantic_resolve_conjunction(
                None,
                request_type(keys=(noun_key(), noun_key()), corpora=("bhsa",)),
                (),
            )
        self.assertEqual(raised.exception.problem.category, "invalid_semantic_conjunction")


if __name__ == "__main__":
    unittest.main()
