from __future__ import annotations

import unittest

import ontotf
from tests.i008._fixtures import (
    FakeLoadedApi,
    compiled_executable_noun_ir,
    loaded_context,
    request,
)


class ExplodingIndex:
    def __index__(self):
        raise ValueError("hostile integer-like node")


class I008AdversarialRedTests(unittest.TestCase):
    def execute_one(self, api):
        ir = compiled_executable_noun_ir(("bhsa",))
        context = loaded_context(ontotf, ir, "bhsa", api)
        return ontotf.execute_exact_semantic(ir, request(ontotf, ("bhsa",)), (context,))

    def test_malformed_second_fall_result_is_loaded_api_failure(self):
        api = FakeLoadedApi(
            values={1: "subs"},
            node_types={1: "word"},
            fall_sequence=(("otype", "sp"), "sp"),
        )
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            self.execute_one(api)
        self.assertEqual(caught.exception.problem.category, "loaded_api_unavailable")
        self.assertEqual(api.F.sp.s_calls, 0)
        self.assertEqual(api.load_calls, 0)

    def test_arbitrary_index_protocol_failure_is_invalid_result_nodes(self):
        api = FakeLoadedApi(
            values={1: "subs"},
            node_types={1: "word"},
            selected=(ExplodingIndex(),),
        )
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            self.execute_one(api)
        self.assertEqual(caught.exception.problem.category, "invalid_result_nodes")
        self.assertEqual(api.load_calls, 0)


if __name__ == "__main__":
    unittest.main()
