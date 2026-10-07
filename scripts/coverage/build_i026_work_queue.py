#!/usr/bin/env python3
"""Build the authoritative P-004 semantic accounting work queue.

I-026 governance/accounting tooling only. The builder consumes committed
coverage manifests, committed inventory evidence, and the reviewed routing
policy. It never accesses the network and creates no ontology mapping
authority.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "docs/research/data/i026/p004-routing-policy.json"
OUTPUT = ROOT / "docs/research/data/generated/i026/p004-work-queue.json"
WORKSTREAMS = tuple("CDEFGH")
MODEL_WORKSTREAMS = tuple("CDEFG")
FAMILIES = ("node_types", "node_features", "edge_features")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"expected JSON object: {path}")
    return value


def _utf16_key(value: str) -> bytes:
    return value.encode("utf-16-be", errors="surrogatepass")


def _json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _item_base(item_id: str, kind: str) -> str:
    prefix = kind + ":"
    if not item_id.startswith(prefix):
        raise ValueError(f"item identity/kind mismatch: {kind} {item_id}")
    payload = item_id[len(prefix) :]
    if kind in {"node_value", "edge_value"}:
        if "=" not in payload:
            raise ValueError(f"value item lacks '=' separator: {item_id}")
        return payload.split("=", 1)[0]
    return payload


def _family(kind: str) -> str:
    if kind == "node_type":
        return "node_types"
    if kind in {"node_feature", "node_value"}:
        return "node_features"
    if kind in {"edge_feature", "edge_value"}:
        return "edge_features"
    raise ValueError(f"unsupported I-026 semantic item kind: {kind}")


def _selected_assessments(item: dict[str, Any]) -> set[str]:
    accounting = item.get("accounting")
    if type(accounting) is not dict:
        return set()
    result: set[str] = set()
    for authority in ("production", "research"):
        selected = accounting.get(authority)
        if type(selected) is dict:
            assessments = selected.get("assessments", [])
            if type(assessments) is list:
                result.update(value for value in assessments if type(value) is str)
    return result


def _present_bases(manifest: dict[str, Any]) -> dict[str, set[str]]:
    result = {family: set() for family in FAMILIES}
    semantic_items = manifest.get("semantic_items")
    if type(semantic_items) is not list:
        raise ValueError("manifest semantic_items must be a list")
    seen: set[str] = set()
    for item in semantic_items:
        if type(item) is not dict:
            raise ValueError("semantic item must be an object")
        item_id = item.get("item_id")
        kind = item.get("kind")
        if type(item_id) is not str or type(kind) is not str:
            raise ValueError("semantic item identity/kind must be strings")
        if item_id in seen:
            raise ValueError(f"duplicate semantic item identity: {item_id}")
        seen.add(item_id)
        result[_family(kind)].add(_item_base(item_id, kind))
    return result


def _exact_name_list(value: Any, *, label: str) -> list[str]:
    if type(value) is not list or any(type(item) is not str or not item for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicate values")
    return list(value)


def _build_policy_indexes(
    corpus_id: str,
    corpus_policy: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str], str]]:
    present = _present_bases(manifest)
    primary: dict[tuple[str, str], str] = {}

    routes = corpus_policy.get("routes", {})
    if type(routes) is not dict:
        raise ValueError(f"{corpus_id}: routes must be an object")
    for workstream in MODEL_WORKSTREAMS:
        spec = routes.get(workstream, {})
        if type(spec) is not dict:
            raise ValueError(f"{corpus_id}: route {workstream} must be an object")
        for family in FAMILIES:
            names = _exact_name_list(
                spec.get(family, []),
                label=f"{corpus_id} {workstream} {family}",
            )
            for name in names:
                if name not in present[family]:
                    raise ValueError(
                        f"{corpus_id}: route references absent native identity "
                        f"{family}:{name}"
                    )
                key = (family, name)
                previous = primary.get(key)
                if previous is not None:
                    raise ValueError(
                        f"{corpus_id}: multiple primary routes for {family}:{name}: "
                        f"{previous}, {workstream}"
                    )
                primary[key] = workstream

    h_index: dict[tuple[str, str], str] = {}
    buckets = corpus_policy.get("h_buckets", {})
    if type(buckets) is not dict:
        raise ValueError(f"{corpus_id}: h_buckets must be an object")
    allowed_buckets = {
        "cross-model",
        "native-only-candidate",
        "unsupported-candidate",
        "needs-focused-research",
    }
    for bucket, spec in buckets.items():
        if bucket not in allowed_buckets:
            raise ValueError(f"{corpus_id}: unsupported H bucket: {bucket}")
        if type(spec) is not dict:
            raise ValueError(f"{corpus_id}: H bucket {bucket} must be an object")
        for family in FAMILIES:
            names = _exact_name_list(
                spec.get(family, []),
                label=f"{corpus_id} H {bucket} {family}",
            )
            for name in names:
                if name not in present[family]:
                    raise ValueError(
                        f"{corpus_id}: H bucket references absent native identity "
                        f"{family}:{name}"
                    )
                key = (family, name)
                if key in primary:
                    raise ValueError(
                        f"{corpus_id}: H bucket overlaps model route for {family}:{name}"
                    )
                if key in h_index:
                    raise ValueError(
                        f"{corpus_id}: duplicate H bucket for {family}:{name}"
                    )
                h_index[key] = bucket
    return primary, h_index


def _evidence_pointer(
    evidence: dict[str, Any],
    *,
    item_id: str,
    kind: str,
) -> str:
    base = _item_base(item_id, kind)
    family = _family(kind)
    token = _json_pointer_token(base)

    if family == "node_types":
        node_types = evidence.get("node_types")
        if type(node_types) is dict and base in node_types:
            return f"/node_types/{token}"
        raise ValueError(f"evidence lacks node type {base}: {item_id}")

    if family == "edge_features":
        edge_features = evidence.get("edge_features")
        if type(edge_features) is dict and base in edge_features:
            return f"/edge_features/{token}"
        raise ValueError(f"evidence lacks edge feature {base}: {item_id}")

    node_features = evidence.get("node_features")
    if type(node_features) is dict and base in node_features:
        return f"/node_features/{token}"

    for key in ("core_node_features", "optional_provenance_node_features"):
        values = evidence.get(key)
        if type(values) is list and base in values:
            return f"/{key}/{values.index(base)}"

    raise ValueError(f"evidence lacks node feature {base}: {item_id}")


def _validate_manifest_binding(
    corpus_id: str,
    corpus_policy: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    checks = (
        ("repository", "repository", "repository"),
        ("denominator_digest", "denominator_digest", "denominator digest"),
        (
            "denominator_source_revision",
            "denominator_source_revision",
            "denominator source revision",
        ),
        ("target_corpus_revision", "target_corpus_revision", "target revision"),
    )
    for policy_key, manifest_key, label in checks:
        if manifest.get(manifest_key) != corpus_policy.get(policy_key):
            raise ValueError(
                f"{corpus_id}: {label} drifted: "
                f"policy={corpus_policy.get(policy_key)!r} "
                f"manifest={manifest.get(manifest_key)!r}"
            )
    if manifest.get("scope_quality") != "machine-exhaustive":
        raise ValueError(f"{corpus_id}: scope is not machine-exhaustive")
    if manifest.get("denominator_source_revision") != manifest.get(
        "target_corpus_revision"
    ):
        raise ValueError(f"{corpus_id}: denominator is stale")
    basis = manifest.get("denominator_basis")
    if type(basis) is not dict:
        raise ValueError(f"{corpus_id}: denominator_basis is absent")
    if basis.get("source") != corpus_policy.get("evidence_source"):
        raise ValueError(f"{corpus_id}: denominator evidence source drifted")


def _h_bucket(
    item: dict[str, Any],
    *,
    explicit: str | None,
) -> tuple[str, str]:
    if explicit is not None:
        return explicit, "explicit-h-policy"
    assessments = _selected_assessments(item)
    if assessments == {"native-only"}:
        return "native-only-candidate", "existing-reviewed-accounting"
    if assessments == {"unsupported"}:
        return "unsupported-candidate", "existing-reviewed-accounting"
    return "needs-focused-research", "conservative-residual"


def _route_gap(
    policy_gap: dict[str, Any],
    *,
    manifest_gap: dict[str, Any],
    evidence: dict[str, Any],
    workstreams: dict[str, Any],
) -> dict[str, Any]:
    workstream = policy_gap.get("workstream")
    if workstream not in WORKSTREAMS:
        raise ValueError(f"accounting gap has invalid workstream: {workstream}")
    expected_issue = workstreams[workstream]["owner_issue"]
    if policy_gap.get("owner_issue") != expected_issue:
        raise ValueError("accounting gap owner issue does not match workstream")
    feature = policy_gap.get("evidence_feature")
    if type(feature) is not str or not feature:
        raise ValueError("accounting gap evidence_feature is absent")
    pointer = _evidence_pointer(
        evidence,
        item_id=f"node_feature:{feature}",
        kind="node_feature",
    )
    result = copy.deepcopy(policy_gap)
    result["evidence_pointer"] = pointer
    result["existing_gap"] = copy.deepcopy(manifest_gap)
    return result


def build_queue(*, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = copy.deepcopy(policy) if policy is not None else load_json(POLICY_PATH)
    if policy.get("schema_version") != 1:
        raise ValueError("I-026 policy schema_version must be 1")
    if policy.get("policy_id") != "p004-routing-v1":
        raise ValueError("I-026 policy_id drifted")

    corpus_order = _exact_name_list(policy.get("corpus_order"), label="corpus_order")
    corpus_policies = policy.get("corpora")
    workstreams = policy.get("workstreams")
    if type(corpus_policies) is not dict or set(corpus_policies) != set(corpus_order):
        raise ValueError("policy corpora do not exactly match corpus_order")
    if type(workstreams) is not dict or set(workstreams) != set(WORKSTREAMS):
        raise ValueError("workstream policy must define exactly C-H")

    rows: list[dict[str, Any]] = []
    manifest_bindings: dict[str, Any] = {}
    technical_exclusions: dict[str, list[str]] = {}
    per_corpus: dict[str, dict[str, int]] = {}
    manifest_gaps: dict[tuple[str, str, str], dict[str, Any]] = {}
    evidence_by_corpus: dict[str, dict[str, Any]] = {}

    for corpus_id in corpus_order:
        corpus_policy = corpus_policies[corpus_id]
        if type(corpus_policy) is not dict:
            raise ValueError(f"{corpus_id}: corpus policy must be an object")
        manifest_path = ROOT / corpus_policy["manifest"]
        manifest = load_json(manifest_path)
        _validate_manifest_binding(corpus_id, corpus_policy, manifest)
        if manifest.get("corpus_id") != corpus_id:
            raise ValueError(f"{corpus_id}: manifest corpus_id drifted")

        evidence_path = ROOT / corpus_policy["evidence_source"]
        evidence = load_json(evidence_path)
        evidence_by_corpus[corpus_id] = evidence
        primary, h_index = _build_policy_indexes(corpus_id, corpus_policy, manifest)

        semantic_items = manifest["semantic_items"]
        semantic_ids = {item["item_id"] for item in semantic_items}
        technical = manifest.get("technical_exclusions", [])
        if type(technical) is not list:
            raise ValueError(f"{corpus_id}: technical_exclusions must be a list")
        technical_ids = [item["item_id"] for item in technical]
        if len(technical_ids) != len(set(technical_ids)):
            raise ValueError(f"{corpus_id}: duplicate technical exclusion")
        overlap = semantic_ids & set(technical_ids)
        if overlap:
            raise ValueError(
                f"{corpus_id}: semantic/technical overlap: {sorted(overlap)}"
            )
        technical_exclusions[corpus_id] = sorted(technical_ids, key=_utf16_key)

        counts = {workstream: 0 for workstream in WORKSTREAMS}
        for item in sorted(semantic_items, key=lambda row: _utf16_key(row["item_id"])):
            item_id = item["item_id"]
            kind = item["kind"]
            family = _family(kind)
            base = _item_base(item_id, kind)

            if kind == "node_value":
                parent = f"node_feature:{base}"
                if parent not in semantic_ids:
                    raise ValueError(
                        f"{corpus_id}: node value lacks semantic parent feature: {item_id}"
                    )
            elif kind == "edge_value":
                parent = f"edge_feature:{base}"
                if parent not in semantic_ids:
                    raise ValueError(
                        f"{corpus_id}: edge value lacks semantic parent feature: {item_id}"
                    )

            workstream = primary.get((family, base), "H")
            if workstream == "H":
                bucket, basis = _h_bucket(
                    item,
                    explicit=h_index.get((family, base)),
                )
            else:
                bucket = "model-workstream"
                basis = "explicit-corpus-policy"

            workstream_spec = workstreams[workstream]
            pointer = _evidence_pointer(
                evidence,
                item_id=item_id,
                kind=kind,
            )
            rows.append(
                {
                    "corpus_id": corpus_id,
                    "item_id": item_id,
                    "kind": kind,
                    "workstream": workstream,
                    "owner_issue": workstream_spec["owner_issue"],
                    "candidate_profile": workstream_spec["candidate_profile"],
                    "routing_bucket": bucket,
                    "routing_basis": basis,
                    "evidence_source": corpus_policy["evidence_source"],
                    "evidence_pointer": pointer,
                    "existing_accounting": copy.deepcopy(item.get("accounting")),
                }
            )
            counts[workstream] += 1

        expected_counts = corpus_policy.get("expected_counts")
        if counts != expected_counts:
            raise ValueError(
                f"{corpus_id}: route counts drifted: expected={expected_counts!r} "
                f"actual={counts!r}"
            )
        per_corpus[corpus_id] = counts
        manifest_bindings[corpus_id] = {
            "manifest": corpus_policy["manifest"],
            "repository": manifest["repository"],
            "denominator_digest": manifest["denominator_digest"],
            "denominator_source_revision": manifest["denominator_source_revision"],
            "target_corpus_revision": manifest["target_corpus_revision"],
            "evidence_source": corpus_policy["evidence_source"],
            "semantic_items": len(semantic_items),
            "technical_exclusions": len(technical_ids),
        }
        for gap in manifest.get("accounting_gaps", []):
            key = (corpus_id, gap.get("item_id"), gap.get("reason"))
            if key in manifest_gaps:
                raise ValueError(f"{corpus_id}: duplicate accounting gap: {key}")
            manifest_gaps[key] = gap

    policy_gaps = policy.get("accounting_gaps")
    if type(policy_gaps) is not list:
        raise ValueError("policy accounting_gaps must be a list")
    policy_gap_keys: set[tuple[str, str, str]] = set()
    routed_gaps: list[dict[str, Any]] = []
    for gap in policy_gaps:
        if type(gap) is not dict:
            raise ValueError("accounting gap route must be an object")
        corpus_id = gap.get("corpus_id")
        key = (corpus_id, gap.get("item_id"), gap.get("reason"))
        if key in policy_gap_keys:
            raise ValueError(f"duplicate accounting gap route: {key}")
        policy_gap_keys.add(key)
        manifest_gap = manifest_gaps.get(key)
        if manifest_gap is None:
            raise ValueError(f"accounting gap route has no manifest gap: {key}")
        if gap.get("evidence_source") != corpus_policies[corpus_id]["evidence_source"]:
            raise ValueError(f"accounting gap evidence source drifted: {key}")
        routed_gaps.append(
            _route_gap(
                gap,
                manifest_gap=manifest_gap,
                evidence=evidence_by_corpus[corpus_id],
                workstreams=workstreams,
            )
        )
    if policy_gap_keys != set(manifest_gaps):
        missing = sorted(set(manifest_gaps) - policy_gap_keys)
        extra = sorted(policy_gap_keys - set(manifest_gaps))
        raise ValueError(
            f"accounting gap routing mismatch: missing={missing!r} extra={extra!r}"
        )

    aggregate = {workstream: 0 for workstream in WORKSTREAMS}
    for counts in per_corpus.values():
        for workstream, count in counts.items():
            aggregate[workstream] += count

    technical_count = sum(len(values) for values in technical_exclusions.values())
    queue: dict[str, Any] = {
        "schema_version": 1,
        "policy_id": policy["policy_id"],
        "manifest_bindings": manifest_bindings,
        "semantic_rows": rows,
        "technical_exclusions": technical_exclusions,
        "accounting_gaps": routed_gaps,
        "counts": {
            "per_corpus": per_corpus,
            "aggregate_workstreams": aggregate,
            "technical_exclusions": technical_count,
        },
        "invariants": {
            "semantic_items": len(rows),
            "zero_orphans": all(row["workstream"] in WORKSTREAMS for row in rows),
            "unique_primary_owner": len(rows)
            == len({(row["corpus_id"], row["item_id"]) for row in rows}),
            "technical_disjoint": True,
        },
    }
    validate_queue(queue, policy=policy)
    return queue


def validate_queue(
    queue: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
) -> None:
    policy = policy if policy is not None else load_json(POLICY_PATH)
    rows = queue.get("semantic_rows")
    technical = queue.get("technical_exclusions")
    if type(rows) is not list or type(technical) is not dict:
        raise ValueError("queue semantic_rows/technical_exclusions shape is invalid")

    expected_items = policy.get("expected_semantic_items")
    if len(rows) != expected_items:
        raise ValueError(
            f"semantic item count drifted: expected={expected_items} actual={len(rows)}"
        )
    keys = [(row.get("corpus_id"), row.get("item_id")) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate primary owner row")

    workstreams = policy["workstreams"]
    recomputed_per_corpus = {
        corpus_id: {workstream: 0 for workstream in WORKSTREAMS}
        for corpus_id in policy["corpus_order"]
    }
    semantic_keys: set[tuple[str, str]] = set()
    for row in rows:
        corpus_id = row.get("corpus_id")
        item_id = row.get("item_id")
        workstream = row.get("workstream")
        if corpus_id not in recomputed_per_corpus:
            raise ValueError(f"unknown corpus in queue row: {corpus_id}")
        if workstream not in workstreams:
            raise ValueError(f"unknown workstream in queue row: {workstream}")
        if row.get("owner_issue") != workstreams[workstream]["owner_issue"]:
            raise ValueError("queue owner issue/workstream mismatch")
        if not row.get("evidence_source") or not row.get("evidence_pointer"):
            raise ValueError("queue row lacks evidence trace")
        recomputed_per_corpus[corpus_id][workstream] += 1
        semantic_keys.add((corpus_id, item_id))

    technical_keys: set[tuple[str, str]] = set()
    for corpus_id, item_ids in technical.items():
        if corpus_id not in recomputed_per_corpus or type(item_ids) is not list:
            raise ValueError("technical exclusion corpus/list shape is invalid")
        for item_id in item_ids:
            key = (corpus_id, item_id)
            if key in technical_keys:
                raise ValueError("duplicate technical exclusion identity")
            technical_keys.add(key)

    overlap = semantic_keys & technical_keys
    if overlap:
        raise ValueError(f"semantic/technical overlap: {sorted(overlap)!r}")

    expected_technical = policy.get("expected_technical_exclusions")
    if len(technical_keys) != expected_technical:
        raise ValueError(
            f"technical exclusion count drifted: expected={expected_technical} "
            f"actual={len(technical_keys)}"
        )

    stored_counts = queue.get("counts")
    if type(stored_counts) is not dict:
        raise ValueError("queue counts object is absent")
    if stored_counts.get("per_corpus") != recomputed_per_corpus:
        raise ValueError("stored per-corpus route counts drifted")

    aggregate = {workstream: 0 for workstream in WORKSTREAMS}
    for counts in recomputed_per_corpus.values():
        for workstream, count in counts.items():
            aggregate[workstream] += count
    if stored_counts.get("aggregate_workstreams") != aggregate:
        raise ValueError("stored aggregate route counts drifted")
    if stored_counts.get("technical_exclusions") != len(technical_keys):
        raise ValueError("stored technical exclusion count drifted")

    invariants = queue.get("invariants")
    if type(invariants) is not dict:
        raise ValueError("queue invariants object is absent")
    if invariants.get("semantic_items") != len(rows):
        raise ValueError("stored semantic invariant count drifted")
    if not invariants.get("zero_orphans"):
        raise ValueError("queue reports orphan semantic items")
    if not invariants.get("unique_primary_owner"):
        raise ValueError("queue reports duplicate primary owners")
    if not invariants.get("technical_disjoint"):
        raise ValueError("queue reports semantic/technical overlap")


def serialized(queue: dict[str, Any]) -> str:
    return json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def check_output(queue: dict[str, Any]) -> None:
    try:
        existing = OUTPUT.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"I-026 generated work queue is missing: {error}") from error
    current = serialized(queue)
    if existing != current:
        raise SystemExit("I-026 generated work queue is stale")


def write_output(queue: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialized(queue), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queue = build_queue()
    if args.stdout:
        print(serialized(queue), end="")
    elif args.check:
        check_output(queue)
    else:
        write_output(queue)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
