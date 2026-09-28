#!/usr/bin/env python3
"""Inventory the exact published Pseudepigrapha-TF release artifact for I-017 research.

Research tooling only. It accepts a local release ZIP, verifies its SHA-256,
loads the materialized Text-Fabric data, and emits a deterministic JSON
inventory. It never downloads corpus data itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from zipfile import ZipFile


BOUNDED_CANDIDATES = (
    "version_kind",
    "is_empty_div",
    "is_gap",
    "is_metadata_only",
    "is_missing_unit_id",
    "is_omission",
    "is_primary",
    "is_source_anomaly",
    "synthetic_witness",
    "undefined_manuscript",
    "w_annotated",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> list[str]:
    with ZipFile(archive) as zf:
        names = [info.filename for info in zf.infolist() if not info.is_dir()]
        root = destination.resolve()
        for name in names:
            candidate = (destination / name).resolve()
            if root not in candidate.parents and candidate != root:
                raise SystemExit(f"unsafe archive member: {name!r}")
        zf.extractall(destination)
    return sorted(names)


def tf_feature_kind(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    header = text.split("\n\n", 1)[0].splitlines()
    if any(line.strip() == "@edge" or line.startswith("@edge") for line in header):
        return "edge"
    if any(line.strip() == "@node" or line.startswith("@node") for line in header):
        return "node"
    return "support"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--release-commit", required=True)
    args = parser.parse_args()

    actual_digest = sha256_file(args.archive)
    if actual_digest != args.expected_sha256:
        raise SystemExit(
            f"release archive SHA-256 mismatch: {actual_digest} != {args.expected_sha256}"
        )

    try:
        from tf.fabric import Fabric
    except ImportError as exc:
        raise SystemExit("Text-Fabric is required for research inventory") from exc

    with tempfile.TemporaryDirectory(prefix="i017-pseudepigrapha-") as tmp:
        root = Path(tmp)
        members = safe_extract(args.archive, root)
        tf_paths = sorted(root.rglob("*.tf"), key=lambda path: path.name)
        if not tf_paths:
            raise SystemExit("release archive contains no .tf feature files")

        locations = sorted({str(path.parent) for path in tf_paths})
        if len(locations) != 1:
            raise SystemExit(f"expected one TF feature directory, got {locations}")
        tf_dir = Path(locations[0])

        TF = Fabric(locations=[str(tf_dir)], modules=[""], silent="deep")
        api = TF.loadAll(silent="deep")
        if api is None:
            raise SystemExit("Text-Fabric failed to load release archive")

        otype_feature = api.TF.features["otype"]
        generic = dict(otype_feature.metaData)
        node_types = sorted(str(value) for value in api.F.otype.all)

        bounded: dict[str, list[object]] = {}
        for name in BOUNDED_CANDIDATES:
            if name not in api.TF.features:
                continue
            feature = api.Fs(name)
            bounded[name] = [value for value, _count in feature.freqList()]

        feature_files = []
        for path in tf_paths:
            feature_files.append(
                {
                    "name": path.stem,
                    "file": path.name,
                    "kind": tf_feature_kind(path),
                    "bytes": path.stat().st_size,
                }
            )

        inventory = {
            "schema_version": 1,
            "source": {
                "repository": "alexsosn/Pseudepigrapha-TF",
                "release_tag": args.release_tag,
                "release_commit": args.release_commit,
                "archive_name": args.archive.name,
                "archive_sha256": actual_digest,
                "tf_version": generic.get("version"),
                "converter_version": generic.get("converterVersion"),
                "upstream_commit": generic.get("upstreamCommit"),
            },
            "members": members,
            "feature_files": feature_files,
            "node_types": node_types,
            "max_slot": api.F.otype.maxSlot,
            "max_node": api.F.otype.maxNode,
            "bounded_candidate_observed_values": bounded,
        }
        print("I017_INVENTORY_BEGIN")
        print(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True))
        print("I017_INVENTORY_END")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
