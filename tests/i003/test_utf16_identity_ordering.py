from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from ontotf.digests import canonical_json_bytes
from ontotf.parent_identity import (
    DIRECTORY_FILES_ALGORITHM,
    PARENT_COMPONENTS_ALGORITHM,
    directory_component_digest,
    parent_manifest_projection,
)


NON_BMP = "\U0001f600"
BMP_PRIVATE_USE = "\ue000"


class UTF16IdentityOrderingTests(unittest.TestCase):
    @staticmethod
    def sha256_bytes(payload: bytes) -> str:
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"

    def test_directory_file_records_use_utf16_code_unit_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payloads = {
                f"{BMP_PRIVATE_USE}.bin": b"private-use",
                f"{NON_BMP}.bin": b"non-bmp",
            }
            for name, payload in payloads.items():
                (root / name).write_bytes(payload)

            # UTF-16 code-unit order puts the non-BMP surrogate pair (D83D...)
            # before U+E000. Python code-point order does the opposite.
            expected_records = [
                {
                    "relative_logical_path": f"{NON_BMP}.bin",
                    "sha256": self.sha256_bytes(payloads[f"{NON_BMP}.bin"]),
                },
                {
                    "relative_logical_path": f"{BMP_PRIVATE_USE}.bin",
                    "sha256": self.sha256_bytes(payloads[f"{BMP_PRIVATE_USE}.bin"]),
                },
            ]
            expected = self.sha256_bytes(canonical_json_bytes(expected_records))
            self.assertEqual(directory_component_digest(root), expected)

    def test_parent_components_use_utf16_code_unit_order(self):
        manifest = {
            "algorithm": PARENT_COMPONENTS_ALGORITHM,
            "components": [
                {
                    "component_id": f"component:{BMP_PRIVATE_USE}",
                    "kind": "sidecar",
                    "identity_algorithm": DIRECTORY_FILES_ALGORITHM,
                    "content_digest": "sha256:private",
                },
                {
                    "component_id": f"component:{NON_BMP}",
                    "kind": "sidecar",
                    "identity_algorithm": DIRECTORY_FILES_ALGORITHM,
                    "content_digest": "sha256:non-bmp",
                },
            ],
        }

        projection = parent_manifest_projection(manifest)
        self.assertEqual(
            [component["component_id"] for component in projection["components"]],
            [f"component:{NON_BMP}", f"component:{BMP_PRIVATE_USE}"],
        )


if __name__ == "__main__":
    unittest.main()
