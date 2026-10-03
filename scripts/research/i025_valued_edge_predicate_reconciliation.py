"""I-025 valued-edge predicate/domain-authority reconciliation.

Research-only probe. It records the post-I-024 contract, pinned Text-Fabric
edge-value mechanics, real TLHdig/BHSA controls, and the smallest reviewed
design candidate for exact valued-edge predicates. It changes no production
runtime behavior.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import fields
from pathlib import Path

from jsonschema import Draft202012Validator
from tf.core.edgefeature import EdgeFeature

import tfont.runtime_prerequisites as runtime_prerequisites
import tfont.runtime_tf_observation as runtime_tf_observation
import tfont.semantic_digest_v2 as semantic_digest_v2
import tfont.semantic_ir as semantic_ir
from tfont.semantic_ir import EdgeStepIR


ROOT = Path(__file__).resolve().parents[2]
TLHDIG = ROOT / "_research" / "tlhdig"
BHSA = ROOT / "_research" / "bhsa"
TLHDIG_REVISION = "0261d2d46b3419a1f907e231a03f749d133cfb5e"
BHSA_REVISION = "4db00e2157915495e1a4d3d57e41223df24775da"
TF_REVISION = "0c45c386916cb52be84098796ec27ce97e5bf9fc"


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def binding_validator(schema: dict) -> Draft202012Validator:
    return Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$defs": schema["$defs"],
            "$ref": "#/$defs/nativeBinding",
        }
    )


def is_valid(validator: Draft202012Validator, value: dict) -> bool:
    return not tuple(validator.iter_errors(value))


def main() -> int:
    if not TLHDIG.is_dir():
        raise SystemExit(f"missing pinned TLHdig checkout: {TLHDIG}")
    if not BHSA.is_dir():
        raise SystemExit(f"missing pinned BHSA checkout: {BHSA}")

    mapping_schema = load_json("src/tfont/schemas/mapping.schema.json")
    profile_schema = load_json("src/tfont/schemas/profile.schema.json")
    bhsa_inventory = load_json("docs/research/data/generated/r005/bhsa.json")
    i024 = load_json(
        "docs/research/data/generated/i024/valued-edge-reconciliation.json"
    )

    validator = binding_validator(mapping_schema)
    valued = {
        "component_id": "tlhdig-tf",
        "node_type": "line",
        "execution_shape": "edge-path",
        "steps": [
            {
                "edge": "witness_resolution",
                "direction": "outgoing",
                "result_node_type": "fragment",
                "valued": True,
                "value_type": "str",
                "value_role": "semantic-qualifier",
            }
        ],
    }
    predicate_candidate = json.loads(json.dumps(valued))
    predicate_candidate["steps"][0]["match_values"] = ["ambiguous"]

    dependency = profile_schema["$defs"]["dependency"]
    dependency_kinds = dependency["properties"]["kind"]["enum"]
    native_value = profile_schema["$defs"]["nativeValuePresentAssertion"]
    value_domain = profile_schema["$defs"]["valueDomainAssertion"]

    edge_source = inspect.getsource(EdgeFeature)
    items_source = inspect.getsource(EdgeFeature.items)
    f_source = inspect.getsource(EdgeFeature.f)
    t_source = inspect.getsource(EdgeFeature.t)
    digest_source = inspect.getsource(semantic_digest_v2)
    binding_identity_source = inspect.getsource(semantic_ir.native_binding_identity)
    dependency_normalizer_source = inspect.getsource(
        semantic_ir._normalize_dependency
    )
    runtime_protocol_source = inspect.getsource(
        runtime_prerequisites.RuntimeObservation
    )
    observation_source = inspect.getsource(runtime_tf_observation.LoadedTFObservation)
    release_projection_source = inspect.getsource(
        runtime_prerequisites._validate_variant
    )
    profile_fingerprint_source = inspect.getsource(
        __import__(
            "tfont.semantic_resolver",
            fromlist=["_profile_release_projection"],
        )._profile_release_projection
    )

    selected_doc = text(TLHDIG / "docs/features/selected.md")
    witness_doc = text(TLHDIG / "docs/features/witness_resolution.md")
    joined_doc = text(TLHDIG / "docs/features/joined.md")
    featuremeta = text(TLHDIG / "programs/tlhdig/featuremeta.py")
    graph = text(TLHDIG / "programs/tlhdig/manuscript_graph.py")
    omap_doc = text(BHSA / "docs/features/omap@ll.md")

    bhsa_edges = bhsa_inventory["edge_features"]
    omap_2017 = bhsa_edges["omap@2017-2021"]
    omap_c = bhsa_edges["omap@c-2021"]

    result = {
        "pinned_sources": {
            "text_fabric": TF_REVISION,
            "tlhdig": TLHDIG_REVISION,
            "bhsa": BHSA_REVISION,
        },
        "current_contract": {
            "mapping_schema_version": mapping_schema["properties"]["schema_version"]["const"],
            "profile_schema_version": profile_schema["properties"]["schema_version"]["const"],
            "dependency_contract_version": profile_schema["properties"][
                "dependency_contract_version"
            ]["const"],
            "dependency_kinds": dependency_kinds,
            "edge_value_domain_kind_exists": "edge-value-domain" in dependency_kinds,
            "native_value_present_fields": native_value["required"],
            "value_domain_fields": value_domain["required"],
            "edge_step_ir_fields": [field.name for field in fields(EdgeStepIR)],
            "valued_path_is_schema_valid": is_valid(validator, valued),
            "step_match_values_is_schema_valid": is_valid(
                validator, predicate_candidate
            ),
            "runtime_observation_has_edge_values": "def edge_values(" in runtime_protocol_source,
            "loaded_tf_observation_has_edge_values": "def edge_values(" in observation_source,
            "semantic_digest_treats_match_values_as_set_like": (
                '"match_values"' in digest_source
            ),
            "native_binding_identity_normalizes_match_values": (
                "match_values" in binding_identity_source
            ),
            "dependency_normalization_sorts_values": (
                'field in {"evidence", "values"}' in dependency_normalizer_source
            ),
            "profile_release_fingerprint_binds_dependency_contract_version": (
                '"dependency_contract_version": signature.dependency_contract_version'
                in profile_fingerprint_source
            ),
            "runtime_accepts_dependency_contract_v1_only": (
                "signature.dependency_contract_version != 1"
                in release_projection_source
            ),
        },
        "text_fabric_mechanics": {
            "edge_feature_exposes_do_values": "self.doValues = doValues" in edge_source,
            "edge_feature_exposes_metadata": "self.meta = metaData" in edge_source,
            "items_is_public_data_iterator": "return self.data.items()" in items_source,
            "valued_outgoing_uses_node_value_pairs": (
                "self.data[n].items()" in f_source
            ),
            "valued_incoming_uses_node_value_pairs": (
                "self.dataInv[n].items()" in t_source
            ),
            "loaded_edge_domain_can_be_observed_without_autoload": True,
        },
        "real_controls": {
            "tlhdig_witness_resolution": {
                "value_role": "semantic-qualifier",
                "value_type": "str",
                "documented_closed_values": ["ambiguous", "unique"],
                "closed_source_evidence": (
                    "unique | ambiguous" in witness_doc
                    and '"witness_resolution": "line -> fragment resolution status: unique | ambiguous'
                    in featuremeta
                ),
                "predicate_use_case": "witness_resolution=ambiguous",
            },
            "tlhdig_joined": {
                "value_role": "semantic-qualifier",
                "value_type": "str",
                "documented_closed_values": ["direct", "indirect"],
                "closed_source_evidence": (
                    "direct/indirect" in joined_doc
                    and 'CONFIDENT_KINDS = frozenset({"direct", "indirect"})' in graph
                ),
                "orientation_is_apparatus_order": (
                    "source apparatus order" in joined_doc
                ),
                "predicate_use_case": "joined=direct",
            },
            "tlhdig_selected": {
                "value_role": "source-evidence",
                "value_type": "str",
                "open_token_domain": (
                    "selector token(s)" in selected_doc
                    and "verbatim" in selected_doc
                    and "Never empty" in selected_doc
                ),
                "semantic_predicate_authority": False,
            },
            "bhsa_omap_2017_2021": {
                "value_role": "technical",
                "value_type": "int",
                "domain_observation": omap_2017.get("domain_observation"),
                "observed_unique_count": omap_2017.get("observed_unique_count"),
                "empty_observation_count": omap_2017.get("empty_observation_count"),
                "semantic_predicate_authority": False,
            },
            "bhsa_omap_c_2021": {
                "value_role": "technical",
                "value_type": "int",
                "domain_observation": omap_c.get("domain_observation"),
                "observed_unique_count": omap_c.get("observed_unique_count"),
                "empty_observation_count": omap_c.get("empty_observation_count"),
                "observed_small_domain_is_not_semantic_closure": (
                    bhsa_inventory["domain_policy"].get(
                        "observed_small_domain_is_not_automatically_categorical"
                    )
                    is True
                ),
                "omap_values_are_correspondence_quality": (
                    "how good the correspondence" in omap_doc
                ),
                "semantic_predicate_authority": False,
            },
        },
        "recommended_i025_slice": {
            "predicate_field": "match_values",
            "predicate_form": "non-empty-finite-set-membership",
            "singleton_means_exact_equality": True,
            "multiple_values_mean_exact_or": True,
            "fuzzy_matching": False,
            "match_values_is_set_like": True,
            "match_values_types": ["str", "int"],
            "match_none": False,
            "empty_string_is_matchable_when_reviewed": True,
            "safe_jcs_integer_required": True,
            "initial_predicate_value_roles": ["semantic-qualifier"],
            "source_evidence_filtering_deferred": True,
            "technical_filtering_deferred": True,
            "dependency_contract_version": 2,
            "new_dependency_kind": "edge-value-domain",
            "edge_value_domain_assertion_fields": [
                "edge",
                "source_node_type",
                "target_node_type",
                "value_type",
                "value_role",
                "values",
                "domain_semantics",
            ],
            "edge_value_domain_uses_native_orientation": True,
            "edge_value_domain_includes_direction": False,
            "edge_value_domain_semantics": "closed-reviewed",
            "edge_value_domain_requires_evidence": True,
            "observed_domain_alone_authorizes_predicate": False,
            "runtime_observation_method": "edge_values",
            "runtime_observation_uses_loaded_edge_items": True,
            "runtime_observation_filters_native_source_target_types": True,
            "runtime_observation_excludes_missing_int_none_from_domain": True,
            "runtime_observation_records_missing_count": True,
            "closed_domain_runtime_rule": "observed-present-values-subset-of-reviewed-values",
            "reviewed_match_value_may_be_absent_at_runtime": True,
            "absent_reviewed_value_yields_valid_empty_result": True,
            "mapping_schema_version_change": False,
            "profile_schema_version_change": False,
            "mapping_digest_algorithm_change": False,
            "native_binding_identity_algorithm_change": False,
            "canonicalization_extension_required_for_match_values": True,
            "profile_release_fingerprint_algorithm_change": False,
            "existing_dependency_v1_profiles_remain_valid": True,
            "new_edge_value_domains_require_dependency_v2": True,
            "execution_filter_order": [
                "validate-pair-node-value",
                "validate-result-node-type",
                "exact-match-values",
                "evidence-node-jcs-bound",
                "accept-frontier-and-evidence",
            ],
            "reuse_i024_evidence_shape": True,
            "evidence_contains_justifying_native_value": True,
            "approximate_mapping_keeps_native_value_match_exact": True,
            "conjunction_uses_filtered_final_nodes": True,
            "reference_execution_reuses_same_filter": True,
            "autoload_or_network": False,
        },
        "i024_boundary_preserved": {
            "path_present_remains_edge_direction_only": i024[
                "recommended_i024_slice"
            ]["path_present_dependency_remains_edge_direction_only"],
            "edge_values_are_already_losslessly_preserved": i024[
                "current_tfont_contract"
            ]["execution_results_have_edge_path_evidence"],
            "nested_evidence_contract": i024["recommended_i024_slice"][
                "nested_evidence_contract"
            ],
        },
    }

    current = result["current_contract"]
    if current["dependency_contract_version"] != 1:
        raise SystemExit("current dependency-contract baseline drifted")
    if current["edge_value_domain_kind_exists"]:
        raise SystemExit("edge-value-domain unexpectedly already exists")
    if current["step_match_values_is_schema_valid"]:
        raise SystemExit("match_values unexpectedly already source-valid")
    if current["runtime_observation_has_edge_values"]:
        raise SystemExit("runtime observation unexpectedly already exposes edge values")
    if current["loaded_tf_observation_has_edge_values"]:
        raise SystemExit("loaded TF observation unexpectedly already exposes edge values")

    mechanics = result["text_fabric_mechanics"]
    if not all(mechanics.values()):
        raise SystemExit("pinned Text-Fabric edge-value mechanics drifted")

    witness = result["real_controls"]["tlhdig_witness_resolution"]
    joined = result["real_controls"]["tlhdig_joined"]
    selected = result["real_controls"]["tlhdig_selected"]
    if not witness["closed_source_evidence"]:
        raise SystemExit("TLHdig witness_resolution closed-domain evidence drifted")
    if not joined["closed_source_evidence"]:
        raise SystemExit("TLHdig joined closed-domain evidence drifted")
    if not selected["open_token_domain"]:
        raise SystemExit("TLHdig selected open source-evidence domain drifted")

    omap = result["real_controls"]["bhsa_omap_c_2021"]
    if (
        not omap["observed_small_domain_is_not_semantic_closure"]
        or not omap["omap_values_are_correspondence_quality"]
    ):
        raise SystemExit("BHSA omap technical negative control drifted")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
