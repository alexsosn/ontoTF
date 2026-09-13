from __future__ import annotations

from importlib.resources import files
from typing import Any, cast

from .semantic_validation import SemanticArtifact, SemanticSourceBundle
from .source_validation import loads_source, validate_source

PRODUCTION_NOUN_CORPORA = ("bhsa", "syriac", "extrabiblical")
_PROFILE_VERSION = "0.1.0"
_OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
_OLIA_ROOT = f"resources/ontologies/olia/{_OLIA_REVISION}"
_CORPUS_EVIDENCE = {
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


class ProductionBundleError(ValueError):
    def __init__(self, corpus_id: object) -> None:
        self.corpus_id = corpus_id
        super().__init__(f"unsupported production Noun corpus: {corpus_id!r}")


def _artifact(kind: str, schema_name: str, source_name: str) -> SemanticArtifact:
    resource = files("tfont").joinpath(*source_name.split("/"))
    data = loads_source(
        resource.read_text(encoding="utf-8"),
        format="json",
        source_name=source_name,
    )
    validate_source(data, schema_name, source_name=source_name)
    return SemanticArtifact(kind, source_name, cast(dict[str, Any], data))


def load_production_noun_bundle(corpus_id: str) -> SemanticSourceBundle:
    if type(corpus_id) is not str or corpus_id not in PRODUCTION_NOUN_CORPORA:
        raise ProductionBundleError(corpus_id)
    root = f"resources/profiles/{corpus_id}/{_PROFILE_VERSION}"
    evidences = tuple(
        _artifact("evidence", "evidence", source_name)
        for source_name in (
            *_CORPUS_EVIDENCE[corpus_id],
            f"{_OLIA_ROOT}/noun-evidence.json",
        )
    )
    return SemanticSourceBundle(
        profile=_artifact("profile", "profile", f"{root}/profile.json"),
        expected_parent_manifest=_artifact(
            "parent-component-manifest",
            "parent-component-manifest",
            f"{root}/parent/expected-components.json",
        ),
        mappings=_artifact("mapping", "mapping", f"{root}/mappings/noun.json"),
        ontology_locks=(
            _artifact("ontology-lock", "ontology-lock", f"{_OLIA_ROOT}/lock.json"),
        ),
        evidences=evidences,
    )


def load_production_noun_bundles() -> tuple[SemanticSourceBundle, ...]:
    return tuple(load_production_noun_bundle(corpus_id) for corpus_id in PRODUCTION_NOUN_CORPORA)


__all__ = [
    "PRODUCTION_NOUN_CORPORA",
    "ProductionBundleError",
    "load_production_noun_bundle",
    "load_production_noun_bundles",
]
