"""Data-first, **parity-only** compiler for already published POS decisions.

This is a migration experiment, NOT an approval issuer. Existing source-reviewed
Mapping v2 files are the only authority in this phase; semantic fields must be
generated from the ledger and *match* independently published artifacts before
their original audit-only review fields may be carried into the result.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .digests import evidence_record_digest
from .semantic_digest_v2 import (
    mapping_semantic_digest_v2,
    projection_semantic_digest_v1,
)
from .source_validation import validate_source

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "src/tfont/resources/batch_pilots/i033a-olia-verb-and-stems.json"
_OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
_OLIA_ROOT = (
    ROOT / "src/tfont/resources/ontologies/olia" / _OLIA_REVISION
)
_OLIA_TERM = "http://purl.org/olia/olia.owl#Verb"
_EXPECTED_CORPORA = frozenset(("bhsa", "syriac", "extrabiblical"))
_POS_KEYS = frozenset((
    "corpus_id", "source_revision", "native", "target",
    "corpus_evidence_id", "corpus_evidence_digest", "ontology_evidence_id",
    "ontology_evidence_digest", "reviewed_mapping_semantic_digest",
    "reviewed_projection_semantic_digest",
))
_NATIVE_ONLY_KEYS = frozenset((
    "corpus_id", "native_feature", "assessment", "common_target",
    "coverage_manifest", "source_ids", "item_ids",
))


class BatchCompilerError(ValueError):
    """Malformed decision or failed parity/trust-boundary check."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BatchCompilerError(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BatchCompilerError(f"unreadable published source {path}") from exc
    _require(type(value) is dict, f"invalid published source object: {path}")
    return value


def load_pilot() -> dict[str, Any]:
    return _load(LEDGER)


def _native_evidence(corpus: str, entry: dict[str, Any]) -> dict[str, str]:
    path = (
        ROOT / "src/tfont/resources/profiles"
        / corpus / "0.3.0/evidence/native-verb-pos.json"
    )
    record = _load(path)
    _require(record.get("source_revision") == entry["source_revision"],
             f"{corpus}: original source revision mismatch")
    _require(record.get("evidence_id") == entry["corpus_evidence_id"],
             f"{corpus}: native evidence identity mismatch")
    _require(record.get("content_digest") == evidence_record_digest(record),
             f"{corpus}: native evidence record digest invalid")
    _require(record["content_digest"] == entry["corpus_evidence_digest"],
             f"{corpus}: evidence drift from approved source")
    _require(record.get("reviewed_content", {}).get("feature") == "sp",
             f"{corpus}: native evidence is not POS")
    return {
        "evidence_id": record["evidence_id"],
        "content_digest": record["content_digest"],
    }


def _ontology_evidence(entry: dict[str, Any]) -> dict[str, str]:
    record = _load(_OLIA_ROOT / "verb-evidence.json")
    lock = _load(_OLIA_ROOT / "lock-linguistic-0.3.0.json")
    _require(record.get("evidence_id") == entry["ontology_evidence_id"],
             "OLiA evidence ID mismatch")
    _require(record.get("content_digest") == evidence_record_digest(record),
             "OLiA evidence record digest invalid")
    _require(record["content_digest"] == entry["ontology_evidence_digest"],
             "OLiA evidence pin differs from reviewed ontology")
    _require(record.get("source_revision") == _OLIA_REVISION
             and lock.get("source_revision") == _OLIA_REVISION,
             "ontology revision drift")
    _require(record["reviewed_content"]["target"] == entry["target"]
             and record["reviewed_content"]["rdf_type"] == "owl:Class"
             and entry["target"] in lock.get("terms_used", [])
             and record["reviewed_content"]["snapshot_digest"] == lock["content_digest"],
             "ontology evidence does not establish a pinned class")
    return {
        "evidence_id": record["evidence_id"],
        "content_digest": record["content_digest"],
    }


def _compile_positive(entry: dict[str, Any]) -> dict[str, Any]:
    _require(type(entry) is dict and set(entry) == _POS_KEYS,
             "positive decision must use exact parity-only schema; review cannot be self-declared")
    corpus = entry["corpus_id"]
    _require(type(corpus) is str and corpus in _EXPECTED_CORPORA,
             "unsupported corpus in published parity pilot")
    native = entry["native"]
    _require(native == {"node_type": "word", "feature": "sp", "value": "verb"},
             "published POS selector has changed")
    _require(entry["target"] == _OLIA_TERM,
             "published positive ontology term changed")
    source = _native_evidence(corpus, entry)
    ontology = _ontology_evidence(entry)
    evidence = [source, ontology]
    binding = {
        "component_id": f"{corpus}-tf",
        "execution_shape": "value-predicate",
        "feature": native["feature"],
        "node_type": native["node_type"],
        "value": native["value"],
    }
    projection = {
        "assessment": "exact",
        "capability_id": "linguistic.part-of-speech",
        "evidence": copy.deepcopy(evidence),
        "formal_kind": "class",
        "native_execution_binding": copy.deepcopy(binding),
        "ontology_lock": "olia-reference-model",
        "profile_id": "linguistic",
        "projection_id": f"projection:{corpus}:olia-verb",
        "publication_relation": None,
        "query_role": "semantic-constraint",
        "reference_kind": "semantic-pivot",
        "semantic_role": "annotation-value",
        "target": entry["target"],
    }
    projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
    mapping = {
        "ambiguous_candidates": [],
        "capabilities": ["linguistic.part-of-speech"],
        "corpus_id": corpus,
        "evidence": copy.deepcopy(evidence),
        "external_references": [],
        "mapping_id": f"mapping:{corpus}:olia-verb",
        "native_binding": binding,
        "native_dependencies": [f"dep:{corpus}:word-sp:verb"],
        "native_state": "positive",
        "profiles": ["linguistic"],
        "projections": [projection],
    }
    mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
    _require(
        mapping["mapping_semantic_digest"] == entry["reviewed_mapping_semantic_digest"]
        and projection["projection_semantic_digest"]
        == entry["reviewed_projection_semantic_digest"],
        f"{corpus}: semantic digest diverges from approved published decision",
    )

    # Import ONLY excluded audit-only fields from an independently published
    # reviewed mapping, after semantic digests have already been checked.
    original = _load(
        ROOT / "src/tfont/resources/profiles"
        / corpus / "0.3.0/mappings/verb.json"
    )
    validate_source(original, "mapping", source_name=f"published:{corpus}:verb")
    _require(len(original["mappings"]) == 1, "ambiguous published mapping")
    published = original["mappings"][0]
    _require(published.get("review", {}).get("status") == "reviewed",
             "published mapping has no reviewed authority")
    _require(published["review"].get("reviewed_mapping_digest")
             == mapping["mapping_semantic_digest"], "published mapping review stale")
    published_projection = published["projections"][0]
    _require(published_projection.get("review", {}).get("status") == "reviewed"
             and published_projection["review"].get("reviewed_mapping_digest")
             == projection["projection_semantic_digest"],
             "published projection review stale")
    for field in ("review",):
        projection[field] = copy.deepcopy(published_projection[field])
        mapping[field] = copy.deepcopy(published[field])
    for field in ("rationale", "introduced_in", "changed_in"):
        if field in published:
            mapping[field] = copy.deepcopy(published[field])
        if field in published_projection:
            projection[field] = copy.deepcopy(published_projection[field])
    _require(mapping == published,
             f"{corpus}: generated Mapping v2 diverges from reviewed published record")
    return mapping


def _compile_native_only(group: dict[str, Any]) -> list[dict[str, Any]]:
    _require(type(group) is dict and set(group) == _NATIVE_ONLY_KEYS,
             "native-only group shape invalid; cannot add target/review claims")
    _require(group["corpus_id"] == "bhsa"
             and group["native_feature"] == "vs"
             and group["assessment"] == "native-only"
             and group["common_target"] is False,
             "native-only disposition may not be promoted")
    approved_path = (
        "src/tfont/resources/coverage/p004-i027b1-bhsa-verb-v1/bhsa.json"
    )
    _require(group["coverage_manifest"] == approved_path,
             "native-only cohort must use reviewed coverage manifest")
    approved = _load(ROOT / approved_path)
    cohort = []
    for item in approved["semantic_items"]:
        prod = item["accounting"]["production"]
        if prod is None or "native-only" not in prod["assessments"]:
            continue
        _require(prod["common_target"] is False
                 and prod["assessments"] == ["native-only"]
                 and prod["source_ids"] == group["source_ids"],
                 "published native-only authority drift")
        cohort.append({
            "item_id": item["item_id"],
            "corpus_id": "bhsa",
            "assessment": "native-only",
            "common_target": False,
            "source_ids": copy.deepcopy(prod["source_ids"]),
        })
    actual_ids = sorted(item["item_id"] for item in cohort)
    wanted_ids = group["item_ids"]
    _require(type(wanted_ids) is list and len(wanted_ids) == 27
             and wanted_ids == sorted(set(wanted_ids))
             and wanted_ids == actual_ids,
             "native-only reviewed item set differs from published source")
    return sorted(cohort, key=lambda item: item["item_id"])


def compile_pilot(ledger: dict[str, Any]) -> dict[str, Any]:
    _require(type(ledger) is dict and set(ledger)
             == {"schema_version", "batch_id", "mode", "positive_pos", "native_only"},
             "batch ledger has invalid top-level keys")
    _require(ledger["schema_version"] == 1
             and ledger["mode"] == "published-parity-only"
             and ledger["batch_id"] == "i033a-published-olia-verb-and-bhsa-stem-parity",
             "batch approval/format policy mismatch")
    entries = ledger["positive_pos"]
    _require(type(entries) is list and len(entries) == 3,
             "pilot must reproduce exactly three published positive mappings")
    corpora = [e.get("corpus_id") if type(e) is dict else None for e in entries]
    _require(set(corpora) == _EXPECTED_CORPORA
             and len(corpora) == len(set(corpora)),
             "positive identities duplicated or missing")
    mappings = [_compile_positive(e) for e in entries]
    native_only = _compile_native_only(ledger["native_only"])
    return {
        "mappings": sorted(mappings, key=lambda row: row["mapping_id"]),
        "native_only": native_only,
    }


def parity_report(ledger: dict[str, Any]) -> dict[str, Any]:
    result = compile_pilot(ledger)
    return {
        "schema_version": 1,
        "batch_id": ledger["batch_id"],
        "authorizes_new_mappings": False,
        "counts": {
            "positive_exact": len(result["mappings"]),
            "reviewed_native_only": len(result["native_only"]),
            "total_decisions": len(result["mappings"]) + len(result["native_only"]),
        },
        "published_semantic_digests": [
            {
                "mapping_id": mapping["mapping_id"],
                "mapping_digest": mapping["mapping_semantic_digest"],
                "projection_digest": mapping["projections"][0]["projection_semantic_digest"],
            }
            for mapping in result["mappings"]
        ],
        "reviewed_native_only_source_ids": ledger["native_only"]["source_ids"],
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
