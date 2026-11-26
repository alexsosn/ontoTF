from __future__ import annotations

import pathlib
import unittest

import ontotf


ROOT = pathlib.Path(__file__).resolve().parents[2]


class I007PublicContractRedTests(unittest.TestCase):
    def test_package_root_exports_runtime_evaluator_surface(self):
        expected = (
            "RUNTIME_EVALUATION_CONTRACT",
            "OBSERVATION_FINGERPRINT_ALGORITHM",
            "RUNTIME_REPORT_FINGERPRINT_ALGORITHM",
            "RuntimeEvaluationError",
            "RuntimeEvaluationReport",
            "RuntimeObservation",
            "LoadedTFObservation",
            "evaluate_runtime_prerequisites",
        )
        for name in expected:
            with self.subTest(name=name):
                self.assertTrue(hasattr(ontotf, name), name)
                self.assertIn(name, ontotf.__all__)

    def test_runtime_documentation_states_security_and_semantic_boundaries(self):
        path = ROOT / "docs" / "runtime-prerequisites.md"
        text = path.read_text(encoding="utf-8")
        required = (
            "verified-exact",
            "verified-compatible",
            "unverified",
            "incompatible",
            "closed-reviewed",
            "observed domain",
            "extent-interpretation",
            "already loaded",
            "does not authenticate",
            "legacy",
            "ontology bundle",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
