#!/usr/bin/env python3
"""Inventory CI steps before migrating legacy GitHub Actions workflows.

This is an ownership guard, not the consolidated workflow itself. A check
cannot be removed until each previously executed run and external source pin
has a documented replacement. No tests are skipped on a heuristic basis.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


class WorkflowOwnershipError(ValueError):
    """Legacy CI check omitted or malformed during ownership migration."""


def _fail(message: str) -> None:
    raise WorkflowOwnershipError(message)


def _string(value: Any, name: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{name} must be a nonempty string")
    return value


def collect_workflow_inventory(root: Path) -> list[dict[str, Any]]:
    directory = root / ".github" / "workflows"
    if not directory.is_dir():
        _fail(f"missing workflow directory: {directory}")
    yaml = YAML(typ="safe")
    paths = sorted(
        [*directory.glob("*.yml"), *directory.glob("*.yaml")],
        key=lambda path: path.name,
    )
    if not paths:
        _fail("no GitHub Actions workflows found")
    inventory = []
    for path in paths:
        try:
            value = yaml.load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            _fail(f"{path}: workflow YAML invalid: {exc}")
        if type(value) is not dict or type(value.get("jobs")) is not dict:
            _fail(f"{path}: workflow jobs must be a mapping")
        runs: list[dict[str, str]] = []
        external: list[dict[str, str]] = []
        actions: list[dict[str, str]] = []
        called_workflows: list[dict[str, str]] = []
        for job_name, job in value["jobs"].items():
            if type(job_name) is not str or type(job) is not dict:
                _fail(f"{path}: malformed job {job_name!r}")
            if "uses" in job:
                called_workflows.append({
                    "job": job_name,
                    "uses": _string(job["uses"], "reusable job reference"),
                })
            # Reusable workflow jobs without 'steps' are valid Actions jobs.
            steps = job.get("steps", [])
            if type(steps) is not list:
                _fail(f"{path}: invalid step list for {job_name}")
            for step_index, step in enumerate(steps):
                if type(step) is not dict:
                    _fail(f"{path}: invalid step {job_name}/{step_index}")
                command = step.get("run")
                if command is not None:
                    runs.append({
                        "job": job_name,
                        "step": str(step_index),
                        "run": _string(command, "shell command").strip(),
                    })
                action = step.get("uses")
                if action is not None:
                    actions.append({
                        "job": job_name,
                        "step": str(step_index),
                        "uses": _string(action, "external/reusable action reference"),
                    })
                if type(action) is str and action.startswith("actions/checkout@"):
                    checkout = step.get("with", {})
                    if type(checkout) is not dict:
                        _fail(f"{path}: checkout inputs invalid")
                    repository, revision = checkout.get("repository"), checkout.get("ref")
                    if repository is not None:
                        external.append({
                            "repository": _string(repository, "external repository"),
                            "ref": _string(revision, "external checkout ref"),
                        })
        inventory.append({
            "path": path.relative_to(root).as_posix(),
            "workflow_name": str(value.get("name", path.name)),
            "runs": runs,
            "external_checkouts": external,
            "actions": actions,
            "called_workflows": called_workflows,
        })
    return inventory


def validate_ownership(
    inventory: list[dict[str, Any]], owners: dict[str, Any]
) -> None:
    if type(owners) is not dict or set(owners) != {"schema_version", "workflows"}:
        _fail("ownership schema fields invalid")
    if owners["schema_version"] != 1 or type(owners["workflows"]) is not dict:
        _fail("ownership schema version/workflows invalid")
    if type(inventory) is not list:
        _fail("inventory must be a list")
    expected_paths = [item["path"] for item in inventory]
    if len(set(expected_paths)) != len(expected_paths):
        _fail("duplicate workflow path")
    actual_paths = set(owners["workflows"])
    if set(expected_paths) != actual_paths:
        _fail(
            f"workflow ownership gap: missing={sorted(set(expected_paths)-actual_paths)} "
            f"unrecognized={sorted(actual_paths-set(expected_paths))}"
        )
    for workflow in inventory:
        path = workflow["path"]
        owner = owners["workflows"][path]
        if type(owner) is not dict or set(owner) != {
            "replacement_job", "retained_run_commands", "retained_checkout_pins",
            "retained_actions", "retained_called_workflows"
        }:
            _fail(f"{path}: incomplete owner contract")
        _string(owner["replacement_job"], "replacement job")
        commands = owner["retained_run_commands"]
        pins = owner["retained_checkout_pins"]
        used_actions = owner["retained_actions"]
        called = owner["retained_called_workflows"]
        if (
            type(commands) is not list
            or any(type(s) is not str for s in commands)
            or type(pins) is not list
            or any(type(s) is not str for s in pins)
            or type(used_actions) is not list
            or any(type(s) is not str for s in used_actions)
            or type(called) is not list
            or any(type(s) is not str for s in called)
        ):
            _fail(f"{path}: invalid command/pin ownership lists")
        expected_commands = {run["run"] for run in workflow["runs"]}
        expected_pins = {
            x["repository"] + "@" + x["ref"]
            for x in workflow["external_checkouts"]
        }
        if set(commands) != expected_commands or len(commands) != len(set(commands)):
            _fail(f"{path}: missing, extra, or duplicate shell command ownership")
        if set(pins) != expected_pins or len(pins) != len(set(pins)):
            _fail(f"{path}: missing, extra, or duplicate source pin ownership")
        expected_actions = {item["uses"] for item in workflow["actions"]}
        expected_called = {item["uses"] for item in workflow["called_workflows"]}
        if set(used_actions) != expected_actions or len(used_actions) != len(set(used_actions)):
            _fail(f"{path}: missing, extra, or duplicate GitHub Action owner")
        if set(called) != expected_called or len(called) != len(set(called)):
            _fail(f"{path}: missing, extra, or duplicate reusable workflow owner")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--ownership", type=Path)
    args = parser.parse_args()
    inventory = collect_workflow_inventory(args.root)
    if args.ownership is not None:
        validate_ownership(inventory, json.loads(args.ownership.read_text(encoding="utf-8")))
    print(json.dumps({"count": len(inventory), "workflows": inventory}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
