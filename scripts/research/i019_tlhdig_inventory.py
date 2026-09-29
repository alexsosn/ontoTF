#!/usr/bin/env python3
"""Inventory an exact shipped TLHdig-TF current artifact without loading TF.

I-019 research intentionally avoids Fabric.loadAll(): the current TLHdig graph
contains millions of nodes and the denominator only needs the materialized
schema, exact artifact identity, node-type census, and selected observed domains.

The script is research tooling, not TFont runtime code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

WARP_NODE = {"otype"}
WARP_EDGE = {"oslots"}
CONFIG_FEATURES = {"otext"}

# These are observations only. Promotion to a bounded semantic vocabulary
# requires separate source/code review.
DOMAIN_PROBES = {
    "add",
    "laes",
    "missing",
    "quot",
    "ras",
    "joined",
    "selected",
    "witness_resolution",
    "mrpsel_kind",
    "join_kind",
    "join_encoding",
    "join_resolved",
    "parse_ok",
    "cu_aligned",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_tf_files(path: Path) -> str:
    """Match the established R-005 deterministic TF-file digest."""
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


def read_header(path: Path) -> tuple[str, bool, dict[str, str]]:
    kind = ""
    valued = False
    metadata: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n\r")
            if not line:
                break
            if line == "@node":
                kind = "node"
            elif line == "@edge":
                kind = "edge"
            elif line == "@config":
                kind = "config"
            elif line == "@edgeValues":
                valued = True
            elif line.startswith("@") and "=" in line:
                key, value = line[1:].split("=", 1)
                metadata[key] = value
    if kind not in {"node", "edge", "config"}:
        raise ValueError(f"{path}: missing supported TF feature-kind header")
    if valued and kind != "edge":
        raise ValueError(f"{path}: @edgeValues on non-edge feature")
    return kind, valued, metadata


def _body_lines(path: Path):
    in_body = False
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n\r")
            if not in_body:
                if line == "":
                    in_body = True
                continue
            if line:
                yield line


def _node_spec_count(spec: str) -> int:
    total = 0
    for part in spec.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty node-spec component in {spec!r}")
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ValueError(f"descending node range: {part}")
            total += end - start + 1
        else:
            int(part)
            total += 1
    return total


def node_type_census(otype: Path) -> dict[str, int]:
    result: Counter[str] = Counter()
    for line in _body_lines(otype):
        fields = line.split("\t")
        if len(fields) != 2:
            raise ValueError(f"unexpected otype body line: {line!r}")
        node_spec, node_type = fields
        result[node_type] += _node_spec_count(node_spec)
    if not result:
        raise ValueError("otype contains no node types")
    return dict(sorted(result.items()))


def observed_domain(path: Path, *, value_type: str, limit: int = 64) -> dict[str, Any]:
    counts: Counter[Any] = Counter()
    records = 0
    for line in _body_lines(path):
        fields = line.split("\t")
        raw = fields[-1]
        if raw == "":
            continue
        records += 1
        value: Any = raw
        if value_type == "int":
            try:
                value = int(raw)
            except ValueError as error:
                raise ValueError(f"{path}: invalid int value {raw!r}") from error
        counts[value] += 1

    ordered = sorted(counts.items(), key=lambda item: (str(type(item[0])), str(item[0])))
    result: dict[str, Any] = {
        "record_lines": records,
        "observed_unique_count": len(ordered),
    }
    if len(ordered) <= limit:
        result["domain_observation"] = "observed_small_domain"
        result["observed_values"] = [value for value, _count in ordered]
        result["observed_frequencies"] = {
            str(value): count for value, count in ordered
        }
    else:
        result["domain_observation"] = "open_or_large_observed_domain"
        sample = sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))[:20]
        result["sample_values"] = [value for value, _count in sample]
    return result


def load_build_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError("BUILD-MANIFEST.json must contain an object")
    return value


def verify_manifest_file_set(tf_dir: Path, manifest: dict[str, Any]) -> None:
    outputs = manifest.get("outputs")
    if type(outputs) is not dict or type(outputs.get("files")) is not dict:
        raise ValueError("BUILD-MANIFEST outputs.files is absent")
    expected = sorted(
        key.removeprefix("main:")
        for key in outputs["files"]
        if key.startswith("main:") and key.endswith(".tf")
    )
    actual = sorted(path.name for path in tf_dir.glob("*.tf") if path.is_file())
    if actual != expected:
        raise ValueError(
            "current TF file set differs from BUILD-MANIFEST: "
            f"missing={sorted(set(expected) - set(actual))} "
            f"extra={sorted(set(actual) - set(expected))}"
        )


def build_inventory(
    tf_dir: Path,
    *,
    repository: str,
    containing_revision: str,
) -> dict[str, Any]:
    manifest_path = tf_dir / "BUILD-MANIFEST.json"
    manifest = load_build_manifest(manifest_path)
    verify_manifest_file_set(tf_dir, manifest)

    tf_files = sorted(path for path in tf_dir.glob("*.tf") if path.is_file())
    features: dict[str, Any] = {}
    for path in tf_files:
        name = path.stem
        kind, valued, metadata = read_header(path)
        item: dict[str, Any] = {
            "kind": kind,
            "valued": valued,
            "value_type": metadata.get("valueType"),
            "description": metadata.get("description"),
            "version": metadata.get("version"),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if name in DOMAIN_PROBES and kind in {"node", "edge"}:
            item["observed_domain"] = observed_domain(
                path,
                value_type=metadata.get("valueType", "str"),
            )
        features[name] = item

    node_features = {
        name: item
        for name, item in features.items()
        if item["kind"] == "node" and name not in WARP_NODE
    }
    edge_features = {
        name: item
        for name, item in features.items()
        if item["kind"] == "edge" and name not in WARP_EDGE
    }
    config_features = {
        name: item
        for name, item in features.items()
        if item["kind"] == "config"
    }
    if set(config_features) != CONFIG_FEATURES:
        raise ValueError(
            f"unexpected config feature set: {sorted(config_features)}"
        )

    outputs = manifest["outputs"]
    provenance_files = sorted(
        key.removeprefix("provenance:")
        for key in outputs["files"]
        if key.startswith("provenance:") and key.endswith(".tf")
    )

    return {
        "schema_version": 1,
        "evidence_kind": "shipped_tf_artifact_headers",
        "corpus_id": "tlhdig",
        "artifact": {
            "repository": repository,
            "containing_revision": containing_revision,
            "tf_version": features["otype"].get("version"),
            "build_manifest_sha256": sha256_file(manifest_path),
            "code_commit": manifest.get("codeCommit"),
            "code_algorithm": manifest.get("code", {}).get("algorithm"),
            "code_digest": manifest.get("code", {}).get("digest"),
            "outputs_algorithm": outputs.get("algorithm"),
            "outputs_digest": outputs.get("digest"),
            "tf_files_sha256": digest_tf_files(tf_dir),
        },
        "slot_type": "sign",
        "node_types": node_type_census(tf_dir / "otype.tf"),
        "node_features": node_features,
        "edge_features": edge_features,
        "excluded_warp_features": {
            "node": sorted(WARP_NODE),
            "edge": sorted(WARP_EDGE),
        },
        "config_features": config_features,
        "optional_provenance_tf_files": provenance_files,
        "counts": {
            "main_tf_files": len(tf_files),
            "node_features_nonwarp": len(node_features),
            "edge_features_nonwarp": len(edge_features),
            "config_features": len(config_features),
            "optional_provenance_tf_files": len(provenance_files),
        },
        "domain_policy": {
            "probed_features": sorted(DOMAIN_PROBES),
            "observed_small_domain_is_not_automatically_categorical": True,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("tf_dir", type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--containing-revision", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_inventory(
        args.tf_dir,
        repository=args.repository,
        containing_revision=args.containing_revision,
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
