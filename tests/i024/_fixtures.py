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
from tests.i023._fixtures import (
    FakeEdgeFeature,
    PathApi,
    edge_path_sources,
)
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


VALUED_STR_STEPS = (
    {
        "edge": "selected",
        "direction": "outgoing",
        "result_node_type": "analysis",
        "valued": True,
        "value_type": "str",
        "value_role": "source-evidence",
    },
)

VALUED_INT_STEPS = (
    {
        "edge": "omap@2017-2021",
        "direction": "outgoing",
        "result_node_type": "word",
        "valued": True,
        "value_type": "int",
        "value_role": "technical",
    },
)

MIXED_STEPS = (
    {
        "edge": "word_line",
        "direction": "outgoing",
        "result_node_type": "line",
        "valued": False,
    },
    {
        "edge": "line_quality",
        "direction": "outgoing",
        "result_node_type": "column",
        "valued": True,
        "value_type": "str",
        "value_role": "semantic-qualifier",
    },
)

EMPTY_TRAILING_STEPS = (
    {
        "edge": "selected",
        "direction": "outgoing",
        "result_node_type": "analysis",
        "valued": True,
        "value_type": "str",
        "value_role": "source-evidence",
    },
    {
        "edge": "analysis_column",
        "direction": "outgoing",
        "result_node_type": "column",
        "valued": False,
    },
)

INCOMING_VALUED_STEPS = (
    {
        "edge": "selected",
        "direction": "incoming",
        "result_node_type": "word",
        "valued": True,
        "value_type": "str",
        "value_role": "source-evidence",
    },
)


class ValuedFakeEdgeFeature(FakeEdgeFeature):
    def __init__(
        self,
        outgoing: dict[int, Iterable[Any]],
        *,
        incoming: dict[int, Iterable[Any]] | None = None,
        value_type: Any = "str",
        do_values: Any = True,
        meta: Any = None,
        raise_on_f: bool = False,
        raise_on_t: bool = False,
    ) -> None:
        super().__init__(
            outgoing,
            incoming=incoming,
            do_values=do_values,
            raise_on_f=raise_on_f,
            raise_on_t=raise_on_t,
        )
        self.meta = {"valueType": value_type} if meta is None else meta


def valued_sources(
    *,
    steps: Iterable[dict[str, Any]] = VALUED_STR_STEPS,
    start_node_type: str = "word",
    projection_route: str = "semantic",
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
    external_references: list[dict[str, Any]] | None = None,
):
    return edge_path_sources(
        start_node_type=start_node_type,
        steps=steps,
        projection_route=projection_route,
        assessment=assessment,
        losses=losses,
        external_references=external_references,
    )


def compiled_valued_ir(**kwargs):
    sources = valued_sources(**kwargs)
    validate_structural_sources(sources)
    return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))


def compiled_authority_valued_ir(
    *,
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
):
    return compiled_valued_ir(
        projection_route="authority",
        assessment=assessment,
        losses=losses,
    )


def compiled_reference_valued_ir():
    return compiled_valued_ir(
        external_references=[
            entity_identity_reference("bhsa"),
            catalogue_reference("bhsa"),
        ]
    )


def selected_api(
    *,
    feature: Any = None,
    selections: dict[str, Iterable[Any]] | None = None,
):
    selected = feature or ValuedFakeEdgeFeature(
        {
            1: ((11, "2a"), (10, "1"), (99, "off-domain")),
            2: ((10, "1bR 1bS"),),
        },
        incoming={
            10: ((1, "1"), (2, "1bR 1bS")),
            11: ((1, "2a"),),
            99: ((1, "off-domain"),),
        },
    )
    return PathApi(
        node_types={
            1: "word",
            2: "word",
            10: "analysis",
            11: "analysis",
            20: "column",
            21: "column",
            99: "phrase",
        },
        features={"selected": selected},
        loaded_edges=("selected",),
        selections=selections,
    )


def integer_api(*, feature: Any = None):
    omap = feature or ValuedFakeEdgeFeature(
        {1: ((2, 1), (3, None))},
        value_type="int",
    )
    return PathApi(
        node_types={1: "word", 2: "word", 3: "word"},
        features={"omap@2017-2021": omap},
        loaded_edges=("omap@2017-2021",),
        selections={"word": (1,)},
    )


def mixed_api():
    return PathApi(
        node_types={
            1: "word",
            2: "word",
            10: "line",
            11: "line",
            20: "column",
            99: "phrase",
        },
        features={
            "word_line": FakeEdgeFeature({1: (10,), 2: (11,)}),
            "line_quality": ValuedFakeEdgeFeature(
                {
                    10: ((20, "direct"),),
                    11: ((20, "indirect"),),
                }
            ),
        },
        loaded_edges=("word_line", "line_quality"),
    )


def empty_trailing_api():
    return PathApi(
        node_types={
            1: "word",
            2: "word",
            10: "analysis",
            20: "column",
            99: "phrase",
        },
        features={
            "selected": ValuedFakeEdgeFeature(
                {
                    1: ((99, "off-domain"),),
                    2: (),
                }
            ),
            "analysis_column": FakeEdgeFeature({10: (20,)}),
        },
        loaded_edges=("selected", "analysis_column"),
    )


def valued_context(tfont_module, ir, api=None):
    return loaded_context(
        tfont_module,
        ir,
        "bhsa",
        api or selected_api(),
    )


def compiled_mixed_conjunction_ir():
    sources = valued_sources()
    first = sources["mappings"]["mappings"][0]

    second = copy.deepcopy(first)
    second["mapping_id"] = "mapping:bhsa:proper-noun"
    second["review"]["review_id"] = "review:bhsa:mapping:proper-noun"
    membership = {
        "component_id": "bhsa-tf",
        "node_type": "analysis",
        "execution_shape": "membership",
    }
    second["native_dependencies"] = ["dep:bhsa:node-type:analysis"]
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
