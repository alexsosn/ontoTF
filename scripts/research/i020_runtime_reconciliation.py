#!/usr/bin/env python3
"""Reconcile reviewed R-016 approximation policy with current runtime contracts.

Research-only probe for I-020. It deliberately uses existing test fixtures and
public production APIs; it does not implement approximate resolution.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import tfont
from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import (
    _refresh_mapping,
    compiled_noun_ir,
    noun_semantic_key,
    prerequisites_for,
)
from tests.i008._fixtures import FakeLoadedApi, compiled_executable_noun_ir, loaded_context
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


def problem_category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


def exact_control() -> dict[str, object]:
    ir = compiled_noun_ir(("bhsa",))
    prerequisites = prerequisites_for(tfont, ir)
    request = tfont.SemanticResolveRequest(
        key=noun_semantic_key(),
        corpora=("bhsa",),
        semantic_mode="exact",
    )
    result = tfont.semantic_resolve(ir, request, prerequisites)

    executable_ir = compiled_executable_noun_ir(("bhsa",))
    api = FakeLoadedApi(
        values={1: "subs", 2: "verb", 3: "subs"},
        node_types={1: "word", 2: "word", 3: "word"},
    )
    context = loaded_context(tfont, executable_ir, "bhsa", api)
    execution = tfont.execute_exact_semantic(
        executable_ir,
        tfont.SemanticResolveRequest(
            key=noun_semantic_key(),
            corpora=("bhsa",),
            semantic_mode="exact",
        ),
        (context,),
    )
    plan = result.plans[0]
    return {
        "resolver_contract": result.resolver_contract,
        "plan_fingerprint": plan.plan_fingerprint,
        "resolution_fingerprint": result.resolution_fingerprint,
        "comparison_state": result.comparison_state,
        "losses": list(result.losses),
        "execution_contract": execution.execution_contract,
        "execution_nodes": list(execution.corpora[0].nodes),
        "execution_resolution_fingerprint": execution.resolution.resolution_fingerprint,
    }


def reviewed_broader_ir():
    sources = noun_sources("bhsa", parent_char="a")
    mapping = sources["mappings"]["mappings"][0]
    projection = mapping["projections"][0]
    projection["assessment"] = "broader"
    projection["approximation"] = {
        "status": "reviewed",
        "eligible": True,
        "losses": ["undercoverage"],
        "rationale": "I-020 research fixture: source selector is a reviewed subset proxy.",
        "review_id": "review:i020:approximation:broader",
        "evidence": [],
    }
    _refresh_mapping(mapping)
    validate_structural_sources(sources)
    validated = validate_semantic_bundle(source_bundle(sources))
    return compile_semantic_ir((validated,))


def approximation_control() -> dict[str, object]:
    ir = reviewed_broader_ir()
    binding = dict(ir.semantic_index)[noun_semantic_key()][0]
    approximation = binding.approximation
    if approximation is None:
        raise AssertionError("validated approximation was lost before runtime IR")
    prerequisites = prerequisites_for(tfont, ir)

    failures: dict[str, str] = {}
    for mode in ("exact", "approximate"):
        try:
            tfont.semantic_resolve(
                ir,
                tfont.SemanticResolveRequest(
                    key=noun_semantic_key(),
                    corpora=("bhsa",),
                    semantic_mode=mode,
                ),
                prerequisites,
            )
        except tfont.SemanticResolutionError as error:
            failures[mode] = problem_category(error)
        else:
            failures[mode] = "unexpected-success"

    return {
        "assessment": binding.assessment,
        "approximation": {
            "status": approximation.status,
            "eligible": approximation.eligible,
            "losses": list(approximation.losses),
            "review_id": approximation.review_id,
            "rationale": approximation.rationale,
        },
        "exact_mode_result": failures["exact"],
        "approximate_mode_result": failures["approximate"],
    }


def main() -> int:
    result = {
        "baseline_main": "6efdb106aaf81f349c1b238344b3a195c2c9bd5f",
        "exact": exact_control(),
        "reviewed_broader": approximation_control(),
        "contracts": {
            "exact_resolver": tfont.EXACT_RESOLVER_CONTRACT,
            "exact_execution": tfont.EXACT_EXECUTION_CONTRACT,
            "exact_conjunction_resolver": tfont.EXACT_CONJUNCTION_RESOLVER_CONTRACT,
            "exact_conjunction_execution": tfont.EXACT_CONJUNCTION_EXECUTION_CONTRACT,
        },
        "conclusion": {
            "approximation_review_reaches_ir": True,
            "exact_mode_refuses_non_exact": True,
            "approximate_mode_not_implemented": True,
            "schema_change_required": False,
            "ir_change_required": False,
        },
    }
    if result["reviewed_broader"]["exact_mode_result"] != "non_exact_mapping":
        raise SystemExit("exact-mode non-exact refusal contract drifted")
    if result["reviewed_broader"]["approximate_mode_result"] != "unsupported_semantic_mode":
        raise SystemExit("current approximate-mode absence contract drifted")
    if result["exact"]["comparison_state"] != "exactly-comparable":
        raise SystemExit("exact comparison state drifted")
    if result["exact"]["losses"] != []:
        raise SystemExit("exact resolution unexpectedly reports semantic losses")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
