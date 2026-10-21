"""F-030 phase 3 RED contract: consolidate Linux-only duplicate CI, not coverage."""
from __future__ import annotations

from pathlib import Path
import unittest

from ruamel.yaml import YAML


ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows"

RETIRED_LINUX_ONLY = (
    "f015-direct-validation-boundary.yml",
    "f016-custom-schema-recursion.yml",
    "f021-feature-id-ownership.yml",
    "f022-semantic-digest-json-boundary.yml",
    "f023-downstream-ownership-enforcement.yml",
    "f024-namespace-scan-failures.yml",
)

SAVED_TEST_SUITES = (
    "f006", "f009", "f015", "f016", "f019", "f020",
    "f021", "f022", "f023", "f024", "i001", "i002", "i004",
    "d004", "d006",
)

PRESERVED_PLATFORM_RUNNERS = (
    "f014-windows-exact-file-paths.yml",
    "f018-handle-bound-file-reads.yml",
    "f019-invalid-source-filesystem-paths.yml",
    "f020-invalid-schema-root-filesystem-paths.yml",
)

PRESERVED_INDEPENDENT_GATES = (
    "i008-exact-execution.yml",
    "i027b3-extrabiblical-source.yml",
    "i027c1-native-pos.yml",
)


class SharedFCoreConsolidation(unittest.TestCase):
    def test_six_duplicate_linux_workflows_retired(self):
        for filename in RETIRED_LINUX_ONLY:
            with self.subTest(filename=filename):
                self.assertFalse((CI / filename).exists())

    def test_original_tests_and_direct_checker_remain(self):
        for package in SAVED_TEST_SUITES:
            with self.subTest(package=package):
                suite = ROOT / "tests" / package
                self.assertTrue((suite / "__init__.py").is_file())
                self.assertTrue(tuple(suite.glob("test_*.py")))
        self.assertTrue((ROOT / "tests/packaging/test_schema_authority.py").is_file())
        self.assertTrue((ROOT / "scripts/check_f_series_ownership.py").is_file())

    def test_four_version_canonical_job_always_executes_ownership_checker(self):
        yaml = YAML(typ="safe")
        workflow = yaml.load((CI / "full-suite.yml").read_text(encoding="utf-8"))
        self.assertIsNone(workflow["on"]["pull_request"])
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        job = workflow["jobs"]["validate"]
        self.assertEqual(job["strategy"]["matrix"], {"python-version": ["3.12", "3.13", "3.14", "3.15"]})
        self.assertFalse(job["strategy"]["fail-fast"])
        self.assertNotIn("if", job)
        self.assertNotIn("continue-on-error", job)
        self.assertEqual(job["steps"][0]["with"]["ref"],
                         "${{ github.event.pull_request.head.sha || github.sha }}")
        command = "python scripts/check_f_series_ownership.py ."
        owning = [x for x in job["steps"] if command in x.get("run", "")]
        self.assertEqual(len(owning), 1)
        self.assertEqual(owning[0]["run"].strip(), command)
        self.assertNotIn("if", owning[0])
        self.assertNotIn("continue-on-error", owning[0])
        steps = "\n".join(s.get("run", "") for s in job["steps"])
        for required in (
            "python -m unittest discover -s tests -v",
            "python -m pytest tests/research -q",
            "python -m pytest tests/architecture -q",
            "python -m build --wheel --outdir dist",
            "python scripts/coverage/build_i026_work_queue.py --check",
        ):
            with self.subTest(required=required):
                self.assertIn(required, steps)

    def test_windows_and_source_gates_retained(self):
        for filename in PRESERVED_PLATFORM_RUNNERS:
            content = (CI / filename).read_text(encoding="utf-8")
            self.assertIn("windows-latest", content, filename)
            self.assertIn("pull_request:", content, filename)
        for filename in PRESERVED_INDEPENDENT_GATES:
            self.assertTrue((CI / filename).is_file(), filename)
        self.assertFalse((CI / "i033e3-protected-batch-review.yml").exists())
        for name in ("i027b3-extrabiblical-source.yml", "i027c1-native-pos.yml"):
            pinned = (CI / name).read_text(encoding="utf-8")
            self.assertIn("repository: ETCBC/", pinned)
            self.assertIn("persist-credentials: false", pinned)


if __name__ == "__main__":
    unittest.main()
