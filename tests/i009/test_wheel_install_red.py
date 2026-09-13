from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


@unittest.skipUnless(os.environ.get("I009_WHEEL_TEST") == "1", "isolated wheel gate runs only in dedicated CI job")
class I009WheelInstallTests(unittest.TestCase):
    def test_built_wheel_contains_and_loads_production_resources_outside_checkout(self):
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dist = root / "dist"
            target = root / "installed"
            outside = root / "outside"
            dist.mkdir()
            target.mkdir()
            outside.mkdir()

            subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)],
                cwd=repo,
                check=True,
            )
            wheels = tuple(dist.glob("*.whl"))
            self.assertEqual(len(wheels), 1)
            wheel = wheels[0]

            expected_entries = {
                "tfont/resources/profiles/bhsa/0.1.0/profile.json",
                "tfont/resources/profiles/bhsa/0.1.0/parent/expected-components.json",
                "tfont/resources/profiles/bhsa/0.1.0/mappings/noun.json",
                "tfont/resources/profiles/syriac/0.1.0/profile.json",
                "tfont/resources/profiles/extrabiblical/0.1.0/profile.json",
                "tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/lock.json",
                "tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/noun-evidence.json",
                "tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/olia.owl",
                "tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/LICENSE.data",
                "tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/ATTRIBUTION.txt",
            }
            with zipfile.ZipFile(wheel) as archive:
                names = set(archive.namelist())
            self.assertTrue(expected_entries <= names, f"missing wheel resources: {sorted(expected_entries - names)}")
            self.assertFalse(any(name.endswith(".tf") for name in names), "I-009 wheel must not bundle corpus TF payloads")
            self.assertFalse(any(name.endswith(".mql") or name.endswith(".mql.gz") for name in names), "I-009 wheel must not bundle corpus MQL payloads")

            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(target), str(wheel)],
                cwd=outside,
                check=True,
            )
            script = r'''
import json
import os
import sys

sys.path.insert(0, os.environ["I009_INSTALLED_TARGET"])
import tfont
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle

assert tfont.PRODUCTION_NOUN_CORPORA == ("bhsa", "syriac", "extrabiblical")
bundles = tfont.load_production_noun_bundles()
assert len(bundles) == 3
validated = tuple(validate_semantic_bundle(bundle) for bundle in bundles)
ir = compile_semantic_ir(validated)
print(json.dumps({"corpora": [row.key.corpus_id for row in ir.variants]}))
'''
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env["I009_INSTALLED_TARGET"] = str(target)
            result = subprocess.run(
                [sys.executable, "-I", "-c", script],
                cwd=outside,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout.strip())
            self.assertEqual(payload["corpora"], ["bhsa", "extrabiblical", "syriac"])


if __name__ == "__main__":
    unittest.main()
