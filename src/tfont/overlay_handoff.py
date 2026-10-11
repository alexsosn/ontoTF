"""Compact unsealed overlay handoffs, never an offline release authority API."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Callable

from .batch_proposals import compile_candidate_batch, packaged_resource
from .candidate_evidence import CandidateEvidenceResources
from .coverage import load_packaged_coverage_manifest
from .digests import canonical_json_bytes
from .external_review_gate import parse_structured_review
from .published_deltas import _source_bundle_signature
from .release_registry import load_profile
from .review_packets import verify_review_packet


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_overlay_handoff(
    packet: dict[str, Any], ledger: dict[str, Any], observation: dict[str, Any], *,
    resource_loader: Callable[[str], dict[str, Any]] = packaged_resource,
) -> dict[str, Any]:
    """Assemble additions from an observation that is NOT authenticated here.

    Protected CLI authenticates before AND after assembly. Consumers must verify
    external workflow attestation and registry policy, never this JSON alone.
    """
    verify_review_packet(packet, ledger, resource_loader=resource_loader)
    _require(type(observation) is dict and set(observation) == {
        "schema_version", "packet_id", "batch_digest", "repository", "pr_number",
        "approved_head_sha", "reviewer_login", "review_id", "submitted_at",
        "counts", "rows", "provenance",
    }, "invalid handoff review observation fields")
    _require(type(observation["schema_version"]) is int and observation["schema_version"] == 1
             and observation["packet_id"] == packet["packet_id"]
             and observation["batch_digest"] == packet["batch_digest"], "observation packet identity drift")
    adjudication = parse_structured_review("ontoTF-batch-review-v1\n" + json.dumps({
        "packet_digest": observation["batch_digest"], "rows": observation["rows"],
    }))
    expected = {r["mapping_id"]: r["decision_digest"] for r in packet["rows"]}
    actual = {r["mapping_id"]: r["decision_digest"] for r in adjudication["rows"]}
    _require(actual == expected, "observation omitted, added or changed a decision")
    counts = {kind: sum(r["disposition"] == kind for r in adjudication["rows"])
              for kind in ("accept", "reject", "needs-evidence")}
    _require(type(observation["counts"]) is dict and observation["counts"] == counts
             and all(type(n) is int for n in observation["counts"].values()), "observation count drift")
    accepted = {r["mapping_id"] for r in adjudication["rows"] if r["disposition"] == "accept"}
    _require(10 <= len(accepted) <= 50, "handoff requires 10–50 accepted new decisions")
    # Installed locks/resources cannot be replaced via an arbitrary in-memory
    # loader. Supplementary records undergo the same protected anchor checks.
    lock_name = ledger["ontology_lock_resource"]
    _require(resource_loader(lock_name) == packaged_resource(lock_name), "protected ontology lock drift")
    source_names = [s["evidence_resource"] for s in ledger["source_registry"].values()]
    evidence_names = source_names + list(ledger["ontology_evidence_resources"].values())
    evidence_by_name = {name: resource_loader(name) for name in evidence_names}
    supplements = {}
    for name, record in evidence_by_name.items():
        try:
            installed = packaged_resource(name)
        except ValueError:
            supplements[name] = record
        else:
            _require(record == installed, "installed evidence replacement")
    if supplements:
        CandidateEvidenceResources(ledger, supplements)
    compilation = compile_candidate_batch(ledger, resource_loader=resource_loader)
    candidates = [m for m in compilation["candidates"] if m["mapping_id"] in accepted]
    rows = {r["mapping_id"]: r for r in packet["rows"]}
    corpora = []
    for corpus in sorted({m["corpus_id"] for m in candidates}):
        _require(corpus in {"bhsa", "syriac"}, "unsupported protected handoff corpus template")
        base = load_profile(corpus)
        version = base.profile.data["profile_version"]
        _require(version == "0.4.0", "pilot base release changed; explicit migration required")
        coverage_set = f"p004-i027c2-{corpus}-adj-adv-v1"
        coverage = load_packaged_coverage_manifest(coverage_set, corpus)
        item_index = {item["item_id"]: item for item in coverage["semantic_items"]}
        inherited_bindings = [m["native_binding"] for m in base.mappings.data["mappings"]]
        inherited_evidence = {e.data["evidence_id"]: e.data for e in base.evidences}
        inherited_dependencies = {d["dependency_id"]: d for d in base.profile.data["dependencies"]}
        mapping_additions, assignments = [], []
        dependencies, added_evidence, references = {}, {}, {}
        for mapping in (m for m in candidates if m["corpus_id"] == corpus):
            binding = mapping["native_binding"]
            _require(binding not in inherited_bindings, "cannot replace an inherited reviewed native selector")
            row = rows[mapping["mapping_id"]]
            item_id, = row["coverage_item_ids"]
            _require(item_id in item_index and item_index[item_id]["accounting"]["production"] is None,
                     "missing denominator item or already reviewed coverage decision")
            _require(coverage["denominator_source_revision"] == ledger["source_registry"][corpus]["target_corpus_revision"],
                     "coverage/source revision drift")
            source = evidence_by_name[ledger["source_registry"][corpus]["evidence_resource"]]
            native_binding = {"evidence_id": source["evidence_id"], "content_digest": source["content_digest"]}
            dep_id, = mapping["native_dependencies"]
            dependency = {"dependency_id": dep_id, "kind": "native-value-present",
                "component_id": binding["component_id"], "assertion": {
                    "feature": binding["feature"], "node_type": binding["node_type"],
                    "value": binding["value"], "value_semantics": "semantic"}, "evidence": [native_binding]}
            if dep_id in inherited_dependencies:
                _require(dependency == inherited_dependencies[dep_id], "inherited dependency replacement")
            else:
                dependencies[dep_id] = dependency
            for evidence_ref in mapping["evidence"]:
                ident = evidence_ref["evidence_id"]
                records = [(name, record) for name, record in evidence_by_name.items()
                           if record["evidence_id"] == ident]
                _require(len(records) == 1, "ambiguous or absent evidence resource")
                name, record = records[0]
                if ident in inherited_evidence:
                    _require(record == inherited_evidence[ident], "inherited evidence replacement")
                    references[ident] = {"evidence_id": ident, "content_digest": record["content_digest"]}
                else:
                    added_evidence[ident] = {"resource": name, "record": record}
            mapping_additions.append(copy.deepcopy(mapping))
            assignments.append({"item_id": item_id, "mapping_id": mapping["mapping_id"],
                "decision_digest": row["decision_digest"], "assessment": row["assessment"],
                "common_target": bool(mapping["projections"])})
        corpora.append({"corpus_id": corpus, "base_release": version,
            "base_bundle_digest": _source_bundle_signature(base),
            "coverage_base": {"resource_set": coverage_set, "manifest_digest": _digest(coverage),
                              "denominator_digest": coverage["denominator_digest"]},
            "mappings": mapping_additions, "added_dependencies": list(dependencies.values()),
            "added_evidence": [added_evidence[k] for k in sorted(added_evidence)],
            "inherited_evidence": [references[k] for k in sorted(references)],
            "coverage_assignments": assignments})
    pack = {"schema_version": 1, "batch_id": ledger["batch_id"],
        "authority": "requires-workflow-attestation-and-registry-validation", "release_authorized": False,
        "ontology_lock_resource": lock_name, "ontology_lock_digest": _digest(packaged_resource(lock_name)),
        "review_observation": copy.deepcopy(observation), "corpora": corpora,
        "counts": {"exact": sum(m["native_state"] == "positive" for m in candidates),
                   "native-only": sum(m["native_state"] == "native-only" for m in candidates)}}
    pack["content_digest"] = _digest(pack)
    return pack
