from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any, Iterable

from tests.i005._fixtures import (
    OLIA_NOUN,
    noun_sources,
    source_bundle,
    validate_structural_sources,
    validated_noun_bundle,
)
from ontotf.semantic_digest_v2 import (
    mapping_semantic_digest_v2,
    projection_semantic_digest_v1,
)
from ontotf.semantic_ir import CompiledSemanticIR, SemanticKey, compile_semantic_ir
from ontotf.semantic_validation import ValidatedSemanticBundle, validate_semantic_bundle


DEFAULT_CORPORA = ("bhsa", "syriac", "extrabiblical")
PARENT_CHARS = {"bhsa": "a", "syriac": "b", "extrabiblical": "c"}
TEST_SOURCE_CONTRACT = "test:i006-prerequisite-v1"


def noun_semantic_key() -> SemanticKey:
    return SemanticKey(
        profile_id="linguistic",
        capability_id="linguistic.part-of-speech",
        target=OLIA_NOUN,
        formal_kind="class",
        semantic_role="annotation-value",
    )


def compiled_noun_ir(corpora: Iterable[str] = DEFAULT_CORPORA) -> CompiledSemanticIR:
    bundles = tuple(
        validated_noun_bundle(corpus_id, parent_char=PARENT_CHARS.get(corpus_id, "d"))
        for corpus_id in corpora
    )
    return compile_semantic_ir(bundles)


def _refresh_mapping(mapping: dict[str, Any]) -> None:
    for projection in mapping.get("projections", []):
        projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
        projection["review"]["reviewed_mapping_digest"] = projection[
            "projection_semantic_digest"
        ]
    mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
    mapping["review"]["reviewed_mapping_digest"] = mapping["mapping_semantic_digest"]


def _validated_sources(sources: dict[str, Any]) -> ValidatedSemanticBundle:
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def validated_assessment_bundle(
    corpus_id: str,
    assessment: str,
    *,
    parent_char: str = "a",
) -> ValidatedSemanticBundle:
    sources = noun_sources(corpus_id, parent_char=parent_char)
    mapping = sources["mappings"]["mappings"][0]
    mapping["projections"][0]["assessment"] = assessment
    _refresh_mapping(mapping)
    return _validated_sources(sources)


def validated_two_binding_bundle(
    corpus_id: str,
    *,
    parent_char: str = "a",
    second_assessment: str = "exact",
) -> ValidatedSemanticBundle:
    sources = noun_sources(corpus_id, parent_char=parent_char)
    first = sources["mappings"]["mappings"][0]
    second = copy.deepcopy(first)
    second["mapping_id"] = f"mapping:{corpus_id}:noun:second"
    second["review"]["review_id"] = f"review:{corpus_id}:mapping:noun:second"
    projection = second["projections"][0]
    projection["projection_id"] = f"projection:{corpus_id}:noun:second"
    projection["assessment"] = second_assessment
    projection["review"]["review_id"] = f"review:{corpus_id}:projection:noun:second"
    _refresh_mapping(second)
    sources["mappings"]["mappings"].append(second)
    return _validated_sources(sources)


def validated_binding_presence_bundle(
    corpus_id: str,
    *,
    parent_char: str = "a",
    value_mode: str,
) -> ValidatedSemanticBundle:
    if value_mode not in {"null", "absent"}:
        raise ValueError("value_mode must be null or absent")
    sources = noun_sources(corpus_id, parent_char=parent_char)
    dependency = sources["profile"]["dependencies"][0]
    mapping = sources["mappings"]["mappings"][0]
    projection = mapping["projections"][0]

    if value_mode == "null":
        dependency["assertion"]["value"] = None
        mapping["native_binding"]["value"] = None
        projection["native_execution_binding"]["value"] = None
    else:
        dependency["kind"] = "feature-present"
        dependency["assertion"].pop("value", None)
        dependency["assertion"].pop("value_semantics", None)
        mapping["native_binding"].pop("value", None)
        projection["native_execution_binding"].pop("value", None)

    _refresh_mapping(mapping)
    return _validated_sources(sources)


def with_bundle_digest(ir: CompiledSemanticIR, digest: str) -> CompiledSemanticIR:
    if len(ir.variants) != 1:
        raise ValueError("bundle mutation helper requires one variant")
    old_variant_ir = ir.variants[0]
    old_key = old_variant_ir.key
    new_key = replace(old_key, ontology_bundle_digest=digest)
    new_signature = replace(
        old_variant_ir.release_signature,
        ontology_bundle_digest=digest,
    )
    new_variant_ir = replace(
        old_variant_ir,
        key=new_key,
        release_signature=new_signature,
    )

    native_index = tuple(
        (
            key,
            tuple(
                replace(row, variant=new_key) if row.variant == old_key else row
                for row in rows
            ),
        )
        for key, rows in ir.native_index
    )
    semantic_index = tuple(
        (
            key,
            tuple(
                replace(row, variant=new_key, ontology_bundle_digest=digest)
                if row.variant == old_key
                else row
                for row in rows
            ),
        )
        for key, rows in ir.semantic_index
    )
    authority_index = tuple(
        (
            key,
            tuple(
                replace(row, variant=new_key, ontology_bundle_digest=digest)
                if row.variant == old_key
                else row
                for row in rows
            ),
        )
        for key, rows in ir.authority_index
    )
    identity_index = tuple(
        (
            key,
            tuple(
                replace(row, variant=new_key) if row.variant == old_key else row
                for row in rows
            ),
        )
        for key, rows in ir.identity_index
    )
    identifier_index = tuple(
        (
            key,
            tuple(
                replace(row, variant=new_key) if row.variant == old_key else row
                for row in rows
            ),
        )
        for key, rows in ir.identifier_index
    )
    capability_facts = tuple(
        (
            replace(key, variant=new_key) if key.variant == old_key else key,
            facts,
        )
        for key, facts in ir.capability_facts
    )
    return replace(
        ir,
        variants=(new_variant_ir,),
        native_index=native_index,
        semantic_index=semantic_index,
        authority_index=authority_index,
        identity_index=identity_index,
        identifier_index=identifier_index,
        capability_facts=capability_facts,
    )
