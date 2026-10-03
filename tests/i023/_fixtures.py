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


OUTGOING_STEPS = (
    {
        "edge": "word_line",
        "direction": "outgoing",
        "result_node_type": "line",
        "valued": False,
    },
    {
        "edge": "line_column",
        "direction": "outgoing",
        "result_node_type": "column",
        "valued": False,
    },
)

LINE_TO_COLUMN_STEPS = (
    {
        "edge": "line_column",
        "direction": "outgoing",
        "result_node_type": "column",
        "valued": False,
    },
)

INCOMING_STEPS = (
    {
        "edge": "line_column",
        "direction": "incoming",
        "result_node_type": "line",
        "valued": False,
    },
    {
        "edge": "word_line",
        "direction": "incoming",
        "result_node_type": "word",
        "valued": False,
    },
)


def edge_path_binding(
    *,
    component_id: str = "bhsa-tf",
    start_node_type: str = "word",
    steps: Iterable[dict[str, Any]] = OUTGOING_STEPS,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "node_type": start_node_type,
        "execution_shape": "edge-path",
        "steps": [copy.deepcopy(step) for step in steps],
    }


def _node_type_dependency(corpus_id: str, node_type: str) -> dict[str, Any]:
    return {
        "dependency_id": f"dep:{corpus_id}:node-type:{node_type}",
        "component_id": f"{corpus_id}-tf",
        "kind": "node-type-present",
        "assertion": {"node_type": node_type},
    }


def _path_dependency(
    corpus_id: str,
    steps: Iterable[dict[str, Any]],
    *,
    suffix: str = "path",
) -> dict[str, Any]:
    return {
        "dependency_id": f"dep:{corpus_id}:{suffix}",
        "component_id": f"{corpus_id}-tf",
        "kind": "path-present",
        "assertion": {
            "steps": [
                {"edge": step["edge"], "direction": step["direction"]}
                for step in steps
            ]
        },
    }


def edge_path_sources(
    *,
    corpus_id: str = "bhsa",
    parent_char: str = "a",
    start_node_type: str = "word",
    steps: Iterable[dict[str, Any]] = OUTGOING_STEPS,
    projection_route: str = "semantic",
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
    external_references: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    step_rows = tuple(copy.deepcopy(tuple(steps)))
    sources = noun_sources(
        corpus_id,
        parent_char=parent_char,
        projection_route=projection_route,
        external_references=external_references,
    )
    component_id = f"{corpus_id}-tf"
    binding = edge_path_binding(
        component_id=component_id,
        start_node_type=start_node_type,
        steps=step_rows,
    )

    node_types: list[str] = []
    for node_type in (start_node_type, *(step["result_node_type"] for step in step_rows)):
        if node_type not in node_types:
            node_types.append(node_type)
    dependencies = [_node_type_dependency(corpus_id, node_type) for node_type in node_types]
    dependencies.append(_path_dependency(corpus_id, step_rows))
    sources["profile"]["dependencies"] = dependencies

    mapping = sources["mappings"]["mappings"][0]
    mapping["native_dependencies"] = [row["dependency_id"] for row in dependencies]
    mapping["native_binding"] = copy.deepcopy(binding)
    if mapping["projections"]:
        projection = mapping["projections"][0]
        projection["native_execution_binding"] = copy.deepcopy(binding)
        projection["assessment"] = assessment
        projection.pop("approximation", None)
        if assessment in {"broader", "narrower", "close"}:
            projection["approximation"] = {
                "status": "reviewed",
                "eligible": True,
                "losses": list(losses),
                "rationale": f"I-023 edge-path fixture {assessment}",
                "review_id": f"review:i023:{corpus_id}:{assessment}",
                "evidence": [],
            }

    for reference in mapping["external_references"]:
        if reference.get("native_binding") is not None:
            reference["native_binding"] = copy.deepcopy(binding)

    _refresh_mapping(mapping)
    return sources


def validated_edge_path_bundle(**kwargs):
    sources = edge_path_sources(**kwargs)
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def compiled_edge_path_ir(**kwargs):
    return compile_semantic_ir((validated_edge_path_bundle(**kwargs),))


class Namespace:
    pass


class PathOtype:
    def __init__(
        self,
        node_types: dict[int, Any],
        *,
        selections: dict[str, Iterable[Any]] | None = None,
        selection_sequences: dict[str, Iterable[Iterable[Any] | BaseException]] | None = None,
        raise_on_v: bool = False,
    ) -> None:
        self.node_types = dict(node_types)
        self.selections = {
            key: tuple(value) for key, value in (selections or {}).items()
        }
        self.selection_sequences = {
            key: tuple(value) for key, value in (selection_sequences or {}).items()
        }
        self.raise_on_v = raise_on_v
        self.s_calls: dict[str, int] = {}
        self.v_calls = 0

    def s(self, node_type: str):
        count = self.s_calls.get(node_type, 0)
        self.s_calls[node_type] = count + 1
        sequence = self.selection_sequences.get(node_type)
        if sequence:
            item = sequence[min(count, len(sequence) - 1)]
            if isinstance(item, BaseException):
                raise item
            return item
        if node_type in self.selections:
            return self.selections[node_type]
        return tuple(
            node
            for node, observed in self.node_types.items()
            if observed == node_type
        )

    def v(self, node: Any):
        self.v_calls += 1
        if self.raise_on_v:
            raise RuntimeError("otype lookup failed")
        try:
            normalized = operator.index(node)
        except TypeError:
            normalized = node
        return self.node_types.get(normalized)


class FakeEdgeFeature:
    def __init__(
        self,
        outgoing: dict[int, Iterable[Any]],
        *,
        incoming: dict[int, Iterable[Any]] | None = None,
        do_values: Any = False,
        raise_on_f: bool = False,
        raise_on_t: bool = False,
    ) -> None:
        self.outgoing = {node: tuple(values) for node, values in outgoing.items()}
        if incoming is None:
            inverse: dict[int, list[int]] = {}
            for source, targets in self.outgoing.items():
                for target in targets:
                    if isinstance(target, tuple):
                        target = target[0]
                    if isinstance(target, int):
                        inverse.setdefault(target, []).append(source)
            self.incoming = {node: tuple(values) for node, values in inverse.items()}
        else:
            self.incoming = {node: tuple(values) for node, values in incoming.items()}
        self.doValues = do_values
        self.raise_on_f = raise_on_f
        self.raise_on_t = raise_on_t
        self.f_calls: list[Any] = []
        self.t_calls: list[Any] = []

    def f(self, node: Any):
        self.f_calls.append(node)
        if self.raise_on_f:
            raise RuntimeError("outgoing traversal failed")
        return self.outgoing.get(node, ())

    def t(self, node: Any):
        self.t_calls.append(node)
        if self.raise_on_t:
            raise RuntimeError("incoming traversal failed")
        return self.incoming.get(node, ())


class EdgeNamespace:
    def __init__(self, features: dict[str, Any]) -> None:
        self.oslots_touched = False
        for name, value in features.items():
            setattr(self, name, value)

    def __getattr__(self, name: str):
        if name == "oslots":
            self.oslots_touched = True
            raise AssertionError("I-023 edge-path execution must not touch oslots")
        raise AttributeError(name)


class PathApi:
    def __init__(
        self,
        *,
        node_types: dict[int, Any] | None = None,
        features: dict[str, Any] | None = None,
        loaded_edges: Iterable[str] = ("word_line", "line_column"),
        eall_sequence: Iterable[Iterable[str] | BaseException] | None = None,
        selections: dict[str, Iterable[Any]] | None = None,
        selection_sequences: dict[str, Iterable[Iterable[Any] | BaseException]] | None = None,
        raise_on_otype_v: bool = False,
    ) -> None:
        self.node_types = dict(
            node_types
            or {
                1: "word",
                2: "word",
                10: "line",
                11: "line",
                20: "column",
                21: "column",
                99: "phrase",
            }
        )
        self.F = Namespace()
        self.F.otype = PathOtype(
            self.node_types,
            selections=selections,
            selection_sequences=selection_sequences,
            raise_on_v=raise_on_otype_v,
        )
        default_features = {
            "word_line": FakeEdgeFeature(
                {
                    1: (11, 10, 99),
                    2: (10,),
                }
            ),
            "line_column": FakeEdgeFeature(
                {
                    11: (21, 20),
                    10: (20,),
                }
            ),
        }
        self.E = EdgeNamespace(features or default_features)
        self.loaded_edges = tuple(loaded_edges)
        self.eall_sequence = None if eall_sequence is None else tuple(eall_sequence)
        self.eall_calls = 0
        self.load_calls = 0

    def Fall(self):
        return ("otype",)

    def Eall(self):
        self.eall_calls += 1
        if self.eall_sequence:
            item = self.eall_sequence[min(self.eall_calls - 1, len(self.eall_sequence) - 1)]
            if isinstance(item, BaseException):
                raise item
            return item
        return self.loaded_edges

    def load(self, *args, **kwargs):
        self.load_calls += 1
        raise AssertionError("I-023 must never autoload features")


def path_api(**kwargs):
    return PathApi(**kwargs)


def edge_path_context(tfont_module, ir, api=None):
    return loaded_context(
        tfont_module,
        ir,
        "bhsa",
        api or path_api(),
    )


def semantic_request(tfont_module):
    return tfont_module.SemanticResolveRequest(
        key=noun_semantic_key(),
        corpora=("bhsa",),
    )


def approximate_request(tfont_module, *, accept_losses=()):
    return tfont_module.ApproximateSemanticResolveRequest(
        key=noun_semantic_key(),
        corpora=("bhsa",),
        semantic_mode="approximate",
        accept_losses=tuple(accept_losses),
    )


def compiled_reference_edge_path_ir():
    refs = [
        entity_identity_reference("bhsa"),
        catalogue_reference("bhsa"),
    ]
    return compiled_edge_path_ir(external_references=refs)


def compiled_authority_edge_path_ir(
    *,
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
):
    return compiled_edge_path_ir(
        projection_route="authority",
        assessment=assessment,
        losses=losses,
    )


def compiled_two_path_ir():
    sources = edge_path_sources()
    first = sources["mappings"]["mappings"][0]

    short_dependency = _path_dependency(
        "bhsa",
        LINE_TO_COLUMN_STEPS,
        suffix="line-column-path",
    )
    sources["profile"]["dependencies"].append(short_dependency)

    second = copy.deepcopy(first)
    second["mapping_id"] = "mapping:bhsa:proper-noun"
    second["review"]["review_id"] = "review:bhsa:mapping:proper-noun"
    second["native_dependencies"] = [
        "dep:bhsa:node-type:line",
        "dep:bhsa:node-type:column",
        short_dependency["dependency_id"],
    ]
    second_binding = edge_path_binding(
        start_node_type="line",
        steps=LINE_TO_COLUMN_STEPS,
    )
    second["native_binding"] = copy.deepcopy(second_binding)

    projection = second["projections"][0]
    projection["projection_id"] = "projection:bhsa:proper-noun"
    projection["target"] = "http://purl.org/olia/olia.owl#ProperNoun"
    projection["review"]["review_id"] = "review:bhsa:projection:proper-noun"
    projection["native_execution_binding"] = copy.deepcopy(second_binding)
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
