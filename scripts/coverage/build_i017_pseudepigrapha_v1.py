#!/usr/bin/env python3
"""Build the current Pseudepigrapha-TF v1.0.0 coverage denominator.

This is deterministic repository/release tooling. It consumes only committed
I-017 research evidence and an explicit reviewed denominator policy. It does
not acquire or load a corpus and has no network dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tfont.coverage import (  # noqa: E402
    P004_PSEUDEPIGRAPHA_V1_RESOURCE,
    coverage_denominator_digest,
    validate_coverage_manifest,
)
from tfont.digests import canonical_json_bytes  # noqa: E402

EVIDENCE = ROOT / "docs/research/data/generated/i017/pseudepigrapha-v1.0.0.json"
POLICY = ROOT / "docs/research/data/i017/pseudepigrapha-denominator-policy.json"
OUTPUT = (
    ROOT
    / "src/tfont/resources/coverage"
    / P004_PSEUDEPIGRAPHA_V1_RESOURCE
    / "pseudepigrapha.json"
)

EXPECTED_RELEASE = {
    "repository": "alexsosn/Pseudepigrapha-TF",
    "commit": "7c4b757bb543a110ae9a252d1281835859136852",
    "tag": "v1.0.0",
    "asset": "tf-1.0.zip",
    "asset_sha256": "d2dfad7e643699617a9493b9f5d724868f8027dd5f2e88bd558451e3e7819b7a",
    "tf_version": "1.0",
    "converter_version": "1.0.0",
    "upstream_commit": "c939dcbacad78c5d18d2c4282cad23c47e19ac07",
    "tf_files_sha256": "9b708add5b9f8ddbfdafa7dd61507956f7987ca6a70b2b9164342bd49003ec61",
}
EXPECTED_SEMANTIC_ITEMS = 113
EXPECTED_TECHNICAL_EXCLUSIONS = 5


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"expected JSON object: {path}")
    return value


def value_item_id(feature: str, value: Any) -> str:
    encoded = canonical_json_bytes(value).decode("utf-8")
    return f"node_value:{feature}={encoded}"


def item_kind(item_id: str) -> str:
    kind = item_id.split(":", 1)[0]
    if kind not in {"node_type", "node_feature", "node_value", "edge_feature"}:
        raise ValueError(f"unsupported I-017 item identity: {item_id}")
    return kind


def _require_exact_release(evidence: dict[str, Any]) -> dict[str, Any]:
    release = evidence.get("release")
    if type(release) is not dict:
        raise ValueError("I-017 evidence release object is absent")
    for key, expected in EXPECTED_RELEASE.items():
        actual = release.get(key)
        if actual != expected:
            raise ValueError(
                f"I-017 release identity mismatch for {key}: "
                f"expected={expected!r} actual={actual!r}"
            )
    return release


def _exact_string_list(value: Any, *, name: str) -> list[str]:
    if type(value) is not list or any(type(item) is not str or not item for item in value):
        raise ValueError(f"{name} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{name} contains duplicate values")
    return list(value)


def _technical_exclusions(
    policy: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[set[str], list[dict[str, Any]]]:
    technical_node = set(
        _exact_string_list(policy["technical_node_features"], name="technical_node_features")
    )
    warp_node = set(
        _exact_string_list(
            policy["technical_warp_node_features"],
            name="technical_warp_node_features",
        )
    )
    warp_edge = set(
        _exact_string_list(
            policy["technical_warp_edge_features"],
            name="technical_warp_edge_features",
        )
    )
    materialized_node = set(evidence["node_features"])
    if not technical_node <= materialized_node:
        raise ValueError(
            "technical node policy references absent materialized features: "
            f"{sorted(technical_node - materialized_node)}"
        )

    observed_warp_node = set(evidence["excluded_warp_features"]["node"])
    observed_warp_edge = set(evidence["excluded_warp_features"]["edge"])
    if warp_node != observed_warp_node or warp_edge != observed_warp_edge:
        raise ValueError(
            "technical warp policy does not exactly account for inventory warp features"
        )

    ids = {
        *(f"node_feature:{name}" for name in technical_node | warp_node),
        *(f"edge_feature:{name}" for name in warp_edge),
    }
    details = policy.get("technical_exclusion_details")
    if type(details) is not dict or set(details) != ids:
        raise ValueError("technical exclusion details do not exactly cover technical identities")

    rows: list[dict[str, Any]] = []
    for item_id in sorted(ids):
        detail = details[item_id]
        if type(detail) is not dict:
            raise ValueError(f"technical detail must be an object: {item_id}")
        source_ids = _exact_string_list(
            detail.get("source_ids"),
            name=f"technical source IDs for {item_id}",
        )
        reason = detail.get("reason")
        if type(reason) is not str or not reason:
            raise ValueError(f"technical exclusion reason is absent: {item_id}")
        rows.append(
            {
                "item_id": item_id,
                "kind": item_kind(item_id),
                "reason": reason,
                "authority": "production",
                "source_ids": sorted(source_ids),
            }
        )
    return technical_node, rows


def _bounded_value_items(
    policy: dict[str, Any],
    semantic_node_features: set[str],
) -> list[str]:
    bounded = policy.get("bounded_node_values")
    sources = policy.get("bounded_sources")
    if type(bounded) is not dict or type(sources) is not dict:
        raise ValueError("bounded value policy/source objects are required")
    if set(bounded) != set(sources):
        raise ValueError("bounded value source IDs must exactly cover bounded features")

    items: list[str] = []
    for feature in sorted(bounded):
        if feature not in semantic_node_features:
            raise ValueError(f"bounded value family is not a semantic node feature: {feature}")
        values = bounded[feature]
        if type(values) is not list or not values:
            raise ValueError(f"bounded value family must be a non-empty list: {feature}")
        encoded = [canonical_json_bytes(value) for value in values]
        if len(encoded) != len(set(encoded)):
            raise ValueError(f"bounded value family contains duplicates: {feature}")
        _exact_string_list(sources[feature], name=f"bounded source IDs for {feature}")
        items.extend(value_item_id(feature, value) for value in values)
    return items


def build_manifest() -> dict[str, Any]:
    evidence = load_json(EVIDENCE)
    policy = load_json(POLICY)
    release = _require_exact_release(evidence)

    if evidence.get("slot_type") != "word":
        raise ValueError("I-017 evidence slot type drifted from word")
    node_types = set(evidence.get("node_types", {}))
    node_features = set(evidence.get("node_features", {}))
    edge_features = set(evidence.get("edge_features", {}))
    if not node_types or not node_features:
        raise ValueError("I-017 evidence has an empty materialized schema")

    technical_node, technical_rows = _technical_exclusions(policy, evidence)
    semantic_node_features = node_features - technical_node
    semantic_ids = {
        *(f"node_type:{name}" for name in node_types),
        *(f"node_feature:{name}" for name in semantic_node_features),
        *(f"edge_feature:{name}" for name in edge_features),
    }
    semantic_ids.update(_bounded_value_items(policy, semantic_node_features))

    technical_ids = {row["item_id"] for row in technical_rows}
    if semantic_ids & technical_ids:
        raise ValueError(
            f"semantic/technical overlap: {sorted(semantic_ids & technical_ids)}"
        )

    # Every materialized non-warp feature is explicitly semantic or technical.
    accounted_node = {
        item_id.split(":", 1)[1]
        for item_id in semantic_ids
        if item_id.startswith("node_feature:")
    } | technical_node
    if accounted_node != node_features:
        raise ValueError(
            "materialized node feature accounting is incomplete: "
            f"missing={sorted(node_features - accounted_node)} "
            f"extra={sorted(accounted_node - node_features)}"
        )
    accounted_edge = {
        item_id.split(":", 1)[1]
        for item_id in semantic_ids
        if item_id.startswith("edge_feature:")
    }
    if accounted_edge != edge_features:
        raise ValueError(
            "materialized semantic edge accounting is incomplete: "
            f"missing={sorted(edge_features - accounted_edge)} "
            f"extra={sorted(accounted_edge - edge_features)}"
        )

    semantic_items = [
        {
            "item_id": item_id,
            "kind": item_kind(item_id),
            "accounting": {"research": None, "production": None},
        }
        for item_id in sorted(semantic_ids)
    ]
    bounded_features = sorted(policy["bounded_node_values"])

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "manifest_id": (
            "coverage:p004-pseudepigrapha-v1.0.0-v1:pseudepigrapha"
        ),
        "corpus_id": "pseudepigrapha",
        "repository": release["repository"],
        "denominator_source_revision": release["commit"],
        "target_corpus_revision": release["commit"],
        "tf_version": release["tf_version"],
        "scope_quality": "machine-exhaustive",
        "denominator_basis": {
            "kind": "generated-r005-inventory",
            "source": (
                "docs/research/data/generated/i017/"
                "pseudepigrapha-v1.0.0.json"
            ),
            "bounded_node_features": bounded_features,
            "artifact_identity": {
                "locator": f"github-release:{release['tag']}/{release['asset']}",
                "sha256": release["asset_sha256"],
                "materialized_sha256": release["tf_files_sha256"],
            },
        },
        "semantic_items": semantic_items,
        "technical_exclusions": technical_rows,
        "accounting_gaps": [],
    }
    manifest["denominator_digest"] = coverage_denominator_digest(manifest)
    validate_coverage_manifest(manifest)

    if len(semantic_items) != EXPECTED_SEMANTIC_ITEMS:
        raise ValueError(
            f"I-017 semantic denominator count drifted: {len(semantic_items)}"
        )
    if len(technical_rows) != EXPECTED_TECHNICAL_EXCLUSIONS:
        raise ValueError(
            f"I-017 technical exclusion count drifted: {len(technical_rows)}"
        )
    return manifest


def serialized(manifest: dict[str, Any]) -> str:
    return json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def check_output(manifest: dict[str, Any]) -> None:
    try:
        existing = OUTPUT.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"I-017 coverage manifest is missing: {error}") from error
    expected = serialized(manifest)
    if existing != expected:
        raise SystemExit("I-017 coverage manifest is stale")


def write_output(manifest: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialized(manifest), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless the committed I-017 manifest matches regeneration",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the deterministic manifest instead of writing it",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest()
    if args.stdout:
        print(serialized(manifest), end="")
    elif args.check:
        check_output(manifest)
    else:
        write_output(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
