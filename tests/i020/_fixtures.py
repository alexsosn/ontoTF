from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import _refresh_mapping, compiled_noun_ir, noun_semantic_key
from tests.i008._fixtures import FakeLoadedApi, loaded_context
from tests.i015.test_exact_conjunction_behavior import (
    compiled_and_contexts as exact_conjunction_contexts,
    key as production_key,
)
from tfont.production_bundles import load_production_linguistic_bundle
from tfont.semantic_ir import CompiledSemanticIR, SemanticKey, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


PARENT_CHARS = {"bhsa": "a", "syriac": "b", "extrabiblical": "c"}


def problem_category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


def prerequisites_for(module, ir: CompiledSemanticIR):
    rows = []
    for variant in ir.variants:
        dependencies = tuple(
            module.DependencyPrerequisiteResult(
                dependency_id=dependency_id,
                result="pass",
                observed_evidence_digest=None,
                evaluator_rule_version="research:i020-v1",
            )
            for dependency_id, _record in variant.release_signature.dependency_records
        )
        bundle_digest = variant.key.ontology_bundle_digest
        rows.append(
            module.RuntimePrerequisiteState(
                variant=variant.key,
                profile_release_fingerprint=module.profile_release_fingerprint(
                    variant.release_signature
                ),
                observed_parent_manifest_digest=variant.key.expected_parent_manifest_digest,
                parent_state="verified-exact",
                dependency_results=dependencies,
                active_ontology_bundle_digest=bundle_digest,
                ontology_bundle_state=(
                    "verified" if bundle_digest is not None else "not-required"
                ),
                source_contract="research:i020-current-runtime-v1",
            )
        )
    return tuple(rows)


def _apply_projection_policy(
    mapping: dict[str, Any],
    *,
    assessment: str,
    losses: tuple[str, ...] = (),
    eligible: bool = True,
    executable: bool = False,
    suffix: str = "",
) -> None:
    projection = mapping["projections"][0]
    projection["assessment"] = assessment
    projection.pop("approximation", None)

    if assessment in {"broader", "narrower", "close"}:
        projection["approximation"] = {
            "status": "reviewed",
            "eligible": eligible,
            "losses": list(losses),
            "rationale": f"I-020 fixture {assessment}{suffix}",
            "review_id": f"review:i020:{mapping['corpus_id']}:{assessment}{suffix}",
            "evidence": [],
        }

    if executable:
        mapping["native_binding"]["execution_shape"] = "value-predicate"
        projection["native_execution_binding"]["execution_shape"] = "value-predicate"

    _refresh_mapping(mapping)


def validated_binding_bundle(
    corpus_id: str,
    *,
    assessment: str = "exact",
    losses: tuple[str, ...] = (),
    eligible: bool = True,
    executable: bool = False,
    native_state: str = "positive",
):
    sources = noun_sources(
        corpus_id,
        parent_char=PARENT_CHARS.get(corpus_id, "d"),
        native_state=native_state,
    )
    if native_state == "positive":
        _apply_projection_policy(
            sources["mappings"]["mappings"][0],
            assessment=assessment,
            losses=losses,
            eligible=eligible,
            executable=executable,
        )
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def compiled_binding_ir(
    rows: tuple[
        tuple[str, str, tuple[str, ...], bool],
        ...,
    ],
    *,
    executable: bool = False,
) -> CompiledSemanticIR:
    return compile_semantic_ir(
        tuple(
            validated_binding_bundle(
                corpus_id,
                assessment=assessment,
                losses=losses,
                eligible=eligible,
                executable=executable,
            )
            for corpus_id, assessment, losses, eligible in rows
        )
    )


def compiled_repeated_approximation_evidence_ir() -> CompiledSemanticIR:
    sources = noun_sources("bhsa", parent_char="a")
    mapping = sources["mappings"]["mappings"][0]
    projection = mapping["projections"][0]
    evidence = copy.deepcopy(projection["evidence"][0])
    projection["assessment"] = "broader"
    projection["approximation"] = {
        "status": "reviewed",
        "eligible": True,
        "losses": ["undercoverage"],
        "rationale": "I-020 repeated-evidence fixture",
        "review_id": "review:i020:bhsa:repeated-evidence",
        "evidence": [copy.deepcopy(evidence), copy.deepcopy(evidence)],
    }
    _refresh_mapping(mapping)
    validate_structural_sources(sources)
    return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))


def compiled_presence_variant_ir(
    *,
    publication_null: bool,
    approximation_evidence_present: bool,
) -> CompiledSemanticIR:
    sources = noun_sources("bhsa", parent_char="a")
    mapping = sources["mappings"]["mappings"][0]
    projection = mapping["projections"][0]
    projection["assessment"] = "broader"
    projection["approximation"] = {
        "status": "reviewed",
        "eligible": True,
        "losses": ["undercoverage"],
        "rationale": "I-020 source-presence fixture",
        "review_id": "review:i020:bhsa:presence",
        "evidence": [],
    }
    if not approximation_evidence_present:
        projection["approximation"].pop("evidence")
    if publication_null:
        projection["publication_relation"] = None
    else:
        projection.pop("publication_relation", None)
    _refresh_mapping(mapping)
    validate_structural_sources(sources)
    return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))


def validated_value_set_approximation_bundle(
    corpus_id: str,
    *,
    assessment: str = "broader",
    losses: tuple[str, ...] = ("undercoverage",),
):
    sources = noun_sources(
        corpus_id,
        parent_char=PARENT_CHARS.get(corpus_id, "d"),
    )
    profile = sources["profile"]
    mapping = sources["mappings"]["mappings"][0]
    projection = mapping["projections"][0]

    first_dependency = profile["dependencies"][0]
    second_dependency = copy.deepcopy(first_dependency)
    second_dependency["dependency_id"] = f"dep:{corpus_id}:word-sp-nmpr"
    second_dependency["assertion"]["value"] = "nmpr"
    profile["dependencies"].append(second_dependency)
    mapping["native_dependencies"].append(second_dependency["dependency_id"])

    for binding in (mapping["native_binding"], projection["native_execution_binding"]):
        binding.pop("value", None)
        binding["values"] = ["nmpr", "subs"]
        binding["execution_shape"] = "value-set-predicate"

    projection["assessment"] = assessment
    projection["approximation"] = {
        "status": "reviewed",
        "eligible": True,
        "losses": list(losses),
        "rationale": "I-020 finite-set fixture",
        "review_id": f"review:i020:{corpus_id}:finite-set",
        "evidence": [],
    }
    _refresh_mapping(mapping)

    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def validated_two_binding_bundle(
    corpus_id: str,
    *,
    first_assessment: str,
    first_losses: tuple[str, ...] = (),
    first_eligible: bool = True,
    second_assessment: str,
    second_losses: tuple[str, ...] = (),
    second_eligible: bool = True,
    executable: bool = False,
):
    sources = noun_sources(
        corpus_id,
        parent_char=PARENT_CHARS.get(corpus_id, "d"),
    )
    first = sources["mappings"]["mappings"][0]
    second = copy.deepcopy(first)

    second["mapping_id"] = f"mapping:{corpus_id}:noun:second"
    second["review"]["review_id"] = f"review:{corpus_id}:mapping:noun:second"
    second_projection = second["projections"][0]
    second_projection["projection_id"] = f"projection:{corpus_id}:noun:second"
    second_projection["review"]["review_id"] = (
        f"review:{corpus_id}:projection:noun:second"
    )

    _apply_projection_policy(
        first,
        assessment=first_assessment,
        losses=first_losses,
        eligible=first_eligible,
        executable=executable,
        suffix=":first",
    )
    _apply_projection_policy(
        second,
        assessment=second_assessment,
        losses=second_losses,
        eligible=second_eligible,
        executable=executable,
        suffix=":second",
    )
    sources["mappings"]["mappings"].append(second)

    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def compiled_two_binding_ir(**kwargs: Any) -> CompiledSemanticIR:
    return compile_semantic_ir((validated_two_binding_bundle("bhsa", **kwargs),))


def replace_semantic_binding(
    ir: CompiledSemanticIR,
    corpus_id: str,
    **changes: Any,
) -> CompiledSemanticIR:
    changed = False
    rows_out = []
    for key, rows in ir.semantic_index:
        next_rows = []
        for row in rows:
            if row.corpus_id == corpus_id and not changed:
                next_rows.append(replace(row, **changes))
                changed = True
            else:
                next_rows.append(row)
        rows_out.append((key, tuple(next_rows)))
    if not changed:
        raise AssertionError(f"no semantic binding for corpus {corpus_id}")
    return replace(ir, semantic_index=tuple(rows_out))


def approximate_request(
    module,
    *,
    corpora: tuple[str, ...] = ("bhsa",),
    accept_losses: tuple[str, ...] = (),
    key: SemanticKey | None = None,
):
    return module.ApproximateSemanticResolveRequest(
        key=key or noun_semantic_key(),
        corpora=corpora,
        semantic_mode="approximate",
        accept_losses=accept_losses,
    )


def approximate_conjunction_request(
    module,
    *names: str,
    corpora: tuple[str, ...] = ("bhsa", "syriac", "extrabiblical"),
    accept_losses: tuple[str, ...] = (),
):
    return module.ApproximateSemanticConjunctionRequest(
        keys=tuple(production_key(name) for name in names),
        corpora=corpora,
        semantic_mode="approximate",
        accept_losses=accept_losses,
    )


def mutated_production_conjunction(
    mutations: dict[str, dict[str, tuple[str, tuple[str, ...], bool]]],
):
    bundles = []
    for corpus_id in ("bhsa", "syriac", "extrabiblical"):
        bundle = copy.deepcopy(load_production_linguistic_bundle(corpus_id))
        wanted = mutations.get(corpus_id, {})
        for mapping in bundle.mappings.data["mappings"]:
            changed = False
            for projection in mapping.get("projections", []):
                name = projection["target"].rsplit("#", 1)[-1]
                if name not in wanted:
                    continue
                assessment, losses, eligible = wanted[name]
                projection["assessment"] = assessment
                projection.pop("approximation", None)
                if assessment in {"broader", "narrower", "close"}:
                    projection["approximation"] = {
                        "status": "reviewed",
                        "eligible": eligible,
                        "losses": list(losses),
                        "rationale": f"I-020 production-fixture mutation {name}",
                        "review_id": f"review:i020:{corpus_id}:{name}:{assessment}",
                        "evidence": [],
                    }
                changed = True
            if changed:
                _refresh_mapping(mapping)
        bundles.append(validate_semantic_bundle(bundle))

    ir = compile_semantic_ir(tuple(bundles))
    _exact_ir, contexts = exact_conjunction_contexts()
    return ir, contexts


def executable_context(module, ir: CompiledSemanticIR, corpus_id: str, api: Any):
    return loaded_context(module, ir, corpus_id, api)


__all__ = [
    "FakeLoadedApi",
    "approximate_conjunction_request",
    "approximate_request",
    "compiled_binding_ir",
    "compiled_presence_variant_ir",
    "compiled_repeated_approximation_evidence_ir",
    "compiled_noun_ir",
    "compiled_two_binding_ir",
    "executable_context",
    "mutated_production_conjunction",
    "noun_semantic_key",
    "prerequisites_for",
    "problem_category",
    "replace_semantic_binding",
    "validated_binding_bundle",
    "validated_value_set_approximation_bundle",
]
