from __future__ import annotations

import copy
from dataclasses import replace

from tests.i005._fixtures import (
    catalogue_reference,
    entity_identity_reference,
    noun_sources,
    source_bundle,
    validate_structural_sources,
)
from tests.i006._fixtures import PARENT_CHARS, _refresh_mapping
from tests.i008._fixtures import FakeLoadedApi, loaded_context
from tests.i020._fixtures import prerequisites_for
from tfont.semantic_ir import CompiledSemanticIR, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


def _validated(sources):
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def authority_ir(
    corpus_id: str = "bhsa",
    *,
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
    eligible: bool = True,
    executable: bool = False,
) -> CompiledSemanticIR:
    sources = noun_sources(
        corpus_id,
        parent_char=PARENT_CHARS.get(corpus_id, "d"),
        projection_route="authority",
    )
    mapping = sources["mappings"]["mappings"][0]
    projection = mapping["projections"][0]
    projection["assessment"] = assessment
    projection.pop("approximation", None)
    if assessment in {"close", "broader", "narrower"}:
        projection["approximation"] = {
            "status": "reviewed",
            "eligible": eligible,
            "losses": list(losses),
            "rationale": f"I-021 authority fixture {assessment}",
            "review_id": f"review:i021:{corpus_id}:authority:{assessment}",
            "evidence": [],
        }
    if executable:
        mapping["native_binding"]["execution_shape"] = "value-predicate"
        projection["native_execution_binding"]["execution_shape"] = "value-predicate"
    _refresh_mapping(mapping)
    return compile_semantic_ir((_validated(sources),))


def authority_two_binding_ir(
    *,
    first_assessment: str,
    second_assessment: str,
    first_losses: tuple[str, ...] = (),
    second_losses: tuple[str, ...] = (),
    executable: bool = False,
) -> CompiledSemanticIR:
    sources = noun_sources("bhsa", parent_char="a", projection_route="authority")
    first = sources["mappings"]["mappings"][0]
    second = copy.deepcopy(first)
    second["mapping_id"] = "mapping:bhsa:authority:second"
    second["review"]["review_id"] = "review:bhsa:authority:second"
    second_projection = second["projections"][0]
    second_projection["projection_id"] = "projection:bhsa:authority:second"
    second_projection["review"]["review_id"] = "review:bhsa:authority:projection:second"

    for mapping, assessment, losses, suffix in (
        (first, first_assessment, first_losses, "first"),
        (second, second_assessment, second_losses, "second"),
    ):
        projection = mapping["projections"][0]
        projection["assessment"] = assessment
        projection.pop("approximation", None)
        if assessment in {"close", "broader", "narrower"}:
            projection["approximation"] = {
                "status": "reviewed",
                "eligible": True,
                "losses": list(losses),
                "rationale": f"I-021 authority fixture {suffix}",
                "review_id": f"review:i021:authority:{suffix}",
                "evidence": [],
            }
        if executable:
            mapping["native_binding"]["execution_shape"] = "value-predicate"
            projection["native_execution_binding"]["execution_shape"] = "value-predicate"
        _refresh_mapping(mapping)

    sources["mappings"]["mappings"] = [first, second]
    return compile_semantic_ir((_validated(sources),))


def reference_ir(
    corpus_id: str = "bhsa",
    *,
    strengths: tuple[str, ...] = ("same-entity",),
    issuer: str = "fixture-catalogue",
    literal_id: str | None = None,
    executable: bool = False,
    native_state: str = "positive",
    duplicate_identifier: bool = False,
) -> CompiledSemanticIR:
    external = f"https://example.org/entity/{corpus_id}"
    refs = []
    for index, strength in enumerate(strengths):
        ref = entity_identity_reference(corpus_id)
        ref["reference_id"] = f"reference:{corpus_id}:identity:{index}"
        ref["external"] = external
        ref["identity_strength"] = strength
        if executable:
            ref["native_binding"]["execution_shape"] = "value-predicate"
        refs.append(ref)

    ident = catalogue_reference(corpus_id)
    ident["external"] = literal_id or f"ID-{corpus_id}"
    ident["issuer_or_namespace"] = issuer
    if executable:
        ident["native_binding"]["execution_shape"] = "value-predicate"
    refs.append(ident)

    if duplicate_identifier:
        duplicate = copy.deepcopy(ident)
        duplicate["reference_id"] += ":duplicate"
        refs.append(duplicate)

    sources = noun_sources(
        corpus_id,
        parent_char=PARENT_CHARS.get(corpus_id, "d"),
        native_state=native_state,
        external_references=refs,
    )
    return compile_semantic_ir((_validated(sources),))


def reference_ir_with_execution_shape(
    execution_shape: str,
    corpus_id: str = "bhsa",
) -> CompiledSemanticIR:
    identity = entity_identity_reference(corpus_id)
    identifier = catalogue_reference(corpus_id)
    for reference in (identity, identifier):
        binding = reference["native_binding"]
        if execution_shape == "value-set-predicate":
            value = binding.pop("value")
            binding["values"] = [value]
        binding["execution_shape"] = execution_shape

    sources = noun_sources(
        corpus_id,
        parent_char=PARENT_CHARS.get(corpus_id, "d"),
        external_references=[identity, identifier],
    )
    return compile_semantic_ir((_validated(sources),))


def identity_external(ir: CompiledSemanticIR) -> str:
    return ir.identity_index[0][0].external_entity_id


def prerequisites(module, ir: CompiledSemanticIR):
    return prerequisites_for(module, ir)


def context(module, ir: CompiledSemanticIR, corpus_id: str = "bhsa"):
    api = FakeLoadedApi(
        values={1: "subs", 2: "verb", 3: "subs"},
        node_types={1: "word", 2: "word", 3: "word"},
    )
    return loaded_context(module, ir, corpus_id, api)


def replace_identity_row(ir: CompiledSemanticIR, **changes) -> CompiledSemanticIR:
    key, rows = ir.identity_index[0]
    changed = replace(rows[0], **changes)
    return replace(ir, identity_index=((key, (changed,)),) + ir.identity_index[1:])


def replace_identifier_row(ir: CompiledSemanticIR, **changes) -> CompiledSemanticIR:
    key, rows = ir.identifier_index[0]
    changed = replace(rows[0], **changes)
    return replace(ir, identifier_index=((key, (changed,)),) + ir.identifier_index[1:])
