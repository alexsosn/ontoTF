from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Protocol

from .digests import canonical_json_bytes
from .runtime_tf_observation import LoadedTFObservation
from .semantic_ir import (
    BundleVariantIR,
    BundleVariantKey,
    ProfileReleaseKey,
    ProfileReleaseSignature,
)
from .semantic_resolver import (
    DependencyPrerequisiteResult,
    RuntimePrerequisiteState,
    SemanticResolutionError,
    profile_release_fingerprint,
)

RUNTIME_EVALUATION_CONTRACT = "tfont-runtime-evaluation-v1"
OBSERVATION_FINGERPRINT_ALGORITHM = "tfont-runtime-observation-jcs-sha256-v1"
RUNTIME_REPORT_FINGERPRINT_ALGORITHM = "tfont-runtime-report-jcs-sha256-v1"

_KIND_RULES = {
    "component-present": "tfont-runtime-component-present-v1",
    "node-type-present": "tfont-runtime-node-type-present-v1",
    "feature-present": "tfont-runtime-feature-present-v1",
    "edge-present": "tfont-runtime-edge-present-v1",
    "path-present": "tfont-runtime-path-present-v1",
    "native-value-present": "tfont-runtime-native-value-present-v1",
    "value-domain": "tfont-runtime-value-domain-v1",
    "extent-interpretation": "tfont-runtime-extent-interpretation-v1",
}
_DIRECTIONS = {"outgoing", "incoming"}
_EXTENT_INTERPRETATIONS = {
    "textualExtent",
    "occurrenceSet",
    "technicalAnchor",
    "noSlot",
}


class RuntimeObservation(Protocol):
    parent_manifest_digest: str

    def component(self, component_id: str) -> tuple[str, str | None]: ...

    def node_type(self, component_id: str, node_type: str) -> str: ...

    def feature(self, component_id: str, node_type: str, feature: str) -> str: ...

    def edge(self, component_id: str, edge: str, direction: str) -> str: ...

    def path(
        self,
        component_id: str,
        steps: tuple[tuple[str, str], ...],
    ) -> str: ...

    def values(
        self,
        component_id: str,
        node_type: str,
        feature: str,
    ) -> tuple[str, tuple[Any, ...]]: ...

    def extent(
        self,
        component_id: str,
        node_type: str,
    ) -> tuple[str, str | None]: ...


@dataclass(frozen=True)
class RuntimeEvaluationReport:
    contract: str
    variant: BundleVariantKey
    profile_release_fingerprint: str
    observed_parent_manifest_digest: str
    compatibility_state: str
    dependency_results: tuple[DependencyPrerequisiteResult, ...]
    active_ontology_bundle_digest: str | None
    ontology_bundle_state: str
    source_contract: str
    report_fingerprint: str

    def to_prerequisite(self) -> RuntimePrerequisiteState:
        return RuntimePrerequisiteState(
            variant=self.variant,
            profile_release_fingerprint=self.profile_release_fingerprint,
            observed_parent_manifest_digest=self.observed_parent_manifest_digest,
            parent_state=self.compatibility_state,
            dependency_results=self.dependency_results,
            active_ontology_bundle_digest=self.active_ontology_bundle_digest,
            ontology_bundle_state=self.ontology_bundle_state,
            source_contract=self.source_contract,
        )


class RuntimeEvaluationError(ValueError):
    pass


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _utf16(value: str) -> bytes:
    return value.encode("utf-16be")


def _require_string(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise RuntimeEvaluationError(f"{label} must be a non-empty string")
    return value


def _scalar_key(value: Any) -> tuple[str, Any]:
    if value is None:
        return ("null", None)
    if type(value) is bool:
        return ("boolean", value)
    if type(value) is int:
        return ("integer", value)
    if type(value) is float:
        if not math.isfinite(value):
            raise RuntimeEvaluationError("non-finite JSON number")
        return ("number", value)
    if type(value) is str:
        return ("string", value)
    raise RuntimeEvaluationError("value is not a JSON scalar")


def _scalar_projection(values: tuple[tuple[str, Any], ...]) -> list[dict[str, Any]]:
    rows = [{"type": kind, "value": value} for kind, value in values]
    rows.sort(key=canonical_json_bytes)
    return rows


def _validate_variant_key(key: Any) -> BundleVariantKey:
    if type(key) is not BundleVariantKey:
        raise RuntimeEvaluationError("variant key has the wrong type")
    for field in (
        key.corpus_id,
        key.authored_profile_id,
        key.profile_version,
        key.expected_parent_manifest_digest,
    ):
        _require_string(field, "variant key field")
    if key.ontology_bundle_digest is not None:
        _require_string(key.ontology_bundle_digest, "variant ontology bundle digest")
    return key


def _validate_release_key(value: Any) -> ProfileReleaseKey:
    if type(value) is not ProfileReleaseKey:
        raise RuntimeEvaluationError("variant release key has the wrong type")
    _require_string(value.corpus_id, "release corpus_id")
    _require_string(value.authored_profile_id, "release authored_profile_id")
    _require_string(value.profile_version, "release profile_version")
    return value


def _validate_release_signature(value: Any) -> ProfileReleaseSignature:
    if type(value) is not ProfileReleaseSignature:
        raise RuntimeEvaluationError("variant release signature has the wrong type")
    try:
        profile_release_fingerprint(value)
    except (SemanticResolutionError, TypeError, AttributeError, ValueError) as error:
        raise RuntimeEvaluationError("variant release signature is malformed") from error
    return value


def _validate_variant(variant: BundleVariantIR) -> None:
    if type(variant) is not BundleVariantIR:
        raise TypeError("variant must be BundleVariantIR")
    key = _validate_variant_key(variant.key)
    release_key = _validate_release_key(variant.release_key)
    signature = _validate_release_signature(variant.release_signature)

    if (
        release_key.corpus_id != key.corpus_id
        or release_key.authored_profile_id != key.authored_profile_id
        or release_key.profile_version != key.profile_version
    ):
        raise RuntimeEvaluationError("variant release key does not match variant key")
    if signature.dependency_contract_version != 1:
        raise RuntimeEvaluationError("unsupported dependency contract version")
    if signature.ontology_bundle_digest != key.ontology_bundle_digest:
        raise RuntimeEvaluationError("variant ontology bundle identity is incoherent")
    if variant.mapping_digests != signature.mapping_digests:
        raise RuntimeEvaluationError("variant mapping authority is incoherent")
    if variant.ontology_locks != signature.ontology_locks:
        raise RuntimeEvaluationError("variant ontology authority is incoherent")

    repeated = (
        (variant.profile_schema_version, signature.profile_schema_version),
        (variant.profile_catalog_version, signature.profile_catalog_version),
        (variant.dependency_contract_version, signature.dependency_contract_version),
        (variant.mapping_schema_version, signature.mapping_schema_version),
        (variant.mapping_semantic_algorithm, signature.mapping_semantic_algorithm),
        (variant.projection_semantic_algorithm, signature.projection_semantic_algorithm),
    )
    if any(left != right for left, right in repeated):
        raise RuntimeEvaluationError(
            "variant repeated contract fields disagree with release signature"
        )


def _expect_exact_keys(
    value: dict[str, Any],
    required: set[str],
    label: str,
) -> None:
    if set(value) != required:
        raise RuntimeEvaluationError(f"{label} has an invalid shape")


def _validate_evidence(value: Any, *, require_nonempty: bool = False) -> None:
    if type(value) is not list:
        if require_nonempty:
            raise RuntimeEvaluationError(
                "closed-reviewed value-domain requires evidence"
            )
        raise RuntimeEvaluationError("dependency evidence has an invalid shape")
    if require_nonempty and not value:
        raise RuntimeEvaluationError(
            "closed-reviewed value-domain requires evidence"
        )
    seen: set[tuple[str, str]] = set()
    for row in value:
        if type(row) is not dict or set(row) != {"evidence_id", "content_digest"}:
            raise RuntimeEvaluationError("dependency evidence has an invalid shape")
        key = (
            _require_string(row.get("evidence_id"), "evidence_id"),
            _require_string(row.get("content_digest"), "content_digest"),
        )
        if key in seen:
            raise RuntimeEvaluationError("dependency evidence contains duplicates")
        seen.add(key)


def _validate_assertion(record: dict[str, Any]) -> None:
    kind = record["kind"]
    assertion = record["assertion"]
    if type(assertion) is not dict:
        raise RuntimeEvaluationError("dependency assertion must be an object")

    if kind == "component-present":
        _expect_exact_keys(assertion, set(), kind)
        return
    if kind == "node-type-present":
        _expect_exact_keys(assertion, {"node_type"}, kind)
        _require_string(assertion["node_type"], "node_type")
        return
    if kind == "feature-present":
        _expect_exact_keys(assertion, {"node_type", "feature"}, kind)
        _require_string(assertion["node_type"], "node_type")
        _require_string(assertion["feature"], "feature")
        return
    if kind == "edge-present":
        _expect_exact_keys(assertion, {"edge", "direction"}, kind)
        _require_string(assertion["edge"], "edge")
        if assertion["direction"] not in _DIRECTIONS:
            raise RuntimeEvaluationError("edge direction is invalid")
        return
    if kind == "path-present":
        _expect_exact_keys(assertion, {"steps"}, kind)
        steps = assertion["steps"]
        if type(steps) is not list or not steps:
            raise RuntimeEvaluationError("path steps must be a non-empty array")
        for step in steps:
            if type(step) is not dict:
                raise RuntimeEvaluationError("path step must be an object")
            _expect_exact_keys(step, {"edge", "direction"}, "path step")
            _require_string(step["edge"], "path edge")
            if step["direction"] not in _DIRECTIONS:
                raise RuntimeEvaluationError("path direction is invalid")
        return
    if kind == "native-value-present":
        _expect_exact_keys(
            assertion,
            {"node_type", "feature", "value", "value_semantics"},
            kind,
        )
        _require_string(assertion["node_type"], "node_type")
        _require_string(assertion["feature"], "feature")
        if assertion["value_semantics"] != "semantic":
            raise RuntimeEvaluationError("native value semantics must be semantic")
        _scalar_key(assertion["value"])
        return
    if kind == "value-domain":
        _expect_exact_keys(
            assertion,
            {"node_type", "feature", "values", "domain_semantics"},
            kind,
        )
        _require_string(assertion["node_type"], "node_type")
        _require_string(assertion["feature"], "feature")
        values = assertion["values"]
        if type(values) is not list or not values:
            raise RuntimeEvaluationError(
                "value-domain values must be a non-empty array"
            )
        tagged = tuple(_scalar_key(value) for value in values)
        identities = {
            canonical_json_bytes({"type": scalar_type, "value": scalar})
            for scalar_type, scalar in tagged
        }
        if len(identities) != len(tagged):
            raise RuntimeEvaluationError(
                "value-domain values must be unique by JSON identity"
            )
        if assertion["domain_semantics"] not in {"observed", "closed-reviewed"}:
            raise RuntimeEvaluationError("value-domain semantics are invalid")
        return
    if kind == "extent-interpretation":
        _expect_exact_keys(assertion, {"node_type", "interpretation"}, kind)
        _require_string(assertion["node_type"], "node_type")
        if assertion["interpretation"] not in _EXTENT_INTERPRETATIONS:
            raise RuntimeEvaluationError("extent interpretation is invalid")
        return
    raise RuntimeEvaluationError("dependency kind is not recognized")


def _dependency_records(
    variant: BundleVariantIR,
) -> tuple[tuple[str, dict[str, Any]], ...]:
    rows: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for row in variant.release_signature.dependency_records:
        if type(row) is not tuple or len(row) != 2:
            raise RuntimeEvaluationError("invalid dependency record envelope")
        dependency_id, encoded = row
        _require_string(dependency_id, "dependency_id")
        if dependency_id in seen:
            raise RuntimeEvaluationError("dependency IDs must be unique")
        _require_string(encoded, "dependency record")
        try:
            record = json.loads(encoded)
        except (TypeError, ValueError) as error:
            raise RuntimeEvaluationError("dependency record is invalid JSON") from error
        if type(record) is not dict:
            raise RuntimeEvaluationError(
                "dependency record must decode to an object"
            )
        if canonical_json_bytes(record).decode("utf-8") != encoded:
            raise RuntimeEvaluationError(
                "dependency record must use canonical JSON encoding"
            )
        allowed_top = {
            "dependency_id",
            "component_id",
            "kind",
            "assertion",
            "evidence",
        }
        required_top = {"dependency_id", "component_id", "kind", "assertion"}
        if not required_top.issubset(record) or not set(record).issubset(allowed_top):
            raise RuntimeEvaluationError("dependency record has an invalid envelope")
        if record["dependency_id"] != dependency_id:
            raise RuntimeEvaluationError("dependency record identity mismatch")
        _require_string(record["component_id"], "component_id")
        kind = _require_string(record["kind"], "dependency kind")
        if kind not in _KIND_RULES:
            raise RuntimeEvaluationError("dependency kind is not recognized")
        _validate_assertion(record)
        requires_evidence = (
            kind == "value-domain"
            and record["assertion"]["domain_semantics"] == "closed-reviewed"
        )
        if "evidence" in record:
            _validate_evidence(
                record["evidence"],
                require_nonempty=requires_evidence,
            )
        elif requires_evidence:
            _validate_evidence(None, require_nonempty=True)
        seen.add(dependency_id)
        rows.append((dependency_id, record))
    rows.sort(key=lambda item: _utf16(item[0]))
    return tuple(rows)


def _unknown(dependency_id: str, kind: str) -> DependencyPrerequisiteResult:
    return DependencyPrerequisiteResult(
        dependency_id=dependency_id,
        result="unknown",
        observed_evidence_digest=None,
        evaluator_rule_version=_KIND_RULES[kind],
    )


def _known(
    dependency_id: str,
    kind: str,
    result: str,
    evidence: dict[str, Any],
) -> DependencyPrerequisiteResult:
    return DependencyPrerequisiteResult(
        dependency_id=dependency_id,
        result=result,
        observed_evidence_digest=_hash(
            {"algorithm": OBSERVATION_FINGERPRINT_ALGORITHM, **evidence}
        ),
        evaluator_rule_version=_KIND_RULES[kind],
    )


def _status_fact(
    dependency_id: str,
    kind: str,
    state: Any,
    evidence: dict[str, Any],
) -> DependencyPrerequisiteResult:
    if state == "present":
        return _known(
            dependency_id,
            kind,
            "pass",
            {**evidence, "state": "present"},
        )
    if state == "absent":
        return _known(
            dependency_id,
            kind,
            "fail",
            {**evidence, "state": "absent"},
        )
    return _unknown(dependency_id, kind)


def _call_status(method: Any, *args: Any) -> Any:
    try:
        return method(*args)
    except Exception:
        return "unknown"


def _observed_values(
    observation: RuntimeObservation,
    component_id: str,
    node_type: str,
    feature: str,
) -> tuple[str, tuple[Any, ...]]:
    try:
        result = observation.values(component_id, node_type, feature)
    except Exception:
        return ("unknown", ())
    if type(result) is not tuple or len(result) != 2:
        return ("unknown", ())
    state, values = result
    if state == "absent":
        return ("absent", ())
    if state != "complete" or type(values) is not tuple:
        return ("unknown", ())
    try:
        tuple(_scalar_key(value) for value in values)
    except RuntimeEvaluationError:
        return ("unknown", ())
    return ("complete", values)


def _values_evidence(
    record: dict[str, Any],
    tagged: tuple[tuple[str, Any], ...],
) -> dict[str, Any]:
    assertion = record["assertion"]
    return {
        "kind": record["kind"],
        "component_id": record["component_id"],
        "node_type": assertion["node_type"],
        "feature": assertion["feature"],
        "complete": True,
        "values": _scalar_projection(tagged),
    }


def _evaluate_dependency(
    dependency_id: str,
    record: dict[str, Any],
    observation: RuntimeObservation,
) -> DependencyPrerequisiteResult:
    kind = record["kind"]
    component_id = record["component_id"]
    assertion = record["assertion"]

    if kind == "component-present":
        try:
            observed = observation.component(component_id)
        except Exception:
            return _unknown(dependency_id, kind)
        if type(observed) is not tuple or len(observed) != 2:
            return _unknown(dependency_id, kind)
        state, content_digest = observed
        if state == "absent":
            return _known(
                dependency_id,
                kind,
                "fail",
                {
                    "kind": kind,
                    "component_id": component_id,
                    "state": "absent",
                    "content_digest": None,
                },
            )
        if (
            state != "present"
            or type(content_digest) is not str
            or not content_digest
        ):
            return _unknown(dependency_id, kind)
        return _known(
            dependency_id,
            kind,
            "pass",
            {
                "kind": kind,
                "component_id": component_id,
                "state": "present",
                "content_digest": content_digest,
            },
        )

    if kind == "node-type-present":
        state = _call_status(
            observation.node_type,
            component_id,
            assertion["node_type"],
        )
        return _status_fact(
            dependency_id,
            kind,
            state,
            {
                "kind": kind,
                "component_id": component_id,
                "node_type": assertion["node_type"],
            },
        )

    if kind == "feature-present":
        state = _call_status(
            observation.feature,
            component_id,
            assertion["node_type"],
            assertion["feature"],
        )
        return _status_fact(
            dependency_id,
            kind,
            state,
            {
                "kind": kind,
                "component_id": component_id,
                "node_type": assertion["node_type"],
                "feature": assertion["feature"],
            },
        )

    if kind == "edge-present":
        state = _call_status(
            observation.edge,
            component_id,
            assertion["edge"],
            assertion["direction"],
        )
        return _status_fact(
            dependency_id,
            kind,
            state,
            {
                "kind": kind,
                "component_id": component_id,
                "edge": assertion["edge"],
                "direction": assertion["direction"],
            },
        )

    if kind == "path-present":
        steps = tuple(
            (step["edge"], step["direction"])
            for step in assertion["steps"]
        )
        state = _call_status(observation.path, component_id, steps)
        return _status_fact(
            dependency_id,
            kind,
            state,
            {
                "kind": kind,
                "component_id": component_id,
                "steps": [
                    {"edge": edge, "direction": direction}
                    for edge, direction in steps
                ],
            },
        )

    if kind in {"native-value-present", "value-domain"}:
        state, values = _observed_values(
            observation,
            component_id,
            assertion["node_type"],
            assertion["feature"],
        )
        if state == "absent":
            return _known(
                dependency_id,
                kind,
                "fail",
                {
                    "kind": kind,
                    "component_id": component_id,
                    "node_type": assertion["node_type"],
                    "feature": assertion["feature"],
                    "state": "absent",
                },
            )
        if state != "complete":
            return _unknown(dependency_id, kind)
        observed = tuple(_scalar_key(value) for value in values)
        evidence = _values_evidence(record, observed)
        observed_keys = {
            canonical_json_bytes({"type": scalar_type, "value": scalar})
            for scalar_type, scalar in observed
        }
        if kind == "native-value-present":
            scalar_type, scalar = _scalar_key(assertion["value"])
            wanted = canonical_json_bytes(
                {"type": scalar_type, "value": scalar}
            )
            return _known(
                dependency_id,
                kind,
                "pass" if wanted in observed_keys else "fail",
                evidence,
            )
        allowed = tuple(_scalar_key(value) for value in assertion["values"])
        allowed_keys = {
            canonical_json_bytes({"type": scalar_type, "value": scalar})
            for scalar_type, scalar in allowed
        }
        if assertion["domain_semantics"] == "observed":
            passed = allowed_keys.issubset(observed_keys)
        else:
            passed = observed_keys.issubset(allowed_keys)
        return _known(
            dependency_id,
            kind,
            "pass" if passed else "fail",
            {
                **evidence,
                "domain_semantics": assertion["domain_semantics"],
            },
        )

    if kind == "extent-interpretation":
        try:
            observed = observation.extent(component_id, assertion["node_type"])
        except Exception:
            return _unknown(dependency_id, kind)
        if type(observed) is not tuple or len(observed) != 2:
            return _unknown(dependency_id, kind)
        state, interpretation = observed
        if state == "absent":
            return _known(
                dependency_id,
                kind,
                "fail",
                {
                    "kind": kind,
                    "component_id": component_id,
                    "node_type": assertion["node_type"],
                    "state": "absent",
                },
            )
        if state != "known" or interpretation not in _EXTENT_INTERPRETATIONS:
            return _unknown(dependency_id, kind)
        return _known(
            dependency_id,
            kind,
            "pass" if interpretation == assertion["interpretation"] else "fail",
            {
                "kind": kind,
                "component_id": component_id,
                "node_type": assertion["node_type"],
                "interpretation": interpretation,
            },
        )

    raise RuntimeEvaluationError("unreachable dependency kind")


def _bundle_state(
    variant: BundleVariantIR,
    active_ontology_bundle_digest: str | None,
) -> tuple[str | None, str]:
    required = variant.key.ontology_bundle_digest
    if required is None:
        if active_ontology_bundle_digest is not None:
            raise RuntimeEvaluationError(
                "active ontology bundle supplied when none is required"
            )
        return (None, "not-required")
    if active_ontology_bundle_digest is None:
        return (None, "unavailable")
    _require_string(
        active_ontology_bundle_digest,
        "active ontology bundle digest",
    )
    if active_ontology_bundle_digest != required:
        raise RuntimeEvaluationError(
            "active ontology bundle does not match selected release"
        )
    return (active_ontology_bundle_digest, "verified")


def _report_projection(report: RuntimeEvaluationReport) -> dict[str, Any]:
    return {
        "algorithm": RUNTIME_REPORT_FINGERPRINT_ALGORITHM,
        "contract": report.contract,
        "variant": {
            "corpus_id": report.variant.corpus_id,
            "authored_profile_id": report.variant.authored_profile_id,
            "profile_version": report.variant.profile_version,
            "expected_parent_manifest_digest": report.variant.expected_parent_manifest_digest,
            "ontology_bundle_digest": report.variant.ontology_bundle_digest,
        },
        "profile_release_fingerprint": report.profile_release_fingerprint,
        "observed_parent_manifest_digest": report.observed_parent_manifest_digest,
        "compatibility_state": report.compatibility_state,
        "dependency_results": [
            {
                "dependency_id": row.dependency_id,
                "result": row.result,
                "observed_evidence_digest": row.observed_evidence_digest,
                "evaluator_rule_version": row.evaluator_rule_version,
            }
            for row in report.dependency_results
        ],
        "active_ontology_bundle_digest": report.active_ontology_bundle_digest,
        "ontology_bundle_state": report.ontology_bundle_state,
        "source_contract": report.source_contract,
    }


def evaluate_runtime_prerequisites(
    variant: BundleVariantIR,
    observation: RuntimeObservation,
    *,
    source_contract: str,
    active_ontology_bundle_digest: str | None = None,
) -> RuntimeEvaluationReport:
    _validate_variant(variant)
    _require_string(source_contract, "source_contract")
    parent_digest = getattr(observation, "parent_manifest_digest", None)
    _require_string(parent_digest, "observation parent manifest digest")

    results = tuple(
        _evaluate_dependency(dependency_id, record, observation)
        for dependency_id, record in _dependency_records(variant)
    )
    if any(row.result == "fail" for row in results):
        compatibility_state = "incompatible"
    elif any(row.result == "unknown" for row in results):
        compatibility_state = "unverified"
    elif parent_digest == variant.key.expected_parent_manifest_digest:
        compatibility_state = "verified-exact"
    elif variant.release_signature.parent_compatibility == "dependency-verified":
        compatibility_state = "verified-compatible"
    else:
        compatibility_state = "incompatible"

    active_digest, ontology_bundle_state = _bundle_state(
        variant,
        active_ontology_bundle_digest,
    )
    try:
        release_fingerprint = profile_release_fingerprint(
            variant.release_signature
        )
    except (SemanticResolutionError, TypeError, AttributeError, ValueError) as error:
        raise RuntimeEvaluationError(
            "variant release signature cannot be fingerprinted"
        ) from error

    values = dict(
        contract=RUNTIME_EVALUATION_CONTRACT,
        variant=variant.key,
        profile_release_fingerprint=release_fingerprint,
        observed_parent_manifest_digest=parent_digest,
        compatibility_state=compatibility_state,
        dependency_results=results,
        active_ontology_bundle_digest=active_digest,
        ontology_bundle_state=ontology_bundle_state,
        source_contract=source_contract,
    )
    provisional = RuntimeEvaluationReport(report_fingerprint="", **values)
    return RuntimeEvaluationReport(
        report_fingerprint=_hash(_report_projection(provisional)),
        **values,
    )
