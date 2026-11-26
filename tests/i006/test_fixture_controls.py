from __future__ import annotations

import unittest

from tests.i006._fixtures import (
    compiled_noun_ir,
    noun_semantic_key,
    validated_binding_presence_bundle,
)
from ontotf.semantic_ir import compile_semantic_ir


class I006FixtureControlTests(unittest.TestCase):
    def test_three_corpus_noun_fixture_compiles_before_resolver_exists(self):
        ir = compiled_noun_ir()
        rows = dict(ir.semantic_index)[noun_semantic_key()]
        self.assertEqual(
            [row.corpus_id for row in rows],
            ["bhsa", "extrabiblical", "syriac"],
        )
        self.assertTrue(all(row.assessment == "exact" for row in rows))
        self.assertTrue(all(row.native_execution_binding.feature == "sp" for row in rows))
        self.assertTrue(all(row.native_execution_binding.value == "subs" for row in rows))

    def test_authored_null_native_value_survives_i004_i005(self):
        bundle = validated_binding_presence_bundle(
            "null-value",
            value_mode="null",
        )
        ir = compile_semantic_ir((bundle,))
        row = dict(ir.semantic_index)[noun_semantic_key()][0]
        self.assertTrue(row.native_execution_binding.value_present)
        self.assertIsNone(row.native_execution_binding.value)

    def test_absent_native_value_survives_i004_i005(self):
        bundle = validated_binding_presence_bundle(
            "absent-value",
            value_mode="absent",
        )
        ir = compile_semantic_ir((bundle,))
        row = dict(ir.semantic_index)[noun_semantic_key()][0]
        self.assertFalse(row.native_execution_binding.value_present)
        self.assertIsNone(row.native_execution_binding.value)


if __name__ == "__main__":
    unittest.main()
