"""Registry-driven loader of immutable, installed semantic profile releases.

This is a compatibility-preserving release-selection layer.  It deliberately
does not authorize new mappings or infer ontology correspondences from names.
Historical loaders in production_bundles.py remain unchanged.
"""
from __future__ import annotations

import re
from importlib.resources import files
from typing import Any

from .digests import evidence_record_digest
from .production_bundles import (
    ProductionBundleError, _artifact, _mapping_artifact,
)
from .semantic_validation import SemanticSourceBundle, validate_semantic_bundle
from .source_validation import loads_source

_CATALOGUE = ("resources", "release_catalog", "v1.json")
_ID = re.compile(r"^[a-z][a-z0-9_-]*$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _fail(message: str) -> None:
    raise ProductionBundleError(message)


def _object(value: Any, keys: set[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        _fail(f"{name}: malformed release catalogue fields")
    return value


def _path(value: Any, prefix: str, name: str) -> str:
    if type(value) is not str or not value.endswith(".json"):
        _fail(f"{name}: expected JSON resource path")
    parts = value.split("/")
    if (
        any(part in {"", ".", ".."} or "\\" in part for part in parts)
        or value.startswith("/")
        or not value.startswith(prefix + "/")
    ):
        _fail(f"{name}: unsafe/out-of-scope package resource path")
    return value


def _source_list(value: Any, prefix: str, name: str) -> tuple[str, ...]:
    if type(value) is not list or not value:
        _fail(f"{name}: release evidence paths must be a nonempty list")
    checked = tuple(_path(x, prefix, name) for x in value)
    if len(checked) != len(set(checked)):
        _fail(f"{name}: repeated evidence resource")
    return checked


def _validate_catalogue(value: Any) -> dict[str, Any]:
    catalog = _object(
        value, {"schema_version", "registry_id", "ontology_models", "corpora"}, "catalogue"
    )
    if catalog["schema_version"] != 1 or catalog["registry_id"] != "tfont-release-catalog-v1":
        _fail("unsupported release catalogue revision")
    models = catalog["ontology_models"]
    corpora = catalog["corpora"]
    if type(models) is not dict or not models or type(corpora) is not dict or not corpora:
        _fail("missing model or corpus registry")
    for model, spec in models.items():
        if type(model) is not str or not _ID.fullmatch(model):
            _fail("invalid model identity")
        _object(spec, {"ontology_revision", "root"}, f"model {model}")
        if type(spec["ontology_revision"]) is not str or not re.fullmatch(
            r"[0-9a-f]{40}", spec["ontology_revision"]
        ):
            _fail(f"{model}: invalid ontology revision pin")
        if spec["root"] != f"resources/ontologies/{model}/{spec['ontology_revision']}":
            _fail(f"{model}: ontology resource root does not match source revision")
    for corpus, spec in corpora.items():
        if type(corpus) is not str or not _ID.fullmatch(corpus):
            _fail("invalid corpus identity")
        _object(spec, {"current", "releases"}, f"corpus {corpus}")
        releases = spec["releases"]
        if type(releases) is not dict or not releases:
            _fail(f"{corpus}: release list missing")
        if spec["current"] not in releases:
            _fail(f"{corpus}: current release alias has no pinned entry")
        for version, rel in releases.items():
            if type(version) is not str or not _VERSION.fullmatch(version):
                _fail(f"{corpus}: invalid release identifier")
            _object(
                rel,
                {"profile", "parent", "native_evidence", "ontology_model",
                 "ontology_lock", "ontology_evidence"},
                f"{corpus}/{version}",
            )
            base = f"resources/profiles/{corpus}/{version}"
            if rel["profile"] != f"{base}/profile.json":
                _fail(f"{corpus}/{version}: wrong-corpus profile resource")
            if rel["parent"] != f"{base}/parent/expected-components.json":
                _fail(f"{corpus}/{version}: wrong-corpus component manifest")
            model = rel["ontology_model"]
            if type(model) is not str or model not in models:
                _fail(f"{corpus}/{version}: unknown ontology model")
            ontology_root = models[model]["root"]
            _path(rel["ontology_lock"], ontology_root, "ontology lock")
            _source_list(rel["native_evidence"], "resources/profiles", "native evidence")
            _source_list(rel["ontology_evidence"], ontology_root, "ontology evidence")
    return catalog


def _load_catalogue() -> dict[str, Any]:
    """Read only packaged local JSON; never fetch a remote default revision."""
    try:
        source = files("tfont").joinpath(*_CATALOGUE)
        decoded = loads_source(
            source.read_text(encoding="utf-8"),
            format="json", source_name="/".join(_CATALOGUE),
        )
    except (OSError, UnicodeError, ValueError) as exc:
        _fail(f"release catalogue unavailable or invalid: {exc}")
    return _validate_catalogue(decoded)


def _load_from_catalogue(
    catalogue: dict[str, Any],
    corpus_id: str,
    release_id: str = "current",
    models: tuple[str, ...] = ("olia",),
) -> SemanticSourceBundle:
    """Private injection point for adversarial tests; validates input exhaustively."""
    catalog = _validate_catalogue(catalogue)
    if (
        type(corpus_id) is not str
        or corpus_id not in catalog["corpora"]
        or type(release_id) is not str
        or type(models) is not tuple
        or len(models) != 1
        or type(models[0]) is not str
    ):
        _fail("unsupported corpus, release, or model selection")
    spec = catalog["corpora"][corpus_id]
    version = spec["current"] if release_id == "current" else release_id
    release = spec["releases"].get(version)
    if release is None or release["ontology_model"] != models[0]:
        _fail(f"{corpus_id}: unavailable release or ontology model")

    try:
        profile = _artifact("profile", "profile", release["profile"])
        parent = _artifact(
            "parent-component-manifest", "parent-component-manifest", release["parent"]
        )
        root = f"resources/profiles/{corpus_id}/{version}"
        if (
            profile.data.get("profile_id") != f"tfont-{corpus_id}"
            or profile.data.get("profile_version") != version
            or profile.data.get("parent_component_manifest") != "parent/expected-components.json"
        ):
            _fail(f"{corpus_id}: profile identity/version/parent mismatch")
        evidence_names = (
            *release["native_evidence"], *release["ontology_evidence"]
        )
        evidences = tuple(
            _artifact("evidence", "evidence", name) for name in evidence_names
        )
        for name, artifact in zip(evidence_names, evidences):
            if artifact.data.get("content_mode") == "normalized-record":
                if artifact.data.get("content_digest") != evidence_record_digest(artifact.data):
                    _fail(f"{name}: evidence content digest is not canonical")
        lock = _artifact(
            "ontology-lock", "ontology-lock", release["ontology_lock"]
        )
        expected_ontology_revision = catalog["ontology_models"][models[0]]["ontology_revision"]
        if lock.data.get("source_revision") != expected_ontology_revision:
            _fail(f"{corpus_id}: ontology source pin does not match catalogue")
        bundle = SemanticSourceBundle(
            profile=profile,
            expected_parent_manifest=parent,
            mappings=_mapping_artifact(root, profile),
            ontology_locks=(lock,),
            evidences=evidences,
        )
        validate_semantic_bundle(bundle)
        return bundle
    except ProductionBundleError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        _fail(f"{corpus_id}/{version}: invalid or missing pinned release resource: {exc}")


def load_profile(
    corpus_id: str,
    release_id: str = "current",
    models: tuple[str, ...] = ("olia",),
) -> SemanticSourceBundle:
    """Load an explicitly registered, source-validated semantic profile release."""
    return _load_from_catalogue(_load_catalogue(), corpus_id, release_id, models)


def list_profile_releases(corpus_id: str) -> tuple[str, ...]:
    """List published installed versions, not experimental/unreviewed branches."""
    catalogue = _load_catalogue()
    if type(corpus_id) is not str or corpus_id not in catalogue["corpora"]:
        _fail(f"unknown corpus {corpus_id!r}")
    versions = catalogue["corpora"][corpus_id]["releases"]
    return tuple(sorted(versions, key=lambda v: tuple(map(int, v.split(".")))))


__all__ = ["load_profile", "list_profile_releases"]
