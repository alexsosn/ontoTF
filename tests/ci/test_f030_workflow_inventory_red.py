from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ci.inventory_workflows import (
    collect_workflow_inventory,
    validate_ownership,
    WorkflowOwnershipError,
)


class F030WorkflowInventoryRed(unittest.TestCase):
    def make_workflows(self, root: Path) -> None:
        directory = root / ".github/workflows"
        directory.mkdir(parents=True)
        (directory / "unit.yml").write_text(
            'name: Test\non: [pull_request]\njobs:\n  test:\n'
            '    runs-on: ubuntu-latest\n    steps:\n'
            '      - uses: actions/checkout@v5\n'
            '      - run: python -m unittest discover -s tests -v\n',
            encoding="utf-8",
        )
        (directory / "source.yml").write_text(
            'name: Verify source\non: [pull_request]\njobs:\n  source:\n'
            '    runs-on: ubuntu-latest\n    steps:\n'
            '      - uses: actions/checkout@v5\n'
            '        with:\n          repository: ETCBC/extrabiblical\n'
            '          ref: 9a56288e6777bad6328856acf055c780e65dd5d9\n'
            '      - run: python scripts/research/i027b3_extract_mql.py --verify-frozen evidence.json\n',
            encoding="utf-8",
        )

    def test_inventory_captures_unique_commands_and_pinned_download(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.make_workflows(root)
            records=collect_workflow_inventory(root)
            self.assertEqual(len(records),2)
            source=next(x for x in records if x["path"].endswith("source.yml"))
            self.assertTrue(any("--verify-frozen" in x["run"] for x in source["runs"]))
            self.assertTrue(any(
                a["repository"]=="ETCBC/extrabiblical"
                and a["ref"]=="9a56288e6777bad6328856acf055c780e65dd5d9"
                for a in source["external_checkouts"]
            ))

    def test_ownership_requires_every_workflow_and_unique_shell_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.make_workflows(root)
            records=collect_workflow_inventory(root)
            only_one={
                "schema_version":1,
                "workflows":{
                    ".github/workflows/unit.yml":{
                        "replacement_job":"release-regression",
                        "retained_run_commands":["python -m unittest discover -s tests -v"],
                        "retained_checkout_pins":[],
                    }
                }
            }
            with self.assertRaises(WorkflowOwnershipError):
                validate_ownership(records,only_one)
            only_one["workflows"][".github/workflows/source.yml"]={
                "replacement_job":"source-pins",
                "retained_run_commands":[],
                "retained_checkout_pins":[],
            }
            with self.assertRaises(WorkflowOwnershipError):
                validate_ownership(records,only_one)
            only_one["workflows"][".github/workflows/source.yml"]={
                "replacement_job":"source-pins",
                "retained_run_commands":[
                    "python scripts/research/i027b3_extract_mql.py --verify-frozen evidence.json"
                ],
                "retained_checkout_pins":[
                    "ETCBC/extrabiblical@9a56288e6777bad6328856acf055c780e65dd5d9"
                ],
            }
            validate_ownership(records,only_one)
            only_one["workflows"][".github/workflows/source.yml"]["retained_checkout_pins"]=[]
            with self.assertRaises(WorkflowOwnershipError):
                validate_ownership(records,only_one)

    def test_real_repository_keeps_source_integrity_commands_visible(self):
        root = Path(__file__).resolve().parents[2]
        inventory = {x["path"]: x for x in collect_workflow_inventory(root)}
        self.assertGreaterEqual(len(inventory), 79)
        original = inventory[".github/workflows/i027b3-extrabiblical-source.yml"]
        self.assertTrue(any(
            "--verify-frozen" in step["run"] for step in original["runs"]
        ))
        self.assertTrue(any(
            source["repository"] == "ETCBC/extrabiblical"
            for source in original["external_checkouts"]
        ))
        baseline = inventory[".github/workflows/full-suite.yml"]
        self.assertTrue(any(
            "unittest discover" in step["run"] for step in baseline["runs"]
        ))

    def test_inventory_fails_on_malformed_job_or_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.make_workflows(root)
            (root/".github/workflows/invalid.yml").write_text(
                "name: Invalid\non: [pull_request]\njobs:\n  unit: null\n",
                encoding="utf-8",
            )
            with self.assertRaises(WorkflowOwnershipError):
                collect_workflow_inventory(root)


if __name__ == "__main__":
    unittest.main()
