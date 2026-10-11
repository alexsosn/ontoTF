"""Fail-closed preview of a versioned native-only -> exact mapping supersession.

No caller-supplied predecessor/review/ontology evidence is authenticated here.
Only a protected release publisher can resolve these records against an
installed immutable base, exact GitHub two-pass review, and a signed release.
This module does NOT activate mappings, mutate coverage, or authorize release.
"""
from __future__ import annotations

import copy
import hashlib
import re
from typing import Any

from .digests import canonical_json_bytes, evidence_record_digest
from .semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1


class NativeSupersessionError(ValueError):
    """Incompatible, stale, weakly sourced, or unauthorized-looking transition."""


_AUTHORITY = "untrusted-supersession-preview"
_REV = re.compile(r"[0-9a-f]{40}\Z")
_VERSION = re.compile(r"([a-z][a-z0-9_-]*)/([0-9]+\.[0-9]+\.[0-9]+)\Z")


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise NativeSupersessionError(reason)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _evidence_binding(record: dict[str, Any], prefix: str) -> dict[str, str]:
    _require(type(record) is dict
             and type(record.get("evidence_id")) is str
             and record["evidence_id"].startswith(prefix)
             and record.get("content_mode") == "normalized-record"
             and type(record.get("source_revision")) is str
             and _REV.fullmatch(record["source_revision"]) is not None,
             "source evidence missing pinned corpus/ontology identity")
    _require(record.get("content_digest") == evidence_record_digest(record),
             "source evidence normalized content digest drift")
    return {"evidence_id": record["evidence_id"],
            "content_digest": record["content_digest"]}


def _plan(
    previous: dict[str, Any],
    candidate: dict[str, Any],
    native_evidence: dict[str, Any],
    ontology_evidence: dict[str, Any],
    ontology_lock: dict[str, Any],
    base_release: str,
    active_mappings: list[dict[str, Any]],
) -> dict[str, Any]:
    _require(type(previous) is dict and type(candidate) is dict,
             "supersession needs mapping objects")
    corpus = previous.get("corpus_id")
    _require(type(corpus) is str and re.fullmatch(r"[a-z][a-z0-9_-]*", corpus) is not None
             and type(base_release) is str
             and _VERSION.fullmatch(base_release) is not None
             and _VERSION.fullmatch(base_release).group(1) == corpus,
             "base release must pin the exact source corpus and version")
    _require(previous.get("native_state") == "native-only"
             and previous.get("projections") == []
             and previous.get("ambiguous_candidates") == []
             and previous.get("external_references") == [],
             "predecessor is not an unprojected reviewed native-only mapping")
    old_id = previous.get("mapping_id")
    new_id = candidate.get("mapping_id")
    _require(type(old_id) is str and old_id.startswith(f"mapping:{corpus}:")
             and type(new_id) is str and new_id.startswith(f"mapping:{corpus}:")
             and new_id != old_id,
             "promotion must use a new mapping identity and preserve the old mapping")
    old_digest = mapping_semantic_digest_v2(previous)
    _require(previous.get("mapping_semantic_digest") == old_digest,
             "predecessor semantic digest is stale")
    prior_review = previous.get("review")
    _require(type(prior_review) is dict
             and prior_review.get("status") == "reviewed"
             and prior_review.get("reviewed_mapping_digest") == old_digest
             and type(prior_review.get("review_id")) is str
             and bool(prior_review["review_id"]),
             "predecessor lacks a content-bound reviewed record (not live authentication)")
    _require("review" not in candidate
             and candidate.get("native_state") == "positive"
             and candidate.get("ambiguous_candidates") == []
             and candidate.get("external_references") == [],
             "new exact proposal must be unreviewed and unambiguous")
    _require(candidate.get("mapping_semantic_digest") ==
             mapping_semantic_digest_v2(candidate),
             "new mapping semantic digest mismatch")
    binding = previous.get("native_binding")
    _require(type(binding) is dict and set(binding) == {
                 "component_id", "node_type", "feature", "value", "execution_shape"}
             and binding.get("component_id") == f"{corpus}-tf"
             and binding.get("node_type") == "word"
             and binding.get("feature") == "sp"
             and binding.get("execution_shape") == "value-predicate"
             and type(binding.get("value")) is str
             and bool(binding["value"]),
             "old selector must be a pinned word-level native POS value")
    _require(type(active_mappings) is list and bool(active_mappings),
             "pinned base must supply a nonempty active mapping index")
    active_ids: set[str] = set()
    active_projection_ids: set[str] = set()
    matches: list[dict[str, Any]] = []
    for existing in active_mappings:
        _require(type(existing) is dict and type(existing.get("mapping_id")) is str
                 and existing["mapping_id"] not in active_ids
                 and existing.get("mapping_semantic_digest")
                     == mapping_semantic_digest_v2(existing),
                 "inherited active mappings contain duplicates or stale digests")
        active_ids.add(existing["mapping_id"])
        if existing.get("native_binding") == binding:
            matches.append(existing)
        for existing_projection in existing.get("projections", []):
            _require(type(existing_projection) is dict
                     and type(existing_projection.get("projection_id")) is str
                     and existing_projection["projection_id"] not in active_projection_ids,
                     "duplicate active projection ID")
            active_projection_ids.add(existing_projection["projection_id"])
    _require(len(matches) == 1
             and canonical_json_bytes(matches[0]) == canonical_json_bytes(previous)
             and old_id in active_ids and new_id not in active_ids,
             "previous mapping must uniquely own active selector and successor ID must be new")
    _require(candidate.get("corpus_id") == corpus
             and candidate.get("native_binding") == binding
             and candidate.get("native_dependencies") == previous.get("native_dependencies")
             and type(previous.get("native_dependencies")) is list
             and len(previous["native_dependencies"]) == 1
             and previous["native_dependencies"][0] ==
                 f'dep:{corpus}:word-sp:{binding["value"]}'
             and candidate.get("profiles") == previous.get("profiles")
             and candidate.get("capabilities") == previous.get("capabilities"),
             "successor silently changed corpus, native selector, or capabilities")
    _require(previous.get("profiles") == ["linguistic"]
             and previous.get("capabilities") == ["linguistic.part-of-speech"],
             "v1 promotion only covers reviewed linguistic part-of-speech")
    source_ref = _evidence_binding(native_evidence, f"evidence:{corpus}:")
    _require(previous.get("evidence") == [source_ref],
             "prior reviewed source evidence is not pinned to the native selector")
    source_content = native_evidence.get("reviewed_content")
    _require(type(source_content) is dict
             and source_content.get("feature") == binding["feature"],
             "native source record does not define the selector feature")
    if "source_definitions" in source_content:
        _require(source_content.get("production_node_type") == "word",
                 "native source definitions do not authorize word-level feature scope")
        _require(type(source_content["source_definitions"]) is dict
                 and binding["value"] in source_content["source_definitions"],
                 "native category not in original source-defined feature domain")
    else:
        values = source_content.get("values")
        scope = source_content.get("production_scope")
        _require(type(values) is dict and binding["value"] in values
                 and type(scope) is dict
                 and scope.get("node_type") == "word"
                 and binding["value"] in scope.get("selected_values", []),
                 "native category not present in pinned reviewed original-source domain")

    _require(type(ontology_lock) is dict
             and type(ontology_lock.get("ontology_id")) is str
             and type(ontology_lock.get("source_revision")) is str
             and _REV.fullmatch(ontology_lock["source_revision"]) is not None
             and type(ontology_lock.get("lock_id")) is str
             and type(ontology_lock.get("content_digest")) is str
             and type(ontology_lock.get("terms_used")) is list,
             "ontology lock identity missing or malformed")
    ont_ref = _evidence_binding(
        ontology_evidence, f'evidence:{ontology_lock["ontology_id"]}:'
    )
    definition = ontology_evidence.get("reviewed_content")
    _require(type(definition) is dict
             and ontology_evidence["source_revision"] == ontology_lock["source_revision"]
             and definition.get("rdf_type") == "owl:Class"
             and definition.get("snapshot_digest") == ontology_lock["content_digest"]
             and type(definition.get("target")) is str
             and definition["target"] in ontology_lock["terms_used"]
             and definition["target"].startswith(ontology_lock.get("term_namespace", "")),
             "ontology term is not a pinned OWL class in the locked snapshot")
    _require(candidate.get("evidence") == [source_ref, ont_ref],
             "candidate must retain exact original native evidence and add one locked class")
    projections = candidate.get("projections")
    _require(type(projections) is list and len(projections) == 1
             and type(projections[0]) is dict,
             "positive supersession needs exactly one class projection")
    projection = projections[0]
    _require(projection.get("projection_id") not in active_projection_ids,
             "candidate projection ID collides with inherited active index")
    _require("review" not in projection
             and projection.get("assessment") == "exact"
             and projection.get("target") == definition["target"]
             and projection.get("formal_kind") == "class"
             and projection.get("ontology_lock") == ontology_lock["lock_id"]
             and projection.get("native_execution_binding") == binding
             and projection.get("evidence") == candidate["evidence"]
             and projection.get("capability_id") == "linguistic.part-of-speech"
             and projection.get("profile_id") == "linguistic"
             and projection.get("semantic_role") == "annotation-value"
             and projection.get("reference_kind") == "semantic-pivot"
             and projection.get("query_role") == "semantic-constraint"
             and projection.get("publication_relation") is None
             and type(projection.get("projection_id")) is str
             and projection["projection_id"].startswith(f"projection:{corpus}:")
             and projection.get("projection_semantic_digest") ==
                 projection_semantic_digest_v1(projection),
             "new class projection is invalid, misbound or has a stale digest")
    active_fingerprint = [
        {"mapping_id": m["mapping_id"], "semantic_digest": m["mapping_semantic_digest"],
         "native_binding": copy.deepcopy(m["native_binding"])}
        for m in sorted(active_mappings, key=lambda row: row["mapping_id"])
    ]
    record = {
        "schema_version": 1,
        "transition_kind": "native-only-to-exact",
        "authority": _AUTHORITY,
        "release_authorized": False,
        "base_release": base_release,
        "active_base_digest": _digest(active_fingerprint),
        "corpus_id": corpus,
        "native_binding": copy.deepcopy(binding),
        "retired": {
            "mapping_id": old_id,
            "semantic_digest": old_digest,
            "native_state": "native-only",
        },
        "candidate": {
            "mapping_id": new_id,
            "semantic_digest": candidate["mapping_semantic_digest"],
            "projection_digest": projection["projection_semantic_digest"],
            "target": definition["target"],
            "assessment": "exact",
        },
        "native_evidence": source_ref,
        "ontology": {
            "model": ontology_lock["ontology_id"],
            "lock_id": ontology_lock["lock_id"],
            "source_revision": ontology_lock["source_revision"],
            "snapshot_digest": ontology_lock["content_digest"],
            "class_evidence": ont_ref,
        },
    }
    record["transition_digest"] = _digest(record)
    return record


def plan_native_only_supersession(
    *, previous: dict[str, Any], candidate: dict[str, Any],
    native_evidence: dict[str, Any], ontology_evidence: dict[str, Any],
    ontology_lock: dict[str, Any], base_release: str,
    active_mappings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build NON-AUTHORITATIVE upgrade lineage; never modify the active index."""
    try:
        return _plan(
            previous, candidate, native_evidence, ontology_evidence,
            ontology_lock, base_release, active_mappings,
        )
    except NativeSupersessionError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        raise NativeSupersessionError("invalid or untrusted source-bound supersession input") from exc


def verify_supersession_preview(
    preview: dict[str, Any], *, previous: dict[str, Any],
    candidate: dict[str, Any], native_evidence: dict[str, Any],
    ontology_evidence: dict[str, Any], ontology_lock: dict[str, Any],
    base_release: str, active_mappings: list[dict[str, Any]],
) -> None:
    """Recompute a preview. This is NOT authenticated review/release verification."""
    _require(type(preview) is dict, "transition preview must be an object")
    expected = plan_native_only_supersession(
        previous=previous, candidate=candidate,
        native_evidence=native_evidence, ontology_evidence=ontology_evidence,
        ontology_lock=ontology_lock, base_release=base_release,
        active_mappings=active_mappings,
    )
    try:
        _require(canonical_json_bytes(preview) == canonical_json_bytes(expected),
                 "transition preview differs from the exact source-bound input")
    except NativeSupersessionError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise NativeSupersessionError("invalid supersession preview JSON") from exc


_BATCH_AUTHORITY = "untrusted-supersession-batch-preview"
_TRANSITION_FIELDS = frozenset({
    "previous", "candidate", "native_evidence",
    "ontology_evidence", "ontology_lock",
})


def plan_native_only_supersession_batch(
    *, transitions: list[dict[str, Any]], base_release: str,
    active_mappings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Plan 1–50 *accepted* promotions in one immutable-base cohort.

    The 10–50 *candidate* review-packet rule is enforced upstream. This
    preflight explicitly has no GitHub review or release authority, and never
    modifies the active mapping index or installed resources.
    """
    try:
        _require(
            type(transitions) is list and 1 <= len(transitions) <= 50,
            "batch must contain 1–50 proposed accepted supersessions",
        )
        _require(type(active_mappings) is list and bool(active_mappings),
                 "batch must have a nonempty pinned active base")
        previews: list[dict[str, Any]] = []
        retired: set[str] = set()
        next_ids: set[str] = set()
        projections: set[str] = set()
        native_bindings: set[bytes] = set()
        base_digest: str | None = None
        corpus_id: str | None = None
        for i, transition in enumerate(transitions):
            _require(
                type(transition) is dict
                and set(transition) == _TRANSITION_FIELDS,
                f"transition {i}: non-source-backed or extraneous fields",
            )
            preview = plan_native_only_supersession(
                previous=transition["previous"],
                candidate=transition["candidate"],
                native_evidence=transition["native_evidence"],
                ontology_evidence=transition["ontology_evidence"],
                ontology_lock=transition["ontology_lock"],
                base_release=base_release,
                active_mappings=active_mappings,
            )
            old_id = preview["retired"]["mapping_id"]
            new_id = preview["candidate"]["mapping_id"]
            projection_id = transition["candidate"]["projections"][0]["projection_id"]
            binding = canonical_json_bytes(preview["native_binding"])
            _require(old_id not in retired, "duplicate retired mapping/selector in batch")
            _require(new_id not in next_ids, "duplicate promoted mapping ID in batch")
            _require(projection_id not in projections, "duplicate promoted projection ID in batch")
            _require(binding not in native_bindings, "duplicate native selector in batch")
            _require(base_digest in (None, preview["active_base_digest"]),
                     "mixed inherited active index in batch")
            _require(corpus_id in (None, preview["corpus_id"]),
                     "batch cannot mix corpus release identities")
            retired.add(old_id)
            next_ids.add(new_id)
            projections.add(projection_id)
            native_bindings.add(binding)
            base_digest = preview["active_base_digest"]
            corpus_id = preview["corpus_id"]
            previews.append(preview)
        _require(not (retired & next_ids),
                 "batch promotion reuses a retired mapping ID")
        previews.sort(key=lambda row: row["retired"]["mapping_id"])
        record = {
            "schema_version": 1,
            "transition_kind": "native-only-to-exact-batch",
            "authority": _BATCH_AUTHORITY,
            "release_authorized": False,
            "base_release": base_release,
            "corpus_id": corpus_id,
            "active_base_digest": base_digest,
            "count": len(previews),
            "transitions": previews,
        }
        record["content_digest"] = _digest(record)
        return record
    except NativeSupersessionError:
        raise
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        raise NativeSupersessionError("invalid or untrusted batch supersession input") from exc


def verify_supersession_batch_preview(
    preview: dict[str, Any], *, transitions: list[dict[str, Any]],
    base_release: str, active_mappings: list[dict[str, Any]],
) -> None:
    """Recompute the entire untrusted batch plan (NOT a review/approval gate)."""
    _require(type(preview) is dict, "batch preview must be an object")
    expected = plan_native_only_supersession_batch(
        transitions=transitions,
        base_release=base_release,
        active_mappings=active_mappings,
    )
    try:
        _require(canonical_json_bytes(preview) == canonical_json_bytes(expected),
                 "batch preview differs from exact source-bound input")
    except NativeSupersessionError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise NativeSupersessionError("invalid untrusted batch preview JSON") from exc


_MULTI_AUTHORITY = "untrusted-multi-corpus-supersession-preview"
_MULTI_COHORT_FIELDS = frozenset({"base_release", "active_mappings", "transitions"})


def plan_multi_corpus_native_supersession(
    *, cohorts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compose 1–50 source-validated accepted promotions across corpus releases.

    Each cohort is independently checked against its own immutable active
    index. This is only an untrusted proposal preview. A protected, live,
    separately reviewed publisher must still authenticate and apply it.
    No corpus-to-corpus mapping equivalence or release authority is implied.
    """
    try:
        _require(type(cohorts) is list and 1 <= len(cohorts) <= 50,
                 "multi-corpus batch must have 1–50 nonempty cohorts")
        records: list[dict[str, Any]] = []
        seen_corpora: set[str] = set()
        total = 0
        for index, cohort in enumerate(cohorts):
            _require(type(cohort) is dict and set(cohort) == _MULTI_COHORT_FIELDS,
                     f"cohort {index}: invalid/authoritative-looking input fields")
            proposal = plan_native_only_supersession_batch(
                transitions=cohort["transitions"],
                base_release=cohort["base_release"],
                active_mappings=cohort["active_mappings"],
            )
            corpus = proposal["corpus_id"]
            _require(corpus not in seen_corpora,
                     "duplicate corpus release cohort in multi-corpus batch")
            seen_corpora.add(corpus)
            total += proposal["count"]
            _require(total <= 50,
                     "multi-corpus batch exceeds 50 proposed accepted promotions")
            records.append({
                "corpus_id": corpus,
                "base_release": proposal["base_release"],
                "count": proposal["count"],
                "batch": proposal,
            })
        records.sort(key=lambda record: record["corpus_id"])
        preview = {
            "schema_version": 1,
            "transition_kind": "native-only-to-exact-multi-corpus",
            "authority": _MULTI_AUTHORITY,
            "release_authorized": False,
            "count": total,
            "corpus_count": len(records),
            "corpora": records,
        }
        preview["content_digest"] = _digest(preview)
        return preview
    except NativeSupersessionError:
        raise
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        raise NativeSupersessionError(
            "invalid or untrusted multi-corpus supersession input"
        ) from exc


def verify_multi_corpus_native_supersession_preview(
    preview: dict[str, Any], *, cohorts: list[dict[str, Any]],
) -> None:
    """Recompute the entire preview; never authenticate GitHub review or release."""
    _require(type(preview) is dict, "multi-corpus preview must be an object")
    expected = plan_multi_corpus_native_supersession(cohorts=cohorts)
    try:
        _require(canonical_json_bytes(preview) == canonical_json_bytes(expected),
                 "multi-corpus preview differs from the source-backed cohorts")
    except NativeSupersessionError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise NativeSupersessionError("invalid multi-corpus preview JSON") from exc



__all__ = [
    "NativeSupersessionError",
    "plan_native_only_supersession",
    "verify_supersession_preview",
    "plan_native_only_supersession_batch",
    "verify_supersession_batch_preview",
    "plan_multi_corpus_native_supersession",
    "verify_multi_corpus_native_supersession_preview",
]
