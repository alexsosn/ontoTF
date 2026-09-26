from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
FULL_COMMAND = "python -m unittest discover -s tests -v"
EXACT_HEAD = "github.event.pull_request.head.sha || github.sha"
SOURCE_REPOSITORY = "github.event.pull_request.head.repo.full_name || github.repository"
SOURCE_BRANCH = "github.event.pull_request.head.ref || github.ref_name"


class FullSuiteWorkflowContractTests(unittest.TestCase):
    def workflow_texts(self) -> dict[str, str]:
        return {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(WORKFLOW_DIR.glob("*.yml"))
        }

    def test_exactly_one_workflow_owns_full_repository_command(self):
        texts = self.workflow_texts()
        owners = sorted(name for name, text in texts.items() if FULL_COMMAND in text)
        self.assertEqual(owners, ["full-suite.yml"])
        self.assertEqual(texts["full-suite.yml"].count(FULL_COMMAND), 1)

    def test_authoritative_workflow_preserves_cross_version_and_trigger_contract(self):
        text = (WORKFLOW_DIR / "full-suite.yml").read_text(encoding="utf-8")
        required_tokens = (
            "push:",
            "pull_request:",
            "workflow_dispatch:",
            "pyproject.toml",
            '"src/**"',
            '"tests/**"',
            '".github/workflows/**"',
            'python-version: ["3.10", "3.12"]',
            "fail-fast: false",
            SOURCE_REPOSITORY,
            SOURCE_BRANCH,
            EXACT_HEAD,
            "cancel-in-progress: true",
            "python -m pip install build",
            FULL_COMMAND,
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_obsolete_i013_candidate_is_retired_with_release_guards_preserved(self):
        texts = self.workflow_texts()
        with self.subTest("legacy candidate absent"):
            self.assertNotIn("i013-release-candidate.yml", texts)

        for suite in ("i013", "i009"):
            with self.subTest(test_suite=suite):
                self.assertTrue(
                    any((ROOT / "tests" / suite).glob("test_*.py")),
                    f"tests/{suite} regressions must remain present",
                )

        with self.subTest("historical v0.1.0 guard"):
            self.assertIn("i013-release.yml", texts)
            historical = texts["i013-release.yml"]
            self.assertNotIn("pull_request:", historical)
            self.assertIn("- main", historical)
            self.assertIn("'docs/releases/v0.1.0.md'", historical)

        with self.subTest("current v0.1.1 guard"):
            self.assertIn("i014-v011-release.yml", texts)


    def test_redundant_d001_readme_workflow_is_retired_with_d003_coverage_preserved(self):
        texts = self.workflow_texts()
        with self.subTest("D-001 absent"):
            self.assertNotIn("d001-readme-status.yml", texts)

        with self.subTest("D-003 present"):
            self.assertIn("d003-readme-i004-status.yml", texts)
            d003 = texts["d003-readme-i004-status.yml"]

        with self.subTest("README docs test preserved"):
            self.assertTrue((ROOT / "tests" / "docs" / "test_readme_status.py").is_file())

        required_tokens = (
            "pull_request:",
            "workflow_dispatch:",
            "README.md",
            "tests/docs/**",
            EXACT_HEAD,
            "python-version:",
            "3.10",
            "3.12",
            "python -m unittest discover -s tests/docs -v",
        )
        for token in required_tokens:
            with self.subTest(d003_token=token):
                self.assertIn(token, d003)


    def test_focused_f007_contract_checks_exact_source_head(self):
        text = (WORKFLOW_DIR / "f007-ci-full-suite-dedup.yml").read_text(encoding="utf-8")
        self.assertIn(EXACT_HEAD, text)
        self.assertIn("tests.ci.test_full_suite_workflow_contract", text)

    def test_f006_keeps_its_cross_version_focused_gate(self):
        text = (WORKFLOW_DIR / "f006-deep-source-nesting.yml").read_text(encoding="utf-8")
        required_tokens = (
            "python-version:",
            "3.10",
            "3.12",
            EXACT_HEAD,
            "python -m pip install build",
            "python -m unittest discover -s tests/f006 -v",
            "python -m unittest discover -s tests/i001 -v",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_f009_keeps_its_cross_version_focused_gate(self):
        text = (WORKFLOW_DIR / "f009-deep-digest-nesting.yml").read_text(encoding="utf-8")
        required_tokens = (
            "python-version:",
            "3.10",
            "3.12",
            EXACT_HEAD,
            "python -m pip install build",
            "python -m unittest discover -s tests/f009 -v",
            "python -m unittest discover -s tests/i002 -v",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_p002_keeps_its_cross_version_focused_gate(self):
        text = (WORKFLOW_DIR / "p002-i004-source-contract.yml").read_text(encoding="utf-8")
        required_tokens = (
            "python-version:",
            "3.10",
            "3.12",
            "python -m pip install -e . build",
            "python -m unittest discover -s tests/p002 -v",
            "python -m unittest discover -s tests/i001 -v",
            "python -m unittest discover -s tests/i002 -v",
            "python -m unittest tests.packaging.test_wheel_schema_resources -v",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_focused_workflows_keep_their_distinct_contracts(self):
        texts = self.workflow_texts()
        required_by_workflow = {
            "d001-readme-status.yml": ("tests.docs.test_readme_status",),
            "f002-wheel-schema-resources.yml": (
                "tests.packaging.test_wheel_schema_resources",
                "discover -s tests/i001",
            ),
            "f003-digest-projection-key-errors.yml": (
                "tests.i002.test_projection_key_error_boundary",
                "discover -s tests/i002",
            ),
            "f004-source-bundle-diagnostic-paths.yml": (
                "tests.i002.test_source_bundle_diagnostic_paths",
                "discover -s tests/i002",
            ),
            "f005-utf16-diagnostic-paths.yml": (
                "tests.i002.test_utf16_diagnostic_paths",
                "discover -s tests/i002",
            ),
            "f006-deep-source-nesting.yml": (
                "discover -s tests/f006",
                "discover -s tests/i001",
            ),
            "f008-p001-design-scope.yml": (
                "discover -s tests/f008",
                "tests/plans/test_p001_plan.py",
            ),
            "f009-deep-digest-nesting.yml": (
                "discover -s tests/f009",
                "discover -s tests/i002",
            ),
            "i001-validation.yml": ("discover -s tests/i001",),
            "i002-validation.yml": ("discover -s tests/i002",),
            "i003-validation.yml": ("discover -s tests/i003",),
            "p002-i004-source-contract.yml": (
                "discover -s tests/p002",
                "discover -s tests/i001",
                "discover -s tests/i002",
                "tests.packaging.test_wheel_schema_resources",
            ),
        }
        for workflow, tokens in required_by_workflow.items():
            if workflow not in texts:
                continue
            for token in tokens:
                with self.subTest(workflow=workflow, token=token):
                    self.assertIn(token, texts[workflow])


if __name__ == "__main__":
    unittest.main()
