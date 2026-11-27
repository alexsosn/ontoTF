from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir
from tests.i006.test_semantic_resolver_contract import prerequisite_for, request_for


RESOLVER = importlib.import_module("ontotf.semantic_resolver")


def assert_invalid_compiled_ir(testcase: unittest.TestCase, ir) -> None:
    state = prerequisite_for(RESOLVER, ir.variants[0])
    with testcase.assertRaises(RESOLVER.SemanticResolutionError) as raised:
        RESOLVER.semantic_resolve(
            ir,
            request_for(RESOLVER, ("bhsa",)),
            (state,),
        )
    testcase.assertEqual(raised.exception.problem.category, "invalid_compiled_ir")


class I006FinalSemanticKeyContainmentTests(unittest.TestCase):
    def test_semantic_binding_variant_must_be_exact_variant_key(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        forged_row = replace(rows[0], variant=[])
        assert_invalid_compiled_ir(
            self,
            replace(ir, semantic_index=((key, (forged_row,)),)),
        )

    def test_semantic_index_key_fields_must_be_deeply_immutable(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        forged_key = replace(key, target=[])
        assert_invalid_compiled_ir(
            self,
            replace(ir, semantic_index=((forged_key, rows),)),
        )


if __name__ == "__main__":
    unittest.main()
