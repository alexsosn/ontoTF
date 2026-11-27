from __future__ import annotations

import operator
from dataclasses import replace
from typing import Any, Iterable

from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import DEFAULT_CORPORA, PARENT_CHARS, _refresh_mapping, noun_semantic_key
from ontotf.semantic_ir import CompiledSemanticIR, compile_semantic_ir
from ontotf.semantic_validation import validate_semantic_bundle


def executable_noun_bundle(
    corpus_id: str,
    *,
    parent_char: str,
    dependency_kind: str = "native-value-present",
):
    sources = noun_sources(corpus_id, parent_char=parent_char)
    dependency = sources["profile"]["dependencies"][0]
    mapping = sources["mappings"]["mappings"][0]
    projection = mapping["projections"][0]

    mapping["native_binding"]["execution_shape"] = "value-predicate"
    projection["native_execution_binding"]["execution_shape"] = "value-predicate"

    if dependency_kind == "feature-present":
        dependency["kind"] = "feature-present"
        dependency["assertion"] = {"node_type": "word", "feature": "sp"}
    elif dependency_kind != "native-value-present":
        raise ValueError("unsupported fixture dependency kind")

    _refresh_mapping(mapping)
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def compiled_executable_noun_ir(
    corpora: Iterable[str] = DEFAULT_CORPORA,
    *,
    dependency_kind: str = "native-value-present",
) -> CompiledSemanticIR:
    return compile_semantic_ir(
        tuple(
            executable_noun_bundle(
                corpus_id,
                parent_char=PARENT_CHARS.get(corpus_id, "d"),
                dependency_kind=dependency_kind,
            )
            for corpus_id in corpora
        )
    )


class NodeFeature:
    def __init__(
        self,
        values: dict[int, Any],
        *,
        selected: Iterable[Any] | None = None,
        raise_on_s: bool = False,
    ) -> None:
        self.values = dict(values)
        self.selected = None if selected is None else tuple(selected)
        self.raise_on_s = raise_on_s
        self.s_calls = 0

    def v(self, node: Any) -> Any:
        try:
            normalized = operator.index(node)
        except TypeError:
            normalized = node
        return self.values.get(normalized)

    def s(self, value: Any):
        self.s_calls += 1
        if self.raise_on_s:
            raise RuntimeError("selector failed")
        if self.selected is not None:
            return self.selected
        return tuple(node for node, observed in self.values.items() if observed == value)


class OtypeFeature:
    def __init__(
        self,
        node_types: dict[int, str],
        *,
        raise_on_v: bool = False,
    ) -> None:
        self.node_types = dict(node_types)
        self.raise_on_v = raise_on_v

    def s(self, node_type: str):
        return tuple(node for node, observed in self.node_types.items() if observed == node_type)

    def v(self, node: Any):
        if self.raise_on_v:
            raise RuntimeError("otype lookup failed")
        try:
            normalized = operator.index(node)
        except TypeError:
            normalized = node
        return self.node_types.get(normalized)


class Namespace:
    pass


class FakeLoadedApi:
    def __init__(
        self,
        *,
        values: dict[int, Any],
        node_types: dict[int, str],
        selected: Iterable[Any] | None = None,
        loaded_features: tuple[str, ...] = ("otype", "sp"),
        fall_sequence: tuple[tuple[str, ...], ...] | None = None,
        raise_on_fall: bool = False,
        raise_on_s: bool = False,
        raise_on_otype_v: bool = False,
    ) -> None:
        self.F = Namespace()
        self.E = Namespace()
        self.F.otype = OtypeFeature(node_types, raise_on_v=raise_on_otype_v)
        self.F.sp = NodeFeature(values, selected=selected, raise_on_s=raise_on_s)
        self.loaded_features = loaded_features
        self.fall_sequence = fall_sequence
        self.raise_on_fall = raise_on_fall
        self.fall_calls = 0
        self.load_calls = 0

    def Fall(self):
        self.fall_calls += 1
        if self.raise_on_fall:
            raise RuntimeError("Fall unavailable")
        if self.fall_sequence:
            index = min(self.fall_calls - 1, len(self.fall_sequence) - 1)
            return self.fall_sequence[index]
        return self.loaded_features

    def Eall(self):
        return ()

    def load(self, *args, **kwargs):
        self.load_calls += 1
        raise AssertionError("I-008 must never autoload features")


class IndexNode:
    def __init__(self, value: int) -> None:
        self.value = value

    def __index__(self) -> int:
        return self.value


def corpus_variant(ir: CompiledSemanticIR, corpus_id: str):
    rows = tuple(row for row in ir.variants if row.key.corpus_id == corpus_id)
    if len(rows) != 1:
        raise AssertionError(f"fixture expected one variant for {corpus_id}")
    return rows[0]


def loaded_context(ontotf_module, ir: CompiledSemanticIR, corpus_id: str, api: Any):
    variant = corpus_variant(ir, corpus_id)
    return ontotf_module.LoadedCorpusContext(
        corpus_id=corpus_id,
        parent_manifest_digest=variant.key.expected_parent_manifest_digest,
        components=(
            ontotf_module.LoadedComponentContext(
                component_id=f"{corpus_id}-tf",
                content_digest="sha256:" + "e" * 64,
                api=api,
            ),
        ),
    )


def request(ontotf_module, corpora: tuple[str, ...]):
    return ontotf_module.SemanticResolveRequest(
        key=noun_semantic_key(),
        corpora=corpora,
    )


def duplicate_variant_ir(ir: CompiledSemanticIR) -> CompiledSemanticIR:
    return replace(ir, variants=ir.variants + ir.variants)
