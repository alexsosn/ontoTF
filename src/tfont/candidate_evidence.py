"""In-memory supplementary proposal evidence; never release/review authority.

Frozen installed source identities and ontology locks remain authoritative.
New native definitions are assertions for independent original-source review.
"""
from __future__ import annotations

import copy
import hashlib
import re
from importlib.resources import files
from typing import Any
from xml.etree import ElementTree

from .batch_proposals import BatchProposalError, packaged_resource
from .digests import evidence_record_digest
from .release_registry import load_profile
from .source_validation import validate_source

MAX_CANDIDATE_EVIDENCE = 32


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise BatchProposalError(message)


class CandidateEvidenceResources:
    """Validate and freeze new evidence objects while retaining installed locks.

    Calling this loader is NOT approval. Coordinates and definitions remain
    proposed assertions, bound by evidence/packet digests for skeptical review.
    """

    def __init__(self, ledger: dict[str, Any], evidence: dict[str, Any]):
        _require(type(evidence) is dict and 1 <= len(evidence) <= MAX_CANDIDATE_EVIDENCE,
                 "candidate evidence must contain 1–32 resources")
        self._evidence = copy.deepcopy(evidence)
        self._bundles: dict[str, Any] = {}
        try:
            _require(type(ledger) is dict
                     and type(ledger.get("source_registry")) is dict
                     and type(ledger.get("ontology_evidence_resources")) is dict,
                     "candidate ledger lacks source/ontology registries")
            native = {spec["evidence_resource"]: corpus
                      for corpus, spec in ledger["source_registry"].items()}
            ontology = set(ledger["ontology_evidence_resources"].values())
            seen_ids: set[str] = set()
            for name, record in self._evidence.items():
                _require(type(name) is str and name.endswith(".json")
                         and name.startswith("resources/")
                         and all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in {".", ".."}
                                 for p in name.split("/")), "unsafe candidate resource identity")
                _require(name in set(native) | ontology,
                         "candidate resource is unused or attempts an ontology lock override")
                _require(not files("tfont").joinpath(*name.split("/")).is_file(),
                         "candidate evidence cannot shadow installed resources")
                validate_source(record, "evidence", source_name=name)
                _require(record["evidence_id"] not in seen_ids, "duplicate candidate evidence identity")
                seen_ids.add(record["evidence_id"])
                _require(record["content_mode"] == "normalized-record"
                         and record["content_digest"] == evidence_record_digest(record),
                         "candidate evidence digest mismatch")
                _require("citation" not in record,
                         "candidate citations must be inside digest-bound normalized content")
                _require(type(record["reviewed_content"]) is dict,
                         "candidate evidence content must be an object")
                if name in native:
                    self._native(record, native[name], ledger["source_registry"][native[name]])
                else:
                    self._ontology(record, ledger)
        except BatchProposalError:
            raise
        except (OSError, KeyError, TypeError, ValueError, ElementTree.ParseError) as exc:
            raise BatchProposalError("invalid candidate evidence or protected source anchor") from exc

    def _bundle(self, corpus: str):
        if corpus not in self._bundles:
            self._bundles[corpus] = load_profile(corpus)
        return self._bundles[corpus]

    def _native(self, record: dict[str, Any], corpus: str, spec: dict[str, Any]) -> None:
        content = record["reviewed_content"]
        bundle = self._bundle(corpus)
        _require(record["evidence_id"] not in {a.data["evidence_id"] for a in bundle.evidences},
                 "candidate evidence cannot reuse installed evidence identities")
        anchors = [a.data for a in bundle.evidences
                   if a.data["evidence_id"].startswith(f"evidence:{corpus}:")
                   and a.data.get("kind") == "corpus-feature-definition"
                   and type(a.data.get("reviewed_content")) is dict
                   and a.data["reviewed_content"].get("production_node_type") == "word"
                   and a.data["reviewed_content"].get("feature") == "sp"]
        _require(any(
            record.get("kind") == anchor["kind"]
            and record.get("source_uri") == anchor["source_uri"]
            and record.get("source_revision") == spec["source_revision"] == anchor["source_revision"]
            and record.get("license_ref") == anchor.get("license_ref")
            and content.get("target_tf_revision") == spec["target_corpus_revision"]
                == anchor["reviewed_content"]["target_tf_revision"]
            and all(content.get(k) == anchor["reviewed_content"].get(k) for k in (
                "feature", "feature_semantics", "production_node_type", "documented_node_types"))
            for anchor in anchors), "candidate native source pin, URI or semantics differ from protected evidence")
        definitions = content.get("source_definitions")
        _require(type(definitions) is dict and bool(definitions), "candidate source definitions absent")
        for definition in definitions.values():
            _require(type(definition) is dict
                     and type(definition.get("gloss")) is str and bool(definition["gloss"].strip())
                     and type(definition.get("line")) is int and definition["line"] > 0,
                     "candidate native definition lacks bound gloss/coordinate")

    def _ontology(self, record: dict[str, Any], ledger: dict[str, Any]) -> None:
        lock = packaged_resource(ledger["ontology_lock_resource"])
        validate_source(lock, "ontology-lock")
        content = record["reviewed_content"]
        licenses = {a.data.get("license_ref")
                    for corpus in ledger["source_registry"]
                    for a in self._bundle(corpus).evidences
                    if a.data.get("kind") == "ontology-definition"
                    and a.data.get("source_uri") == lock["source_uri"]
                    and a.data.get("source_revision") == lock["source_revision"]}
        _require(record["evidence_id"] not in {a.data["evidence_id"]
                 for corpus in ledger["source_registry"] for a in self._bundle(corpus).evidences},
                 "candidate evidence cannot reuse installed evidence identities")
        _require(record.get("kind") == "ontology-definition"
                 and record.get("source_uri") == lock["source_uri"]
                 and record.get("source_revision") == ledger["ontology_revision"] == lock["source_revision"]
                 and record.get("license_ref") in licenses and record.get("license_ref") is not None
                 and content.get("snapshot_digest") == lock["content_digest"]
                 and content.get("rdf_type") == "owl:Class"
                 and content.get("target") in lock["terms_used"],
                 "candidate ontology source, license, kind or trusted lock membership differs")
        raw = files("tfont").joinpath(*lock["snapshot_artifact"].split("/")).read_bytes()
        _require("sha256:" + hashlib.sha256(raw).hexdigest() == lock["content_digest"],
                 "protected ontology snapshot digest mismatch")
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        target = content["target"]
        classes = {element.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
                   for element in ElementTree.fromstring(raw).iter("{http://www.w3.org/2002/07/owl#}Class")}
        lines = raw.decode("utf-8").splitlines()
        line = content.get("declaration_line")
        _require(target in classes and content.get("original_source_blob") == blob
                 and type(line) is int and 1 <= line <= len(lines)
                 and re.fullmatch(r'\s*<owl:Class\s+rdf:about="' + re.escape(target) + r'"\s*>\s*', lines[line - 1]) is not None,
                 "candidate ontology class/blob/declaration not in protected RDF")

    def __call__(self, name: str) -> dict[str, Any]:
        if name in self._evidence:
            return copy.deepcopy(self._evidence[name])
        return packaged_resource(name)
