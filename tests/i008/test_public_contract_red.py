from __future__ import annotations

import inspect
import unittest

import ontotf


class I008PublicContractRedTests(unittest.TestCase):
    def test_request_oriented_execution_surface_is_exported(self):
        required = (
            "LoadedComponentContext",
            "LoadedCorpusContext",
            "ExactCorpusExecution",
            "ExactExecutionResult",
            "ExactExecutionProblem",
            "ExactExecutionError",
            "execute_exact_semantic",
        )
        missing = tuple(name for name in required if not hasattr(ontotf, name))
        self.assertEqual(missing, (), f"missing I-008 public surface: {missing}")

    def test_public_executor_has_no_plan_authority_parameter(self):
        executor = getattr(ontotf, "execute_exact_semantic", None)
        if executor is None:
            self.skipTest("RED: public executor not implemented yet")
        parameters = inspect.signature(executor).parameters
        self.assertEqual(tuple(parameters), ("ir", "request", "contexts"))
        self.assertNotIn("plan", parameters)
        self.assertNotIn("prerequisites", parameters)


if __name__ == "__main__":
    unittest.main()
