from __future__ import annotations

import copy
import operator
from typing import Any, Iterable

from tests.i005._fixtures import (
    catalogue_reference,
    entity_identity_reference,
    noun_sources,
    source_bundle,
    validate_structural_sources,
)
from tests.i006._fixtures import _refresh_mapping, noun_semantic_key
from tests.i008._fixtures import loaded_context
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
    projection_route: str = "semantic",
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
    external_references: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    sources = noun_sources(
        corpus_id,
        parent_char=parent_char,
        projection_route=projection_route,
        external_references=external_references,
    )
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
    if mapping["projections"]:
        projection = mapping["projections"][0]
        projection["native_execution_binding"] = dict(binding)
        projection["assessment"] = assessment
        projection.pop("approximation", None)
        if assessment in {"broader", "narrower", "close"}:
            projection["approximation"] = {
                "status": "reviewed",
                "eligible": True,
                "losses": list(losses),
                "rationale": f"I-022 membership fixture {assessment}",
                "review_id": f"review:i022:{corpus_id}:{assessment}",
                "evidence": [],
            }

    for reference in mapping["external_references"]:
        if reference.get("native_binding") is not None:
            reference["native_binding"] = dict(binding)

    _refresh_mapping(mapping)
    return sources


def validated_membership_bundle(**kwargs):
    sources = membership_sources(**kwargs)
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def compiled_membership_ir(**kwargs):
    return compile_semantic_ir((validated_membership_bundle(**kwargs),))


class Namespace:
    pass


class MembershipOtype:
    def __init__(
        self,
        selections: Iterable[Any] = ((4, 2, 7),),
        *,
        node_types: dict[int, Any] | None = None,
        raise_on_v: bool = False,
    ) -> None:
        self.selections = tuple(selections)
        self.node_types = dict(node_types or {4: "word", 2: "word", 7: "word"})
        self.raise_on_v = raise_on_v
        self.s_calls = 0
        self.v_calls = 0

    def s(self, node_type: str):
        self.s_calls += 1
        if not self.selections:
            return ()
        index = min(self.s_calls - 1, len(self.selections) - 1)
        value = self.selections[index]
        if isinstance(value, BaseException):
            raise value
        return value

    def v(self, node: Any):
        self.v_calls += 1
        if self.raise_on_v:
            raise RuntimeError("otype lookup failed")
        try:
            normalized = operator.index(node)
        except TypeError:
            normalized = node
        return self.node_types.get(normalized)


class ExplodingEdges:
    def __init__(self) -> None:
        self.touched = False

    def __getattr__(self, name: str):
        self.touched = True
        raise AssertionError(f"I-022 membership must not access edge API: {name}")


class MembershipApi:
    def __init__(
        self,
        *,
        selections: Iterable[Any] = ((4, 2, 7),),
        node_types: dict[int, Any] | None = None,
        raise_on_v: bool = False,
    ) -> None:
        self.F = Namespace()
        self.F.otype = MembershipOtype(
            selections,
            node_types=node_types,
            raise_on_v=raise_on_v,
        )
        self.E = ExplodingEdges()
        self.load_calls = 0

    def Fall(self):
        return ("otype",)

    def Eall(self):
        self.E.touched = True
        raise AssertionError("I-022 membership must not enumerate edge features")

    def load(self, *args, **kwargs):
        self.load_calls += 1
        raise AssertionError("I-022 membership must never autoload features")


def membership_api(
    *,
    selections: Iterable[Any] = ((4, 2, 7),),
    node_types: dict[int, Any] | None = None,
    raise_on_v: bool = False,
):
    return MembershipApi(
        selections=selections,
        node_types=node_types,
        raise_on_v=raise_on_v,
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


def approximate_membership_request(tfont_module, *, accept_losses=()):
    return tfont_module.ApproximateSemanticResolveRequest(
        key=noun_semantic_key(),
        corpora=("bhsa",),
        semantic_mode="approximate",
        accept_losses=tuple(accept_losses),
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


def compiled_reference_membership_ir():
    refs = [
        entity_identity_reference("bhsa"),
        catalogue_reference("bhsa"),
    ]
    return compiled_membership_ir(external_references=refs)


def compiled_authority_membership_ir(
    *,
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
):
    return compiled_membership_ir(
        projection_route="authority",
        assessment=assessment,
        losses=losses,
    )


def compiled_two_key_membership_ir():
    sources = membership_sources()
    first = sources["mappings"]["mappings"][0]
    second = copy.deepcopy(first)
    second["mapping_id"] = "mapping:bhsa:proper-noun"
    second["review"]["review_id"] = "review:bhsa:mapping:proper-noun"
    projection = second["projections"][0]
    projection["projection_id"] = "projection:bhsa:proper-noun"
    projection["target"] = "http://purl.org/olia/olia.owl#ProperNoun"
    projection["review"]["review_id"] = "review:bhsa:projection:proper-noun"
    sources["locks"][0]["terms_used"].append(
        "http://purl.org/olia/olia.owl#ProperNoun"
    )
    _refresh_mapping(second)
    sources["mappings"]["mappings"].append(second)
    validate_structural_sources(sources)
    return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))


def proper_noun_key(tfont_module):
    return tfont_module.SemanticKey(
        profile_id="linguistic",
        capability_id="linguistic.part-of-speech",
        target="http://purl.org/olia/olia.owl#ProperNoun",
        formal_kind="class",
        semantic_role="annotation-value",
    )
