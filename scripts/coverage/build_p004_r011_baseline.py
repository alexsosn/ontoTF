#!/usr/bin/env python3
"""Build the immutable P-004 / R-011 coverage-accounting baseline.

This is repository/release tooling, not a corpus downloader. It consumes only
committed R-005/R-011 evidence and current reviewed I-015 production mappings.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tfont.coverage import (  # noqa: E402
    COVERAGE_ASSESSMENTS,
    P004_R011_BASELINE_CORPORA,
    coverage_denominator_digest,
    validate_coverage_manifest,
)
from tfont.digests import canonical_json_bytes  # noqa: E402

PILOTS = ROOT / "docs/research/data/r-011/pilots.json"
OVERRIDES = ROOT / "docs/research/data/r-011/mapping-overrides.json"
RAW_POLICY = ROOT / "docs/research/data/r-011/raw-schema-policy.json"
OUTPUT = ROOT / "src/tfont/resources/coverage/p004-r011-baseline-v1"

TARGET_REVISIONS = {
    "bhsa": "4db00e2157915495e1a4d3d57e41223df24775da",
    "cuc": "ad69400f5446e1c8217af01659c7c10ab00c015b",
    "syriac": "bb0eaa7e21b020a26b7566d2e495da9b1f84a919",
    "extrabiblical": "9a56288e6777bad6328856acf055c780e65dd5d9",
    "pseudepigrapha": "7c4b757bb543a110ae9a252d1281835859136852",
    "oracc": "85d2f131202882d40b05b65bfb4c83e8b1238426",
    "tlhdig": "bc4a206690c1856d3cfde8b291f626c45a712640",
}

PRODUCTION_MAPPING_FILES = {
    corpus: (
        ROOT / f"src/tfont/resources/profiles/{corpus}/0.2.0/mappings/noun.json",
        ROOT / f"src/tfont/resources/profiles/{corpus}/0.2.0/mappings/noun-morphology.json",
    )
    for corpus in ("bhsa", "syriac", "extrabiblical")
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"expected JSON object: {path}")
    return value


def apply_overrides(
    pilots: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = {
        row["id"]: copy.deepcopy(row)
        for row in pilots["mappings"]
    }
    for mapping_id in overrides.get("exclude_mapping_ids", []):
        if mapping_id not in rows:
            raise ValueError(f"override excludes unknown mapping: {mapping_id}")
        del rows[mapping_id]
    for mapping_id, patch in overrides.get("mapping_overrides", {}).items():
        if mapping_id not in rows:
            raise ValueError(f"override references unknown mapping: {mapping_id}")
        rows[mapping_id].update(copy.deepcopy(patch))
    return rows


def value_item_id(feature: str, value: Any) -> str:
    encoded = canonical_json_bytes(value).decode("utf-8")
    return f"node_value:{feature}={encoded}"


def item_kind(item_id: str) -> str:
    prefix = item_id.split(":", 1)[0]
    allowed = {
        "node_type",
        "node_feature",
        "node_value",
        "edge_feature",
        "edge_value",
        "external_reference",
        "assertion_shape",
    }
    if prefix not in allowed:
        raise ValueError(f"unsupported coverage item identity: {item_id}")
    return prefix


def denominator_items(
    corpus_id: str,
    corpus_meta: dict[str, Any],
    corpus_policy: dict[str, Any],
) -> tuple[set[str], dict[str, set[str]], str, str]:
    inventory_rel = corpus_meta.get("inventory")
    value_families: dict[str, set[str]] = {}

    if inventory_rel:
        inventory_path = ROOT / inventory_rel
        inventory = load_json(inventory_path)
        available = {
            *(f"node_type:{name}" for name in inventory.get("node_types", {})),
            *(f"node_feature:{name}" for name in inventory.get("node_features", {})),
            *(f"edge_feature:{name}" for name in inventory.get("edge_features", {})),
        }
        for feature in corpus_policy.get("bounded_features", []):
            feature_row = inventory.get("node_features", {}).get(feature)
            if not isinstance(feature_row, dict):
                raise ValueError(f"{corpus_id}: bounded feature absent: {feature}")
            values = feature_row.get("observed_values")
            if not isinstance(values, list) or not values:
                raise ValueError(
                    f"{corpus_id}: bounded feature has no explicit observed values: {feature}"
                )
            family = {value_item_id(feature, value) for value in values}
            value_families[feature] = family
            available.update(family)
        return (
            available,
            value_families,
            "machine-exhaustive",
            inventory_rel,
        )

    manual = corpus_policy.get("manual_items", [])
    if not isinstance(manual, list) or not manual:
        raise ValueError(f"{corpus_id}: curated denominator is empty")
    return (
        set(manual),
        value_families,
        "bounded-curated",
        "docs/research/data/r-011/raw-schema-policy.json",
    )


def research_accounting(
    corpus_id: str,
    corpus_policy: dict[str, Any],
    rows: dict[str, dict[str, Any]],
    value_families: dict[str, set[str]],
    available: set[str],
) -> dict[str, dict[str, Any]]:
    refs: dict[str, set[str]] = {}
    for mapping_id, values in corpus_policy.get("mapping_refs", {}).items():
        refs[mapping_id] = set(values)
    for mapping_id, families in corpus_policy.get("mapping_value_families", {}).items():
        refs.setdefault(mapping_id, set())
        for family in families:
            if family not in value_families:
                raise ValueError(
                    f"{corpus_id}: unbounded research value family requested: {family}"
                )
            refs[mapping_id].update(value_families[family])

    by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mapping_id, item_ids in refs.items():
        row = rows.get(mapping_id)
        if row is None:
            raise ValueError(f"{corpus_id}: raw policy references unknown effective mapping: {mapping_id}")
        if row["corpus"] != corpus_id:
            raise ValueError(f"{corpus_id}: mapping belongs to {row['corpus']}: {mapping_id}")
        missing = item_ids - available
        if missing:
            raise ValueError(
                f"{corpus_id}: research refs absent from denominator: {sorted(missing)}"
            )
        for item_id in item_ids:
            by_item[item_id].append(row)

    result: dict[str, dict[str, Any]] = {}
    for item_id, mapped_rows in by_item.items():
        assessments = sorted({row["assessment"] for row in mapped_rows})
        unknown = set(assessments) - COVERAGE_ASSESSMENTS
        if unknown:
            raise ValueError(f"{corpus_id}: unknown research assessment: {sorted(unknown)}")
        result[item_id] = {
            "assessments": assessments,
            "common_target": any(row.get("target") is not None for row in mapped_rows),
            "source_ids": sorted({row["id"] for row in mapped_rows}),
        }
    return result


def _binding_items(binding: dict[str, Any]) -> list[str]:
    shape = binding.get("execution_shape")
    feature = binding.get("feature")
    if shape == "value-predicate":
        return [value_item_id(feature, binding["value"])]
    if shape == "value-set-predicate":
        return [value_item_id(feature, value) for value in binding["values"]]
    raise ValueError(f"I-016 production bridge does not support binding shape: {shape}")


def production_accounting(
    corpus_id: str,
    available: set[str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    paths = PRODUCTION_MAPPING_FILES.get(corpus_id)
    if paths is None:
        return {}, []

    inside: dict[str, dict[str, set[str] | bool]] = {}
    outside: dict[str, dict[str, set[str] | bool]] = {}

    for path in paths:
        data = load_json(path)
        for mapping in data["mappings"]:
            if mapping.get("review", {}).get("status") != "reviewed":
                continue
            for projection in mapping.get("projections", []):
                if projection.get("review", {}).get("status") != "reviewed":
                    continue
                assessment = projection.get("assessment")
                if assessment != "exact":
                    raise ValueError(
                        f"{corpus_id}: I-016 bridge expected exact production mapping: "
                        f"{mapping['mapping_id']}={assessment}"
                    )
                for item_id in _binding_items(projection["native_execution_binding"]):
                    bucket = inside if item_id in available else outside
                    row = bucket.setdefault(
                        item_id,
                        {
                            "assessments": set(),
                            "source_ids": set(),
                            "profiles": set(),
                            "capabilities": set(),
                            "common_target": False,
                        },
                    )
                    row["assessments"].add(assessment)  # type: ignore[union-attr]
                    row["source_ids"].add(mapping["mapping_id"])  # type: ignore[union-attr]
                    row["profiles"].update(mapping.get("profiles", []))  # type: ignore[union-attr]
                    row["capabilities"].add(projection["capability_id"])  # type: ignore[union-attr]
                    row["common_target"] = True

    result: dict[str, dict[str, Any]] = {}
    for item_id, row in inside.items():
        result[item_id] = {
            "assessments": sorted(row["assessments"]),  # type: ignore[arg-type]
            "common_target": bool(row["common_target"]),
            "source_ids": sorted(row["source_ids"]),  # type: ignore[arg-type]
            "profiles": sorted(row["profiles"]),  # type: ignore[arg-type]
            "capabilities": sorted(row["capabilities"]),  # type: ignore[arg-type]
        }

    gaps: list[dict[str, Any]] = []
    for item_id, row in sorted(outside.items()):
        gaps.append(
            {
                "item_id": item_id,
                "kind": item_kind(item_id),
                "authority": "production",
                "reason": "outside-denominator",
                "assessments": sorted(row["assessments"]),  # type: ignore[arg-type]
                "common_target": bool(row["common_target"]),
                "source_ids": sorted(row["source_ids"]),  # type: ignore[arg-type]
                "profiles": sorted(row["profiles"]),  # type: ignore[arg-type]
                "capabilities": sorted(row["capabilities"]),  # type: ignore[arg-type]
            }
        )
    return result, gaps

def build_manifests() -> dict[str, dict[str, Any]]:
    pilots = load_json(PILOTS)
    overrides = load_json(OVERRIDES)
    policy = load_json(RAW_POLICY)
    rows = apply_overrides(pilots, overrides)

    if set(pilots["corpora"]) != set(P004_R011_BASELINE_CORPORA):
        raise ValueError("pilot corpus set does not match P-004 baseline contract")
    if set(policy["corpora"]) != set(P004_R011_BASELINE_CORPORA):
        raise ValueError("raw policy corpus set does not match P-004 baseline contract")

    manifests: dict[str, dict[str, Any]] = {}
    for corpus_id in P004_R011_BASELINE_CORPORA:
        meta = pilots["corpora"][corpus_id]
        corpus_policy = policy["corpora"][corpus_id]
        available, value_families, scope_quality, basis_source = denominator_items(
            corpus_id,
            meta,
            corpus_policy,
        )
        research = research_accounting(
            corpus_id,
            corpus_policy,
            rows,
            value_families,
            available,
        )
        production, accounting_gaps = production_accounting(corpus_id, available)

        semantic_items = []
        for item_id in sorted(available):
            semantic_items.append(
                {
                    "item_id": item_id,
                    "kind": item_kind(item_id),
                    "accounting": {
                        "research": research.get(item_id),
                        "production": production.get(item_id),
                    },
                }
            )

        basis_kind = (
            "generated-r005-inventory"
            if scope_quality == "machine-exhaustive"
            else "curated-r011-baseline"
        )
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "manifest_id": f"coverage:p004-r011-baseline-v1:{corpus_id}",
            "corpus_id": corpus_id,
            "repository": meta["repository"],
            "denominator_source_revision": meta["revision"],
            "target_corpus_revision": TARGET_REVISIONS[corpus_id],
            "scope_quality": scope_quality,
            "denominator_basis": {
                "kind": basis_kind,
                "source": basis_source,
                "bounded_node_features": sorted(corpus_policy.get("bounded_features", [])),
            },
            "semantic_items": semantic_items,
            "technical_exclusions": [],
            "accounting_gaps": accounting_gaps,
        }
        if meta.get("tf_version"):
            manifest["tf_version"] = meta["tf_version"]
        manifest["denominator_digest"] = coverage_denominator_digest(manifest)
        validate_coverage_manifest(manifest)
        manifests[corpus_id] = manifest
    return manifests


def serialized(manifest: dict[str, Any]) -> str:
    return json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def check_outputs(manifests: dict[str, dict[str, Any]]) -> None:
    expected_names = {f"{corpus_id}.json" for corpus_id in manifests}
    actual_names = (
        {path.name for path in OUTPUT.glob("*.json")}
        if OUTPUT.exists()
        else set()
    )
    if actual_names != expected_names:
        raise SystemExit(
            f"coverage baseline file set mismatch: expected={sorted(expected_names)} "
            f"actual={sorted(actual_names)}"
        )

    mismatches: list[str] = []
    for corpus_id, manifest in manifests.items():
        path = OUTPUT / f"{corpus_id}.json"
        if path.read_text(encoding="utf-8") != serialized(manifest):
            mismatches.append(corpus_id)
    if mismatches:
        raise SystemExit(f"coverage baseline resources are stale: {sorted(mismatches)}")


def write_outputs(manifests: dict[str, dict[str, Any]]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected_names = {f"{corpus_id}.json" for corpus_id in manifests}
    for path in OUTPUT.glob("*.json"):
        if path.name not in expected_names:
            path.unlink()
    for corpus_id, manifest in manifests.items():
        (OUTPUT / f"{corpus_id}.json").write_text(
            serialized(manifest),
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless committed baseline resources equal deterministic regeneration",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifests = build_manifests()
    if sum(len(value["semantic_items"]) for value in manifests.values()) != 685:
        raise SystemExit("historical P-004/R-011 denominator drifted from 685 items")
    if args.check:
        check_outputs(manifests)
    else:
        write_outputs(manifests)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
