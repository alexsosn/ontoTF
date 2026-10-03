"""I-024 valued-edge execution reconciliation.

Research-only probe. It records the current post-I-023 contract, pinned
Text-Fabric mechanics, and real TLHdig/BHSA valued-edge semantics used to
choose the smallest lossless production slice.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import fields
from pathlib import Path

from jsonschema import Draft202012Validator
from tf.convert import tf as tf_convert
from tf.core.edgefeature import EdgeFeature

from tfont.semantic_execution import (
    ApproximateAuthorityCorpusExecution,
    ApproximateConjunctionCorpusExecution,
    ApproximateCorpusExecution,
    ExactAuthorityCorpusExecution,
    ExactConjunctionCorpusExecution,
    ExactCorpusExecution,
    IdentifierCorpusExecution,
    IdentityCorpusExecution,
)
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


def tf_header(path: Path) -> tuple[str, ...]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            value = line.rstrip("\n")
            if value == "":
                break
            rows.append(value)
    return tuple(rows)


def dataclass_fields(value) -> list[str]:
    return [field.name for field in fields(value)]


def main() -> int:
    if not TLHDIG.is_dir():
        raise SystemExit(f"missing pinned TLHdig checkout: {TLHDIG}")
    if not BHSA.is_dir():
        raise SystemExit(f"missing pinned BHSA checkout: {BHSA}")

    schema = load_json("src/tfont/schemas/mapping.schema.json")
    validator = binding_validator(schema)
    unvalued = {
        "component_id": "tlhdig-tf",
        "node_type": "word",
        "execution_shape": "edge-path",
        "steps": [
            {
                "edge": "selected",
                "direction": "outgoing",
                "result_node_type": "analysis",
                "valued": False,
            }
        ],
    }
    valued_candidate = json.loads(json.dumps(unvalued))
    valued_candidate["steps"][0].update(
        {
            "valued": True,
            "value_type": "str",
            "value_role": "source-evidence",
        }
    )

    selected_doc = text(TLHDIG / "docs/features/selected.md")
    witness_doc = text(TLHDIG / "docs/features/witness_resolution.md")
    joined_doc = text(TLHDIG / "docs/features/joined.md")
    readme = text(TLHDIG / "README.md")
    convert = text(TLHDIG / "programs/tlhdig/convert.py")
    graph = text(TLHDIG / "programs/tlhdig/manuscript_graph.py")
    convert_tests = text(TLHDIG / "programs/tests/test_convert.py")
    joins_report = text(TLHDIG / "reports/manuscript-joins.md")

    selected_header = tf_header(TLHDIG / "tf/0.4.0/selected.tf")
    witness_header = tf_header(TLHDIG / "tf/0.4.0/witness_resolution.tf")
    joined_header = tf_header(TLHDIG / "tf/0.4.0/joined.tf")

    bhsa_inventory = load_json("docs/research/data/generated/r005/bhsa.json")
    bhsa_valued = {
        name: {
            "description": row.get("metadata", {}).get("description"),
            "value_type": row.get("metadata", {}).get("valueType"),
            "valued": row.get("valued"),
        }
        for name, row in bhsa_inventory.get("edge_features", {}).items()
        if row.get("valued") is True
    }
    omap_doc = text(BHSA / "docs/features/omap@ll.md")

    edge_source = inspect.getsource(EdgeFeature)
    parser_source = inspect.getsource(tf_convert._readDataTf)

    result_dataclasses = {
        cls.__name__: dataclass_fields(cls)
        for cls in (
            ExactCorpusExecution,
            ApproximateCorpusExecution,
            ExactAuthorityCorpusExecution,
            ApproximateAuthorityCorpusExecution,
            IdentityCorpusExecution,
            IdentifierCorpusExecution,
            ExactConjunctionCorpusExecution,
            ApproximateConjunctionCorpusExecution,
        )
    }

    result = {
        "pinned_sources": {
            "text_fabric": TF_REVISION,
            "tlhdig": TLHDIG_REVISION,
            "bhsa": BHSA_REVISION,
        },
        "current_tfont_contract": {
            "edge_step_ir_fields": dataclass_fields(EdgeStepIR),
            "unvalued_edge_path_is_schema_valid": is_valid(validator, unvalued),
            "valued_candidate_is_schema_valid": is_valid(validator, valued_candidate),
            "execution_result_fields": result_dataclasses,
            "execution_results_have_edge_path_evidence": any(
                "edge_path_evidence" in value
                or "constituent_edge_path_evidence" in value
                for value in result_dataclasses.values()
            ),
        },
        "text_fabric_mechanics": {
            "edge_feature_has_do_values": "self.doValues = doValues" in edge_source,
            "edge_feature_has_meta": "self.meta = metaData" in edge_source,
            "outgoing_returns_value_pairs_when_valued": (
                "destination node and the" in (EdgeFeature.f.__doc__ or "")
                and "value" in (EdgeFeature.f.__doc__ or "").lower()
            ),
            "incoming_returns_value_pairs_when_valued": (
                "start node and the" in (EdgeFeature.t.__doc__ or "")
                and "value" in (EdgeFeature.t.__doc__ or "").lower()
            ),
            "declared_value_type_supports_int": 'valueType == "int"' in parser_source,
            "empty_integer_value_can_decode_to_none": (
                "else None" in parser_source and "if isNum" in parser_source
            ),
            "string_empty_value_is_representable": (
                'else ""' in parser_source and 'if valTf == ""' in parser_source
            ),
        },
        "tlhdig_real_edges": {
            "selected": {
                "header_has_edge_values": "@edgeValues" in selected_header,
                "header_value_type": next(
                    (row.split("=", 1)[1] for row in selected_header if row.startswith("@valueType=")),
                    None,
                ),
                "word_to_analysis": "word -> analysis" in selected_doc,
                "selector_tokens_verbatim": (
                    "selector token" in selected_doc.lower()
                    and "verbatim" in selected_doc.lower()
                ),
                "multi_selection_is_real": "selects two analyses" in convert,
                "same_analysis_tokens_are_joined": (
                    "alternatives that share an" in convert
                    and "analysis are joined" in convert
                ),
                "examples_are_preserved": (
                    'picked == {1: "1", 2: "2a"}' in convert_tests
                    and 'picked == {1: "1bR 1bS"}' in convert_tests
                ),
                "recommended_value_role": "source-evidence",
                "filter_in_i024": False,
            },
            "witness_resolution": {
                "header_has_edge_values": "@edgeValues" in witness_header,
                "header_value_type": next(
                    (row.split("=", 1)[1] for row in witness_header if row.startswith("@valueType=")),
                    None,
                ),
                "line_to_fragment": "line -> fragment" in witness_doc,
                "closed_real_values_documented": (
                    "unique | ambiguous" in witness_doc
                    and "witness_resolution=unique|ambiguous" in readme
                ),
                "block_local_resolution_is_explicit": (
                    "block" in graph.lower()
                    and "ambiguous" in graph
                    and "unique" in graph
                ),
                "recommended_value_role": "semantic-qualifier",
                "filter_in_i024": False,
            },
            "joined": {
                "header_has_edge_values": "@edgeValues" in joined_header,
                "header_value_type": next(
                    (row.split("=", 1)[1] for row in joined_header if row.startswith("@valueType=")),
                    None,
                ),
                "fragment_to_fragment": "fragment -> fragment" in joined_doc,
                "closed_real_values_documented": "direct/indirect" in joined_doc,
                "orientation_is_source_order_not_semantic_direction": (
                    "source apparatus order" in joined_doc
                    and "not semantic direction" in readme
                ),
                "authoritative_ledger_is_joinstmt": (
                    "Authoritative statement multiplicity remains on `joinstmt` nodes."
                    in joins_report
                ),
                "recommended_value_role": "semantic-qualifier",
                "filter_in_i024": False,
            },
        },
        "bhsa_technical_control": {
            "valued_edges": bhsa_valued,
            "omap_is_version_mapping": "previous version" in omap_doc,
            "omap_value_describes_correspondence_quality": (
                "how good the correspondence" in omap_doc
            ),
            "recommended_value_role": "technical",
            "semantic_promotion_is_not_authorized": True,
        },
        "recommended_i024_slice": {
            "step_fields_when_valued": [
                "edge",
                "direction",
                "result_node_type",
                "valued",
                "value_type",
                "value_role",
            ],
            "value_type_enum": ["str", "int"],
            "value_role_enum": [
                "semantic-qualifier",
                "source-evidence",
                "technical",
            ],
            "accepted_values_or_value_predicates": False,
            "value_predicates_follow_up_issue": 253,
            "dependency_contract_version_change": False,
            "path_present_dependency_remains_edge_direction_only": True,
            "runtime_requires_do_values_true": True,
            "runtime_requires_declared_value_type_match": True,
            "missing_integer_value_none_is_preserved_not_coerced": True,
            "empty_string_is_preserved_not_treated_as_absence": True,
            "bool_is_not_an_integer_edge_value": True,
            "evidence_is_layered_edge_dag_not_expanded_path_cartesian_product": True,
            "evidence_records_all_steps_when_any_step_is_valued": True,
            "evidence_records_native_edge_orientation": True,
            "evidence_records_value_presence_separately_from_value": True,
            "evidence_excludes_off_domain_neighbors": True,
            "runtime_validates_value_before_domain_filter": True,
            "evidence_has_deterministic_fingerprint": True,
            "evidence_binds_execution_plan_fingerprint": True,
            "single_result_evidence_field": "edge_path_evidence",
            "conjunction_evidence_field": "constituent_edge_path_evidence",
            "conjunction_evidence_is_plan_aligned_with_none_placeholders": True,
            "outer_execution_contract_version_change": False,
            "nested_evidence_contract": "tfont-edge-path-evidence-v1",
            "mapping_schema_version_change": False,
            "mapping_digest_algorithm_change": False,
            "native_binding_identity_algorithm_change": False,
            "semantic_approximation_does_not_approximate_native_edge_values": True,
        },
    }

    if result["current_tfont_contract"]["edge_step_ir_fields"] != [
        "edge",
        "direction",
        "result_node_type",
        "valued",
    ]:
        raise SystemExit("I-023 EdgeStepIR contract drifted")
    if not result["current_tfont_contract"]["unvalued_edge_path_is_schema_valid"]:
        raise SystemExit("I-023 unvalued edge path is not available")
    if result["current_tfont_contract"]["valued_candidate_is_schema_valid"]:
        raise SystemExit("valued edge path unexpectedly became source-valid before I-024")
    if result["current_tfont_contract"]["execution_results_have_edge_path_evidence"]:
        raise SystemExit("edge-path evidence unexpectedly exists before I-024")

    mechanics = result["text_fabric_mechanics"]
    if not all(mechanics.values()):
        raise SystemExit("pinned Text-Fabric valued-edge mechanics drifted")

    for edge in ("selected", "witness_resolution", "joined"):
        facts = result["tlhdig_real_edges"][edge]
        if not facts["header_has_edge_values"] or facts["header_value_type"] != "str":
            raise SystemExit(f"TLHdig {edge} valued-edge metadata drifted")

    if not result["tlhdig_real_edges"]["selected"]["examples_are_preserved"]:
        raise SystemExit("TLHdig selected source-token examples drifted")
    if not result["tlhdig_real_edges"]["witness_resolution"]["closed_real_values_documented"]:
        raise SystemExit("TLHdig witness resolution semantics drifted")
    if not result["tlhdig_real_edges"]["joined"]["authoritative_ledger_is_joinstmt"]:
        raise SystemExit("TLHdig joined provenance boundary drifted")

    technical = result["bhsa_technical_control"]
    if set(technical["valued_edges"]) != {"omap@2017-2021", "omap@c-2021"}:
        raise SystemExit("BHSA valued-edge technical control drifted")
    if not technical["omap_value_describes_correspondence_quality"]:
        raise SystemExit("BHSA omap value semantics drifted")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
