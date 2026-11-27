from __future__ import annotations

import importlib.util
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ontotf.source_validation import SCHEMA_FILES  # noqa: E402

BUILD_AVAILABLE = importlib.util.find_spec("build") is not None


class SdistSchemaResourceTests(unittest.TestCase):
    @unittest.skipUnless(BUILD_AVAILABLE, "packaging regression requires the build test tool")
    def test_sdist_contains_all_canonical_structural_schemas(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dist = tmp_path / "dist"
            outside = tmp_path / "outside"
            dist.mkdir()
            outside.mkdir()

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--sdist",
                    "--outdir",
                    str(dist),
                    str(ROOT),
                ],
                check=True,
                cwd=outside,
            )
            sdists = list(dist.glob("*.tar.gz"))
            self.assertEqual(len(sdists), 1, sdists)

            with tarfile.open(sdists[0], "r:gz") as archive:
                names = set(archive.getnames())

            missing = []
            for filename in SCHEMA_FILES.values():
                suffix = f"/src/ontotf/schemas/{filename}"
                if not any(name.endswith(suffix) for name in names):
                    missing.append(filename)
            self.assertFalse(missing, f"missing sdist schema resources: {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
