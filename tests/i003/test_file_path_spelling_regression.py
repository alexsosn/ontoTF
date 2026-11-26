from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from ontotf.parent_identity import IdentityError, file_component_digest


class FilePathSpellingRegressionTests(unittest.TestCase):
    def assert_file_spelling_rejected(self, path: str) -> None:
        with self.assertRaises(IdentityError):
            file_component_digest(path)

    def test_exact_file_rejects_trailing_separator_and_dot_spellings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"exact bytes")

            expected = file_component_digest(path)
            self.assert_file_spelling_rejected(str(path) + os.sep)
            self.assert_file_spelling_rejected(str(path) + os.sep + ".")
            self.assertEqual(file_component_digest(path), expected)


if __name__ == "__main__":
    unittest.main()
