#!/usr/bin/env python3
"""Build a separate, pinned current P-004 queue; never rewrite I-026 history."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from tfont.coverage import (
    coverage_denominator_digest, load_coverage_manifest, validate_coverage_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
LEGACY_SCRIPT = ROOT / "scripts/coverage/build_i026_work_queue.py"
LEGACY_QUEUE = ROOT / "docs/research/data/generated/i026/p004-work-queue.json"
POLICY = ROOT / "docs/research/data/i026/p004-routing-policy.json"
SELECTOR = ROOT / "docs/research/data/i027d/p004-current-manifest-selection.json"
OUTPUT = ROOT / "docs/research/data/generated/i027d/p004-current-work-queue.json"
EXPECTED_COUNTS = {"C":380, "D":67, "E":153, "F":161, "G":39, "H":134}
EXPECTED_TOTALS = {"semantic_items":934, "technical_exclusions":15}
CONTROLLED_RELEASES = {
    "bhsa": {
        "manifest": "src/tfont/resources/coverage/p004-i027b1-bhsa-verb-v1/bhsa.json",
        "increments": 28, "reviewed": 35, "shared": 8, "native_only": 27,
    },
    "syriac": {
        "manifest": "src/tfont/resources/coverage/p004-i027b2-syriac-verb-v1/syriac.json",
        "increments": 1, "reviewed": 7, "shared": 7, "native_only": 0,
    },
    "extrabiblical": {
        "manifest": "src/tfont/resources/coverage/p004-i027b4-extrabiblical-verb-v1/extrabiblical.json",
        "increments": 1, "reviewed": 8, "shared": 8, "native_only": 0,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"expected JSON object: {path}")
    return value


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def _load_i026():
    spec = importlib.util.spec_from_file_location("i026_work_queue", LEGACY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load pinned historical I-026 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_historical_queue() -> dict[str, Any]:
    original = _load_i026().build_queue()
    if _load_i026().serialized(original) != LEGACY_QUEUE.read_text(encoding="utf-8"):
        raise ValueError("I-026 historical source queue changed; cannot publish current view")
    return original


def load_selection() -> dict[str, Any]:
    return load_json(SELECTOR)


def _expected_increment(corpus: str, item_id: str) -> dict[str, Any] | None:
    if corpus == "bhsa" and (
        item_id == "node_feature:vs"
        or (item_id.startswith('node_value:vs="') and item_id.endswith('"'))
    ):
        return {
            "assessments": ["native-only"],
            "capabilities": ["linguistic.morphology"],
            "common_target": False,
            "profiles": ["linguistic"],
            "source_ids": ["i027a:bhsa-vs-pinned-source-review"],
        }
    if item_id == 'node_value:sp="verb"' and corpus in CONTROLLED_RELEASES:
        return {
            "assessments": ["exact"],
            "capabilities": ["linguistic.part-of-speech"],
            "common_target": True,
            "profiles": ["linguistic"],
            "source_ids": [f"mapping:{corpus}:olia-verb"],
        }
    return None


def validate_successor(
    corpus: str,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> None:
    validate_coverage_manifest(baseline)
    validate_coverage_manifest(candidate)
    if candidate["corpus_id"] != corpus or baseline["corpus_id"] != corpus:
        raise ValueError(f"{corpus}: corpus identity drift")
    if coverage_denominator_digest(baseline) != coverage_denominator_digest(candidate):
        raise ValueError(f"{corpus}: semantic denominator digest drift")
    if baseline["denominator_digest"] != candidate["denominator_digest"]:
        raise ValueError(f"{corpus}: stored denominator digest drift")

    for field in baseline:
        if field in {"manifest_id", "semantic_items"}:
            continue
        if candidate.get(field) != baseline[field]:
            raise ValueError(f"{corpus}: historical {field} drift")
    if set(candidate) != set(baseline):
        raise ValueError(f"{corpus}: manifest schema/metadata drift")
    original = {row["item_id"]: row for row in baseline["semantic_items"]}
    successor = {row["item_id"]: row for row in candidate["semantic_items"]}
    if len(original) != len(baseline["semantic_items"]) or len(successor) != len(candidate["semantic_items"]):
        raise ValueError(f"{corpus}: duplicate semantic item")
    if set(original) != set(successor):
        raise ValueError(f"{corpus}: semantic identity set drift")

    upgrades: dict[str, dict[str, Any]] = {}
    for item_id in original:
        old = original[item_id]
        new = successor[item_id]
        if {key: value for key, value in old.items() if key != "accounting"} != {
            key: value for key, value in new.items() if key != "accounting"
        }:
            raise ValueError(f"{corpus}: semantic item definition drift: {item_id}")
        old_account, new_account = old["accounting"], new["accounting"]
        if old_account["research"] != new_account["research"]:
            raise ValueError(f"{corpus}: research authority drift: {item_id}")
        previous, current = old_account["production"], new_account["production"]
        if previous is not None and previous != current:
            raise ValueError(f"{corpus}: previously reviewed production changed: {item_id}")
        if previous is None and current is not None:
            approved = _expected_increment(corpus, item_id)
            if current != approved:
                raise ValueError(f"{corpus}: unsupported production mapping or source binding: {item_id}")
            upgrades[item_id] = current

    controls = CONTROLLED_RELEASES.get(corpus)
    if controls is not None:
        if len(upgrades) != controls["increments"]:
            raise ValueError(f"{corpus}: incomplete production improvement slice")
        if 'node_value:sp="verb"' not in upgrades:
            raise ValueError(f"{corpus}: missing exact OLiA Verb mapping")
    elif upgrades:
        raise ValueError(f"{corpus}: unplanned production upgrade")

    rows = [x["accounting"]["production"] for x in candidate["semantic_items"]]
    reviewed = sum(x is not None for x in rows)
    common = sum(x is not None and x["common_target"] for x in rows)
    native_only = sum(x is not None and "native-only" in x["assessments"] for x in rows)
    if controls is not None and (reviewed, common, native_only) != (
        controls["reviewed"], controls["shared"], controls["native_only"]
    ):
        raise ValueError(f"{corpus}: production coverage totals drift")


def _check_selection(selection: dict[str, Any], policy: dict[str, Any]) -> None:
    if (
        selection.get("schema_version") != 1
        or selection.get("selection_id") != "p004-current-v1"
        or selection.get("underlying_policy_id") != "p004-routing-v1"
        or selection.get("underlying_policy_path")
        != "docs/research/data/i026/p004-routing-policy.json"
        or policy.get("policy_id") != selection["underlying_policy_id"]
    ):
        raise ValueError("current queue selection identity drift")
    corpora = policy["corpus_order"]
    fields = (
        "selected_manifests", "selected_blob_shas", "baseline_blob_shas",
        "expected_production_by_corpus",
    )
    for field in fields:
        if type(selection.get(field)) is not dict or set(selection[field]) != set(corpora):
            raise ValueError(f"current queue selection invalid {field}")

    for corpus in corpora:
        selected = selection["selected_manifests"][corpus]
        source = policy["corpora"][corpus]["manifest"]
        current = CONTROLLED_RELEASES.get(corpus)
        if selected != (current["manifest"] if current else source):
            raise ValueError(f"{corpus}: unexpected current coverage release (stale/downgrade)")
        for key in ("selected_blob_shas", "baseline_blob_shas"):
            blob = selection[key][corpus]
            if type(blob) is not str or len(blob) != 40 or any(ch not in "0123456789abcdef" for ch in blob):
                raise ValueError(f"{corpus}: invalid selected git blob identity")


def build_current_queue(*, selection: dict[str, Any] | None = None) -> dict[str, Any]:
    i026 = _load_i026()
    policy = load_json(POLICY)
    historical = verify_historical_queue()
    selection = copy.deepcopy(selection if selection is not None else load_selection())
    _check_selection(selection, policy)

    current_policy = copy.deepcopy(policy)
    totals: dict[str, dict[str, int]] = {}
    for corpus in policy["corpus_order"]:
        original_path = ROOT / policy["corpora"][corpus]["manifest"]
        selected_path = ROOT / selection["selected_manifests"][corpus]
        if git_blob_sha(original_path) != selection["baseline_blob_shas"][corpus]:
            raise ValueError(f"{corpus}: baseline Git blob drift")
        if git_blob_sha(selected_path) != selection["selected_blob_shas"][corpus]:
            raise ValueError(f"{corpus}: selected Git blob drift")
        original = load_coverage_manifest(original_path)
        selected = load_coverage_manifest(selected_path)
        validate_successor(corpus, original, selected)
        prod = [item["accounting"]["production"] for item in selected["semantic_items"]]
        actual = {
            "reviewed_items": sum(x is not None for x in prod),
            "shared_target_items": sum(x is not None and x["common_target"] for x in prod),
            "native_only_items": sum(x is not None and "native-only" in x["assessments"] for x in prod),
        }
        if actual != selection["expected_production_by_corpus"][corpus]:
            raise ValueError(f"{corpus}: expected production counts drift")
        totals[corpus] = actual
        current_policy["corpora"][corpus]["manifest"] = selection["selected_manifests"][corpus]

    current = i026.build_queue(policy=current_policy)
    if current["counts"] != historical["counts"] or current["invariants"] != historical["invariants"]:
        raise ValueError("P-004 routing counts or primary ownership changed")
    if current["counts"]["aggregate_workstreams"] != EXPECTED_COUNTS:
        raise ValueError("P-004 seven-model workstream split drift")
    if current["counts"]["technical_exclusions"] != EXPECTED_TOTALS["technical_exclusions"]:
        raise ValueError("P-004 technical exclusion count drift")
    if len(current["semantic_rows"]) != EXPECTED_TOTALS["semantic_items"]:
        raise ValueError("P-004 semantic denominator drift")
    current["current_view"] = {
        "view_id": selection["selection_id"],
        "underlying_policy_id": selection["underlying_policy_id"],
        "selection_path": "docs/research/data/i027d/p004-current-manifest-selection.json",
        "production_by_corpus": totals,
    }
    return current


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    options = parser.parse_args()
    output = serialized(build_current_queue())
    if options.stdout:
        print(output, end="")
    elif options.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != output:
            raise SystemExit("I-027D versioned current P-004 queue missing or stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
