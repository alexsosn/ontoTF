#!/usr/bin/env python3
"""Build the current ORACC-TF registered-candidate coverage denominator.

This deterministic repository tooling consumes only committed I-018 evidence
and explicit reviewed policy. It never acquires/builds a corpus, imports
Text-Fabric or ORACC-TF, or accesses the network.
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
    P004_ORACC_0_4_0_RESOURCE,
    coverage_denominator_digest,
    validate_coverage_manifest,
)
from tfont.digests import canonical_json_bytes  # noqa: E402

EVIDENCE = ROOT / "docs/research/data/generated/i018/oracc-0.4.0.json"
POLICY = ROOT / "docs/research/data/i018/oracc-denominator-policy.json"
OUTPUT = (
    ROOT
    / "src/tfont/resources/coverage"
    / P004_ORACC_0_4_0_RESOURCE
    / "oracc.json"
)

EXPECTED_CANDIDATE = {
    "repository": "alexsosn/ORACC-TF",
    "builder_commit": "f6f189bbd99d72bfdc7044555bd3113aa7b54232",
    "dataset": "assyrian-royal-inscriptions",
    "tf_version": "0.4.0",
    "riao_tree": "b03bf0544f4c83710dc6ea88b26b6389e9b85645",
    "rinap_tree": "96ddf1d4e6bbf37b6ec4a3e37f42e8fae899593c",
    "datasets_blob": "584d4671959b4f5d35535bc796521299eb6e040e",
    "tei_archive": "riao-teiCorpus-20241202.zip",
    "tei_sha256": "b793d8920db58908e3a044b7f2d1a204c1ba0784e880007e0cd7941333e841bd",
    "candidate_tree_sha256": "cbcc8299c1f5d02bc082ded824452fe3fb0a7857656a0556039a31667c48af1b",
    "tf_files_sha256": "5d23f56eaa9461d7a6f42dc11a8c2f5d7307ba9820f49869400c5ac9af8bf34f",
}
EXPECTED_BUILD = {
    "source_members": 2081,
    "readable_source_members": 2078,
    "unreadable_source_members": 3,
    "documents": 2078,
    "populated_documents": 1845,
    "stub_documents": 233,
    "words": 320975,
    "semantic_signs": 792651,
    "synthetic_slots": 689,
    "tf_slots": 793340,
    "lines": 56226,
    "lexemes": 8025,
    "translation_units": 6792,
    "translation_gaps": 2509,
}
EXPECTED_SIDECARS = [{"path": "translation-gaps.json", "bytes": 967987}]
EXPECTED_SEMANTIC_ITEMS = 99
EXPECTED_TECHNICAL_EXCLUSIONS = 6
FORBIDDEN_DOCUMENTED_ONLY = {
    "node_type:translation_note",
    "node_feature:translation_note_id",
    "node_feature:translation_note_text",
    "edge_feature:translation_note_unit",
}


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


def _require_exact_mapping(
    actual: Any,
    expected: dict[str, Any],
    *,
    name: str,
) -> dict[str, Any]:
    if type(actual) is not dict:
        raise ValueError(f"{name} object is absent")
    if actual != expected:
        missing = {key: expected[key] for key in expected if actual.get(key) != expected[key]}
        extra = {key: actual[key] for key in actual if key not in expected}
        raise ValueError(f"{name} identity drifted: changed={missing!r} extra={extra!r}")
    return actual


def _validate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    candidate = _require_exact_mapping(
        evidence.get("candidate"),
        EXPECTED_CANDIDATE,
        name="I-018 candidate",
    )
    _require_exact_mapping(
        evidence.get("build"),
        EXPECTED_BUILD,
        name="I-018 build census",
    )
    if evidence.get("sidecars") != EXPECTED_SIDECARS:
        raise ValueError(
            f"I-018 sidecar identity drifted: expected={EXPECTED_SIDECARS!r} "
            f"actual={evidence.get('sidecars')!r}"
        )
    if evidence.get("slot_type") != "sign":
        raise ValueError("I-018 slot type drifted from sign")

    node_types = evidence.get("node_types")
    node_features = evidence.get("node_features")
    edge_features = evidence.get("edge_features")
    if type(node_types) is not dict or len(node_types) != 10:
        raise ValueError("I-018 materialized node-type census drifted")
    if type(node_features) is not dict or len(node_features) != 75:
        raise ValueError("I-018 materialized node-feature census drifted")
    if type(edge_features) is not dict or len(edge_features) != 8:
        raise ValueError("I-018 materialized edge-feature census drifted")

    actual_ids = {
        *(f"node_type:{name}" for name in node_types),
        *(f"node_feature:{name}" for name in node_features),
        *(f"edge_feature:{name}" for name in edge_features),
    }
    leaked = actual_ids & FORBIDDEN_DOCUMENTED_ONLY
    if leaked:
        raise ValueError(
            "documented-only translation-note schema became materialized: "
            f"{sorted(leaked)}"
        )
    return candidate


def value_item_id(feature: str, value: Any) -> str:
    encoded = canonical_json_bytes(value).decode("utf-8")
    return f"node_value:{feature}={encoded}"


def item_kind(item_id: str) -> str:
    kind = item_id.split(":", 1)[0]
    if kind not in {"node_type", "node_feature", "node_value", "edge_feature"}:
        raise ValueError(f"unsupported I-018 item identity: {item_id}")
    return kind


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
    candidate = _validate_evidence(evidence)

    node_types = set(evidence["node_types"])
    node_features = set(evidence["node_features"])
    edge_features = set(evidence["edge_features"])

    technical_node, technical_rows = _technical_exclusions(policy, evidence)
    semantic_node_features = node_features - technical_node
    semantic_ids = {
        *(f"node_type:{name}" for name in node_types),
        *(f"node_feature:{name}" for name in semantic_node_features),
        *(f"edge_feature:{name}" for name in edge_features),
    }
    semantic_ids.update(_bounded_value_items(policy, semantic_node_features))

    technical_ids = {row["item_id"] for row in technical_rows}
    overlap = semantic_ids & technical_ids
    if overlap:
        raise ValueError(f"semantic/technical overlap: {sorted(overlap)}")

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

    leaked = semantic_ids & FORBIDDEN_DOCUMENTED_ONLY
    if leaked:
        raise ValueError(f"documented-only translation-note identities leaked: {sorted(leaked)}")

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
        "manifest_id": "coverage:p004-oracc-0.4.0-f6f189b-v1:oracc",
        "corpus_id": "oracc",
        "repository": candidate["repository"],
        "denominator_source_revision": candidate["builder_commit"],
        "target_corpus_revision": candidate["builder_commit"],
        "tf_version": candidate["tf_version"],
        "scope_quality": "machine-exhaustive",
        "denominator_basis": {
            "kind": "generated-r005-inventory",
            "source": "docs/research/data/generated/i018/oracc-0.4.0.json",
            "bounded_node_features": sorted(policy["bounded_node_values"]),
            "artifact_identity": {
                "locator": (
                    "registered-build:alexsosn/ORACC-TF@"
                    f"{candidate['builder_commit']}:"
                    f"{candidate['dataset']}/tf/{candidate['tf_version']}"
                ),
                "sha256": candidate["candidate_tree_sha256"],
                "materialized_sha256": candidate["tf_files_sha256"],
            },
        },
        "semantic_items": semantic_items,
        "technical_exclusions": technical_rows,
        "accounting_gaps": [],
    }
    manifest["denominator_digest"] = coverage_denominator_digest(manifest)
    validate_coverage_manifest(manifest)

    if len(semantic_items) != EXPECTED_SEMANTIC_ITEMS:
        raise ValueError(f"I-018 semantic denominator count drifted: {len(semantic_items)}")
    if len(technical_rows) != EXPECTED_TECHNICAL_EXCLUSIONS:
        raise ValueError(f"I-018 technical exclusion count drifted: {len(technical_rows)}")
    return manifest


def serialized(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def check_output(manifest: dict[str, Any]) -> None:
    try:
        existing = OUTPUT.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"I-018 coverage manifest is missing: {error}") from error
    if existing != serialized(manifest):
        raise SystemExit("I-018 coverage manifest is stale")


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
