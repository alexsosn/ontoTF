from __future__ import annotations

import re
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

F_DOC_RE = re.compile(r"^(F-[0-9]{3})-.*\.md$")
F_WORKFLOW_RE = re.compile(r"^f([0-9]{3})-.*\.ya?ml$")
F_TEST_RE = re.compile(r"^f([0-9]{3})$")
MARKDOWN_OWNER_RE = re.compile(r"^\*\*Issue:\*\* #([1-9][0-9]*)\s*$")
WORKFLOW_OWNER_RE = re.compile(r"^# Issue: #([1-9][0-9]*)\s*$")
SIDECAR_OWNER_RE = re.compile(r"^Issue: #([1-9][0-9]*)\n?$")

FROZEN_MISSING = {
    "docs/plans/F-012-file-hash-object-binding-plan.md": 80,
    "docs/plans/F-014-windows-exact-file-paths-plan.md": 84,
    "docs/plans/F-015-error-precedence-amendment.md": 87,
    ".github/workflows/f002-wheel-schema-resources.yml": 21,
    ".github/workflows/f006-deep-source-nesting.yml": 32,
    ".github/workflows/f007-ci-full-suite-dedup.yml": 34,
    ".github/workflows/f008-p001-design-scope.yml": 66,
    ".github/workflows/f009-deep-digest-nesting.yml": 69,
    ".github/workflows/f010-deep-directory-identity.yml": 71,
    ".github/workflows/f011-node24-actions.yml": 78,
    ".github/workflows/f012-file-hash-object-binding.yml": 80,
    ".github/workflows/f014-windows-exact-file-paths.yml": 84,
    ".github/workflows/f015-direct-validation-boundary.yml": 87,
    ".github/workflows/f016-custom-schema-recursion.yml": 88,
    ".github/workflows/f018-handle-bound-file-reads.yml": 90,
    ".github/workflows/f019-invalid-source-filesystem-paths.yml": 94,
    ".github/workflows/f020-invalid-schema-root-filesystem-paths.yml": 95,
    ".github/workflows/f021-feature-id-ownership.yml": 99,
    ".github/workflows/f022-semantic-digest-json-boundary.yml": 103,
    "tests/f006/issue-owner.txt": 32,
    "tests/f008/issue-owner.txt": 66,
    "tests/f009/issue-owner.txt": 69,
    "tests/f010/issue-owner.txt": 71,
    "tests/f012/issue-owner.txt": 80,
    "tests/f014/issue-owner.txt": 84,
    "tests/f015/issue-owner.txt": 87,
    "tests/f016/issue-owner.txt": 88,
    "tests/f018/issue-owner.txt": 90,
    "tests/f019/issue-owner.txt": 94,
    "tests/f020/issue-owner.txt": 95,
    "tests/f021/issue-owner.txt": 99,
    "tests/f022/issue-owner.txt": 103,
}


# These historical carrier paths were intentionally retired by F-030 / #291,
# with executable tests retained in tests/i002 and the unconditional full suite.
# Do not count deletion of a workflow as a missing owner declaration.
RETIRED_FOCUSED_WORKFLOWS = (
    ".github/workflows/f003-digest-projection-key-errors.yml",
    ".github/workflows/f004-source-bundle-diagnostic-paths.yml",
    ".github/workflows/f005-utf16-diagnostic-paths.yml",
    # F-030 phase 3: original regression modules remain in shared full suite.
    ".github/workflows/f015-direct-validation-boundary.yml",
    ".github/workflows/f016-custom-schema-recursion.yml",
    ".github/workflows/f021-feature-id-ownership.yml",
    ".github/workflows/f022-semantic-digest-json-boundary.yml",
    ".github/workflows/f023-downstream-ownership-enforcement.yml",
    ".github/workflows/f024-namespace-scan-failures.yml",
)

# These four paths were in the *original* frozen inventory. Their ownership
# remains historically true even when they no longer exist as CI workflows.
# Keep FROZEN_MISSING unchanged for audit; only the *active* expectation moves.
RETIRED_FROZEN_CARRIERS = {
    ".github/workflows/f015-direct-validation-boundary.yml": 87,
    ".github/workflows/f016-custom-schema-recursion.yml": 88,
    ".github/workflows/f021-feature-id-ownership.yml": 99,
    ".github/workflows/f022-semantic-digest-json-boundary.yml": 103,
}


def markdown_owners(text: str) -> tuple[list[int], list[tuple[int, str]]]:
    owners: list[int] = []
    malformed: list[tuple[int, str]] = []
    lines = text.splitlines()
    for line_no in range(2, min(len(lines), 12) + 1):
        line = lines[line_no - 1]
        if line.startswith("## "):
            break
        match = MARKDOWN_OWNER_RE.fullmatch(line)
        if match:
            owners.append(int(match.group(1)))
        elif line.lstrip().startswith("**Issue:**"):
            malformed.append((line_no, line))
    return owners, malformed


def workflow_owners(text: str) -> tuple[list[int], list[tuple[int, str]]]:
    owners: list[int] = []
    malformed: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines()[:12], start=1):
        match = WORKFLOW_OWNER_RE.fullmatch(line)
        if match:
            owners.append(int(match.group(1)))
        elif line.lstrip().startswith("# Issue:"):
            malformed.append((line_no, line))
    return owners, malformed


def sidecar_owner(text: str) -> int | None:
    match = SIDECAR_OWNER_RE.fullmatch(text)
    return int(match.group(1)) if match else None


def research_authority(root: Path) -> tuple[dict[str, int], list[str]]:
    groups: dict[str, set[int]] = defaultdict(set)
    errors: list[str] = []
    research_dir = root / "docs" / "research"
    for path in sorted(research_dir.glob("F-[0-9][0-9][0-9]-*.md")):
        if not path.is_file():
            continue
        match = F_DOC_RE.fullmatch(path.name)
        if match is None:
            continue
        owners, malformed = markdown_owners(path.read_text(encoding="utf-8"))
        rel = path.relative_to(root).as_posix()
        if malformed or len(owners) != 1:
            errors.append(
                f"invalid_research_owner: {rel}: owners={owners!r}: malformed={malformed!r}"
            )
            continue
        groups[match.group(1)].add(owners[0])

    authority: dict[str, int] = {}
    for feature, owners in sorted(groups.items()):
        if len(owners) != 1:
            errors.append(f"conflicting_research_owner: {feature}: {sorted(owners)!r}")
        else:
            authority[feature] = next(iter(owners))
    return authority, sorted(errors)


def relation_error(feature: str, owner: int, authority: dict[str, int], path: str) -> str | None:
    expected = authority.get(feature)
    if expected is None:
        return f"unknown_feature: {path}: {feature}"
    if owner != expected:
        return f"conflicting_owner: {path}: {feature}: expected #{expected}, found #{owner}"
    return None


def scan_downstream(
    root: Path, authority: dict[str, int]
) -> tuple[dict[str, int], list[str], list[str]]:
    missing: dict[str, int] = {}
    errors: list[str] = []
    matching: list[str] = []

    plans_dir = root / "docs" / "plans"
    for path in sorted(plans_dir.glob("F-[0-9][0-9][0-9]-*.md")):
        if not path.is_file():
            continue
        match = F_DOC_RE.fullmatch(path.name)
        if match is None:
            continue
        feature = match.group(1)
        rel = path.relative_to(root).as_posix()
        expected = authority.get(feature)
        if expected is None:
            errors.append(f"unknown_feature: {rel}: {feature}")
            continue
        owners, malformed = markdown_owners(path.read_text(encoding="utf-8"))
        if malformed:
            errors.append(f"malformed_plan_owner: {rel}: {malformed!r}")
        if len(owners) > 1:
            errors.append(f"duplicate_plan_owner: {rel}: {owners!r}")
        if malformed or len(owners) > 1:
            continue
        if not owners:
            missing[rel] = expected
            continue
        error = relation_error(feature, owners[0], authority, rel)
        if error:
            errors.append(error)
        else:
            matching.append(rel)

    workflows_dir = root / ".github" / "workflows"
    if workflows_dir.is_dir():
        for path in sorted(workflows_dir.iterdir()):
            if not path.is_file():
                continue
            match = F_WORKFLOW_RE.fullmatch(path.name)
            if match is None:
                continue
            feature = f"F-{match.group(1)}"
            rel = path.relative_to(root).as_posix()
            expected = authority.get(feature)
            if expected is None:
                errors.append(f"unknown_feature: {rel}: {feature}")
                continue
            owners, malformed = workflow_owners(path.read_text(encoding="utf-8"))
            if malformed:
                errors.append(f"malformed_workflow_owner: {rel}: {malformed!r}")
            if len(owners) > 1:
                errors.append(f"duplicate_workflow_owner: {rel}: {owners!r}")
            if malformed or len(owners) > 1:
                continue
            if not owners:
                missing[rel] = expected
                continue
            error = relation_error(feature, owners[0], authority, rel)
            if error:
                errors.append(error)
            else:
                matching.append(rel)

    tests_dir = root / "tests"
    if tests_dir.is_dir():
        for package in sorted(tests_dir.iterdir()):
            if not package.is_dir():
                continue
            match = F_TEST_RE.fullmatch(package.name)
            if match is None:
                continue
            feature = f"F-{match.group(1)}"
            sidecar = package / "issue-owner.txt"
            rel = sidecar.relative_to(root).as_posix()
            expected = authority.get(feature)
            if expected is None:
                errors.append(f"unknown_feature: {package.relative_to(root).as_posix()}: {feature}")
                continue
            if not sidecar.is_file():
                missing[rel] = expected
                continue
            owner = sidecar_owner(sidecar.read_text(encoding="utf-8"))
            if owner is None:
                errors.append(f"malformed_test_owner: {rel}")
                continue
            error = relation_error(feature, owner, authority, rel)
            if error:
                errors.append(error)
            else:
                matching.append(rel)

    return dict(sorted(missing.items())), sorted(errors), sorted(matching)


class DownstreamOwnershipParserControls(unittest.TestCase):
    def test_canonical_markdown_owner_is_bounded(self):
        text = "# F fixture\n**Issue:** #87\n\n## Body\n**Issue:** #999\n"
        self.assertEqual(markdown_owners(text), ([87], []))

    def test_malformed_and_duplicate_markdown_are_visible(self):
        text = "# F fixture\n **Issue:** #87\n**Issue:** #87\n**Issue:** #87\n"
        owners, malformed = markdown_owners(text)
        self.assertEqual(owners, [87, 87])
        self.assertEqual(malformed, [(2, " **Issue:** #87")])

    def test_canonical_workflow_owner_is_accepted(self):
        self.assertEqual(workflow_owners("# Issue: #87\nname: x\n"), ([87], []))

    def test_indented_and_duplicate_workflow_owners_are_visible(self):
        owners, malformed = workflow_owners(
            " # Issue: #87\n# Issue: #87\n# Issue: #87\nname: x\n"
        )
        self.assertEqual(owners, [87, 87])
        self.assertEqual(malformed, [(1, " # Issue: #87")])

    def test_workflow_owner_is_hard_bounded_to_line_12(self):
        text = "\n".join(["name: x", *("# filler" for _ in range(11)), "# Issue: #87"])
        self.assertEqual(workflow_owners(text), ([], []))

    def test_yml_and_yaml_names_are_in_namespace(self):
        for name in ("f015-x.yml", "f015-x.yaml"):
            with self.subTest(name=name):
                match = F_WORKFLOW_RE.fullmatch(name)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), "015")

    def test_sidecar_grammar_is_exact(self):
        self.assertEqual(sidecar_owner("Issue: #87\n"), 87)
        self.assertEqual(sidecar_owner("Issue: #87"), 87)
        for bad in (" Issue: #87\n", "Issue: #0\n", "Issue: #87\nextra\n", "# Issue: #87\n"):
            with self.subTest(bad=bad):
                self.assertIsNone(sidecar_owner(bad))

    def test_relation_distinguishes_conflict_and_unknown(self):
        authority = {"F-015": 87}
        self.assertEqual(
            relation_error("F-015", 90, authority, "artifact"),
            "conflicting_owner: artifact: F-015: expected #87, found #90",
        )
        self.assertEqual(
            relation_error("F-999", 90, authority, "artifact"),
            "unknown_feature: artifact: F-999",
        )

    def test_scan_results_are_deterministically_sorted(self):
        authority = {"F-900": 1, "F-901": 2}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "plans").mkdir(parents=True)
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "tests" / "f901").mkdir(parents=True)
            (root / "tests" / "f900").mkdir(parents=True)
            (root / "docs" / "plans" / "F-901-z.md").write_text("# x\n", encoding="utf-8")
            (root / "docs" / "plans" / "F-900-a.md").write_text("# x\n", encoding="utf-8")
            missing, errors, matching = scan_downstream(root, authority)
        self.assertEqual(list(missing), sorted(missing))
        self.assertEqual(errors, sorted(errors))
        self.assertEqual(matching, sorted(matching))


class RepositoryMigrationREDTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.authority, cls.authority_errors = research_authority(ROOT)
        cls.missing, cls.downstream_errors, cls.matching = scan_downstream(ROOT, cls.authority)

    def test_research_authority_is_valid(self):
        self.assertEqual(self.authority_errors, [])
        self.assertTrue(self.authority)

    def test_existing_explicit_downstream_claims_are_valid(self):
        self.assertEqual(self.downstream_errors, [])

    def test_plan_namespace_is_fully_accounted_for(self):
        actual_plans = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "docs" / "plans").glob("F-[0-9][0-9][0-9]-*.md")
            if path.is_file() and F_DOC_RE.fullmatch(path.name)
        }
        plan_matches = {
            path for path in self.matching if path.startswith("docs/plans/")
        }
        plan_missing = {
            path for path in self.missing if path.startswith("docs/plans/")
        }
        self.assertTrue(plan_matches.isdisjoint(plan_missing))
        self.assertEqual(plan_matches | plan_missing, actual_plans)

    def test_intentionally_retired_f_series_workflow_carriers(self):
        self.assertTrue(set(RETIRED_FROZEN_CARRIERS) <= set(RETIRED_FOCUSED_WORKFLOWS))
        for relative in RETIRED_FOCUSED_WORKFLOWS:
            with self.subTest(path=relative):
                self.assertFalse((ROOT / relative).exists())
                if relative in RETIRED_FROZEN_CARRIERS:
                    self.assertEqual(
                        FROZEN_MISSING[relative], RETIRED_FROZEN_CARRIERS[relative]
                    )
                else:
                    self.assertNotIn(relative, FROZEN_MISSING)

    def test_frozen_carriers_are_missing_or_matching(self):
        # Historical snapshot is immutable; retired CI owners are explicitly
        # tombstoned rather than silently erasing original ownership metadata.
        frozen = {
            path: owner for path, owner in sorted(FROZEN_MISSING.items())
            if path not in RETIRED_FOCUSED_WORKFLOWS
        }
        unexpected_missing = set(self.missing) - set(frozen)
        self.assertEqual(unexpected_missing, set())
        for path, owner in self.missing.items():
            self.assertEqual(owner, frozen[path], path)

        matching = set(self.matching)
        observed_frozen = set(self.missing) | (matching & set(frozen))
        self.assertEqual(observed_frozen, set(frozen))

    def test_migration_is_complete(self):
        self.assertEqual(self.missing, {})


if __name__ == "__main__":
    unittest.main()
