from __future__ import annotations

import unittest

from ontotf.semantic_ir import SemanticIRError, compile_semantic_ir


class I005SemanticIREdgeContractTests(unittest.TestCase):
    def test_empty_bundle_iterable_fails_closed(self):
        with self.assertRaises(SemanticIRError) as raised:
            compile_semantic_ir(())
        self.assertEqual(raised.exception.problem.category, "invalid_bundle_scope")


if __name__ == "__main__":
    unittest.main()
