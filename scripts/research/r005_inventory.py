#!/usr/bin/env python3
"""Generate an empirical Text-Fabric feature/domain inventory for R-005.

This is research tooling, not ontoTF runtime code. It consumes an already checked-out
TF dataset and records what that exact artifact actually contains: node/edge feature
metadata, applicable node types, observed value cardinalities, small observed domains,
and edge source/target types.

The generator intentionally distinguishes ``observed_small_domain`` from a documented
closed categorical vocabulary. Small cardinality alone is not evidence that a feature
is semantically closed; R-005's curated research inventory may promote an observed
small domain to ``categorical_bounded`` only when corpus documentation/source semantics
support that claim.

Dense TF files can expose empty-string records through the loaded API. Those records
mean that no semantic value is present at that position; they are counted separately
and never treated as members of the observed value domain or as evidence that a
feature applies to that node type.

Requires Text-Fabric. The research baseline was inspected against TF 13.1.0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

WARP_NODE = {"otype"}
WARP_EDGE = {"oslots"}


def _stable_value(value: Any) -> str | int | float | bool | None:
    """Return a JSON-safe scalar representation without inventing semantics."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _is_empty_observation(value: Any) -> bool:
    """Identify a TF record that carries no semantic feature value."""
    return value is None or value == ""


def summarize_values(
    values: Iterable[Any], *, small_domain_limit: int = 64, sample_limit: int = 20
) -> dict[str, Any]:
    """Summarize observed non-empty values conservatively.

    ``observed_small_domain`` means only that the pinned artifact has few distinct
    non-empty values. It does *not* assert that the source vocabulary is formally
    closed. Empty-string/None records are counted separately because TF dense
    feature representations may expose them even though no semantic value exists.
    """
    raw_values = [_stable_value(v) for v in values]
    empty_count = sum(1 for value in raw_values if _is_empty_observation(value))
    semantic_values = [value for value in raw_values if not _is_empty_observation(value)]
    counts = Counter(semantic_values)
    ordered = sorted(counts.items(), key=lambda item: (str(type(item[0])), str(item[0])))
    result: dict[str, Any] = {
        "observed_unique_count": len(ordered),
        "observation_count": sum(counts.values()),
        "raw_observation_count": len(raw_values),
        "empty_observation_count": empty_count,
    }
    if len(ordered) <= small_domain_limit:
        result["domain_observation"] = "observed_small_domain"
        result["observed_values"] = [value for value, _count in ordered]
        result["observed_frequencies"] = {
            str(value): count for value, count in ordered
        }
    else:
        result["domain_observation"] = "open_or_large_observed_domain"
        most_common = sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))[:sample_limit]
        result["sample_values"] = [value for value, _count in most_common]
    return result


def _metadata(feature: Any) -> dict[str, Any]:
    meta = getattr(feature, "meta", {}) or {}
    return {
        str(key): _stable_value(value)
        for key, value in sorted(meta.items(), key=lambda item: str(item[0]))
    }


def inventory_api(api: Any, *, small_domain_limit: int = 64) -> dict[str, Any]:
    """Inventory a loaded Text-Fabric public API object.

    The function is separated from loading so unit tests can exercise census logic
    without requiring Text-Fabric or a network checkout.
    """
    otype = api.F.otype
    node_features: dict[str, Any] = {}
    edge_features: dict[str, Any] = {}

    for name in api.Fall(warp=False):
        feature = api.Fs(name)
        items = list(feature.items())
        semantic_items = [
            (node, value)
            for node, value in items
            if not _is_empty_observation(value)
        ]
        applies_to = sorted(
            {otype.v(node) for node, _value in semantic_items if otype.v(node)}
        )
        info = {
            "kind": "node",
            "metadata": _metadata(feature),
            "applies_to": applies_to,
            "nodes_with_value": len(semantic_items),
            "node_records_seen": len(items),
        }
        info.update(
            summarize_values(
                (value for _node, value in items),
                small_domain_limit=small_domain_limit,
            )
        )
        node_features[name] = info

    for name in api.Eall(warp=False):
        feature = api.Es(name)
        source_types: set[str] = set()
        target_types: set[str] = set()
        edge_values: list[Any] = []
        edge_count = 0
        valued = bool(getattr(feature, "doValues", False))

        for source, targets in feature.items():
            source_type = otype.v(source)
            if source_type:
                source_types.add(source_type)
            if valued:
                iterator = targets.items()
                for target, value in iterator:
                    edge_count += 1
                    target_type = otype.v(target)
                    if target_type:
                        target_types.add(target_type)
                    edge_values.append(value)
            else:
                for target in targets:
                    edge_count += 1
                    target_type = otype.v(target)
                    if target_type:
                        target_types.add(target_type)

        info = {
            "kind": "edge",
            "metadata": _metadata(feature),
            "valued": valued,
            "source_types": sorted(source_types),
            "target_types": sorted(target_types),
            "edge_count": edge_count,
        }
        if valued:
            info.update(
                summarize_values(
                    edge_values,
                    small_domain_limit=small_domain_limit,
                )
            )
        edge_features[name] = info

    type_counts = Counter(value for _node, value in otype.items())
    return {
        "slot_type": getattr(otype, "slotType", None),
        "node_types": dict(sorted(type_counts.items())),
        "node_features": node_features,
        "edge_features": edge_features,
        "excluded_warp_features": {
            "node": sorted(WARP_NODE),
            "edge": sorted(WARP_EDGE),
        },
    }


def _new_scope(collect_values: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"count": 0}
    if collect_values:
        result.update(value_domain="complete_observed", values={})
    return result


def _record_scope(scope: dict[str, Any], value: Any, limit: int) -> None:
    scope["count"] += 1
    if _is_empty_observation(value):
        scope["empty_values"] = scope.get("empty_values", 0) + 1
        return
    if scope.get("value_domain") != "complete_observed":
        return
    # TF string and integer feature values use their lexical XML spelling.
    # A TF feature has one declared scalar datatype, not mixed int/string keys.
    key = str(value)
    values = scope["values"]
    if key not in values and len(values) >= limit:
        # Never publish a partial list disguised as a complete domain.
        del scope["values"]
        scope["value_domain"] = "overflow"
        scope["distinct_values_at_least"] = limit + 1
        return
    values[key] = values.get(key, 0) + 1


def inventory_scoped_api(
    api: Any, *, node_value_features: Iterable[str] = (),
    edge_value_features: Iterable[str] = (), domain_limit: int = 512,
) -> dict[str, Any]:
    """Inventory actual native scopes using the loaded TF API.

    All non-warp features and actual directed edge-type pairs are counted.
    Only explicitly selected source-documented categorical families publish
    value labels; free text, identifiers and other open domains do not leak
    into the report. An overflow reports a lower bound, never a partial list.
    This is observation evidence, not an ontology applicability decision.
    """
    if domain_limit < 1:
        raise ValueError("domain_limit must be positive")
    node_value_features = set(node_value_features)
    edge_value_features = set(edge_value_features)
    node_names = sorted(api.Fall(warp=False))
    edge_names = sorted(api.Eall(warp=False))
    if node_value_features - set(node_names):
        raise ValueError(f"Unknown node value features: {sorted(node_value_features - set(node_names))}")
    if edge_value_features - set(edge_names):
        raise ValueError(f"Unknown edge value features: {sorted(edge_value_features - set(edge_names))}")
    otype = api.F.otype

    def node_type(node):
        kind = otype.v(node)
        if not kind:
            raise ValueError(f"Missing node type for TF node {node}")
        return kind

    node_features = {}
    edge_features = {}
    for name in node_names:
        feature = api.Fs(name)
        collect = name in node_value_features
        scopes = {}
        empty = 0
        for node, value in feature.items():
            kind = node_type(node)
            if _is_empty_observation(value):
                empty += 1
                continue
            if kind not in scopes:
                scopes[kind] = _new_scope(collect)
            _record_scope(scopes[kind], value, domain_limit)
        node_features[name] = {
            "scopes": scopes,
            "empty_records": empty,
            "value_type": getattr(feature, "meta", {}).get("valueType"),
            "categorical_values_requested": collect,
        }

    for name in edge_names:
        feature = api.Es(name)
        valued = bool(getattr(feature, "doValues", False))
        collect = name in edge_value_features
        if collect and not valued:
            raise ValueError(f"Cannot inventory values of unvalued edge {name}")
        # TF omap@old-new maps nodes across two different versions. Applying
        # the current otype to old node IDs can fabricate endpoint types.
        if name.startswith("omap@"):
            if collect:
                raise ValueError(f"Cannot inventory local values of cross-version edge {name}")
            edge_features[name] = {
                "valued": valued, "scope_status": "cross_version",
                "edge_count": sum(len(targets) for _, targets in feature.items()),
                "categorical_values_requested": False,
            }
            continue
        pairs = {}
        for source, targets in feature.items():
            source_type = node_type(source)
            iterator = targets.items() if valued else ((target, None) for target in targets)
            for target, value in iterator:
                pair = (source_type, node_type(target))
                if pair not in pairs:
                    pairs[pair] = _new_scope(collect)
                if valued:
                    _record_scope(pairs[pair], value, domain_limit)
                else:
                    pairs[pair]["count"] += 1
        edge_features[name] = {
            "valued": valued,
            "value_type": getattr(feature, "meta", {}).get("valueType"),
            "categorical_values_requested": collect,
            "pairs": [{"from": source, "to": target, **scope}
                      for (source, target), scope in sorted(pairs.items())],
        }

    return {
        "slot_type": getattr(otype, "slotType", None),
        "node_types": dict(sorted(Counter(value for _, value in otype.items()).items())),
        "node_features": node_features,
        "edge_features": edge_features,
        "domain_policy": {
            "limit_per_scope": domain_limit,
            "node_value_features": sorted(node_value_features),
            "edge_value_features": sorted(edge_value_features),
            "empty_string_and_none_records_are_not_domain_members": True,
            "observed_values_are_not_ontology_applicability": True,
        },
        "excluded_warp_features": {"node": sorted(WARP_NODE), "edge": sorted(WARP_EDGE)},
    }


def digest_tf_files(path: Path) -> str:
    """Hash the exact TF feature files in deterministic path/content order."""
    digest = hashlib.sha256()
    files = sorted(
        (candidate for candidate in path.glob("*.tf") if candidate.is_file()),
        key=lambda p: p.name,
    )
    for file in files:
        digest.update(file.name.encode("utf-8"))
        digest.update(b"\0")
        with file.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def load_tf(path: Path) -> Any:
    try:
        from tf.fabric import Fabric
    except ImportError as exc:  # pragma: no cover - environment-dependent integration path
        raise SystemExit(
            "Text-Fabric is required to inventory a corpus. "
            "Install the research baseline with `pip install text-fabric==13.1.0`."
        ) from exc

    fabric = Fabric(locations=str(path), silent="deep")
    api = fabric.loadAll(silent="deep")
    if api is True:
        api = getattr(fabric, "api", None)
    if not api:
        raise SystemExit(f"Could not load Text-Fabric dataset at {path}")
    return api


def build_inventory(
    path: Path,
    *,
    corpus_id: str,
    repository: str | None,
    revision: str | None,
    tf_version: str | None,
    small_domain_limit: int = 64,
) -> dict[str, Any]:
    api = load_tf(path)
    result = inventory_api(api, small_domain_limit=small_domain_limit)
    result.update(
        {
            "schema_version": 1,
            "evidence_kind": "loaded_tf_artifact",
            "corpus_id": corpus_id,
            "repository": repository,
            "revision": revision,
            "tf_version": tf_version,
            "tf_files_sha256": digest_tf_files(path),
            "domain_policy": {
                "small_domain_limit": small_domain_limit,
                "observed_small_domain_is_not_automatically_categorical": True,
                "empty_string_and_none_records_are_not_domain_members": True,
            },
        }
    )
    return result


def scoped_identity(*, corpus_id, repository, revision, tf_version,
                    catalog_version=None, archive_sha256=None):
    """Keep the catalog version (sometimes release ID) distinct from TF version."""
    return dict(schema_version=2, evidence_kind="loaded_tf_scoped_artifact",
                corpus_id=corpus_id, repository=repository, revision=revision,
                tf_version=tf_version, catalog_version=catalog_version or tf_version,
                archive_sha256=archive_sha256)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="directory containing the exact *.tf files")
    parser.add_argument("--corpus-id", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--revision")
    parser.add_argument("--tf-version")
    parser.add_argument("--small-domain-limit", type=int, default=64)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--catalog-version")
    parser.add_argument("--archive-sha256")
    parser.add_argument("--scoped", action="store_true", help="emit scoped empirical census instead of historical R-005 format")
    parser.add_argument("--node-value-features", nargs="*", default=[])
    parser.add_argument("--edge-value-features", nargs="*", default=[])
    parser.add_argument("--domain-limit", type=int, default=512)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.scoped:
        result = inventory_scoped_api(load_tf(args.path),
                                      node_value_features=args.node_value_features,
                                      edge_value_features=args.edge_value_features,
                                      domain_limit=args.domain_limit)
        result.update(scoped_identity(corpus_id=args.corpus_id, repository=args.repository,
                                      revision=args.revision, tf_version=args.tf_version,
                                      catalog_version=args.catalog_version,
                                      archive_sha256=args.archive_sha256))
        result["tf_files_sha256"] = digest_tf_files(args.path)
    else:
        result = build_inventory(
            args.path,
            corpus_id=args.corpus_id,
            repository=args.repository,
            revision=args.revision,
            tf_version=args.tf_version,
            small_domain_limit=args.small_domain_limit,
        )
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
