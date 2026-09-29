#!/usr/bin/env python3
"""Build the current TLHdig-TF 0.4.0 coverage denominator.

This deterministic repository tooling consumes only committed I-019 research
schema evidence and an explicit reviewed denominator policy. It does not load,
acquire or rebuild TLHdig and has no network or Text-Fabric dependency.
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
    P004_TLHDIG_0_4_0_RESOURCE,
    coverage_denominator_digest,
    validate_coverage_manifest,
)
from tfont.digests import canonical_json_bytes  # noqa: E402

EVIDENCE = ROOT / "docs/research/data/generated/i019/tlhdig-0.4.0.json"
POLICY = ROOT / "docs/research/data/i019/tlhdig-denominator-policy.json"
OUTPUT = (
    ROOT
    / "src/tfont/resources/coverage"
    / P004_TLHDIG_0_4_0_RESOURCE
    / "tlhdig.json"
)

EXPECTED_ARTIFACT = {
    "repository": "alexsosn/TLHdig-TF",
    "containing_revision": "bc4a206690c1856d3cfde8b291f626c45a712640",
    "source_version": "0.3",
    "tf_version": "0.4.0",
    "build_manifest_sha256": "56e47a19b61293f0cec23ba12d884bef3d1e072a87c9acdd9c609bb190f7a6f4",
    "code_commit": "fb5d93b5d112b77da756893c5561f99c05617c7b",
    "code_algorithm": "tlhdig-current-code-v1",
    "code_digest": "sha256:d8337017e18d9d906521e7c1c4d6fb7c6274b607d9b8118ff9c5cd64c459d403",
    "outputs_algorithm": "tlhdig-current-tree-v2",
    "outputs_digest": "sha256:d0160532d03b86069132681ba68e23d3039bcebb96eb5684507ce660ea3b1634",
    "core_tf_files_sha256": "bb946e21f56249738c6b71fe50adbb588c7233d97ebb928a0b3ea83b46650fd6",
    "provenance_tf_files_sha256": "f66b1e7c4dd67670d0cc1a0094d8bed95b200740d80eca168ad692601a9e685d",
    "materialized_tf_files_sha256": "fb447193b4f24a753154fbfdd4105cb855953af483b1160984435cf3f6422e6c",
}
EXPECTED_COUNTS = {
    "main_tf_files": 137,
    "node_types": 17,
    "core_node_features_nonwarp": 120,
    "optional_provenance_node_features": 2,
    "provenance_tf_files": 2,
    "edge_features_nonwarp": 14,
}
EXPECTED_NODE_TYPES = {
    "analysis", "cluster", "colon", "column", "docgroup", "document", "edit",
    "fragment", "joinstmt", "layout", "lex", "line", "note", "paragraph",
    "sign", "surface", "word",
}
EXPECTED_PROVENANCE = {"src_span", "srcxml"}
EXPECTED_SEMANTIC_ITEMS = 256
EXPECTED_TECHNICAL_EXCLUSIONS = 4
EXPECTED_NODE_VALUE_ITEMS = 101
EXPECTED_EDGE_VALUE_ITEMS = 4


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"expected JSON object: {path}")
    return value


def _exact_string_list(value: Any, *, name: str) -> list[str]:
    if type(value) is not list or any(type(item) is not str or not item for item in value):
        raise ValueError(f"{name} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{name} contains duplicate values")
    return list(value)


def _require_exact_mapping(actual: Any, expected: dict[str, Any], *, name: str) -> dict[str, Any]:
    if type(actual) is not dict:
        raise ValueError(f"{name} object is absent")
    if actual != expected:
        raise ValueError(f"{name} identity drifted: expected={expected!r} actual={actual!r}")
    return actual


def _validate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    artifact = _require_exact_mapping(
        evidence.get("artifact"),
        EXPECTED_ARTIFACT,
        name="I-019 artifact",
    )
    _require_exact_mapping(
        evidence.get("counts"),
        EXPECTED_COUNTS,
        name="I-019 schema census",
    )
    if evidence.get("slot_type") != "sign":
        raise ValueError("I-019 slot type drifted from sign")
    if set(evidence.get("node_types", {})) != EXPECTED_NODE_TYPES:
        raise ValueError("I-019 node-type set drifted")
    core = evidence.get("core_node_features")
    if type(core) is not list or len(core) != 120 or len(set(core)) != 120:
        raise ValueError("I-019 core node-feature set drifted")
    provenance = evidence.get("optional_provenance_node_features")
    if type(provenance) is not list or set(provenance) != EXPECTED_PROVENANCE:
        raise ValueError("I-019 provenance feature set drifted")
    edges = evidence.get("edge_features")
    if type(edges) is not dict or len(edges) != 14:
        raise ValueError("I-019 edge-feature set drifted")
    if evidence.get("excluded_warp_features") != {"node": ["otype"], "edge": ["oslots"]}:
        raise ValueError("I-019 warp feature boundary drifted")
    if evidence.get("config_features") != ["otext"]:
        raise ValueError("I-019 config feature boundary drifted")
    return artifact


def value_item_id(kind: str, feature: str, value: Any) -> str:
    encoded = canonical_json_bytes(value).decode("utf-8")
    return f"{kind}:{feature}={encoded}"


def item_kind(item_id: str) -> str:
    kind = item_id.split(":", 1)[0]
    if kind not in {
        "node_type",
        "node_feature",
        "node_value",
        "edge_feature",
        "edge_value",
    }:
        raise ValueError(f"unsupported I-019 item identity: {item_id}")
    return kind


def _technical_exclusions(
    policy: dict[str, Any],
    materialized_node_features: set[str],
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
    if not technical_node <= materialized_node_features:
        raise ValueError(
            "technical node policy references absent materialized features: "
            f"{sorted(technical_node - materialized_node_features)}"
        )
    if warp_node != set(evidence["excluded_warp_features"]["node"]):
        raise ValueError("technical warp node policy does not match evidence")
    if warp_edge != set(evidence["excluded_warp_features"]["edge"]):
        raise ValueError("technical warp edge policy does not match evidence")

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
            raise ValueError(f"technical exclusion detail must be an object: {item_id}")
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


def _bounded_items(
    policy: dict[str, Any],
    *,
    value_key: str,
    source_key: str,
    semantic_features: set[str],
    item_prefix: str,
) -> list[str]:
    bounded = policy.get(value_key)
    sources = policy.get(source_key)
    if type(bounded) is not dict or type(sources) is not dict:
        raise ValueError(f"{value_key}/{source_key} policy objects are required")
    if set(bounded) != set(sources):
        raise ValueError(f"{source_key} must exactly cover {value_key}")

    items: list[str] = []
    for feature in sorted(bounded):
        if feature not in semantic_features:
            raise ValueError(f"bounded family is not a semantic materialized feature: {feature}")
        values = bounded[feature]
        if type(values) is not list or not values:
            raise ValueError(f"bounded family must be a non-empty list: {feature}")
        encoded = [canonical_json_bytes(value) for value in values]
        if len(encoded) != len(set(encoded)):
            raise ValueError(f"bounded family contains duplicates: {feature}")
        _exact_string_list(sources[feature], name=f"bounded source IDs for {feature}")
        items.extend(value_item_id(item_prefix, feature, value) for value in values)
    return items


def build_manifest() -> dict[str, Any]:
    evidence = load_json(EVIDENCE)
    policy = load_json(POLICY)
    artifact = _validate_evidence(evidence)

    node_types = set(evidence["node_types"])
    core_node_features = set(evidence["core_node_features"])
    provenance_node_features = set(evidence["optional_provenance_node_features"])
    materialized_node_features = core_node_features | provenance_node_features
    edge_features = set(evidence["edge_features"])

    if core_node_features & provenance_node_features:
        raise ValueError("core and provenance node-feature sets overlap")

    technical_node, technical_rows = _technical_exclusions(
        policy,
        materialized_node_features,
        evidence,
    )
    semantic_node_features = materialized_node_features - technical_node
    semantic_ids = {
        *(f"node_type:{name}" for name in node_types),
        *(f"node_feature:{name}" for name in semantic_node_features),
        *(f"edge_feature:{name}" for name in edge_features),
    }

    node_values = _bounded_items(
        policy,
        value_key="bounded_node_values",
        source_key="bounded_node_sources",
        semantic_features=semantic_node_features,
        item_prefix="node_value",
    )
    edge_values = _bounded_items(
        policy,
        value_key="bounded_edge_values",
        source_key="bounded_edge_sources",
        semantic_features=edge_features,
        item_prefix="edge_value",
    )
    semantic_ids.update(node_values)
    semantic_ids.update(edge_values)

    technical_ids = {row["item_id"] for row in technical_rows}
    overlap = semantic_ids & technical_ids
    if overlap:
        raise ValueError(f"semantic/technical overlap: {sorted(overlap)}")

    accounted_node = {
        item_id.split(":", 1)[1]
        for item_id in semantic_ids
        if item_id.startswith("node_feature:")
    } | technical_node
    if accounted_node != materialized_node_features:
        raise ValueError(
            "materialized node feature accounting is incomplete: "
            f"missing={sorted(materialized_node_features - accounted_node)} "
            f"extra={sorted(accounted_node - materialized_node_features)}"
        )

    accounted_edge = {
        item_id.split(":", 1)[1]
        for item_id in semantic_ids
        if item_id.startswith("edge_feature:")
    }
    if accounted_edge != edge_features:
        raise ValueError(
            "materialized edge feature accounting is incomplete: "
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

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "manifest_id": "coverage:p004-tlhdig-0.4.0-bc4a206-v1:tlhdig",
        "corpus_id": "tlhdig",
        "repository": artifact["repository"],
        "denominator_source_revision": artifact["containing_revision"],
        "target_corpus_revision": artifact["containing_revision"],
        "tf_version": artifact["tf_version"],
        "scope_quality": "machine-exhaustive",
        "denominator_basis": {
            "kind": "generated-r005-inventory",
            "source": "docs/research/data/generated/i019/tlhdig-0.4.0.json",
            "bounded_node_features": sorted(policy["bounded_node_values"]),
            "bounded_edge_features": sorted(policy["bounded_edge_values"]),
            "artifact_identity": {
                "locator": (
                    "shipped-build:alexsosn/TLHdig-TF@"
                    f"{artifact['containing_revision']}:"
                    "tf/0.4.0+tf-provenance/0.4.0"
                ),
                "sha256": artifact["outputs_digest"].removeprefix("sha256:"),
                "materialized_sha256": artifact["materialized_tf_files_sha256"],
            },
        },
        "semantic_items": semantic_items,
        "technical_exclusions": technical_rows,
        "accounting_gaps": [],
    }
    manifest["denominator_digest"] = coverage_denominator_digest(manifest)
    validate_coverage_manifest(manifest)

    if len(node_values) != EXPECTED_NODE_VALUE_ITEMS:
        raise ValueError(f"I-019 bounded node value count drifted: {len(node_values)}")
    if len(edge_values) != EXPECTED_EDGE_VALUE_ITEMS:
        raise ValueError(f"I-019 bounded edge value count drifted: {len(edge_values)}")
    if len(semantic_items) != EXPECTED_SEMANTIC_ITEMS:
        raise ValueError(f"I-019 semantic denominator count drifted: {len(semantic_items)}")
    if len(technical_rows) != EXPECTED_TECHNICAL_EXCLUSIONS:
        raise ValueError(f"I-019 technical exclusion count drifted: {len(technical_rows)}")
    return manifest


def serialized(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def check_output(manifest: dict[str, Any]) -> None:
    try:
        existing = OUTPUT.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"I-019 coverage manifest is missing: {error}") from error
    if existing != serialized(manifest):
        raise SystemExit("I-019 coverage manifest is stale")


def write_output(manifest: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialized(manifest), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
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
