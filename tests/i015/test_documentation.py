from __future__ import annotations

import unittest
from pathlib import Path


class I015DocumentationTests(unittest.TestCase):
    def test_readme_distinguishes_published_release_from_development_noun_layer(self):
        readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
        required = (
            "Development source after v0.1.1",
            "load_production_linguistic_bundles()",
            "execute_exact_conjunction",
            "not part of the published v0.1.1 wheel",
            "ProperNoun",
            "Masculine",
            "Feminine",
            "Singular",
            "Plural",
            "Dual",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, readme)


if __name__ == "__main__":
    unittest.main()
