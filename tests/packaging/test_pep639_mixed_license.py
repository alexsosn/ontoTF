from __future__ import annotations

import email.policy
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
LICENSE_FILES = (
    "LICENSE",
    f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/LICENSE.data",
    f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/ATTRIBUTION.txt",
)
PACKAGE_OLIA_PREFIX = f"tfont/resources/ontologies/olia/{OLIA_REVISION}"
LEGACY_CLASSIFIER = "License :: OSI Approved :: MIT License"


class Pep639MetadataContractTests(unittest.TestCase):
    def test_pyproject_uses_reviewed_pep639_contract(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertRegex(text, r'(?m)^requires\s*=\s*\["setuptools>=77\.0\.3",\s*"wheel"\]\s*$')
        self.assertRegex(text, r'(?m)^license\s*=\s*"MIT AND CC-BY-3\.0"\s*$')
        self.assertNotIn('license = {file = "LICENSE"}', text)
        self.assertNotIn(LEGACY_CLASSIFIER, text)

        match = re.search(r'(?ms)^license-files\s*=\s*\[(.*?)^\]\s*$', text)
        self.assertIsNotNone(match, "project.license-files is absent")
        license_block = match.group(1)
        for path in LICENSE_FILES:
            with self.subTest(path=path):
                self.assertIn(f'"{path}"', license_block)


@unittest.skipUnless(
    os.environ.get("I157_PACKAGING_TEST") == "1",
    "PEP 639 archive gate runs only in dedicated CI",
)
class Pep639BuiltDistributionTests(unittest.TestCase):
    def test_wheel_and_sdist_preserve_mixed_license_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            tmp = Path(temporary)
            dist = tmp / "dist"
            outside = tmp / "outside"
            target = tmp / "installed"
            dist.mkdir()
            outside.mkdir()
            target.mkdir()

            build = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--sdist",
                    "--outdir",
                    str(dist),
                    str(ROOT),
                ],
                cwd=outside,
                check=False,
                capture_output=True,
                text=True,
            )
            combined_output = build.stdout + "\n" + build.stderr
            self.assertEqual(build.returncode, 0, combined_output)

            for warning_fragment in (
                "project.license as a TOML table is deprecated",
                "License classifiers are deprecated",
            ):
                with self.subTest(warning_fragment=warning_fragment):
                    self.assertNotIn(warning_fragment, combined_output)

            wheels = tuple(dist.glob("*.whl"))
            sdists = tuple(dist.glob("*.tar.gz"))
            self.assertEqual(len(wheels), 1, wheels)
            self.assertEqual(len(sdists), 1, sdists)

            self._assert_wheel(wheels[0])
            self._assert_sdist(sdists[0])
            self._assert_clean_install_resource_access(wheels[0], target, outside)

    def _assert_metadata(self, metadata_bytes: bytes, source: str):
        message = BytesParser(policy=email.policy.default).parsebytes(metadata_bytes)
        self.assertEqual(message.get("Version"), "0.1.0", source)
        self.assertEqual(
            message.get("License-Expression"),
            "MIT AND CC-BY-3.0",
            source,
        )
        self.assertEqual(set(message.get_all("License-File", [])), set(LICENSE_FILES), source)
        self.assertIsNone(message.get("License"), source)
        self.assertNotIn(LEGACY_CLASSIFIER, message.get_all("Classifier", []), source)

    def _assert_wheel(self, wheel: Path):
        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
            metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
            self.assertEqual(len(metadata_names), 1, metadata_names)
            metadata_name = metadata_names[0]
            self._assert_metadata(archive.read(metadata_name), "wheel METADATA")
            dist_info = metadata_name.rsplit("/", 1)[0]

            for path in LICENSE_FILES:
                archive_path = f"{dist_info}/licenses/{path}"
                with self.subTest(archive_path=archive_path):
                    self.assertIn(archive_path, names)
                    self.assertEqual(archive.read(archive_path), (ROOT / path).read_bytes())

            package_resource_paths = {
                f"{PACKAGE_OLIA_PREFIX}/LICENSE.data":
                    ROOT / f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/LICENSE.data",
                f"{PACKAGE_OLIA_PREFIX}/ATTRIBUTION.txt":
                    ROOT / f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/ATTRIBUTION.txt",
                f"{PACKAGE_OLIA_PREFIX}/olia.owl":
                    ROOT / f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/olia.owl",
            }
            for archive_path, source_path in package_resource_paths.items():
                with self.subTest(package_resource=archive_path):
                    self.assertIn(archive_path, names)
                    self.assertEqual(archive.read(archive_path), source_path.read_bytes())

            self.assertFalse(any(name.endswith(".tf") for name in names))
            self.assertFalse(any(name.endswith(".mql") or name.endswith(".mql.gz") for name in names))

    def _assert_sdist(self, sdist: Path):
        with tarfile.open(sdist, "r:gz") as archive:
            names = set(archive.getnames())
            pkg_info_names = [
                name
                for name in names
                if name.endswith("/PKG-INFO") and name.count("/") == 1
            ]
            self.assertEqual(len(pkg_info_names), 1, pkg_info_names)
            pkg_info_name = pkg_info_names[0]
            member = archive.extractfile(pkg_info_name)
            self.assertIsNotNone(member)
            self._assert_metadata(member.read(), "sdist PKG-INFO")
            root_name = pkg_info_name.split("/", 1)[0]

            for path in LICENSE_FILES:
                archive_path = f"{root_name}/{path}"
                with self.subTest(archive_path=archive_path):
                    self.assertIn(archive_path, names)
                    member = archive.extractfile(archive_path)
                    self.assertIsNotNone(member)
                    self.assertEqual(member.read(), (ROOT / path).read_bytes())

            self.assertFalse(any(name.endswith(".tf") for name in names))
            self.assertFalse(any(name.endswith(".mql") or name.endswith(".mql.gz") for name in names))

    def _assert_clean_install_resource_access(self, wheel: Path, target: Path, outside: Path):
        install = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--target",
                str(target),
                str(wheel),
            ],
            cwd=outside,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(install.returncode, 0, install.stdout + "\n" + install.stderr)

        expected = {}
        for name in ("LICENSE.data", "ATTRIBUTION.txt"):
            source = ROOT / f"src/tfont/resources/ontologies/olia/{OLIA_REVISION}/{name}"
            expected[name] = hashlib.sha256(source.read_bytes()).hexdigest()

        script = r"""
import hashlib
import importlib.resources
import json
import os
import sys

target = os.environ["I157_INSTALLED_TARGET"]
sys.path.insert(0, target)

import tfont

root = importlib.resources.files("tfont")
base = root.joinpath("resources", "ontologies", "olia", os.environ["I157_OLIA_REVISION"])
payload = {}
for name in ("LICENSE.data", "ATTRIBUTION.txt"):
    payload[name] = hashlib.sha256(base.joinpath(name).read_bytes()).hexdigest()
payload["package_file"] = str(tfont.__file__)
print(json.dumps(payload, sort_keys=True))
"""
        env = os.environ.copy()
        env["I157_INSTALLED_TARGET"] = str(target)
        env["I157_OLIA_REVISION"] = OLIA_REVISION
        result = subprocess.run(
            [sys.executable, "-I", "-c", script],
            cwd=outside,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertTrue(Path(payload.pop("package_file")).resolve().is_relative_to(target.resolve()))
        self.assertEqual(payload, expected)


if __name__ == "__main__":
    unittest.main()
