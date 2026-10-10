"""I-022 structural execution reconciliation.

Research-only probe. It records the exact current source/IR/runtime gap and
corpus mechanics needed before structural execution can be planned.
"""

from __future__ import annotations

import inspect
import json
import re
from dataclasses import fields
from pathlib import Path

from jsonschema import Draft202012Validator
from tf.core.edgefeature import EdgeFeature
from tf.core.oslotsfeature import OslotsFeature
from tf.core.otypefeature import OtypeFeature

from tfont.semantic_ir import NativeBindingIR


ROOT = Path(__file__).resolve().parents[2]
BASELINE_MAIN = "d1da009cc49b3dc812a395e0813c51500c28fa08"
TF_UPSTREAM_REVISION = "0c45c386916cb52be84098796ec27ce97e5bf9fc"


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def binding_validator(schema: dict) -> Draft202012Validator:
    wrapper = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": "#/$defs/nativeBinding",
    }
    return Draft202012Validator(wrapper)


def is_valid(validator: Draft202012Validator, value: dict) -> bool:
    return not tuple(validator.iter_errors(value))


def corpus_summary(path: str) -> dict:
    data = load_json(path)
    edges = data.get("edge_features", {})
    return {
        "slot_type": data.get("slot_type"),
        "node_types": sorted(data.get("node_types", {})),
        "edge_count": len(edges),
        "edge_names": sorted(edges),
        "valued_edges": sorted(
            name for name, row in edges.items() if row.get("valued") is True
        ),
    }


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
                ("projection", item.get("projection_id"), item.get("native_execution_binding"))
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
    rows.sort(key=lambda row: (
        row["path"],
        row["owner_kind"],
        row["owner_id"] or "",
        row["execution_shape"],
    ))
    return {
        "execution_shapes": sorted(shapes),
        "binding_count": len(rows),
        "structural_bindings": structural,
    }


def main() -> int:
    schema = load_json("src/tfont/schemas/mapping.schema.json")
    validator = binding_validator(schema)
    execution_shapes = schema["$defs"]["nativeBinding"]["properties"][
        "execution_shape"
    ]["enum"]

    membership_typed = {
        "component_id": "fixture-tf",
        "node_type": "word",
        "execution_shape": "membership",
    }
    membership_forbidden = {
        "feature": "sp",
        "value": "subs",
        "closed_values": ["subs"],
        "values": ["subs"],
        "edge": "mother",
        "direction": "outgoing",
        "steps": [{"edge": "mother", "direction": "outgoing"}],
        "interpretation": "occurrenceSet",
    }
    examples = {
        "membership_shape_only": {"execution_shape": "membership"},
        "membership_typed": membership_typed,
        **{
            f"membership_with_{field}": {**membership_typed, field: value}
            for field, value in membership_forbidden.items()
        },
        "edge_path_shape_only": {"execution_shape": "edge-path"},
        "edge_path_steps_only": {
            "execution_shape": "edge-path",
            "steps": [{"edge": "mother", "direction": "outgoing"}],
        },
        "edge_path_typed_start": {
            "component_id": "fixture-tf",
            "node_type": "clause",
            "execution_shape": "edge-path",
            "steps": [{
                "edge": "mother",
                "direction": "outgoing",
                "result_node_type": "clause",
                "valued": False,
            }],
        },
    }

    execution_source = (
        ROOT / "src/tfont/semantic_execution.py"
    ).read_text(encoding="utf-8")
    runtime_shapes = sorted(
        set(re.findall(r'binding\.execution_shape == "([^"]+)"', execution_source))
    )

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

    cuc = corpus_summary("docs/research/data/generated/r005/cuc.json")
    oracc = corpus_summary(
        "docs/research/data/generated/i018/oracc-0.4.0.json"
    )
    tlhdig = corpus_summary(
        "docs/research/data/generated/i019/tlhdig-0.4.0.json"
    )
    bhsa = corpus_summary("docs/research/data/generated/r005/bhsa.json")

    oracc_details = load_json(
        "docs/research/data/generated/i018/oracc-0.4.0.json"
    )["edge_features"]
    bhsa_details = load_json(
        "docs/research/data/generated/r005/bhsa.json"
    )["edge_features"]

    result = {
        "baseline_main": BASELINE_MAIN,
        "current_contract": {
            "execution_shapes": execution_shapes,
            "native_binding_ir_fields": [field.name for field in fields(NativeBindingIR)],
            "schema_acceptance": {
                name: is_valid(validator, value) for name, value in examples.items()
            },
            "membership_has_closed_shape_rule": (
                not is_valid(validator, examples["membership_shape_only"])
                and is_valid(validator, examples["membership_typed"])
                and all(
                    not is_valid(validator, examples[f"membership_with_{field}"])
                    for field in membership_forbidden
                )
            ),
            "edge_path_has_closed_shape_rule": (
                not is_valid(validator, examples["edge_path_shape_only"])
                and not is_valid(validator, examples["edge_path_steps_only"])
                and is_valid(validator, examples["edge_path_typed_start"])
            ),
            "runtime_execution_shapes": runtime_shapes,
            "tfont_declares_text_fabric_runtime_dependency": (
                '"text-fabric' in pyproject or "'text-fabric" in pyproject
            ),
            "packaged_production_mappings": production_shapes,
        },
        "text_fabric_api": {
            "upstream_revision": TF_UPSTREAM_REVISION,
            "otype_membership_signature": str(inspect.signature(OtypeFeature.s)),
            "edge_outgoing_signature": str(inspect.signature(EdgeFeature.f)),
            "edge_incoming_signature": str(inspect.signature(EdgeFeature.t)),
            "oslots_signature": str(inspect.signature(OslotsFeature.s)),
            "otype_membership_documented": "all nodes" in (OtypeFeature.s.__doc__ or "").lower(),
            "outgoing_direction_documented": "outgoing" in (EdgeFeature.f.__doc__ or "").lower(),
            "incoming_direction_documented": "incoming" in (EdgeFeature.t.__doc__ or "").lower(),
        },
        "corpus_mechanics": {
            "cuc": cuc,
            "oracc": {
                **oracc,
                "typed_edges": {
                    name: {
                        "source_types": oracc_details[name].get("source_types", []),
                        "target_types": oracc_details[name].get("target_types", []),
                        "valued": oracc_details[name].get("valued"),
                    }
                    for name in ("word_line", "line_column", "translation_line")
                },
            },
            "tlhdig": tlhdig,
            "bhsa": {
                **bhsa,
                "typed_edges": {
                    name: {
                        "source_types": bhsa_details[name].get("source_types", []),
                        "target_types": bhsa_details[name].get("target_types", []),
                        "valued": bhsa_details[name].get("valued"),
                    }
                    for name in ("mother", "functional_parent")
                },
            },
        },
        "conclusion": {
            "membership_mechanics_available": True,
            "membership_requires_source_contract_amendment": False,
            "membership_production_runtime_available": True,
            "edge_traversal_mechanics_available": True,
            "edge_path_requires_source_contract_amendment": False,
            "edge_path_start_selector_is_currently_normatively_undefined": False,
            "edge_path_production_runtime_available": True,
            "extent_interpretation_should_not_be_direct_execution_authority": True,
            "technical_anchor_must_not_imply_textual_extent": True,
            "no_slot_must_not_fabricate_slot_membership": True,
            "warp_may_be_used_internally_without_semantic_promotion": True,
            "research_authorizes_production_runtime_change": False,
        },
    }

    # Guard the findings this reconciliation is intended to measure.
    expected_shapes = {
        "membership",
        "value-predicate",
        "value-set-predicate",
        "edge-path",
        "identity-key",
        "inspection-only",
    }
    if set(execution_shapes) != expected_shapes:
        raise SystemExit("native execution-shape vocabulary drifted")
    if runtime_shapes != ["edge-path", "membership", "value-predicate", "value-set-predicate"]:
        raise SystemExit("structural runtime execution support drifted")
    if result["current_contract"]["schema_acceptance"]["membership_shape_only"]:
        raise SystemExit("shape-only membership must fail the closed source contract")
    if not result["current_contract"]["schema_acceptance"]["membership_typed"]:
        raise SystemExit("typed membership must satisfy the closed source contract")
    if any(
        result["current_contract"]["schema_acceptance"][f"membership_with_{field}"]
        for field in membership_forbidden
    ):
        raise SystemExit("membership source contract accepts a forbidden field")
    if not result["current_contract"]["membership_has_closed_shape_rule"]:
        raise SystemExit("membership closed-shape reconciliation failed")
    if result["current_contract"]["schema_acceptance"]["edge_path_shape_only"]:
        raise SystemExit("shape-only edge-path must fail the closed I-023 source contract")
    if result["current_contract"]["schema_acceptance"]["edge_path_steps_only"]:
        raise SystemExit("steps-only edge-path must fail the closed I-023 source contract")
    if not result["current_contract"]["schema_acceptance"]["edge_path_typed_start"]:
        raise SystemExit("typed unvalued edge-path must satisfy the closed I-023 source contract")
    if not result["current_contract"]["edge_path_has_closed_shape_rule"]:
        raise SystemExit("edge-path closed-shape reconciliation failed")
    if result["current_contract"]["tfont_declares_text_fabric_runtime_dependency"]:
        raise SystemExit("TFont runtime dependency boundary drifted")
    if production_shapes["execution_shapes"] != [
        "value-predicate",
        "value-set-predicate",
    ]:
        raise SystemExit("packaged production execution-shape inventory drifted")
    if production_shapes["structural_bindings"]:
        raise SystemExit("packaged production structural bindings appeared")
    if cuc["edge_count"] != 0:
        raise SystemExit("CUC non-warp edge inventory drifted")
    if set(("word_line", "line_column", "translation_line")) - set(oracc["edge_names"]):
        raise SystemExit("ORACC structural edge evidence drifted")
    if set(("lexeme", "analyses", "witness", "startsAt", "endsAt")) - set(
        tlhdig["edge_names"]
    ):
        raise SystemExit("TLHdig structural edge evidence drifted")
    if set(("mother", "functional_parent")) - set(bhsa["edge_names"]):
        raise SystemExit("BHSA structural edge evidence drifted")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
