from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import tfont
from tfont import (
    PRODUCTION_NOUN_CORPORA,
    LoadedComponentContext,
    LoadedCorpusContext,
    SemanticKey,
    SemanticResolutionError,
    SemanticResolveRequest,
    compile_semantic_ir,
    execute_exact_semantic,
    load_production_noun_bundles,
    validate_semantic_bundle,
)

CONTRACT = "tfont-v01-noun-acceptance-v1"
OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
OLIA_RELEASE = f"snapshot-{OLIA_REVISION}"
OLIA_NOUN = "http://purl.org/olia/olia.owl#Noun"
OLIA_NAMESPACE = "http://purl.org/olia/olia.owl#"
OLIA_CONTENT_DIGEST = "sha256:5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd"
REVIEW_SOURCE = "https://github.com/alexsosn/ontoTF/pull/156#issuecomment-5646831801"

ORACLE: dict[str, dict[str, Any]] = {
    "bhsa": {
        "component_id": "bhsa-tf",
        "parent_digest": "sha256:cc2c65cd79b2cb7faf1a34b94feb3cc2d3291e7064cbec942c53b0e05f1b0837",
        "component_digest": "sha256:5178414e293a743fc98768abcab5b9cb268e14ad56fd2cfbac544ae2869d2e6f",
        "mapping_id": "mapping:bhsa:olia-noun",
        "mapping_digest": "sha256:1584b737cc14b14c6178a651d96e4d14c21414bcd55c216b4dbf45133ab02729",
        "mapping_review_id": "review:bhsa:olia-noun:mapping",
        "projection_id": "projection:bhsa:olia-noun",
        "projection_digest": "sha256:60b78e009d3ca5797ad090c9fb82a2a928c2b44a0a9f23c90b95f86238388c41",
        "projection_review_id": "review:bhsa:olia-noun:projection",
        "execution_shape": "value-set-predicate",
        "values": ("nmpr", "subs"),
        "value": None,
        "dependencies": ("dep:bhsa:word-sp:nmpr", "dep:bhsa:word-sp:subs"),
        "nodes": {
            1: ("word", "subs"),
            2: ("word", "nmpr"),
            3: ("word", "verb"),
            4: ("lex", "nmpr"),
        },
        "expected_nodes": (1, 2),
    },
    "syriac": {
        "component_id": "syriac-tf",
        "parent_digest": "sha256:afb5a826b9ebe10cdd4ca23d96e00ee7bf677d06496cfcfcee6bb37d2ecff6c4",
        "component_digest": "sha256:54a2596d5525f3afb34db0a89d5511e6b8471ce4a93fae4825b22f0945ab62ef",
        "mapping_id": "mapping:syriac:olia-noun",
        "mapping_digest": "sha256:ae7fe7e2bff7d43524b78f68afc548cdde51e20bc32ecf2d082aec2f390043a1",
        "mapping_review_id": "review:syriac:olia-noun:mapping",
        "projection_id": "projection:syriac:olia-noun",
        "projection_digest": "sha256:7aab23f738faa2c4fde2909a280618863284ddf8ec63c6a0e237ecb111a5d1a2",
        "projection_review_id": "review:syriac:olia-noun:projection",
        "execution_shape": "value-predicate",
        "values": None,
        "value": "subs",
        "dependencies": ("dep:syriac:word-sp:subs",),
        "nodes": {
            11: ("word", "subs"),
            12: ("word", "subs"),
            13: ("word", "verb"),
        },
        "expected_nodes": (11, 12),
    },
    "extrabiblical": {
        "component_id": "extrabiblical-tf",
        "parent_digest": "sha256:d39fe3f4848cadb14ae5ef453a5150ea6281b2874728566198d7de10d72bec4a",
        "component_digest": "sha256:d0ca9bdf90bfdefe19861c2c68e91071650ed511b8a79270490238b30274aee0",
        "mapping_id": "mapping:extrabiblical:olia-noun",
        "mapping_digest": "sha256:5ccd4e2648595c439c374b383e6e3f5abe747aa3997fe863918e733c5ddb0c2c",
        "mapping_review_id": "review:extrabiblical:olia-noun:mapping",
        "projection_id": "projection:extrabiblical:olia-noun",
        "projection_digest": "sha256:8827054ce6355fd05172b2dc7ed58030240637c0ba93092e518f11b9b3a24907",
        "projection_review_id": "review:extrabiblical:olia-noun:projection",
        "execution_shape": "value-set-predicate",
        "values": ("nmpr", "subs"),
        "value": None,
        "dependencies": (
            "dep:extrabiblical:word-sp:nmpr",
            "dep:extrabiblical:word-sp:subs",
        ),
        "nodes": {
            21: ("word", "nmpr"),
            22: ("word", "subs"),
            23: ("word", "verb"),
            24: ("lex", "subs"),
        },
        "expected_nodes": (21, 22),
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_sha256(value: Any, label: str) -> None:
    require(
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:]),
        f"{label} is not a canonical sha256 identity: {value!r}",
    )


def _under(path: Path, root: Path) -> bool:
    path = path.resolve()
    root = root.resolve()
    return path == root or root in path.parents


def assert_install_isolation() -> None:
    forbidden = os.environ.get("TFONT_ACCEPTANCE_FORBID_ROOT")
    if not forbidden:
        return
    root = Path(forbidden)
    package_file = Path(tfont.__file__)
    require(not _under(package_file, root), f"tfont imported from forbidden checkout: {package_file}")
    require(not _under(Path.cwd(), root), f"acceptance cwd is inside forbidden checkout: {Path.cwd()}")


class FeatureAPI:
    def __init__(self, owner: "LoadedAPI") -> None:
        self.owner = owner

    def v(self, node: int) -> Any:
        self.owner.sp_value_calls += 1
        row = self.owner.nodes.get(node)
        return None if row is None else row[1]

    def s(self, value: Any) -> tuple[int, ...]:
        self.owner.selector_calls += 1
        return tuple(node for node, (_node_type, sp) in self.owner.nodes.items() if sp == value)


class OtypeAPI:
    def __init__(self, owner: "LoadedAPI") -> None:
        self.owner = owner

    def s(self, node_type: str) -> tuple[int, ...]:
        self.owner.otype_selector_calls += 1
        return tuple(node for node, (kind, _sp) in self.owner.nodes.items() if kind == node_type)

    def v(self, node: int) -> Any:
        self.owner.otype_value_calls += 1
        row = self.owner.nodes.get(node)
        return None if row is None else row[0]


class Features:
    def __init__(self, owner: "LoadedAPI") -> None:
        self.sp = FeatureAPI(owner)
        self.otype = OtypeAPI(owner)


class LoadedAPI:
    def __init__(self, nodes: dict[int, tuple[str, str]]) -> None:
        self.nodes = dict(nodes)
        self.F = Features(self)
        self.selector_calls = 0
        self.sp_value_calls = 0
        self.otype_selector_calls = 0
        self.otype_value_calls = 0
        self.load_calls = 0

    def Fall(self) -> tuple[str, ...]:
        return ("otype", "sp")

    def load(self, *_args: Any, **_kwargs: Any) -> None:
        self.load_calls += 1
        raise AssertionError("acceptance API must never autoload corpus features")


def raw_release_checks(bundles: tuple[Any, ...], validated: tuple[Any, ...]) -> None:
    require(tuple(PRODUCTION_NOUN_CORPORA) == ("bhsa", "syriac", "extrabiblical"), "production corpus contract drifted")
    require(len(bundles) == 3 and len(validated) == 3, "expected exactly three production bundles")

    for corpus_id, bundle, checked in zip(PRODUCTION_NOUN_CORPORA, bundles, validated):
        oracle = ORACLE[corpus_id]
        require(checked.expected_parent_manifest_digest == oracle["parent_digest"], f"{corpus_id}: parent digest drift")

        profile = bundle.profile.data
        require(profile.get("parent_compatibility") == "exact-only", f"{corpus_id}: release is not explicit exact-only")

        manifest = bundle.expected_parent_manifest.data
        components = manifest.get("components")
        require(isinstance(components, list) and len(components) == 1, f"{corpus_id}: unexpected parent component set")
        component = components[0]
        require(component.get("component_id") == oracle["component_id"], f"{corpus_id}: component id drift")
        require(component.get("content_digest") == oracle["component_digest"], f"{corpus_id}: component digest drift")

        mappings = bundle.mappings.data.get("mappings")
        require(isinstance(mappings, list) and len(mappings) == 1, f"{corpus_id}: unexpected mapping set")
        mapping = mappings[0]
        require(mapping.get("mapping_id") == oracle["mapping_id"], f"{corpus_id}: mapping id drift")
        require(mapping.get("mapping_semantic_digest") == oracle["mapping_digest"], f"{corpus_id}: mapping semantic digest drift")
        review = mapping.get("review", {})
        require(review.get("review_id") == oracle["mapping_review_id"], f"{corpus_id}: mapping review id drift")
        require(review.get("status") == "reviewed", f"{corpus_id}: mapping review is not reviewed")
        require(review.get("reviewed_mapping_digest") == oracle["mapping_digest"], f"{corpus_id}: mapping review digest drift")
        require(review.get("review_source") == REVIEW_SOURCE, f"{corpus_id}: mapping review source drift")

        projections = mapping.get("projections")
        require(isinstance(projections, list) and len(projections) == 1, f"{corpus_id}: unexpected projection set")
        projection = projections[0]
        require(projection.get("projection_id") == oracle["projection_id"], f"{corpus_id}: projection id drift")
        require(projection.get("projection_semantic_digest") == oracle["projection_digest"], f"{corpus_id}: projection semantic digest drift")
        projection_review = projection.get("review", {})
        require(projection_review.get("review_id") == oracle["projection_review_id"], f"{corpus_id}: projection review id drift")
        require(projection_review.get("status") == "reviewed", f"{corpus_id}: projection review is not reviewed")
        require(projection_review.get("reviewed_mapping_digest") == oracle["projection_digest"], f"{corpus_id}: projection review digest drift")
        require(projection_review.get("review_source") == REVIEW_SOURCE, f"{corpus_id}: projection review source drift")
        require(projection.get("target") == OLIA_NOUN, f"{corpus_id}: OLiA Noun target drift")

        require(len(bundle.ontology_locks) == 1, f"{corpus_id}: unexpected ontology-lock set")
        lock = bundle.ontology_locks[0].data
        require(lock.get("source_revision") == OLIA_REVISION, f"{corpus_id}: OLiA revision drift")
        require(lock.get("release") == OLIA_RELEASE, f"{corpus_id}: OLiA release drift")
        require(lock.get("content_digest") == OLIA_CONTENT_DIGEST, f"{corpus_id}: OLiA content digest drift")
        require(lock.get("term_namespace") == OLIA_NAMESPACE, f"{corpus_id}: OLiA namespace drift")
        require(lock.get("terms_used") == [OLIA_NOUN], f"{corpus_id}: OLiA terms-used drift")


def build_contexts(*, drift_bhsa_parent: bool = False) -> tuple[tuple[LoadedCorpusContext, ...], dict[str, LoadedAPI]]:
    apis: dict[str, LoadedAPI] = {}
    contexts: list[LoadedCorpusContext] = []
    for corpus_id in PRODUCTION_NOUN_CORPORA:
        oracle = ORACLE[corpus_id]
        api = LoadedAPI(oracle["nodes"])
        apis[corpus_id] = api
        parent = oracle["parent_digest"]
        if drift_bhsa_parent and corpus_id == "bhsa":
            parent = "sha256:" + "0" * 64
        contexts.append(
            LoadedCorpusContext(
                corpus_id=corpus_id,
                parent_manifest_digest=parent,
                components=(
                    LoadedComponentContext(
                        component_id=oracle["component_id"],
                        content_digest=oracle["component_digest"],
                        api=api,
                    ),
                ),
            )
        )
    return tuple(contexts), apis


def request() -> SemanticResolveRequest:
    return SemanticResolveRequest(
        key=SemanticKey(
            profile_id="linguistic",
            capability_id="linguistic.part-of-speech",
            target=OLIA_NOUN,
            formal_kind="class",
            semantic_role="annotation-value",
        ),
        corpora=tuple(PRODUCTION_NOUN_CORPORA),
        semantic_mode="exact",
    )


def plan_checks(result: Any, apis: dict[str, LoadedAPI]) -> None:
    require(result.execution_contract == "tfont-exact-execution-v1", "execution contract drifted")
    require(result.resolution.request == request(), "resolution did not preserve the exact request")
    require_sha256(result.resolution.resolution_fingerprint, "resolution fingerprint")
    require(result.resolution.losses == (), "exact production acceptance unexpectedly reports losses")

    result_corpora = tuple(row.corpus_id for row in result.corpora)
    require(result_corpora == ("bhsa", "extrabiblical", "syriac"), f"nondeterministic corpus result order: {result_corpora!r}")
    plans = {plan.corpus_id: plan for plan in result.resolution.plans}
    require(set(plans) == set(PRODUCTION_NOUN_CORPORA), "resolution plans do not cover production corpora")

    for row in result.corpora:
        corpus_id = row.corpus_id
        oracle = ORACLE[corpus_id]
        plan = row.plan
        require(row.nodes == oracle["expected_nodes"], f"{corpus_id}: result nodes drifted: {row.nodes!r}")
        require(plan.corpus_id == corpus_id, f"{corpus_id}: plan corpus mismatch")
        require(plans[corpus_id].plan_fingerprint == plan.plan_fingerprint, f"{corpus_id}: execution plan is not the resolved plan")
        require(plan.semantic_key == request().key, f"{corpus_id}: semantic key drift")
        require(plan.mapping_id == oracle["mapping_id"], f"{corpus_id}: selected mapping drift")
        require(plan.projection_id == oracle["projection_id"], f"{corpus_id}: selected projection drift")
        require(plan.mapping_semantic_digest == oracle["mapping_digest"], f"{corpus_id}: plan mapping digest drift")
        require(plan.projection_semantic_digest == oracle["projection_digest"], f"{corpus_id}: plan projection digest drift")
        require(plan.mapping_review.review_id == oracle["mapping_review_id"], f"{corpus_id}: plan mapping review drift")
        require(plan.mapping_review.status == "reviewed", f"{corpus_id}: plan mapping review status drift")
        require(plan.mapping_review.reviewed_semantic_digest == oracle["mapping_digest"], f"{corpus_id}: plan mapping review binding drift")
        require(plan.projection_review.review_id == oracle["projection_review_id"], f"{corpus_id}: plan projection review drift")
        require(plan.projection_review.status == "reviewed", f"{corpus_id}: plan projection review status drift")
        require(plan.projection_review.reviewed_semantic_digest == oracle["projection_digest"], f"{corpus_id}: plan projection review binding drift")
        require(plan.expected_parent_manifest_digest == oracle["parent_digest"], f"{corpus_id}: plan expected parent drift")
        require(plan.observed_parent_manifest_digest == oracle["parent_digest"], f"{corpus_id}: plan observed parent drift")
        require(plan.parent_state == "verified-exact", f"{corpus_id}: plan is not exact-parent authorized")
        require(tuple(plan.native_dependencies) == oracle["dependencies"], f"{corpus_id}: native dependency closure drift")
        require_sha256(plan.profile_release_fingerprint, f"{corpus_id}: profile release fingerprint")
        require_sha256(plan.prerequisite_fingerprint, f"{corpus_id}: prerequisite fingerprint")
        require_sha256(plan.native_execution_binding_identity, f"{corpus_id}: native binding identity")
        require_sha256(plan.plan_fingerprint, f"{corpus_id}: plan fingerprint")

        binding = plan.native_execution_binding
        require(binding.component_id == oracle["component_id"], f"{corpus_id}: binding component drift")
        require(binding.node_type == "word" and binding.feature == "sp", f"{corpus_id}: binding is not word.sp")
        require(binding.execution_shape == oracle["execution_shape"], f"{corpus_id}: execution shape drift")
        if oracle["values"] is not None:
            require(binding.values == oracle["values"], f"{corpus_id}: selected value set drift")
            require(binding.value_present is False and binding.value is None, f"{corpus_id}: set binding mixed with scalar value")
        else:
            require(binding.values is None, f"{corpus_id}: scalar binding unexpectedly has values")
            require(binding.value_present is True and binding.value == oracle["value"], f"{corpus_id}: scalar value drift")

        lock = plan.ontology_lock
        require(lock.lock_id == "olia-reference-model", f"{corpus_id}: plan ontology lock id drift")
        require(lock.ontology_id == "olia", f"{corpus_id}: plan ontology id drift")
        require(lock.release == OLIA_RELEASE, f"{corpus_id}: plan OLiA release drift")
        require(lock.content_digest == OLIA_CONTENT_DIGEST, f"{corpus_id}: plan OLiA digest drift")
        require(lock.term_namespace == OLIA_NAMESPACE, f"{corpus_id}: plan OLiA namespace drift")

        report = row.runtime_report
        require(report.variant == plan.variant, f"{corpus_id}: runtime report variant differs from plan")
        require(report.variant.expected_parent_manifest_digest == oracle["parent_digest"], f"{corpus_id}: runtime expected parent drift")
        require(report.observed_parent_manifest_digest == oracle["parent_digest"], f"{corpus_id}: runtime observed parent drift")
        require(report.compatibility_state == "verified-exact", f"{corpus_id}: runtime compatibility is not exact")
        require(report.profile_release_fingerprint == plan.profile_release_fingerprint, f"{corpus_id}: runtime/profile release mismatch")
        require(report.source_contract == "tfont-exact-execution-runtime-v1", f"{corpus_id}: runtime source contract drift")
        require(tuple(dep.dependency_id for dep in report.dependency_results) == oracle["dependencies"], f"{corpus_id}: runtime dependencies drift")
        require(all(dep.result == "pass" for dep in report.dependency_results), f"{corpus_id}: runtime dependency did not pass")
        require_sha256(report.report_fingerprint, f"{corpus_id}: runtime report fingerprint")
        require(apis[corpus_id].load_calls == 0, f"{corpus_id}: acceptance triggered autoload")


def negative_parent_drift(ir: Any) -> None:
    contexts, apis = build_contexts(drift_bhsa_parent=True)
    try:
        execute_exact_semantic(ir, request(), contexts)
    except SemanticResolutionError as error:
        require(error.problem.category == "parent_incompatible", f"wrong drift problem: {error.problem.category!r}")
    else:
        raise AssertionError("parent drift unexpectedly executed")
    for corpus_id, api in apis.items():
        require(api.selector_calls == 0, f"{corpus_id}: native selector ran before drift rejection")
        require(api.load_calls == 0, f"{corpus_id}: drift path triggered autoload")


def main() -> None:
    assert_install_isolation()
    bundles = load_production_noun_bundles()
    validated = tuple(validate_semantic_bundle(bundle) for bundle in bundles)
    raw_release_checks(bundles, validated)
    ir = compile_semantic_ir(validated)

    variants = {variant.key.corpus_id: variant for variant in ir.variants}
    require(set(variants) == set(PRODUCTION_NOUN_CORPORA), "compiled variants do not cover production corpora")
    for corpus_id, variant in variants.items():
        oracle = ORACLE[corpus_id]
        require(variant.key.expected_parent_manifest_digest == oracle["parent_digest"], f"{corpus_id}: compiled parent drift")
        require(variant.release_signature.parent_compatibility == "exact-only", f"{corpus_id}: compiled parent policy drift")
        require(dict(variant.mapping_digests) == {oracle["mapping_id"]: oracle["mapping_digest"]}, f"{corpus_id}: compiled mapping authority drift")

    contexts, apis = build_contexts()
    result = execute_exact_semantic(ir, request(), contexts)
    plan_checks(result, apis)
    negative_parent_drift(ir)

    payload = {
        "contract": CONTRACT,
        "corpora": {row.corpus_id: list(row.nodes) for row in result.corpora},
        "resolution_fingerprint": result.resolution.resolution_fingerprint,
        "status": "pass",
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
