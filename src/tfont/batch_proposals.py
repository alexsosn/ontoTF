"""Generate digest-correct, *unreviewed* batch mapping candidates from pinned evidence.

The output deliberately omits required Mapping v2 review records. It cannot
be loaded as a production bundle. A separate independent approval/publisher
must authorize decisions before any runtime profile or coverage delta exists.
"""
from __future__ import annotations

import copy
import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable

from .digests import evidence_record_digest
from .semantic_digest_v2 import (
    mapping_semantic_digest_v2, projection_semantic_digest_v1,
)
from .source_validation import loads_source, validate_source


LEDGER_RESOURCE = "resources/batch_pilots/i033c-adj-adv-proposals.json"
IDENTITY = re.compile(r"^[a-z][a-z0-9_-]*$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")
_SOURCE_KEYS = {"source_revision", "target_corpus_revision", "evidence_resource", "component_id"}
_DECISION_KEYS = {"corpus_id", "value", "term_key", "assessment", "rationale"}
_TOP_KEYS = {
    "schema_version", "batch_id", "mode", "ontology_model",
    "ontology_revision", "ontology_lock_resource",
    "ontology_evidence_resources", "source_registry", "defaults", "decisions",
}
_DEFAULTS = {
    "profile_id": "linguistic", "capability_id": "linguistic.part-of-speech",
    "semantic_role": "annotation-value", "native_node_type": "word",
    "feature": "sp",
}


class BatchProposalError(ValueError):
    """Source integrity, review boundary or closed-shape proposal failure."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BatchProposalError(message)


def _closed(value: Any, keys: set[str], where: str) -> dict[str, Any]:
    _require(type(value) is dict and set(value) == keys, f"{where}: unknown/missing fields")
    return value


def _path(name: str, prefix: str) -> str:
    _require(type(name) is str and name.endswith(".json"), "non-JSON source resource")
    parts = name.split("/")
    _require(bool(parts) and name.startswith(prefix + "/")
             and all(p not in {"", ".", ".."} and "\\" not in p for p in parts),
             "unsafe or foreign resource path")
    return name


def packaged_resource(name: str) -> dict[str, Any]:
    _path(name, "resources")
    try:
        raw = files("tfont").joinpath(*name.split("/")).read_text(encoding="utf-8")
        value = loads_source(raw, format="json", source_name=name)
    except (OSError, UnicodeError, ValueError) as exc:
        raise BatchProposalError(f"invalid packaged resource: {name}") from exc
    _require(type(value) is dict, "resource must be JSON object")
    return value


def load_ledger() -> dict[str, Any]:
    return packaged_resource(LEDGER_RESOURCE)


def _verified_evidence(
    resource: str,
    prefix: str,
    read: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    _path(resource, prefix)
    try:
        evidence = read(resource)
        validate_source(evidence, "evidence", source_name=resource)
        _require(
            evidence.get("content_mode") == "normalized-record"
            and evidence.get("content_digest") == evidence_record_digest(evidence),
            f"source evidence digest mismatch: {resource}",
        )
    except BatchProposalError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise BatchProposalError(f"invalid evidence source: {resource}") from exc
    return evidence


def compile_candidate_batch(
    ledger: dict[str, Any],
    *,
    resource_loader: Callable[[str], dict[str, Any]] = packaged_resource,
) -> dict[str, Any]:
    """Compile a bounded cohort; never import or synthesize a reviewed receipt."""
    obj = _closed(ledger, _TOP_KEYS, "batch")
    _require(obj["schema_version"] == 1 and obj["mode"] == "proposal-only",
             "only unreviewed proposal batches are supported")
    _require(type(obj["batch_id"]) is str and bool(IDENTITY.fullmatch(obj["batch_id"])),
             "invalid batch identity")
    model, revision = obj["ontology_model"], obj["ontology_revision"]
    _require(type(model) is str and bool(IDENTITY.fullmatch(model))
             and type(revision) is str and bool(_REVISION.fullmatch(revision)),
             "invalid ontology source identity")
    root = f"resources/ontologies/{model}/{revision}"
    lock_name = _path(obj["ontology_lock_resource"], root)
    try:
        lock = resource_loader(lock_name)
        validate_source(lock, "ontology-lock", source_name=lock_name)
    except (OSError, TypeError, KeyError, ValueError) as exc:
        raise BatchProposalError("invalid pinned ontology lock") from exc
    _require(
        lock.get("source_revision") == revision
        and lock.get("ontology_id") == model
        and type(lock.get("content_digest")) is str
        and type(lock.get("terms_used")) is list
        and type(lock.get("lock_id")) is str,
        "ontology lock source revision/identity drift",
    )
    ontology_specs = obj["ontology_evidence_resources"]
    sources = obj["source_registry"]
    _require(type(ontology_specs) is dict and bool(ontology_specs)
             and type(sources) is dict and bool(sources), "source registries missing")
    _require(_closed(obj["defaults"], set(_DEFAULTS), "POS defaults") == _DEFAULTS,
             "unsupported pilot template defaults")

    native_sources: dict[str, tuple[dict[str, Any], dict[str, str]]] = {}
    for corpus, spec in sources.items():
        _require(type(corpus) is str and bool(IDENTITY.fullmatch(corpus)),
                 "invalid corpus identity")
        entry = _closed(spec, _SOURCE_KEYS, "corpus source")
        _require(
            type(entry["source_revision"]) is str and bool(_REVISION.fullmatch(entry["source_revision"]))
            and type(entry["target_corpus_revision"]) is str
            and bool(_REVISION.fullmatch(entry["target_corpus_revision"]))
            and entry["component_id"] == f"{corpus}-tf",
            f"{corpus}: source revision/component identity drift",
        )
        evidence_name = _path(entry["evidence_resource"],
                              f"resources/profiles/{corpus}")
        record = _verified_evidence(evidence_name,
                                    f"resources/profiles/{corpus}", resource_loader)
        content = record.get("reviewed_content", {})
        _require(
            record.get("source_revision") == entry["source_revision"]
            and record.get("evidence_id", "").startswith(f"evidence:{corpus}:")
            and content.get("feature") == "sp"
            and content.get("production_node_type") == "word"
            and content.get("target_tf_revision") == entry["target_corpus_revision"]
            and type(content.get("source_definitions")) is dict,
            f"{corpus}: native source feature/provenance mismatch",
        )
        native_sources[corpus] = (record, entry)

    terms: dict[str, dict[str, Any]] = {}
    for key, resource in ontology_specs.items():
        _require(type(key) is str and bool(IDENTITY.fullmatch(key)),
                 "invalid ontology term key")
        record = _verified_evidence(resource, root, resource_loader)
        content = record["reviewed_content"]
        _require(
            record.get("evidence_id", "").startswith(f"evidence:{model}:")
            and record.get("source_revision") == revision
            and content.get("rdf_type") == "owl:Class"
            and content.get("snapshot_digest") == lock["content_digest"]
            and content.get("target") in lock["terms_used"]
            and content.get("target", "").rsplit("#", 1)[-1].lower() == key,
            f"ontology target {key} lacks pinned owl:Class evidence or identity",
        )
        terms[key] = record

    raw_decisions = obj["decisions"]
    _require(type(raw_decisions) is list and 1 <= len(raw_decisions) <= 50,
             "batch must have 1–50 candidate decisions")
    results: list[dict[str, Any]] = []
    seen_native: set[tuple[str, str]] = set()
    seen_mappings: set[str] = set()
    for decision in raw_decisions:
        row = _closed(decision, _DECISION_KEYS, "decision")
        corpus, value, key = row["corpus_id"], row["value"], row["term_key"]
        _require(type(corpus) is str and corpus in native_sources
                 and type(value) is str and bool(IDENTITY.fullmatch(value))
                 and type(key) is str and key in terms,
                 "unregistered source corpus, native value or ontology target")
        _require(row["assessment"] == "exact"
                 and type(row["rationale"]) is str and row["rationale"].strip(),
                 "only reasoned exact-class proposals supported by this pilot")
        pair = (corpus, value)
        _require(pair not in seen_native, f"duplicate native selector: {pair}")
        seen_native.add(pair)
        source, spec = native_sources[corpus]
        native_content = source["reviewed_content"]
        _require(value in native_content["source_definitions"],
                 f"{corpus}: absent or unsupported original POS category {value}")
        ontology = terms[key]
        source_binding = {
            "evidence_id": source["evidence_id"],
            "content_digest": source["content_digest"],
        }
        ontology_binding = {
            "evidence_id": ontology["evidence_id"],
            "content_digest": ontology["content_digest"],
        }
        evidence = [source_binding, ontology_binding]
        binding = {
            "component_id": spec["component_id"],
            "node_type": "word",
            "feature": "sp",
            "value": value,
            "execution_shape": "value-predicate",
        }
        mapping_id = f"mapping:{corpus}:{model}-{key}"
        _require(mapping_id not in seen_mappings, "two selectors claim one mapping identity")
        seen_mappings.add(mapping_id)
        projection = {
            "assessment": "exact",
            "capability_id": _DEFAULTS["capability_id"],
            "evidence": copy.deepcopy(evidence),
            "formal_kind": "class",
            "native_execution_binding": copy.deepcopy(binding),
            "ontology_lock": lock["lock_id"],
            "profile_id": _DEFAULTS["profile_id"],
            "projection_id": f"projection:{corpus}:{model}-{key}",
            "publication_relation": None,
            "query_role": "semantic-constraint",
            "reference_kind": "semantic-pivot",
            "semantic_role": _DEFAULTS["semantic_role"],
            "target": ontology["reviewed_content"]["target"],
        }
        projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
        mapping = {
            "ambiguous_candidates": [],
            "capabilities": [_DEFAULTS["capability_id"]],
            "corpus_id": corpus,
            "evidence": evidence,
            "external_references": [],
            "mapping_id": mapping_id,
            "native_binding": binding,
            "native_dependencies": [f"dep:{corpus}:word-sp:{value}"],
            "native_state": "positive",
            "profiles": [_DEFAULTS["profile_id"]],
            "projections": [projection],
            "rationale": row["rationale"],
        }
        mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
        results.append(mapping)
    results.sort(key=lambda row: row["mapping_id"])
    return {
        "schema_version": 1,
        "batch_id": obj["batch_id"],
        "mode": "proposal-only",
        "release_authorized": False,
        "count": len(results),
        "candidates": results,
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
