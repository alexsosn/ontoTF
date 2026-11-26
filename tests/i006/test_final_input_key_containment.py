from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir
from tests.i006.test_semantic_resolver_contract import prerequisite_for, request_for


RESOLVER = importlib.import_module("ontotf.semantic_resolver")


class I006FinalInputKeyContainmentTests(unittest.TestCase):
    def test_request_profile_id_must_fail_semantically_before_set_membership(self):
        ir = compiled_noun_ir(("bhsa",))
        request = request_for(RESOLVER, ("bhsa",))
        request = replace(request, key=replace(request.key, profile_id=[]))
        state = prerequisite_for(RESOLVER, ir.variants[0])

        with self.assertRaises(RESOLVER.SemanticResolutionError) as raised:
            RESOLVER.semantic_resolve(ir, request, (state,))

        self.assertEqual(raised.exception.problem.category, "unknown_request_vocabulary")

    def test_prerequisite_variant_fields_fail_as_invalid_prerequisite_before_hashing(self):
        ir = compiled_noun_ir(("bhsa",))
        request = request_for(RESOLVER, ("bhsa",))
        state = prerequisite_for(RESOLVER, ir.variants[0])
        state = replace(state, variant=replace(state.variant, corpus_id=[]))

        with self.assertRaises(RESOLVER.SemanticResolutionError) as raised:
            RESOLVER.semantic_resolve(ir, request, (state,))

        self.assertEqual(raised.exception.problem.category, "invalid_prerequisite")


if __name__ == "__main__":
    unittest.main()
