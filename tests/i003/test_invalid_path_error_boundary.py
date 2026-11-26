from __future__ import annotations

import unittest

from ontotf.parent_identity import (
    IdentityError,
    directory_component_digest,
    file_component_digest,
    tf_payload_digest,
)


class InvalidFilesystemPathBoundaryTests(unittest.TestCase):
    def assert_filesystem_error(self, func) -> None:
        path = "component\0invalid"
        try:
            func(path)
        except Exception as exc:  # inspect the public boundary, including the pre-fix raw ValueError
            self.assertIsInstance(exc, IdentityError)
            problem = exc.problem
            self.assertEqual(problem.category, "filesystem_error")
            self.assertEqual(problem.path, path)
            return
        self.fail("embedded-NUL filesystem path unexpectedly succeeded")

    def test_file_component_rejects_embedded_nul_through_identity_error(self):
        self.assert_filesystem_error(file_component_digest)

    def test_directory_component_rejects_embedded_nul_through_identity_error(self):
        self.assert_filesystem_error(directory_component_digest)

    def test_tf_payload_rejects_embedded_nul_through_identity_error(self):
        self.assert_filesystem_error(tf_payload_digest)


if __name__ == "__main__":
    unittest.main()
