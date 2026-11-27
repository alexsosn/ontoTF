from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ontotf.source_validation import SCHEMA_FILES  # noqa: E402


class SchemaAuthorityTests(unittest.TestCase):
    def test_packaged_schema_tree_is_the_only_canonical_source_tree(self):
        self.assertFalse(
            (ROOT / "schemas").exists(),
            "repository-root schemas/ would duplicate the packaged canonical schema tree",
        )
        packaged = ROOT / "src" / "ontotf" / "schemas"
        self.assertEqual(
            {path.name for path in packaged.glob("*.json")},
            set(SCHEMA_FILES.values()),
        )


if __name__ == "__main__":
    unittest.main()
