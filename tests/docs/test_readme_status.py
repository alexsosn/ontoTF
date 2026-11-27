from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"


class ReadmeStatusContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = README.read_text(encoding="utf-8")
        cls.lowered = cls.readme.lower()

    def test_bootstrap_and_old_validation_only_status_are_retired(self):
        for stale in (
            "first project phase is **research only**",
            "compatibility evaluation, semantic ir/compiler and runtime resolution, and corpus-specific mappings are not yet shipped capabilities",
            "compatibility evaluation, semantic ir/compiler, runtime resolution, and corpus-specific mapping releases remain later stages",
            "cross-artifact semantic validation, compatibility evaluation",
        ):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, self.lowered)

    def test_foundation_capabilities_are_still_described(self):
        for shipped in (
            "source and cross-artifact validation",
            "deterministic parent/component and semantic digests",
            "strict json/yaml source loading",
            "canonicalization",
            "parent identity for files",
        ):
            with self.subTest(shipped=shipped):
                self.assertIn(shipped, self.lowered)

    def test_shipped_exact_slice_and_public_execution_are_described(self):
        for shipped in (
            "olia noun", "bhsa", "syriac", "extrabiblical",
            "load_production_noun_bundle", "validate_semantic_bundle",
            "compile_semantic_ir", "execute_exact_semantic",
            "exact reviewed parent manifest", "fail closed",
        ):
            with self.subTest(shipped=shipped):
                self.assertIn(shipped, self.lowered)
        self.assertIn("mapping and projection", self.lowered)
        self.assertIn("reviews", self.lowered)

    def test_review_validation_is_not_misrepresented_as_automatic_scholarly_review(self):
        for overclaim in (
            "all semantic source bundles are reviewed",
            "every corpus version is compatible",
            "reviewed native record states",
        ):
            with self.subTest(overclaim=overclaim):
                self.assertNotIn(overclaim, self.lowered)
        self.assertIn("explicitly reviewed", self.lowered)

    def test_real_corpora_and_pypi_are_not_falsely_claimed(self):
        self.assertIn("api doubles", self.lowered)
        self.assertIn("not actual downloaded corpora", self.lowered)
        self.assertIn("not bundled", self.lowered)
        self.assertIn("no pypi publication of the renamed package is claimed", self.lowered)
        self.assertNotIn("tests.i008._fixtures", self.readme)
        self.assertNotIn("FakeLoadedApi", self.readme)

    def test_exact_only_drift_is_not_bypassed_by_forged_hash(self):
        self.assertIn("tf_payload_digest(tf_dir)", self.readme)
        self.assertIn("parent_manifest_digest(observed_manifest)", self.readme)
        self.assertIn("observed_component != expected_component", self.readme)
        self.assertIn("observed_parent != validated.expected_parent_manifest_digest", self.readme)
        self.assertIn("caller-supplied plan or public hash cannot authorize", self.lowered)

    def test_current_install_and_maintainer_links(self):
        self.assertIn("python -m pip install -e .", self.readme)
        self.assertIn("use documentation at that tag for its installation and API examples", self.readme)
        self.assertIn("https://github.com/alexsosn/ontoTF/releases/tag/v0.1.1", self.readme)
        self.assertIn("metadata-only", self.lowered)
        self.assertIn("https://github.com/alexsosn/ontoTF/issues", self.readme)
        self.assertTrue(self.readme.startswith("# ontoTF\n"))

    def test_historical_v010_release_notes_are_truthful(self):
        notes = ROOT / "docs" / "releases" / "v0.1.0.md"
        self.assertTrue(notes.is_file(), "published v0.1.0 release notes are absent")
        # Historical bytes are preserved at the release tag; this copy is current documentation.
        text = notes.read_text(encoding="utf-8")
        self.assertIn("https://github.com/alexsosn/ontoTF/releases/tag/v0.1.0", text)
        self.assertIn("actual filename", text)
        for marker in (
            "0.1.0",
            "Noun",
            "BHSA",
            "Syriac",
            "ExtraBiblical",
            "CC BY 3.0",
            "MIT",
            "API doubles",
        ):
            with self.subTest(v010_release_note_marker=marker):
                self.assertIn(marker, text)

    def test_historical_v011_release_notes_are_truthful(self):
        notes = ROOT / "docs" / "releases" / "v0.1.1.md"
        self.assertTrue(notes.is_file(), "published v0.1.1 release notes are absent")
        text = notes.read_text(encoding="utf-8")
        self.assertIn("https://github.com/alexsosn/ontoTF/releases/tag/v0.1.1", text)
        self.assertIn("actual filename", text)
        for marker in (
            "metadata-only",
            "MIT AND CC-BY-3.0",
            "BHSA",
            "Syriac",
            "ExtraBiblical",
            "pip install ontotf",
            "not",
            "PyPI",
        ):
            with self.subTest(release_note_marker=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
