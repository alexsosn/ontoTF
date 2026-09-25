from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
LICENSE_FILES = (
    "LICENSE",
    f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/LICENSE.data",
    f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/ATTRIBUTION.txt",
)


class I014V011ReleaseContractTests(unittest.TestCase):
    def test_current_package_version_is_v011(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertRegex(text, r'(?m)^version\s*=\s*"0\.1\.1"\s*$')

    def test_pep639_mixed_license_contract_is_preserved(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertRegex(text, r'(?m)^license\s*=\s*"MIT AND CC-BY-3\.0"\s*$')
        self.assertNotIn('license = {file = "LICENSE"}', text)
        self.assertNotIn("License :: OSI Approved :: MIT License", text)
        for path in LICENSE_FILES:
            with self.subTest(path=path):
                self.assertIn(f'"{path}"', text)

    def test_readme_points_to_v011_metadata_only_patch(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/alexsosn/ontoTF/releases/tag/v0.1.1", text)
        self.assertIn("tfont-0.1.1-py3-none-any.whl", text)
        self.assertIn("metadata-only", text.lower())
        self.assertIn("pip install tfont", text)
        self.assertIn("not** a supported PyPI installation claim", text)
        self.assertIn("not bundled", text.lower())

    def test_v011_release_notes_define_patch_boundary(self):
        notes = ROOT / "docs" / "releases" / "v0.1.1.md"
        self.assertTrue(notes.is_file(), "v0.1.1 release notes are absent")
        text = notes.read_text(encoding="utf-8")
        for required in (
            "v0.1.1",
            "metadata-only",
            "MIT AND CC-BY-3.0",
            "v0.1.0",
            "BHSA",
            "Syriac",
            "ExtraBiblical",
            "GitHub",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertIn("not", text.lower())
        self.assertIn("PyPI", text)
        self.assertIn("corpus", text.lower())

    def test_profile_versions_remain_v010(self):
        for corpus in ("bhsa", "syriac", "extrabiblical"):
            path = (
                ROOT
                / "src"
                / "tfont"
                / "resources"
                / "profiles"
                / corpus
                / "0.1.0"
                / "profile.json"
            )
            with self.subTest(corpus=corpus):
                self.assertTrue(path.is_file())
                profile = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(profile["profile_version"], "0.1.0")


if __name__ == "__main__":
    unittest.main()
