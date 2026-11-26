"""Immutable *published-release* deltas, without granting new review authority.

This module reads only registered, already-reviewed packaged releases. A local
proposal, self-declared review flag or supplied GitHub JSON can NEVER use this
interface to publish. It proves semantic parity and provides the compact
reference format needed by a later protected, externally attested publisher.

These are data references, not copies of past noun/morphology/verb mappings or
coverage denominators. Historical release resources remain untouched.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any

from .digests import canonical_json_bytes
from .production_bundles import _artifact
from .release_registry import load_profile
from .semantic_validation import (
    SemanticArtifact, SemanticSourceBundle, validate_semantic_bundle,
)


class PublishedDeltaError(ValueError):
    """A source/target published release or immutable overlay differs."""


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise PublishedDeltaError(message)


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _source_bundle_signature(bundle: SemanticSourceBundle) -> str:
    return _sha({
        "profile": bundle.profile.data,
        "parent": bundle.expected_parent_manifest.data,
        "mappings": bundle.mappings.data,
        "locks": [x.data for x in bundle.ontology_locks],
        "evidence": [x.data for x in bundle.evidences],
    })


def _published_release(corpus: str, release: str) -> SemanticSourceBundle:
    try:
        _require(type(corpus) is str and type(release) is str
                 and release != "current", "must select explicit published release")
        bundle = load_profile(corpus, release_id=release)
        validate_semantic_bundle(bundle)
        return bundle
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise PublishedDeltaError("missing or invalid published immutable release") from exc


def _mapping_index(bundle: SemanticSourceBundle) -> dict[str, dict[str, Any]]:
    rows = bundle.mappings.data["mappings"]
    ids = [x["mapping_id"] for x in rows]
    _require(len(ids) == len(set(ids)), "duplicate published mapping IDs")
    return {x["mapping_id"]: x for x in rows}


def _new_mapping_sources(
    corpus: str, release: str, profile: SemanticArtifact,
    ids: set[str],
) -> dict[str, str]:
    """Locate new IDs by inspecting the *published* target source fragments."""
    results: dict[str, str] = {}
    path_prefix = f"resources/profiles/{corpus}/{release}/"
    for part in profile.data["mapping_sources"]:
        _require(type(part) is str and part.startswith("mappings/")
                 and ".." not in part.split("/") and "\\" not in part,
                 "unsafe published mapping path")
        resource = path_prefix + part
        artifact = _artifact("mapping", "mapping", resource)
        for entry in artifact.data["mappings"]:
            ident = entry["mapping_id"]
            if ident in ids:
                _require(ident not in results, "duplicate new published mapping source")
                results[ident] = resource
    _require(set(results) == ids, "added mapping not in published fragment")
    return results


def _difference(
    corpus: str, base: SemanticSourceBundle, target: SemanticSourceBundle,
    *,
    base_release: str, target_release: str,
) -> dict[str, Any]:
    b, t = base.profile.data, target.profile.data
    _require(b["profile_id"] == t["profile_id"] == f"tfont-{corpus}"
             and b["profile_version"] == base_release
             and t["profile_version"] == target_release,
             "published corpus/profile identity drift")
    _require(base.expected_parent_manifest.data == target.expected_parent_manifest.data,
             "published parent-component identity changed")
    excluded = {"profile_version", "mapping_sources", "dependencies"}
    _require(
        {k:v for k,v in b.items() if k not in excluded}
        == {k:v for k,v in t.items() if k not in excluded},
        "non-additive published profile semantic change",
    )

    old_rows, new_rows = _mapping_index(base), _mapping_index(target)
    for ident, original in old_rows.items():
        _require(ident in new_rows
                 and canonical_json_bytes(original) == canonical_json_bytes(new_rows[ident]),
                 "published overlay changed or deleted inherited reviewed mapping")
    new_ids = set(new_rows) - set(old_rows)
    _require(bool(new_ids), "published target adds no new mapping")
    mapping_locations = _new_mapping_sources(corpus, target_release, target.profile, new_ids)
    old_dep = {row["dependency_id"]:row for row in b["dependencies"]}
    next_dep = {row["dependency_id"]:row for row in t["dependencies"]}
    _require(len(old_dep) == len(b["dependencies"])
             and len(next_dep) == len(t["dependencies"]), "duplicate native dependency")
    for ident, old in old_dep.items():
        _require(ident in next_dep
                 and canonical_json_bytes(next_dep[ident]) == canonical_json_bytes(old),
                 "published overlay replaced or removed inherited native dependency")
    added_dep = set(next_dep) - set(old_dep)

    prev_ev={row.data["evidence_id"]:row for row in base.evidences}
    next_ev={row.data["evidence_id"]:row for row in target.evidences}
    _require(len(prev_ev)==len(base.evidences)
             and len(next_ev)==len(target.evidences),"duplicate evidence ID")
    for ident,original in prev_ev.items():
        _require(ident in next_ev
                 and canonical_json_bytes(next_ev[ident].data)
                     == canonical_json_bytes(original.data),
                 "inherited evidence changed or disappeared")
    added_ev=set(next_ev)-set(prev_ev)
    # Only the actual published target lock can extend the set of terms.
    for original_lock in base.ontology_locks:
        candidates=[x for x in target.ontology_locks
                    if x.data["lock_id"]==original_lock.data["lock_id"]]
        _require(len(candidates)==1
                 and candidates[0].data["source_revision"]
                     == original_lock.data["source_revision"]
                 and set(original_lock.data["terms_used"])
                     <= set(candidates[0].data["terms_used"]),
                 "target ontology lock loses prior terms or changes revision")

    referenced_dependencies: set[str] = set()
    for ident in new_ids:
        mapped = new_rows[ident]
        used = set(mapped["native_dependencies"])
        _require(used <= set(next_dep),
                 "new mapping references an undeclared native dependency")
        referenced_dependencies.update(used)
        refs={ref["evidence_id"] for ref in mapped["evidence"]}
        _require(refs <= set(next_ev), "new mapping lacks pinned published evidence")
    _require(added_dep <= referenced_dependencies,
             "published overlay introduces an unused native dependency")

    return {
        "schema_version": 1,
        "authority": "published-registry-parity-only",
        "corpus_id": corpus,
        "base_release": base_release,
        "target_release": target_release,
        "base_bundle_digest": _source_bundle_signature(base),
        "target_bundle_digest": _source_bundle_signature(target),
        "ontology_model": "olia",
        "ontology_lock_digest": _sha([x.data for x in target.ontology_locks]),
        "added_mappings": [
            {
                "mapping_id": ident,
                "source_resource": mapping_locations[ident],
                "semantic_digest": new_rows[ident]["mapping_semantic_digest"],
            }
            for ident in sorted(new_ids)
        ],
        "added_dependencies": [
            {"dependency_id":ident,"record_digest":_sha(next_dep[ident])}
            for ident in sorted(added_dep)
        ],
        "added_evidence": [
            {
                "evidence_id":ident,
                "source_resource":next_ev[ident].source_name,
                "content_digest":next_ev[ident].data["content_digest"],
            }
            for ident in sorted(added_ev)
        ],
    }


def build_published_delta(
    corpus_id: str, base_release: str, target_release: str,
) -> dict[str, Any]:
    """Create a compact delta only between *already published* catalog releases.

    This is deliberately NOT a new-release publisher or authority verifier.
    """
    _require(type(base_release) is str and type(target_release) is str
             and base_release != target_release, "invalid immutable release pair")
    base = _published_release(corpus_id, base_release)
    target = _published_release(corpus_id, target_release)
    return _difference(
        corpus_id,base,target,base_release=base_release,target_release=target_release
    )


def load_published_delta(delta: dict[str, Any]) -> SemanticSourceBundle:
    """Recompose from inherited + added *published* records; fail on drift.

    No external approval JSON is accepted here. Every source is re-read from
    the registry before exact JCS comparison, and the result is revalidated.
    """
    _require(type(delta) is dict, "delta must be a JSON object")
    _require(type(delta.get("authority")) is str
             and delta.get("authority")=="published-registry-parity-only",
             "only published-registry parity deltas are supported")
    allowed = {
        "schema_version","authority","corpus_id","base_release","target_release",
        "base_bundle_digest","target_bundle_digest","ontology_model",
        "ontology_lock_digest","added_mappings","added_dependencies","added_evidence",
    }
    _require(set(delta)==allowed, "unexpected release or reviewer-authority fields")
    _require(type(delta["schema_version"]) is int and delta["schema_version"]==1,
             "unsupported published delta schema")
    expected=build_published_delta(
        delta["corpus_id"],delta["base_release"],delta["target_release"],
    )
    _require(canonical_json_bytes(delta)==canonical_json_bytes(expected),
             "published overlay differs from validated installed release sources")

    corpus,base_release,target_release=(
        delta["corpus_id"],delta["base_release"],delta["target_release"]
    )
    base=_published_release(corpus,base_release)
    target=_published_release(corpus,target_release)
    base_rows=copy.deepcopy(base.mappings.data["mappings"])
    known={x["mapping_id"] for x in base_rows}
    appended=[
        copy.deepcopy(row)
        for row in target.mappings.data["mappings"]
        if row["mapping_id"] not in known
    ]
    profile=copy.deepcopy(base.profile.data)
    profile["profile_version"]=target_release
    profile["dependencies"]=copy.deepcopy(base.profile.data["dependencies"])+[
        copy.deepcopy(row) for row in target.profile.data["dependencies"]
        if row["dependency_id"] not in {
            old["dependency_id"] for old in base.profile.data["dependencies"]
        }
    ]
    # Legacy loader mappings are named by the target profile; new delta
    # catalogs will instead reference a base release and a changed fragment.
    profile["mapping_sources"]=copy.deepcopy(target.profile.data["mapping_sources"])
    composite=SemanticSourceBundle(
        profile=SemanticArtifact("profile",target.profile.source_name,profile),
        expected_parent_manifest=SemanticArtifact(
            "parent-component-manifest",target.expected_parent_manifest.source_name,
            copy.deepcopy(base.expected_parent_manifest.data),
        ),
        mappings=SemanticArtifact(
            "mapping",target.mappings.source_name,
            {"schema_version":2,"mappings":base_rows+appended},
        ),
        ontology_locks=target.ontology_locks,
        evidences=target.evidences,
    )
    validate_semantic_bundle(composite)
    _require(composite==target,
             "recomposed additive delta differs from immutable published target")
    return composite


__all__ = [
    "PublishedDeltaError","build_published_delta","load_published_delta",
]
