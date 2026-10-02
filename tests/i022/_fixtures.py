from __future__ import annotations

from typing import Any

from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import _refresh_mapping, noun_semantic_key
from tests.i008._fixtures import FakeLoadedApi, loaded_context
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


def membership_sources(
    *,
    corpus_id: str = "bhsa",
    parent_char: str = "a",
    dependency_kind: str = "node-type-present",
    dependency_component: str | None = None,
    dependency_node_type: str = "word",
    node_type: str = "word",
) -> dict[str, Any]:
    sources = noun_sources(corpus_id, parent_char=parent_char)
    component_id = f"{corpus_id}-tf"
    dependency = sources["profile"]["dependencies"][0]
    dependency["kind"] = dependency_kind
    dependency["component_id"] = dependency_component or component_id
    dependency["assertion"] = (
        {"node_type": dependency_node_type}
        if dependency_kind == "node-type-present"
        else {}
    )

    mapping = sources["mappings"]["mappings"][0]
    binding = {
        "component_id": component_id,
        "node_type": node_type,
        "execution_shape": "membership",
    }
    mapping["native_binding"] = dict(binding)
    mapping["projections"][0]["native_execution_binding"] = dict(binding)
    _refresh_mapping(mapping)
    return sources


def validated_membership_bundle(**kwargs):
    sources = membership_sources(**kwargs)
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def compiled_membership_ir(**kwargs):
    return compile_semantic_ir((validated_membership_bundle(**kwargs),))


def membership_api(
    *,
    nodes: tuple[int, ...] = (4, 2, 7),
    node_type: str = "word",
):
    return FakeLoadedApi(
        values={node: "unused" for node in nodes},
        node_types={node: node_type for node in nodes},
        loaded_features=("otype",),
    )


def membership_context(tfont_module, ir, api=None):
    return loaded_context(
        tfont_module,
        ir,
        "bhsa",
        api or membership_api(),
    )


def membership_request(tfont_module):
    return tfont_module.SemanticResolveRequest(
        key=noun_semantic_key(),
        corpora=("bhsa",),
    )


def compiled_edge_path_ir():
    sources = membership_sources()
    mapping = sources["mappings"]["mappings"][0]
    binding = {
        "component_id": "bhsa-tf",
        "node_type": "word",
        "execution_shape": "edge-path",
    }
    mapping["native_binding"] = dict(binding)
    mapping["projections"][0]["native_execution_binding"] = dict(binding)
    _refresh_mapping(mapping)
    validate_structural_sources(sources)
    return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))
