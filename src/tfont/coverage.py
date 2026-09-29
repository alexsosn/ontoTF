from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from .digests import canonical_json_bytes
from .semantic_vocabulary import CAPABILITY_IDS, PROFILE_IDS, PROJECTION_ASSESSMENTS
from .source_validation import load_source, loads_source, validate_source

COVERAGE_DENOMINATOR_ALGORITHM = "tfont-coverage-denominator-jcs-sha256-v1"
P004_R011_BASELINE_RESOURCE = "p004-r011-baseline-v1"
P004_PSEUDEPIGRAPHA_V1_RESOURCE = "p004-pseudepigrapha-v1.0.0-v1"
P004_R011_BASELINE_CORPORA = (
    "bhsa",
    "cuc",
    "extrabiblical",
    "oracc",
    "pseudepigrapha",
    "syriac",
    "tlhdig",
)

COVERAGE_ASSESSMENTS = frozenset(
    set(PROJECTION_ASSESSMENTS) | {"ambiguous", "native-only", "unsupported"}
)
TARGET_BEARING_ASSESSMENTS = frozenset(PROJECTION_ASSESSMENTS)
ITEM_KINDS = frozenset(
    {
        "node_type",
        "node_feature",
        "node_value",
        "edge_feature",
        "edge_value",
        "external_reference",
        "assertion_shape",
    }
)


@dataclass(frozen=True)
class CoverageProblem:
    category: str
    message: str
    path: tuple[str | int, ...] = ()
    corpus_id: str | None = None


class CoverageError(ValueError):
    def __init__(self, problem: CoverageProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


@dataclass(frozen=True)
class CoverageReport:
    corpus_id: str
    denominator_digest: str
    semantic_items: int
    technical_exclusions: int
    research_reviewed_items: int
    research_common_target_items: int
    production_reviewed_items: int
    production_unreviewed_items: int
    production_common_target_items: int
    research_outside_denominator_items: int
    research_outside_denominator_item_ids: tuple[str, ...]
    production_outside_denominator_items: int
    production_outside_denominator_item_ids: tuple[str, ...]
    production_assessment_counts: tuple[tuple[str, int], ...]
    scope_quality: str
    freshness: str
    bounded_scope_complete: bool
    corpus_wide_completion_claim_eligible: bool


def _fail(
    category: str,
    message: str,
    *,
    path: tuple[str | int, ...] = (),
    corpus_id: str | None = None,
) -> None:
    raise CoverageError(
        CoverageProblem(
            category=category,
            message=message,
            path=path,
            corpus_id=corpus_id,
        )
    )


def _utf16(value: str) -> bytes:
    try:
        return value.encode("utf-16be")
    except UnicodeEncodeError as error:
        _fail("invalid_manifest", str(error))
    raise AssertionError("unreachable")


def _exact_dict(value: Any, *, path: tuple[str | int, ...] = ()) -> dict[str, Any]:
    if type(value) is not dict:
        _fail("invalid_manifest", "coverage manifest object must be an exact dict", path=path)
    return value


def _canonical_strings(
    values: Any,
    *,
    path: tuple[str | int, ...],
) -> list[str]:
    if type(values) is not list:
        _fail("invalid_manifest", "expected an exact list", path=path)
    result: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if type(value) is not str or not value:
            _fail(
                "invalid_manifest",
                "set-like value must be a non-empty exact string",
                path=path + (index,),
            )
        if value in seen:
            _fail("duplicate_id", f"duplicate set-like value: {value}", path=path + (index,))
        seen.add(value)
        result.append(value)
    result.sort(key=_utf16)
    return result


def _validate_accounting_layer(
    layer: dict[str, Any],
    *,
    authority: str,
    path: tuple[str | int, ...],
    corpus_id: str,
) -> None:
    assessments = _canonical_strings(layer["assessments"], path=path + ("assessments",))
    unknown = set(assessments) - COVERAGE_ASSESSMENTS
    if unknown:
        _fail(
            "unknown_assessment",
            f"unknown coverage assessment: {sorted(unknown)}",
            path=path + ("assessments",),
            corpus_id=corpus_id,
        )
    source_ids = _canonical_strings(layer["source_ids"], path=path + ("source_ids",))
    if not source_ids:
        _fail(
            "missing_authority",
            "reviewed coverage accounting requires at least one source ID",
            path=path + ("source_ids",),
            corpus_id=corpus_id,
        )

    expected_target = any(value in TARGET_BEARING_ASSESSMENTS for value in assessments)
    if layer["common_target"] is not expected_target:
        _fail(
            "target_state_mismatch",
            "common_target disagrees with target-bearing assessment state",
            path=path + ("common_target",),
            corpus_id=corpus_id,
        )

    if authority == "research":
        if "profiles" in layer or "capabilities" in layer:
            _fail(
                "invalid_authority",
                "research accounting cannot claim production profile/capability membership",
                path=path,
                corpus_id=corpus_id,
            )
        return

    profiles = (
        _canonical_strings(layer["profiles"], path=path + ("profiles",))
        if "profiles" in layer
        else []
    )
    capabilities = (
        _canonical_strings(layer["capabilities"], path=path + ("capabilities",))
        if "capabilities" in layer
        else []
    )
    unknown_profiles = set(profiles) - PROFILE_IDS
    unknown_capabilities = set(capabilities) - CAPABILITY_IDS
    if unknown_profiles:
        _fail(
            "unknown_profile",
            f"unknown coverage profile: {sorted(unknown_profiles)}",
            path=path + ("profiles",),
            corpus_id=corpus_id,
        )
    if unknown_capabilities:
        _fail(
            "unknown_capability",
            f"unknown coverage capability: {sorted(unknown_capabilities)}",
            path=path + ("capabilities",),
            corpus_id=corpus_id,
        )
    if profiles and capabilities:
        missing_profiles = {
            capability.split(".", 1)[0]
            for capability in capabilities
            if capability.split(".", 1)[0] not in profiles
        }
        if missing_profiles:
            _fail(
                "capability_profile_mismatch",
                f"capability owner profile missing: {sorted(missing_profiles)}",
                path=path + ("capabilities",),
                corpus_id=corpus_id,
            )


def coverage_denominator_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    source = _exact_dict(manifest)
    basis = _exact_dict(source["denominator_basis"], path=("denominator_basis",))

    semantic_items: list[dict[str, str]] = []
    seen_semantic: set[str] = set()
    for index, item_value in enumerate(source["semantic_items"]):
        item = _exact_dict(item_value, path=("semantic_items", index))
        item_id = item["item_id"]
        if item_id in seen_semantic:
            _fail("duplicate_id", f"duplicate semantic item ID: {item_id}", path=("semantic_items", index, "item_id"))
        seen_semantic.add(item_id)
        semantic_items.append({"item_id": item_id, "kind": item["kind"]})
    semantic_items.sort(key=lambda item: _utf16(item["item_id"]))

    technical_exclusions: list[dict[str, Any]] = []
    seen_technical: set[str] = set()
    for index, row_value in enumerate(source["technical_exclusions"]):
        row = _exact_dict(row_value, path=("technical_exclusions", index))
        item_id = row["item_id"]
        if item_id in seen_technical:
            _fail("duplicate_id", f"duplicate technical exclusion ID: {item_id}", path=("technical_exclusions", index, "item_id"))
        seen_technical.add(item_id)
        technical_exclusions.append(
            {
                "item_id": item_id,
                "kind": row["kind"],
                "reason": row["reason"],
                "authority": row["authority"],
                "source_ids": _canonical_strings(
                    row["source_ids"],
                    path=("technical_exclusions", index, "source_ids"),
                ),
            }
        )
    technical_exclusions.sort(key=lambda item: _utf16(item["item_id"]))

    basis_projection: dict[str, Any] = {
        "kind": basis["kind"],
        "source": basis["source"],
        "bounded_node_features": _canonical_strings(
            basis["bounded_node_features"],
            path=("denominator_basis", "bounded_node_features"),
        ),
    }
    if "artifact_identity" in basis:
        artifact = _exact_dict(
            basis["artifact_identity"],
            path=("denominator_basis", "artifact_identity"),
        )
        basis_projection["artifact_identity"] = {
            "locator": artifact["locator"],
            "sha256": artifact["sha256"],
            "materialized_sha256": artifact["materialized_sha256"],
        }

    projection: dict[str, Any] = {
        "algorithm": COVERAGE_DENOMINATOR_ALGORITHM,
        "schema_version": source["schema_version"],
        "corpus_id": source["corpus_id"],
        "repository": source["repository"],
        "denominator_source_revision": source["denominator_source_revision"],
        "target_corpus_revision": source["target_corpus_revision"],
        "scope_quality": source["scope_quality"],
        "denominator_basis": basis_projection,
        "semantic_items": semantic_items,
        "technical_exclusions": technical_exclusions,
    }
    if "tf_version" in source:
        projection["tf_version"] = source["tf_version"]
    return projection


def coverage_denominator_digest(manifest: dict[str, Any]) -> str:
    payload = canonical_json_bytes(coverage_denominator_projection(manifest))
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def validate_coverage_manifest(manifest: dict[str, Any]) -> None:
    source = _exact_dict(manifest)
    validate_source(source, "coverage-manifest", source_name=source.get("manifest_id", "coverage-manifest"))
    corpus_id = source["corpus_id"]

    semantic_ids: set[str] = set()
    for index, item_value in enumerate(source["semantic_items"]):
        item = _exact_dict(item_value, path=("semantic_items", index))
        item_id = item["item_id"]
        kind = item["kind"]
        if kind not in ITEM_KINDS:
            _fail("unknown_item_kind", f"unknown item kind: {kind}", path=("semantic_items", index, "kind"), corpus_id=corpus_id)
        if not item_id.startswith(f"{kind}:"):
            _fail(
                "item_identity_mismatch",
                "item_id prefix must match item kind",
                path=("semantic_items", index, "item_id"),
                corpus_id=corpus_id,
            )
        if item_id in semantic_ids:
            _fail("duplicate_id", f"duplicate semantic item ID: {item_id}", path=("semantic_items", index, "item_id"), corpus_id=corpus_id)
        semantic_ids.add(item_id)

        accounting = _exact_dict(item["accounting"], path=("semantic_items", index, "accounting"))
        for authority in ("research", "production"):
            layer = accounting[authority]
            if layer is not None:
                _validate_accounting_layer(
                    _exact_dict(layer, path=("semantic_items", index, "accounting", authority)),
                    authority=authority,
                    path=("semantic_items", index, "accounting", authority),
                    corpus_id=corpus_id,
                )

    technical_ids: set[str] = set()
    for index, row_value in enumerate(source["technical_exclusions"]):
        row = _exact_dict(row_value, path=("technical_exclusions", index))
        item_id = row["item_id"]
        kind = row["kind"]
        if not item_id.startswith(f"{kind}:"):
            _fail(
                "item_identity_mismatch",
                "technical item_id prefix must match item kind",
                path=("technical_exclusions", index, "item_id"),
                corpus_id=corpus_id,
            )
        if item_id in technical_ids:
            _fail("duplicate_id", f"duplicate technical exclusion ID: {item_id}", path=("technical_exclusions", index, "item_id"), corpus_id=corpus_id)
        if item_id in semantic_ids:
            _fail(
                "denominator_overlap",
                "item cannot be both semantic and technically excluded",
                path=("technical_exclusions", index, "item_id"),
                corpus_id=corpus_id,
            )
        technical_ids.add(item_id)
        _canonical_strings(row["source_ids"], path=("technical_exclusions", index, "source_ids"))

    gap_ids: set[str] = set()
    for index, gap_value in enumerate(source["accounting_gaps"]):
        gap = _exact_dict(gap_value, path=("accounting_gaps", index))
        item_id = gap["item_id"]
        kind = gap["kind"]
        if not item_id.startswith(f"{kind}:"):
            _fail(
                "item_identity_mismatch",
                "accounting-gap item_id prefix must match item kind",
                path=("accounting_gaps", index, "item_id"),
                corpus_id=corpus_id,
            )
        if item_id in gap_ids:
            _fail(
                "duplicate_id",
                f"duplicate accounting gap ID: {item_id}",
                path=("accounting_gaps", index, "item_id"),
                corpus_id=corpus_id,
            )
        if item_id in semantic_ids or item_id in technical_ids:
            _fail(
                "denominator_overlap",
                "accounting gap must remain outside semantic and technical denominator sets",
                path=("accounting_gaps", index, "item_id"),
                corpus_id=corpus_id,
            )
        gap_ids.add(item_id)
        layer = {
            "assessments": gap["assessments"],
            "common_target": gap["common_target"],
            "source_ids": gap["source_ids"],
        }
        if "profiles" in gap:
            layer["profiles"] = gap["profiles"]
        if "capabilities" in gap:
            layer["capabilities"] = gap["capabilities"]
        _validate_accounting_layer(
            layer,
            authority=gap["authority"],
            path=("accounting_gaps", index),
            corpus_id=corpus_id,
        )

    expected = coverage_denominator_digest(source)
    if source["denominator_digest"] != expected:
        _fail(
            "denominator_digest_mismatch",
            "stored denominator digest does not match canonical denominator projection",
            path=("denominator_digest",),
            corpus_id=corpus_id,
        )


def load_coverage_manifest(path: str | Path) -> dict[str, Any]:
    data = load_source(path)
    source = _exact_dict(data)
    validate_coverage_manifest(source)
    return source


_RESOURCE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _validate_resource_component(value: Any, *, name: str) -> str:
    if type(value) is not str or not _RESOURCE_COMPONENT.fullmatch(value):
        _fail(
            "invalid_resource_component",
            f"{name} must be a safe package resource component",
        )
    return value


def load_packaged_coverage_manifest(
    resource_set: str,
    corpus_id: str,
) -> dict[str, Any]:
    resource_set = _validate_resource_component(resource_set, name="resource_set")
    corpus_id = _validate_resource_component(corpus_id, name="corpus_id")
    resource = files("tfont").joinpath(
        "resources",
        "coverage",
        resource_set,
        f"{corpus_id}.json",
    )
    try:
        text = resource.read_text(encoding="utf-8")
    except OSError as error:
        _fail(
            "missing_resource",
            str(error),
            corpus_id=corpus_id,
        )
    data = loads_source(
        text,
        format="json",
        source_name=f"tfont:resources/coverage/{resource_set}/{corpus_id}.json",
    )
    source = _exact_dict(data)
    validate_coverage_manifest(source)
    return source


def load_p004_r011_baseline_manifests() -> dict[str, dict[str, Any]]:
    return {
        corpus_id: load_packaged_coverage_manifest(
            P004_R011_BASELINE_RESOURCE,
            corpus_id,
        )
        for corpus_id in P004_R011_BASELINE_CORPORA
    }


def coverage_report(manifest: dict[str, Any]) -> CoverageReport:
    validate_coverage_manifest(manifest)
    corpus_id = manifest["corpus_id"]
    items = manifest["semantic_items"]

    research_reviewed = 0
    research_common = 0
    production_reviewed = 0
    production_common = 0
    assessment_counts: dict[str, int] = {}

    for item in items:
        research = item["accounting"]["research"]
        production = item["accounting"]["production"]
        if research is not None:
            research_reviewed += 1
            if research["common_target"]:
                research_common += 1
        if production is not None:
            production_reviewed += 1
            if production["common_target"]:
                production_common += 1
            for assessment in set(production["assessments"]):
                assessment_counts[assessment] = assessment_counts.get(assessment, 0) + 1

    semantic_count = len(items)
    production_unreviewed = semantic_count - production_reviewed
    research_gap_ids = tuple(
        sorted(
            (
                row["item_id"]
                for row in manifest["accounting_gaps"]
                if row["authority"] == "research"
            ),
            key=_utf16,
        )
    )
    production_gap_ids = tuple(
        sorted(
            (
                row["item_id"]
                for row in manifest["accounting_gaps"]
                if row["authority"] == "production"
            ),
            key=_utf16,
        )
    )
    freshness = (
        "current"
        if manifest["denominator_source_revision"] == manifest["target_corpus_revision"]
        else "stale"
    )
    bounded_scope_complete = production_unreviewed == 0 and not manifest["accounting_gaps"]
    technical_authority_complete = all(
        row["authority"] == "production" for row in manifest["technical_exclusions"]
    )
    corpus_wide_eligible = (
        manifest["scope_quality"] == "machine-exhaustive"
        and freshness == "current"
        and bounded_scope_complete
        and technical_authority_complete
    )

    return CoverageReport(
        corpus_id=corpus_id,
        denominator_digest=manifest["denominator_digest"],
        semantic_items=semantic_count,
        technical_exclusions=len(manifest["technical_exclusions"]),
        research_reviewed_items=research_reviewed,
        research_common_target_items=research_common,
        production_reviewed_items=production_reviewed,
        production_unreviewed_items=production_unreviewed,
        production_common_target_items=production_common,
        research_outside_denominator_items=len(research_gap_ids),
        research_outside_denominator_item_ids=research_gap_ids,
        production_outside_denominator_items=len(production_gap_ids),
        production_outside_denominator_item_ids=production_gap_ids,
        production_assessment_counts=tuple(sorted(assessment_counts.items(), key=lambda item: _utf16(item[0]))),
        scope_quality=manifest["scope_quality"],
        freshness=freshness,
        bounded_scope_complete=bounded_scope_complete,
        corpus_wide_completion_claim_eligible=corpus_wide_eligible,
    )
