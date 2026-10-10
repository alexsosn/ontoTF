"""I-023 edge-path execution reconciliation.

Research probe plus post-implementation current-state guard. Historical
research findings remain documented in the report; this script records the
current source/IR/runtime boundary after I-023 productionization.
"""

from __future__ import annotations

import inspect
import json
import re
from dataclasses import fields
from pathlib import Path

from jsonschema import Draft202012Validator
from tf.core.edgefeature import EdgeFeature

from tfont.runtime_tf_observation import LoadedTFObservation
from tfont.semantic_ir import EdgeStepIR, NativeBindingIR


ROOT = Path(__file__).resolve().parents[2]
BASELINE_MAIN = "c8b38cfb5656b161acbf1b9afcde3655770ee69f"
TF_UPSTREAM_REVISION = "0c45c386916cb52be84098796ec27ce97e5bf9fc"


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


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


def production_mapping_shapes(*, historical_only: bool = False) -> dict:
    """Audit production mappings; optionally reproduce the pinned I-022/23 baseline.

    Historical research reports were frozen when only 0.1.0/0.2.0 profiles
    existed. Additive profile releases must not rewrite those snapshots.
    Always audit *all* releases separately for forbidden structural shapes.
    """
    root = ROOT / "src/tfont/resources/profiles"
    rows = []
    shapes = set()
    structural = []
    for path in sorted(root.glob("*/*/mappings/*.json")):
        if historical_only and path.parent.parent.name not in {"0.1.0", "0.2.0"}:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        relative = str(path.relative_to(ROOT))
        for mapping in data.get("mappings", []):
            candidates = [
                ("mapping", mapping.get("mapping_id"), mapping.get("native_binding")),
            ]
            candidates.extend(
                (
                    "projection",
                    item.get("projection_id"),
                    item.get("native_execution_binding"),
                )
                for item in mapping.get("projections", [])
            )
            candidates.extend(
                ("reference", item.get("reference_id"), item.get("native_binding"))
                for item in mapping.get("external_references", [])
            )
            for owner_kind, owner_id, binding in candidates:
                if type(binding) is not dict:
                    continue
                shape = binding.get("execution_shape")
                if type(shape) is str:
                    shapes.add(shape)
                    row = {
                        "path": relative,
                        "owner_kind": owner_kind,
                        "owner_id": owner_id,
                        "execution_shape": shape,
                    }
                    rows.append(row)
                    if shape in {"membership", "edge-path"}:
                        structural.append(row)
    rows.sort(
        key=lambda row: (
            row["path"],
            row["owner_kind"],
            row["owner_id"] or "",
            row["execution_shape"],
        )
    )
    return {
        "execution_shapes": sorted(shapes),
        "binding_count": len(rows),
        "structural_bindings": structural,
    }


def edge_summary(inventory: dict, edge: str) -> dict:
    row = inventory["edge_features"][edge]
    return {
        "source_types": row.get("source_types", []),
        "target_types": row.get("target_types", []),
        "valued": row.get("valued"),
    }


def main() -> int:
    schema = load_json("src/tfont/schemas/mapping.schema.json")
    validator = binding_validator(schema)

    old_typed_start = {
        "component_id": "fixture-tf",
        "node_type": "word",
        "execution_shape": "edge-path",
        "steps": [{"edge": "word_line", "direction": "outgoing"}],
    }
    typed_path = {
        "component_id": "fixture-tf",
        "node_type": "word",
        "execution_shape": "edge-path",
        "steps": [
            {
                "edge": "word_line",
                "direction": "outgoing",
                "result_node_type": "line",
                "valued": False,
            }
        ],
    }
    valued_path = json.loads(json.dumps(typed_path))
    valued_path["steps"][0]["valued"] = True

    examples = {
        "edge_path_shape_only": {"execution_shape": "edge-path"},
        "edge_path_steps_only": {
            "execution_shape": "edge-path",
            "steps": [{"edge": "word_line", "direction": "outgoing"}],
        },
        "edge_path_old_typed_start": old_typed_start,
        "edge_path_one_step_alias": {
            "component_id": "fixture-tf",
            "node_type": "word",
            "execution_shape": "edge-path",
            "edge": "word_line",
            "direction": "outgoing",
        },
        "edge_path_typed_unvalued": typed_path,
        "edge_path_typed_with_feature": {**typed_path, "feature": "sp"},
        "edge_path_typed_with_interpretation": {
            **typed_path,
            "interpretation": "occurrenceSet",
        },
        "edge_path_typed_valued_true": valued_path,
    }

    execution_source = (
        ROOT / "src/tfont/semantic_execution.py"
    ).read_text(encoding="utf-8")
    runtime_shapes = sorted(
        set(re.findall(r'binding\.execution_shape == "([^"]+)"', execution_source))
    )
    conjunction_start = execution_source.index("def _validate_conjunction_node_domains")
    conjunction_end = execution_source.index(
        "def execute_exact_conjunction", conjunction_start
    )
    conjunction_source = execution_source[conjunction_start:conjunction_end]

    path_source = inspect.getsource(LoadedTFObservation.path)
    edge_init_source = inspect.getsource(EdgeFeature.__init__)
    r007 = (
        ROOT / "docs/research/R-007-tf-structural-semantics.md"
    ).read_text(encoding="utf-8")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # Keep the historical evidence reproducible while validating the full
    # current release catalog against the same non-structural safety boundary.
    production_shapes = production_mapping_shapes(historical_only=True)
    all_production_shapes = production_mapping_shapes()
    if all_production_shapes["execution_shapes"] != [
        "value-predicate", "value-set-predicate"
    ] or all_production_shapes["structural_bindings"]:
        raise SystemExit("current released profile has forbidden execution shape")
    if all_production_shapes["binding_count"] < production_shapes["binding_count"]:
        raise SystemExit("current production catalog lost historical bindings")

    oracc = load_json("docs/research/data/generated/i018/oracc-0.4.0.json")
    tlhdig = load_json("docs/research/data/generated/i019/tlhdig-0.4.0.json")
    bhsa = load_json("docs/research/data/generated/r005/bhsa.json")

    oracc_word_line = edge_summary(oracc, "word_line")
    oracc_line_column = edge_summary(oracc, "line_column")
    bhsa_mother = edge_summary(bhsa, "mother")
    tlhdig_valued = sorted(
        name
        for name, row in tlhdig["edge_features"].items()
        if row.get("valued") is True
    )

    acceptance = {
        name: is_valid(validator, value) for name, value in examples.items()
    }
    edge_path_closed = (
        not acceptance["edge_path_shape_only"]
        and not acceptance["edge_path_steps_only"]
        and not acceptance["edge_path_old_typed_start"]
        and not acceptance["edge_path_one_step_alias"]
        and acceptance["edge_path_typed_unvalued"]
        and not acceptance["edge_path_typed_with_feature"]
        and not acceptance["edge_path_typed_with_interpretation"]
        and not acceptance["edge_path_typed_valued_true"]
    )

    result = {
        "baseline_main": BASELINE_MAIN,
        "current_contract": {
            "conjunction_uses_shape_aware_result_domain": (
                "_execution_result_domain(plan)" in conjunction_source
            ),
            "edge_path_has_closed_shape_rule": edge_path_closed,
            "edge_step_ir_fields": [field.name for field in fields(EdgeStepIR)],
            "native_binding_ir_fields": [field.name for field in fields(NativeBindingIR)],
            "packaged_production_mappings": production_shapes,
            "path_prerequisite_checks_valuedness": "doValues" in path_source,
            "r007_requires_edge_source_target_and_valuedness": (
                "source selector/type" in r007
                and "target selector/type" in r007
                and "valued vs unvalued" in r007
            ),
            "runtime_execution_shapes": runtime_shapes,
            "schema_acceptance": acceptance,
            "tfont_declares_text_fabric_runtime_dependency": (
                '"text-fabric' in pyproject or "'text-fabric" in pyproject
            ),
        },
        "text_fabric_api": {
            "upstream_revision": TF_UPSTREAM_REVISION,
            "edge_constructor_signature": str(inspect.signature(EdgeFeature.__init__)),
            "edge_outgoing_signature": str(inspect.signature(EdgeFeature.f)),
            "edge_incoming_signature": str(inspect.signature(EdgeFeature.t)),
            "edge_value_flag_is_explicit_implementation_state": (
                "self.doValues = doValues" in edge_init_source
            ),
            "valued_outgoing_pairs_documented": (
                "destination node and the" in (EdgeFeature.f.__doc__ or "")
                and "value" in (EdgeFeature.f.__doc__ or "").lower()
            ),
            "valued_incoming_pairs_documented": (
                "start node and the" in (EdgeFeature.t.__doc__ or "")
                and "value" in (EdgeFeature.t.__doc__ or "").lower()
            ),
        },
        "corpus_mechanics": {
            "oracc_word_line": oracc_word_line,
            "oracc_line_column": oracc_line_column,
            "oracc_word_to_column_path_is_unvalued": (
                oracc_word_line["valued"] is False
                and oracc_line_column["valued"] is False
                and oracc_word_line["source_types"] == ["word"]
                and oracc_word_line["target_types"] == ["line"]
                and oracc_line_column["source_types"] == ["line"]
                and oracc_line_column["target_types"] == ["column"]
            ),
            "bhsa_mother": bhsa_mother,
            "tlhdig_valued_edges": tlhdig_valued,
        },
        "conclusion": {
            "edge_path_production_runtime_available": True,
            "edge_path_source_contract_closed": True,
            "edge_step_result_domain_is_explicit": True,
            "edge_step_valued_false_is_explicit": True,
            "valued_true_edges_remain_unsupported_until_i024": True,
            "node_type_is_start_selector": True,
            "conjunction_result_domain_is_shape_aware": True,
            "full_path_loaded_api_preflight_required": True,
            "empty_post_traversal_result_is_valid": True,
            "empty_start_after_fresh_authorization_is_runtime_drift": True,
            "result_order_policy": (
                "stable-first-discovery-from-canonical-start-and-edge-order"
            ),
            "path_provenance_remains_in_reviewed_plan_and_runtime_report": True,
            "no_new_text_fabric_runtime_dependency": True,
            "research_authorizes_production_runtime_change": False,
        },
    }

    expected_native_fields = [
        "component_id",
        "node_type",
        "feature",
        "value_present",
        "value",
        "closed_values",
        "edge",
        "direction",
        "steps",
        "interpretation",
        "execution_shape",
        "values",
    ]
    if result["current_contract"]["native_binding_ir_fields"] != expected_native_fields:
        raise SystemExit("NativeBindingIR field set drifted")
    if result["current_contract"]["edge_step_ir_fields"] != [
        "edge",
        "direction",
        "result_node_type",
        "valued",
        "value_type",
        "value_role",
        "match_values",
    ]:
        raise SystemExit("typed EdgeStepIR contract drifted")
    if runtime_shapes != [
        "edge-path",
        "membership",
        "value-predicate",
        "value-set-predicate",
    ]:
        raise SystemExit("edge-path runtime execution support drifted")
    if not edge_path_closed:
        raise SystemExit("typed unvalued edge-path source contract is not closed")
    if not result["current_contract"]["conjunction_uses_shape_aware_result_domain"]:
        raise SystemExit("conjunction result-domain helper drifted")
    if result["current_contract"]["path_prerequisite_checks_valuedness"]:
        raise SystemExit("P-002 path prerequisite unexpectedly absorbed valuedness")
    if not result["current_contract"]["r007_requires_edge_source_target_and_valuedness"]:
        raise SystemExit("accepted R-007 edge contract wording drifted")
    if not result["text_fabric_api"]["edge_value_flag_is_explicit_implementation_state"]:
        raise SystemExit("pinned Text-Fabric EdgeFeature no longer exposes doValues state")
    if production_shapes["execution_shapes"] != [
        "value-predicate",
        "value-set-predicate",
    ]:
        raise SystemExit("packaged production execution-shape inventory drifted")
    if production_shapes["structural_bindings"]:
        raise SystemExit("packaged production structural bindings appeared")
    if result["current_contract"]["tfont_declares_text_fabric_runtime_dependency"]:
        raise SystemExit("TFont runtime dependency boundary drifted")
    if not result["corpus_mechanics"]["oracc_word_to_column_path_is_unvalued"]:
        raise SystemExit("ORACC word->line->column mechanics drifted")
    if not tlhdig_valued:
        raise SystemExit("TLHdig valued-edge control disappeared")
    if bhsa_mother["valued"] is not False:
        raise SystemExit("BHSA mother edge valuedness drifted")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
