"""Release-candidate acceptance: actual package version and truthful user guidance."""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class I013ReleaseCandidateTests(unittest.TestCase):
    def test_readme_describes_shipped_slice_without_stale_negations(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("OLiA", readme)
        self.assertIn("BHSA", readme)
        self.assertIn("Syriac", readme)
        self.assertIn("ExtraBiblical", readme)
        self.assertIn("execute_exact_semantic", readme)
        self.assertIn("load_production_noun_bundle", readme)
        self.assertNotIn("Compatibility evaluation, semantic IR/compiler and runtime resolution, and corpus-specific mappings are not yet shipped capabilities", readme)
        self.assertNotIn("does not compile semantic IR", readme)
        self.assertNotIn("remain later stages", readme)
        self.assertIn("https://github.com/alexsosn/ontoTF/issues", readme)
        self.assertNotIn("https://github.com/alexsosn/TFont/issues", readme)

    def test_first_success_uses_real_local_tf_and_observed_identity(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in (
            "BHSA_TF_DIR", "tf.fabric", "Fabric(", "TF.load(",
            "tf_payload_digest(", "parent_manifest_digest(",
            "LoadedComponentContext(", "LoadedCorpusContext(",
            "validate_semantic_bundle(", "compile_semantic_ir(",
            "SemanticResolveRequest(", "execute_exact_semantic(",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)
        self.assertNotIn("tests.i008._fixtures", readme)
        self.assertNotIn("FakeLoadedApi", readme)
        self.assertIn("not bundled", readme.lower())

    def test_release_notes_separate_actual_functionality_and_test_limitations(self):
        notes = ROOT / "docs" / "releases" / "v0.1.0.md"
        self.assertTrue(notes.is_file(), "versioned release notes are absent")
        text = notes.read_text(encoding="utf-8")
        for required in ("0.1.0", "Noun", "BHSA", "Syriac", "ExtraBiblical", "CC BY 3.0", "MIT", "already-loaded", "API doubles"):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
