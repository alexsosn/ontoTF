from __future__ import annotations

from importlib.resources import files
from typing import Any, cast

from .semantic_validation import SemanticArtifact, SemanticSourceBundle
from .source_validation import loads_source, validate_source

PRODUCTION_NOUN_CORPORA = ("bhsa", "syriac", "extrabiblical")
PRODUCTION_LINGUISTIC_CORPORA = PRODUCTION_NOUN_CORPORA
_NOUN_PROFILE_VERSION = "0.1.0"
_LINGUISTIC_PROFILE_VERSION = "0.2.0"
_OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
_OLIA_ROOT = f"resources/ontologies/olia/{_OLIA_REVISION}"

_NOUN_EVIDENCE = {
    "bhsa": ("resources/profiles/bhsa/0.1.0/evidence/native-pos.json",),
    "syriac": (
        "resources/profiles/syriac/0.1.0/evidence/native-pos.json",
        "resources/profiles/syriac/0.1.0/evidence/proper-noun-encoding.json",
    ),
    "extrabiblical": (
        "resources/profiles/extrabiblical/0.1.0/evidence/native-pos-enum.json",
        "resources/profiles/extrabiblical/0.1.0/evidence/feature-authority.json",
        "resources/profiles/bhsa/0.1.0/evidence/native-pos.json",
    ),
}
_LINGUISTIC_EVIDENCE = {
    "bhsa": (
        "resources/profiles/bhsa/0.2.0/evidence/native-pos.json",
        "resources/profiles/bhsa/0.2.0/evidence/native-gender.json",
        "resources/profiles/bhsa/0.2.0/evidence/native-number.json",
    ),
    "syriac": (
        "resources/profiles/syriac/0.2.0/evidence/native-pos.json",
        "resources/profiles/syriac/0.2.0/evidence/proper-noun-encoding.json",
        "resources/profiles/syriac/0.2.0/evidence/noun-morphology.json",
    ),
    "extrabiblical": (
        "resources/profiles/extrabiblical/0.2.0/evidence/native-pos-enum.json",
        "resources/profiles/extrabiblical/0.2.0/evidence/feature-authority.json",
        "resources/profiles/extrabiblical/0.2.0/evidence/native-gender-observed.json",
        "resources/profiles/extrabiblical/0.2.0/evidence/native-number-observed.json",
        "resources/profiles/bhsa/0.2.0/evidence/native-pos.json",
        "resources/profiles/bhsa/0.2.0/evidence/native-gender.json",
        "resources/profiles/bhsa/0.2.0/evidence/native-number.json",
    ),
}


class ProductionBundleError(ValueError):
    def __init__(self, corpus_id: object) -> None:
        self.corpus_id = corpus_id
        super().__init__(f"unsupported production corpus: {corpus_id!r}")


def _artifact(kind: str, schema_name: str, source_name: str) -> SemanticArtifact:
    resource = files("tfont").joinpath(*source_name.split("/"))
    data = loads_source(
        resource.read_text(encoding="utf-8"),
        format="json",
        source_name=source_name,
    )
    validate_source(data, schema_name, source_name=source_name)
    return SemanticArtifact(kind, source_name, cast(dict[str, Any], data))


def _mapping_artifact(root: str, profile: SemanticArtifact) -> SemanticArtifact:
    sources = profile.data.get("mapping_sources")
    if type(sources) is not list or not sources:
        raise ProductionBundleError(profile.data.get("profile_id"))
    artifacts: list[SemanticArtifact] = []
    for relative in sources:
        if type(relative) is not str or not relative:
            raise ProductionBundleError(profile.data.get("profile_id"))
        artifacts.append(_artifact("mapping", "mapping", f"{root}/{relative}"))
    if len(artifacts) == 1:
        return artifacts[0]
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        rows.extend(cast(list[dict[str, Any]], artifact.data["mappings"]))
    combined = {"schema_version": 2, "mappings": rows}
    validate_source(combined, "mapping", source_name=f"{root}/mappings/combined")
    return SemanticArtifact("mapping", f"{root}/mappings/combined", combined)


def _load_bundle(
    corpus_id: str,
    *,
    corpora: tuple[str, ...],
    profile_version: str,
    evidence_sources: dict[str, tuple[str, ...]],
    lock_name: str,
    include_morphology_evidence: bool,
) -> SemanticSourceBundle:
    if type(corpus_id) is not str or corpus_id not in corpora:
        raise ProductionBundleError(corpus_id)
    root = f"resources/profiles/{corpus_id}/{profile_version}"
    profile = _artifact("profile", "profile", f"{root}/profile.json")
    ontology_evidence = [f"{_OLIA_ROOT}/noun-evidence.json"]
    if include_morphology_evidence:
        ontology_evidence.append(f"{_OLIA_ROOT}/noun-morphology-evidence.json")
    evidences = tuple(
        _artifact("evidence", "evidence", source_name)
        for source_name in (*evidence_sources[corpus_id], *ontology_evidence)
    )
    return SemanticSourceBundle(
        profile=profile,
        expected_parent_manifest=_artifact(
            "parent-component-manifest",
            "parent-component-manifest",
            f"{root}/parent/expected-components.json",
        ),
        mappings=_mapping_artifact(root, profile),
        ontology_locks=(
            _artifact("ontology-lock", "ontology-lock", f"{_OLIA_ROOT}/{lock_name}"),
        ),
        evidences=evidences,
    )


def load_production_noun_bundle(corpus_id: str) -> SemanticSourceBundle:
    return _load_bundle(
        corpus_id,
        corpora=PRODUCTION_NOUN_CORPORA,
        profile_version=_NOUN_PROFILE_VERSION,
        evidence_sources=_NOUN_EVIDENCE,
        lock_name="lock.json",
        include_morphology_evidence=False,
    )


def load_production_noun_bundles() -> tuple[SemanticSourceBundle, ...]:
    return tuple(load_production_noun_bundle(corpus_id) for corpus_id in PRODUCTION_NOUN_CORPORA)


def load_production_linguistic_bundle(corpus_id: str) -> SemanticSourceBundle:
    return _load_bundle(
        corpus_id,
        corpora=PRODUCTION_LINGUISTIC_CORPORA,
        profile_version=_LINGUISTIC_PROFILE_VERSION,
        evidence_sources=_LINGUISTIC_EVIDENCE,
        lock_name="lock-linguistic-0.2.0.json",
        include_morphology_evidence=True,
    )


def load_production_linguistic_bundles() -> tuple[SemanticSourceBundle, ...]:
    return tuple(
        load_production_linguistic_bundle(corpus_id)
        for corpus_id in PRODUCTION_LINGUISTIC_CORPORA
    )


__all__ = [
    "PRODUCTION_LINGUISTIC_CORPORA",
    "PRODUCTION_NOUN_CORPORA",
    "ProductionBundleError",
    "load_production_linguistic_bundle",
    "load_production_linguistic_bundles",
    "load_production_noun_bundle",
    "load_production_noun_bundles",
]
