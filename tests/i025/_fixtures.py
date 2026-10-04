from __future__ import annotations

import copy
from typing import Any, Iterable

from tests.i005._fixtures import (
    catalogue_reference,
    entity_identity_reference,
    source_bundle,
    validate_structural_sources,
)
from tests.i006._fixtures import _refresh_mapping
from tests.i008._fixtures import loaded_context
from tests.i023._fixtures import PathApi, edge_path_sources
from tests.i024._fixtures import ValuedFakeEdgeFeature
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


SEMANTIC_STR_VALUES = ("ambiguous", "unique")


def predicate_step(
    *,
    direction: str = "outgoing",
    value_type: str = "str",
    value_role: str = "semantic-qualifier",
    match_values: Iterable[Any] = ("ambiguous",),
    edge: str | None = None,
    result_node_type: str | None = None,
) -> dict[str, Any]:
    if edge is None:
        edge = "witness_resolution" if value_type == "str" else "quality_score"
    if result_node_type is None:
        result_node_type = "fragment" if direction == "outgoing" else "line"
    return {
        "edge": edge,
        "direction": direction,
        "result_node_type": result_node_type,
        "valued": True,
        "value_type": value_type,
        "value_role": value_role,
        "match_values": list(match_values),
    }


def edge_domain_dependency(
    sources: dict[str, Any],
    *,
    edge: str = "witness_resolution",
    source_node_type: str = "line",
    target_node_type: str = "fragment",
    value_type: str = "str",
    value_role: str = "semantic-qualifier",
    values: Iterable[Any] = SEMANTIC_STR_VALUES,
    domain_semantics: str = "closed-reviewed",
    dependency_id: str = "dep:bhsa:witness-resolution:domain",
) -> dict[str, Any]:
    evidence = sources["evidences"][0]
    return {
        "dependency_id": dependency_id,
        "component_id": "bhsa-tf",
        "kind": "edge-value-domain",
        "assertion": {
            "edge": edge,
            "source_node_type": source_node_type,
            "target_node_type": target_node_type,
            "value_type": value_type,
            "value_role": value_role,
            "values": list(values),
            "domain_semantics": domain_semantics,
        },
        "evidence": [
            {
                "evidence_id": evidence["evidence_id"],
                "content_digest": evidence["content_digest"],
            }
        ],
    }


def predicate_sources(
    *,
    direction: str = "outgoing",
    value_type: str = "str",
    value_role: str = "semantic-qualifier",
    match_values: Iterable[Any] = ("ambiguous",),
    domain_values: Iterable[Any] | None = None,
    domain_value_role: str = "semantic-qualifier",
    domain_semantics: str = "closed-reviewed",
    projection_route: str = "semantic",
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
    external_references: list[dict[str, Any]] | None = None,
):
    start_node_type = "line" if direction == "outgoing" else "fragment"
    step = predicate_step(
        direction=direction,
        value_type=value_type,
        value_role=value_role,
        match_values=match_values,
    )
    sources = edge_path_sources(
        start_node_type=start_node_type,
        steps=(step,),
        projection_route=projection_route,
        assessment=assessment,
        losses=losses,
        external_references=external_references,
    )
    sources["profile"]["dependency_contract_version"] = 2

    if domain_values is None:
        domain_values = SEMANTIC_STR_VALUES if value_type == "str" else (1, 2)
    edge = step["edge"]
    dependency = edge_domain_dependency(
        sources,
        edge=edge,
        source_node_type="line",
        target_node_type="fragment",
        value_type=value_type,
        value_role=domain_value_role,
        values=domain_values,
        domain_semantics=domain_semantics,
        dependency_id=f"dep:bhsa:{edge}:domain",
    )
    sources["profile"]["dependencies"].append(dependency)

    mapping = sources["mappings"]["mappings"][0]
    mapping["native_dependencies"].append(dependency["dependency_id"])
    _refresh_mapping(mapping)
    return sources


def validated_predicate_bundle(**kwargs):
    sources = predicate_sources(**kwargs)
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def compiled_predicate_ir(**kwargs):
    return compile_semantic_ir((validated_predicate_bundle(**kwargs),))


def compiled_authority_predicate_ir(
    *,
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
    **kwargs,
):
    return compiled_predicate_ir(
        projection_route="authority",
        assessment=assessment,
        losses=losses,
        **kwargs,
    )


def compiled_reference_predicate_ir(**kwargs):
    return compiled_predicate_ir(
        external_references=[
            entity_identity_reference("bhsa"),
            catalogue_reference("bhsa"),
        ],
        **kwargs,
    )


def compiled_mixed_conjunction_predicate_ir():
    sources = predicate_sources()
    first = sources["mappings"]["mappings"][0]

    second = copy.deepcopy(first)
    second["mapping_id"] = "mapping:bhsa:proper-noun"
    second["review"]["review_id"] = "review:bhsa:mapping:proper-noun"
    membership = {
        "component_id": "bhsa-tf",
        "node_type": "fragment",
        "execution_shape": "membership",
    }
    second["native_dependencies"] = ["dep:bhsa:node-type:fragment"]
    second["native_binding"] = copy.deepcopy(membership)

    projection = second["projections"][0]
    projection["projection_id"] = "projection:bhsa:proper-noun"
    projection["target"] = "http://purl.org/olia/olia.owl#ProperNoun"
    projection["review"]["review_id"] = "review:bhsa:projection:proper-noun"
    projection["native_execution_binding"] = copy.deepcopy(membership)
    sources["locks"][0]["terms_used"].append(
        "http://purl.org/olia/olia.owl#ProperNoun"
    )
    _refresh_mapping(second)
    sources["mappings"]["mappings"].append(second)

    validate_structural_sources(sources)
    return compile_semantic_ir(
        (validate_semantic_bundle(source_bundle(sources)),)
    )


class ObservableValuedEdgeFeature(ValuedFakeEdgeFeature):
    def __init__(
        self,
        outgoing: dict[int, Iterable[Any]],
        *,
        incoming: dict[int, Iterable[Any]] | None = None,
        value_type: Any = "str",
        do_values: Any = True,
        meta: Any = None,
        item_data: Any = None,
        raise_on_items: bool = False,
    ) -> None:
        super().__init__(
            outgoing,
            incoming=incoming,
            value_type=value_type,
            do_values=do_values,
            meta=meta,
        )
        self.item_calls = 0
        self.raise_on_items = raise_on_items
        if item_data is None:
            data: dict[Any, Any] = {}
            for source, rows in self.outgoing.items():
                targets: dict[Any, Any] = {}
                for row in rows:
                    if type(row) is tuple and len(row) == 2:
                        targets[row[0]] = row[1]
                data[source] = targets
            self.item_data = data
        else:
            self.item_data = item_data

    def items(self):
        self.item_calls += 1
        if self.raise_on_items:
            raise RuntimeError("edge items unavailable")
        return self.item_data.items()


def predicate_feature(*, value_type: str = "str"):
    if value_type == "int":
        return ObservableValuedEdgeFeature(
            {1: ((10, 1), (11, None)), 2: ((10, 2),)},
            incoming={
                10: ((1, 1), (2, 2)),
                11: ((1, None),),
            },
            value_type="int",
        )
    return ObservableValuedEdgeFeature(
        {
            1: ((10, "ambiguous"), (11, "unique"), (99, "ambiguous")),
            2: ((10, "unique"),),
        },
        incoming={
            10: ((1, "ambiguous"), (2, "unique")),
            11: ((1, "unique"),),
            99: ((1, "ambiguous"),),
        },
        value_type="str",
    )


def predicate_api(
    *,
    feature: Any = None,
    value_type: str = "str",
    selections: dict[str, Iterable[Any]] | None = None,
):
    edge = "witness_resolution" if value_type == "str" else "quality_score"
    feature = feature or predicate_feature(value_type=value_type)
    return PathApi(
        node_types={
            1: "line",
            2: "line",
            10: "fragment",
            11: "fragment",
            99: "word",
        },
        features={edge: feature},
        loaded_edges=(edge,),
        selections=selections,
    )


def predicate_context(tfont_module, ir, api=None, *, value_type: str = "str"):
    return loaded_context(
        tfont_module,
        ir,
        "bhsa",
        api or predicate_api(value_type=value_type),
    )


def predicate_observation(tfont_module, ir, api=None, *, value_type: str = "str"):
    variant = ir.variants[0]
    loaded = api or predicate_api(value_type=value_type)
    return tfont_module.LoadedTFObservation(
        parent_manifest_digest=variant.key.expected_parent_manifest_digest,
        components={
            "bhsa-tf": (
                "sha256:" + "e" * 64,
                loaded,
            )
        },
    )
