"""R-020 denotational mapping-semantics research probe.

Research only. This script reads shipped production OLiA mappings, exercises a
small finite-set model for TFont's exact/approximate answer relations, and emits
deterministic evidence for docs/research/R-020-denotational-mapping-semantics.md.
It changes no production behavior.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CORPORA = ("bhsa", "syriac", "extrabiblical")
MAPPING_FILES = ("noun.json", "noun-morphology.json")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile_dependency_kinds() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for corpus in CORPORA:
        profile = _load(
            ROOT
            / "src/tfont/resources/profiles"
            / corpus
            / "0.2.0"
            / "profile.json"
        )
        result[corpus] = sorted(
            {dependency["kind"] for dependency in profile["dependencies"]}
        )
    return result


def _projection_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for corpus in CORPORA:
        base = ROOT / "src/tfont/resources/profiles" / corpus / "0.2.0" / "mappings"
        for name in MAPPING_FILES:
            bundle = _load(base / name)
            for mapping in bundle["mappings"]:
                for projection in mapping["projections"]:
                    rows.append(
                        {
                            "corpus_id": corpus,
                            "mapping_id": mapping["mapping_id"],
                            "native_binding": mapping["native_binding"],
                            "target": projection["target"],
                            "assessment": projection["assessment"],
                            "formal_kind": projection["formal_kind"],
                            "semantic_role": projection["semantic_role"],
                        }
                    )
    return rows


def _name(iri: str) -> str:
    return iri.rsplit("#", 1)[-1]


def _subset(left: set[str], right: set[str]) -> bool:
    return left <= right


def _finite_witnesses() -> dict[str, Any]:
    exact_target = {"a", "b"}
    exact_answer = {"a", "b"}

    under_target = {"a", "b"}
    under_answer = {"a"}

    over_target = {"a"}
    over_answer = {"a", "b"}

    # Mixed-direction conjunction counterexample:
    # A1 <= T1 (undercoverage) and T2 <= A2 (overcoverage), but after
    # intersection neither inclusion need hold.
    target_1 = {"a", "b", "c"}
    answer_1 = {"a", "b"}
    target_2 = {"b", "c"}
    answer_2 = {"a", "b", "c"}
    mixed_target = target_1 & target_2
    mixed_answer = answer_1 & answer_2

    # Uniform undercoverage is closed under intersection.
    under_target_2 = {"b", "c"}
    under_answer_2 = {"b"}
    uniform_under_target = target_1 & under_target_2
    uniform_under_answer = answer_1 & under_answer_2

    # Uniform overcoverage is also closed under intersection.
    over_target_1 = {"a", "b"}
    over_answer_1 = {"a", "b", "c"}
    over_target_2 = {"b"}
    over_answer_2 = {"b", "c"}
    uniform_over_target = over_target_1 & over_target_2
    uniform_over_answer = over_answer_1 & over_answer_2

    return {
        "exact": {
            "answer": sorted(exact_answer),
            "target": sorted(exact_target),
            "answer_equals_target": exact_answer == exact_target,
        },
        "undercoverage": {
            "answer": sorted(under_answer),
            "target": sorted(under_target),
            "answer_subset_target": _subset(under_answer, under_target),
            "target_minus_answer": sorted(under_target - under_answer),
        },
        "overcoverage": {
            "answer": sorted(over_answer),
            "target": sorted(over_target),
            "target_subset_answer": _subset(over_target, over_answer),
            "answer_minus_target": sorted(over_answer - over_target),
        },
        "uniform_undercoverage_conjunction": {
            "answer": sorted(uniform_under_answer),
            "target": sorted(uniform_under_target),
            "answer_subset_target": _subset(
                uniform_under_answer, uniform_under_target
            ),
        },
        "uniform_overcoverage_conjunction": {
            "answer": sorted(uniform_over_answer),
            "target": sorted(uniform_over_target),
            "target_subset_answer": _subset(
                uniform_over_target, uniform_over_answer
            ),
        },
        "mixed_direction_conjunction": {
            "answer": sorted(mixed_answer),
            "target": sorted(mixed_target),
            "answer_subset_target": _subset(mixed_answer, mixed_target),
            "target_subset_answer": _subset(mixed_target, mixed_answer),
            "false_positive_witnesses": sorted(mixed_answer - mixed_target),
            "false_negative_witnesses": sorted(mixed_target - mixed_answer),
        },
    }


def main() -> int:
    rows = _projection_rows()
    dependency_kinds = _profile_dependency_kinds()
    assessments = Counter(row["assessment"] for row in rows)
    corpora = Counter(row["corpus_id"] for row in rows)
    targets = Counter(_name(row["target"]) for row in rows)

    noun_rows = {
        row["corpus_id"]: row["native_binding"]
        for row in rows
        if _name(row["target"]) == "Noun"
    }
    proper_noun_rows = {
        row["corpus_id"]: row["native_binding"]
        for row in rows
        if _name(row["target"]) == "ProperNoun"
    }

    witnesses = _finite_witnesses()

    result = {
        "current_production_controls": {
            "profile_version": "0.2.0",
            "corpora": list(CORPORA),
            "projection_count": len(rows),
            "projection_count_by_corpus": dict(sorted(corpora.items())),
            "assessment_counts": dict(sorted(assessments.items())),
            "target_counts": dict(sorted(targets.items())),
            "all_targets_are_olia_classes": all(
                row["target"].startswith("http://purl.org/olia/olia.owl#")
                and row["formal_kind"] == "class"
                for row in rows
            ),
            "all_semantic_roles_are_annotation_value": all(
                row["semantic_role"] == "annotation-value" for row in rows
            ),
            "dependency_kinds_by_corpus": dependency_kinds,
            "total_annotation_completeness_claim_present": False,
            "noun_native_bindings": noun_rows,
            "proper_noun_native_bindings": proper_noun_rows,
        },
        "minimal_model": {
            "corpus_query_domain": "U_c = TF nodes of the reviewed query node domain",
            "native_selector_denotation": "N_c(b) subseteq U_c",
            "represented_target_query_denotation": "T_rep_c(t) subseteq U_c",
            "hypothetical_truth_extension": "T_truth_c(t) subseteq U_c",
            "represented_target_is_not_materialized_independently": True,
            "truth_extension_is_outside_current_tfont_authority": True,
            "current_profiles_do_not_claim_total_annotation_completeness": True,
            "assessment_constraints": {
                "exact": "N = T_rep",
                "broader": "N subseteq T_rep",
                "narrower": "T_rep subseteq N",
                "close": "no inclusion follows from assessment alone",
                "related": "non-substitutive; no inclusion follows",
                "ambiguous": "no unique target denotation",
                "native-only": "native denotation exists without shared target",
                "unsupported": "no authorized shared execution denotation",
            },
            "answer_guarantees": {
                "no-loss": "A = T_rep",
                "undercoverage": "A subseteq T_rep",
                "overcoverage": "T_rep subseteq A",
                "undercoverage+overcoverage": "neither inclusion is guaranteed",
            },
            "refusal_is_not_empty_set": True,
            "cross_corpus_node_sets_share_no_common_universe": True,
            "relation_between_T_rep_and_T_truth": "unknown without separate coverage/quality authority",
        },
        "finite_set_checks": witnesses,
        "derived_findings": {
            "production_exact_rows_are_coherent": (
                len(rows) == 21 and assessments == Counter({"exact": 21})
            ),
            "production_profiles_lack_total_annotation_completeness_claim": all(
                kinds == ["native-value-present"]
                for kinds in dependency_kinds.values()
            ),
            "bhsa_and_extrabiblical_noun_use_value_sets": all(
                noun_rows[corpus]["execution_shape"] == "value-set-predicate"
                for corpus in ("bhsa", "extrabiblical")
            ),
            "syriac_noun_uses_scalar_value": (
                noun_rows["syriac"]["execution_shape"] == "value-predicate"
            ),
            "proper_noun_uses_different_native_features_across_corpora": (
                proper_noun_rows["bhsa"]["feature"] == "sp"
                and proper_noun_rows["extrabiblical"]["feature"] == "sp"
                and proper_noun_rows["syriac"]["feature"] == "ls"
            ),
            "uniform_undercoverage_intersection_preserves_lower_bound": (
                witnesses["uniform_undercoverage_conjunction"][
                    "answer_subset_target"
                ]
            ),
            "uniform_overcoverage_intersection_preserves_upper_bound": (
                witnesses["uniform_overcoverage_conjunction"][
                    "target_subset_answer"
                ]
            ),
            "mixed_direction_intersection_has_no_inclusion_bound": (
                not witnesses["mixed_direction_conjunction"][
                    "answer_subset_target"
                ]
                and not witnesses["mixed_direction_conjunction"][
                    "target_subset_answer"
                ]
            ),
        },
        "recommendation": {
            "productionization": "defer-public-runtime-api",
            "verification_model": "go",
            "reason": (
                "The model clarifies existing exact/directional loss semantics and "
                "supports static coherence checks, but target extensions are usually "
                "reviewed/intensional rather than independently enumerable. Keep the "
                "semantics as a verification/explanation model until R-021/R-022/R-023 "
                "settle composition, bound, and query-calculus needs."
            ),
            "smallest_future_slice": [
                "pure derived answer-relation helper: equal|subset|superset|unbounded",
                "static assessment/loss coherence verifier",
                "explanation/provenance projection derived from existing reviewed fields",
            ],
            "requires_new_corpus_annotation": False,
            "requires_ontology_reasoner": False,
            "requires_materialized_target_extensions": False,
        },
    }

    checks = result["derived_findings"]
    if not all(checks.values()):
        raise SystemExit(f"R-020 production/prototype invariant drifted: {checks}")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
