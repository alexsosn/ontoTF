#!/usr/bin/env python3
"""Inventory the exact shipped TLHdig-TF 0.4.0 core + provenance schema.

Research tooling only. It verifies the repository BUILD-MANIFEST and inventories
feature headers plus otype without importing Text-Fabric or loading the 3.4M-slot
graph. Value-vocabulary closure is reviewed from converter source separately;
raw .tf serialization lines are deliberately not treated as semantic values.
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
CONFIG = {"otext"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_tf_files(path: Path) -> str:
    h = hashlib.sha256()
    for file in sorted(path.glob("*.tf"), key=lambda p: p.name):
        if not file.is_file():
            continue
        h.update(file.name.encode("utf-8"))
        h.update(b"\0")
        with file.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        h.update(b"\0")
    return h.hexdigest()


def digest_tf_modules(modules: tuple[tuple[str, Path], ...]) -> str:
    """Hash all materialized TF modules with module-qualified paths."""
    h = hashlib.sha256()
    for module, directory in modules:
        for file in sorted(directory.glob("*.tf"), key=lambda p: p.name):
            if not file.is_file():
                continue
            h.update(f"{module}/{file.name}".encode("utf-8"))
            h.update(b"\\0")
            with file.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
            h.update(b"\\0")
    return h.hexdigest()


def read_header(path: Path) -> dict[str, Any]:
    markers: set[str] = set()
    metadata: dict[str, str] = {}
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            if not line:
                break
            if not line.startswith("@"):
                raise ValueError(f"{path}: malformed header line {line!r}")
            body = line[1:]
            if "=" in body:
                key, value = body.split("=", 1)
                metadata[key] = value
            else:
                markers.add(body)
    kinds = [name for name in ("node", "edge", "config") if name in markers]
    if len(kinds) != 1:
        raise ValueError(f"{path}: expected one node/edge/config marker; got {kinds}")
    if "edgeValues" in markers and kinds[0] != "edge":
        raise ValueError(f"{path}: edgeValues without edge")
    return {
        "kind": kinds[0],
        "valued": "edgeValues" in markers,
        "metadata": dict(sorted(metadata.items())),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def otype_inventory(path: Path) -> tuple[str, dict[str, int]]:
    """Decode otype.tf's simple range form and recover the contiguous slot type."""
    counts: Counter[str] = Counter()
    slot_type: str | None = None
    in_body = False
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            if not in_body:
                if not line:
                    in_body = True
                continue
            if not line:
                continue
            fields = line.split("\t")
            if len(fields) == 1:
                # TF node feature compression: one value means the next node.
                value = fields[0]
                if slot_type is None:
                    slot_type = value
                counts[value] += 1
                continue
            if len(fields) == 2:
                node_spec, value = fields
                if slot_type is None:
                    slot_type = value
                if "-" in node_spec:
                    start, end = node_spec.split("-", 1)
                    counts[value] += int(end) - int(start) + 1
                else:
                    counts[value] += 1
                continue
            raise ValueError(f"{path}: unsupported otype body record: {line!r}")
    if not counts or slot_type is None:
        raise ValueError(f"{path}: empty otype census")
    return slot_type, dict(sorted(counts.items()))


def _manifest_output_sets(manifest: dict[str, Any]) -> tuple[set[str], set[str]]:
    files = manifest["outputs"]["files"]
    main = {
        key.removeprefix("main:")
        for key in files
        if key.startswith("main:") and key.endswith(".tf")
    }
    provenance = {
        key.removeprefix("provenance:")
        for key in files
        if key.startswith("provenance:") and key.endswith(".tf")
    }
    return main, provenance


def _inventory_dir(path: Path) -> dict[str, dict[str, Any]]:
    return {
        file.stem: read_header(file)
        for file in sorted(path.glob("*.tf"), key=lambda p: p.name)
        if file.is_file()
    }


def build_inventory(
    core_dir: Path,
    provenance_dir: Path,
    *,
    repository: str,
    containing_revision: str,
) -> dict[str, Any]:
    manifest_path = core_dir / "BUILD-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["tfVersion"] != core_dir.name:
        raise ValueError("BUILD-MANIFEST tfVersion does not match core directory")

    core = _inventory_dir(core_dir)
    provenance = _inventory_dir(provenance_dir)
    expected_main, expected_provenance = _manifest_output_sets(manifest)
    if set(file.name for file in core_dir.glob("*.tf")) != expected_main:
        raise ValueError("core TF file set differs from BUILD-MANIFEST outputs")
    if set(file.name for file in provenance_dir.glob("*.tf")) != expected_provenance:
        raise ValueError("provenance TF file set differs from BUILD-MANIFEST outputs")

    if set(core) & set(provenance):
        raise ValueError(f"feature name collision across modules: {sorted(set(core) & set(provenance))}")

    node_features = {
        name: row for name, row in core.items()
        if row["kind"] == "node" and name not in WARP_NODE
    }
    edge_features = {
        name: row for name, row in core.items()
        if row["kind"] == "edge" and name not in WARP_EDGE
    }
    config_features = {
        name: row for name, row in core.items()
        if row["kind"] == "config"
    }
    provenance_nodes = {
        name: row for name, row in provenance.items()
        if row["kind"] == "node"
    }
    unexpected_provenance = {
        name: row["kind"] for name, row in provenance.items()
        if row["kind"] != "node"
    }
    if unexpected_provenance:
        raise ValueError(f"unexpected non-node provenance features: {unexpected_provenance}")

    slot_type, node_types = otype_inventory(core_dir / "otype.tf")

    return {
        "schema_version": 1,
        "evidence_kind": "shipped_tf_artifact_headers",
        "corpus_id": "tlhdig",
        "artifact": {
            "repository": repository,
            "containing_revision": containing_revision,
            "tf_version": manifest["tfVersion"],
            "source_version": manifest["sourceVersion"],
            "build_manifest_sha256": sha256_file(manifest_path),
            "code_commit": manifest["codeCommit"],
            "code_algorithm": manifest["code"]["algorithm"],
            "code_digest": manifest["code"]["digest"],
            "outputs_algorithm": manifest["outputs"]["algorithm"],
            "outputs_digest": manifest["outputs"]["digest"],
            "core_tf_files_sha256": digest_tf_files(core_dir),
            "provenance_tf_files_sha256": digest_tf_files(provenance_dir),
            "materialized_tf_files_sha256": digest_tf_modules(
                (("core", core_dir), ("provenance", provenance_dir))
            ),
        },
        "slot_type": slot_type,
        "node_types": node_types,
        "node_features": node_features,
        "optional_provenance_node_features": provenance_nodes,
        "edge_features": edge_features,
        "excluded_warp_features": {
            "node": sorted(WARP_NODE),
            "edge": sorted(WARP_EDGE),
        },
        "config_features": config_features,
        "counts": {
            "node_types": len(node_types),
            "core_node_features_nonwarp": len(node_features),
            "optional_provenance_node_features": len(provenance_nodes),
            "edge_features_nonwarp": len(edge_features),
            "main_tf_files": len(core),
            "provenance_tf_files": len(provenance),
        },
        "domain_policy": {
            "tf_body_lines_are_not_semantic_domain_evidence": True,
            "closed_value_families_require_converter_source_review": True,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("core_dir", type=Path)
    parser.add_argument("--provenance-dir", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_inventory(
        args.core_dir,
        args.provenance_dir,
        repository=args.repository,
        containing_revision=args.revision,
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
