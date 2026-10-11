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
        inherited_mapping_ids = {m["mapping_id"] for m in base.mappings.data["mappings"]}
        inherited_projection_ids = {p["projection_id"] for m in base.mappings.data["mappings"]
                                    for p in m["projections"]}
        inherited_evidence = {e.data["evidence_id"]: e.data for e in base.evidences}
        inherited_dependencies = {d["dependency_id"]: d for d in base.profile.data["dependencies"]}
        mapping_additions, assignments = [], []
        dependencies, added_evidence, references = {}, {}, {}
        for mapping in (m for m in candidates if m["corpus_id"] == corpus):
            _require(mapping["mapping_id"] not in inherited_mapping_ids,
                     "cannot replace an inherited mapping identity")
            _require(not any(p["projection_id"] in inherited_projection_ids for p in mapping["projections"]),
                     "cannot replace an inherited projection identity")
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


def verify_overlay_handoff_integrity(pack: dict[str, Any]) -> None:
    """Check *only* structural/immutable-base integrity of an unsealed handoff.

    This function is intentionally NOT approval, attestation verification, a
    trusted release builder, or an install/semantic bundle loader. A malicious
    author can recompute hashes: only the protected live GitHub review gate and
    trusted workflow attestation can establish the external review principal.
    """
    from .digests import evidence_record_digest
    from .semantic_digest_v2 import (
        mapping_semantic_digest_v2, projection_semantic_digest_v1,
    )

    _require(type(pack) is dict and set(pack) == {
        "schema_version", "batch_id", "authority", "release_authorized",
        "ontology_lock_resource", "ontology_lock_digest", "review_observation",
        "corpora", "counts", "content_digest",
    }, "invalid unsealed overlay fields")
    _require(type(pack["schema_version"]) is int and pack["schema_version"] == 1
             and pack["authority"] == "requires-workflow-attestation-and-registry-validation"
             and type(pack["release_authorized"]) is bool
             and pack["release_authorized"] is False,
             "overlay has unsupported schema or forged release authority")
    _require(type(pack["content_digest"]) is str
             and pack["content_digest"] == _digest({
                 key: value for key, value in pack.items() if key != "content_digest"
             }), "overlay envelope checksum mismatch")

    observation = pack["review_observation"]
    _require(type(observation) is dict and set(observation) == {
        "schema_version", "packet_id", "batch_digest", "repository", "pr_number",
        "approved_head_sha", "reviewer_login", "review_id", "submitted_at",
        "counts", "rows", "provenance",
    }, "invalid unsealed review observation fields")
    _require(type(observation["schema_version"]) is int
             and observation["schema_version"] == 1,
             "invalid review observation version")
    parsed = parse_structured_review("ontoTF-batch-review-v1\n" + json.dumps({
        "packet_digest": observation["batch_digest"],
        "rows": observation["rows"],
    }))
    decisions = {row["mapping_id"]: row for row in parsed["rows"]}
    _require(type(observation["counts"]) is dict
             and set(observation["counts"]) == {"accept", "reject", "needs-evidence"}
             and all(type(v) is int and v >= 0
                     for v in observation["counts"].values())
             and all(observation["counts"][state] ==
                     sum(row["disposition"] == state for row in decisions.values())
                     for state in observation["counts"]),
             "unsealed observation row-count mismatch")
    accepted = {mapping_id: row for mapping_id, row in decisions.items()
                if row["disposition"] == "accept"}
    _require(10 <= len(accepted) <= 50, "unsealed batch must contain 10-50 accepts")
    _require(type(pack["batch_id"]) is str and pack["batch_id"]
             and observation["packet_id"] == "review-request:" + pack["batch_id"],
             "unsealed packet/batch identity drift")

    _require(type(pack["ontology_lock_resource"]) is str
             and pack["ontology_lock_resource"].startswith("resources/ontologies/olia/")
             and _digest(packaged_resource(pack["ontology_lock_resource"]))
                 == pack["ontology_lock_digest"],
             "unsealed ontology lock not a pinned installed resource")
    lock = packaged_resource(pack["ontology_lock_resource"])

    _require(type(pack["counts"]) is dict and set(pack["counts"]) == {
        "exact", "native-only",
    }, "unsealed mapping counts malformed")
    _require(type(pack["corpora"]) is list and 1 <= len(pack["corpora"]) <= 2,
             "unsupported unsealed pilot corpus count")
    corpora_seen, mapping_ids, coverage_keys = set(), set(), set()
    counts = {"exact": 0, "native-only": 0}
    for corpus_pack in pack["corpora"]:
        _require(type(corpus_pack) is dict and set(corpus_pack) == {
            "corpus_id", "base_release", "base_bundle_digest", "coverage_base",
            "mappings", "added_dependencies", "added_evidence",
            "inherited_evidence", "coverage_assignments",
        }, "unsealed per-corpus fields malformed")
        corpus = corpus_pack["corpus_id"]
        _require(type(corpus) is str and corpus in {"bhsa", "syriac"}
                 and corpus not in corpora_seen,
                 "duplicate or unsupported unsealed corpus identity")
        corpora_seen.add(corpus)
        base = load_profile(corpus)
        _require(corpus_pack["base_release"] == "0.4.0"
                 and base.profile.data["profile_version"] == "0.4.0"
                 and corpus_pack["base_bundle_digest"] == _source_bundle_signature(base),
                 "unsealed installed base bundle mismatch")

        coverage_set = f"p004-i027c2-{corpus}-adj-adv-v1"
        coverage = load_packaged_coverage_manifest(coverage_set, corpus)
        spec = corpus_pack["coverage_base"]
        _require(type(spec) is dict and set(spec) == {
            "resource_set", "manifest_digest", "denominator_digest",
        } and spec == {
            "resource_set": coverage_set,
            "manifest_digest": _digest(coverage),
            "denominator_digest": coverage["denominator_digest"],
        }, "unsealed coverage base/denominator mismatch")
        covered = {row["item_id"]: row for row in coverage["semantic_items"]}
        original_ids = {m["mapping_id"] for m in base.mappings.data["mappings"]}
        original_bindings = [m["native_binding"] for m in base.mappings.data["mappings"]]
        original_deps = {d["dependency_id"]: d for d in base.profile.data["dependencies"]}
        original_evidence = {e.data["evidence_id"]: e.data for e in base.evidences}

        added_evidence = {}
        _require(type(corpus_pack["added_evidence"]) is list
                 and type(corpus_pack["inherited_evidence"]) is list,
                 "unsealed evidence lists malformed")
        for entry in corpus_pack["added_evidence"]:
            _require(type(entry) is dict and set(entry) == {"resource", "record"}
                     and type(entry["resource"]) is str
                     and entry["resource"].startswith(f"resources/profiles/{corpus}/")
                     and entry["resource"].endswith(".json")
                     and all(part not in {"", ".", ".."}
                             for part in entry["resource"].split("/")),
                     "unsealed new evidence path malformed")
            record = entry["record"]
            _require(type(record) is dict
                     and record.get("content_mode") == "normalized-record"
                     and record.get("content_digest") == evidence_record_digest(record)
                     and type(record.get("evidence_id")) is str
                     and record["evidence_id"] not in added_evidence
                     and record["evidence_id"] not in original_evidence,
                     "unsealed new evidence invalid or shadows installed evidence")
            added_evidence[record["evidence_id"]] = record
        inherited = set()
        for ref in corpus_pack["inherited_evidence"]:
            _require(type(ref) is dict
                     and set(ref) == {"evidence_id", "content_digest"}
                     and type(ref["evidence_id"]) is str
                     and ref["evidence_id"] in original_evidence
                     and original_evidence[ref["evidence_id"]]["content_digest"]
                         == ref["content_digest"]
                     and ref["evidence_id"] not in inherited,
                     "unsealed inherited evidence drift or duplicate")
            inherited.add(ref["evidence_id"])

        _require(type(corpus_pack["added_dependencies"]) is list,
                 "unsealed dependency list invalid")
        added_deps = {}
        for dep in corpus_pack["added_dependencies"]:
            _require(type(dep) is dict
                     and set(dep) == {
                         "dependency_id", "kind", "component_id",
                         "assertion", "evidence",
                     }
                     and type(dep["dependency_id"]) is str
                     and dep["dependency_id"] not in added_deps
                     and dep["dependency_id"] not in original_deps
                     and dep["kind"] == "native-value-present",
                     "unsealed native dependency invalid or duplicated")
            added_deps[dep["dependency_id"]] = dep

        _require(type(corpus_pack["mappings"]) is list
                 and type(corpus_pack["coverage_assignments"]) is list,
                 "unsealed mappings/coverage must be arrays")
        per_map = {}
        values = set()
        used_deps, used_added_ev, used_inherited_ev = set(), set(), set()
        for m in corpus_pack["mappings"]:
            _require(type(m) is dict and "review" not in m
                     and type(m.get("mapping_id")) is str
                     and m["mapping_id"].startswith(f"mapping:{corpus}:")
                     and m["mapping_id"] not in original_ids
                     and m["mapping_id"] not in per_map
                     and m["mapping_id"] not in mapping_ids
                     and m.get("mapping_semantic_digest") == mapping_semantic_digest_v2(m),
                     "unsealed candidate mapping invalid, reviewed, or conflicting")
            ident = m["mapping_id"]
            per_map[ident] = m
            mapping_ids.add(ident)
            binding = m.get("native_binding")
            _require(type(binding) is dict and set(binding) == {
                "component_id", "node_type", "feature", "value", "execution_shape",
            } and binding["component_id"] == f"{corpus}-tf"
                     and binding["node_type"] == "word"
                     and binding["feature"] == "sp"
                     and binding["execution_shape"] == "value-predicate"
                     and type(binding["value"]) is str
                     and binding["value"].isalpha()
                     and binding not in original_bindings
                     and binding["value"] not in values,
                     "unsealed candidate native selector collides or leaves pilot scope")
            values.add(binding["value"])
            dep_id = f'dep:{corpus}:word-sp:{binding["value"]}'
            _require(m.get("native_dependencies") == [dep_id],
                     "unsealed candidate dependency join invalid")
            native_refs = [ref for ref in m.get("evidence", [])
                           if type(ref) is dict and type(ref.get("evidence_id")) is str
                           and ref["evidence_id"].startswith(f"evidence:{corpus}:")]
            _require(len(native_refs) == 1,
                     "unsealed candidate lacks unique corpus source authority")
            native_ref = native_refs[0]
            source_record = added_evidence.get(native_ref["evidence_id"],
                                                original_evidence.get(native_ref["evidence_id"]))
            source_content = source_record.get("reviewed_content", {}) if source_record else {}
            _require(type(source_content) is dict
                     and source_content.get("feature") == "sp"
                     and source_content.get("production_node_type") == "word"
                     and type(source_content.get("source_definitions")) is dict
                     and binding["value"] in source_content["source_definitions"],
                     "unsealed candidate selector has no pinned source definition")
            if dep_id in added_deps:
                dep = added_deps[dep_id]
                _require(dep["component_id"] == binding["component_id"]
                         and dep["assertion"] == {
                             "feature": "sp", "node_type": "word",
                             "value": binding["value"], "value_semantics": "semantic",
                         }
                         and dep["evidence"] == [native_ref],
                         "unsealed candidate native dependency mismatches selector or source")
                used_deps.add(dep_id)
            else:
                _require(dep_id in original_deps
                         and original_deps[dep_id]["evidence"] == [native_ref],
                         "unsealed inherited native dependency/evidence drift")
            _require(type(m.get("evidence")) is list and m["evidence"],
                     "unsealed candidate source evidence missing")
            for ref in m["evidence"]:
                _require(type(ref) is dict
                         and set(ref) == {"evidence_id", "content_digest"},
                         "unsealed candidate evidence binding malformed")
                ident_ev = ref["evidence_id"]
                if ident_ev in added_evidence:
                    _require(ref["content_digest"] == added_evidence[ident_ev]["content_digest"],
                             "unsealed candidate new evidence digest drift")
                    used_added_ev.add(ident_ev)
                elif ident_ev in original_evidence:
                    _require(ident_ev in inherited
                             and ref["content_digest"] == original_evidence[ident_ev]["content_digest"],
                             "unsealed candidate inherited evidence drift")
                    used_inherited_ev.add(ident_ev)
                else:
                    raise ValueError("unsealed candidate references unknown evidence")
            projections = m.get("projections")
            _require(type(projections) is list, "unsealed projections malformed")
            if m.get("native_state") == "native-only":
                _require(not projections and not m.get("ambiguous_candidates")
                         and not m.get("external_references"),
                         "native-only candidate fabricated ontology projection")
                counts["native-only"] += 1
            else:
                _require(m.get("native_state") == "positive" and len(projections) == 1,
                         "unsealed positive requires exactly one reviewed-candidate projection")
                proj = projections[0]
                _require(type(proj) is dict and "review" not in proj
                         and proj.get("assessment") == "exact"
                         and proj.get("native_execution_binding") == binding
                         and proj.get("evidence") == m["evidence"]
                         and proj.get("target") in lock.get("terms_used", [])
                         and proj.get("projection_semantic_digest") == projection_semantic_digest_v1(proj),
                         "unsealed positive projection invalid or outside locked terms")
                counts["exact"] += 1

        _require(set(added_deps) == used_deps
                 and set(added_evidence) == used_added_ev
                 and inherited == used_inherited_ev,
                 "unsealed unused or missing evidence/dependencies")
        assigned = set()
        for row in corpus_pack["coverage_assignments"]:
            _require(type(row) is dict and set(row) == {
                "item_id", "mapping_id", "decision_digest", "assessment", "common_target",
            }, "unsealed coverage assignment fields malformed")
            ident = row["mapping_id"]
            _require(ident in per_map and ident not in assigned,
                     "unsealed coverage assignment duplicate or unmatched mapping")
            assigned.add(ident)
            mapping = per_map[ident]
            item_id = f'node_value:sp="{mapping["native_binding"]["value"]}"'
            _require(row["item_id"] == item_id and item_id in covered
                     and covered[item_id]["accounting"]["production"] is None
                     and (corpus, item_id) not in coverage_keys,
                     "unsealed coverage item outside denominator or already reviewed")
            coverage_keys.add((corpus, item_id))
            decision = accepted.get(ident)
            _require(decision is not None
                     and row["decision_digest"] == decision["decision_digest"]
                     and type(row["common_target"]) is bool
                     and row["common_target"] == (mapping["native_state"] == "positive")
                     and row["assessment"] == (
                         "exact" if mapping["native_state"] == "positive" else "native-only"
                     ), "unsealed review/coverage candidate assignment drift")
        _require(assigned == set(per_map), "unsealed coverage assignments incomplete")

    _require(mapping_ids == set(accepted), "unsealed accepted review rows not fully represented")
    _require(type(pack["counts"]["exact"]) is int
             and type(pack["counts"]["native-only"]) is int
             and pack["counts"] == counts
             and sum(counts.values()) == len(accepted),
             "unsealed positive/native-only counts inconsistent")
    # Intentionally return None, not an approval token, reviewed bundle, or
    # release-authorized receipt. An external signing/reviewer check is mandatory.
    return None
