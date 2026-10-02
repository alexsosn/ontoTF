from __future__ import annotations

import operator
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .digests import canonical_json_bytes
from .runtime_prerequisites import (
    LoadedTFObservation,
    RuntimeEvaluationReport,
    evaluate_runtime_prerequisites,
)
from .semantic_ir import BundleVariantIR, BundleVariantKey, CompiledSemanticIR, EdgeStepIR, NativeBindingIR
from .semantic_resolver import (
    ApproximateAuthorityResolveRequest,
    ApproximateAuthorityResolutionResult,
    ApproximateNativePlan,
    AuthorityNativePlan,
    AuthorityResolveRequest,
    AuthorityResolutionResult,
    IdentifierNativePlan,
    IdentifierResolveRequest,
    IdentifierResolutionResult,
    IdentityNativePlan,
    IdentityResolveRequest,
    IdentityResolutionResult,
    ApproximateSemanticConjunctionRequest,
    ApproximateSemanticConjunctionResolutionResult,
    ApproximateSemanticResolutionResult,
    ApproximateSemanticResolveRequest,
    ExactNativePlan,
    SemanticConjunctionRequest,
    SemanticConjunctionResolutionResult,
    SemanticResolutionResult,
    SemanticResolveRequest,
    _validate_approximate_authority_request,
    _validate_approximate_conjunction_request,
    _validate_approximate_request,
    _validate_authority_request,
    _validate_identifier_request,
    _validate_identity_request,
    authority_resolve_approximate,
    authority_resolve_exact,
    identifier_resolve,
    identity_resolve,
    semantic_resolve,
    semantic_resolve_approximate,
    semantic_resolve_approximate_conjunction,
    semantic_resolve_conjunction,
)

EXACT_EXECUTION_CONTRACT = "tfont-exact-execution-v1"
EXACT_EXECUTION_RUNTIME_SOURCE_CONTRACT = "tfont-exact-execution-runtime-v1"
APPROXIMATE_EXECUTION_CONTRACT = "tfont-approximate-execution-v1"
APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT = "tfont-approximate-execution-runtime-v1"
APPROXIMATE_CONJUNCTION_EXECUTION_CONTRACT = "tfont-approximate-semantic-conjunction-execution-v1"
REFERENCE_EXECUTION_RUNTIME_SOURCE_CONTRACT = "tfont-reference-execution-runtime-v1"
EXACT_AUTHORITY_EXECUTION_CONTRACT = "tfont-exact-authority-execution-v1"
APPROXIMATE_AUTHORITY_EXECUTION_CONTRACT = "tfont-approximate-authority-execution-v1"
IDENTITY_EXECUTION_CONTRACT = "tfont-identity-execution-v1"
IDENTIFIER_EXECUTION_CONTRACT = "tfont-identifier-execution-v1"


@dataclass(frozen=True)
class LoadedComponentContext:
    component_id: str
    content_digest: str
    api: Any = field(repr=False, compare=False)


@dataclass(frozen=True)
class LoadedCorpusContext:
    corpus_id: str
    parent_manifest_digest: str
    components: tuple[LoadedComponentContext, ...]
    active_ontology_bundle_digest: str | None = None


@dataclass(frozen=True)
class ExactCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plan: ExactNativePlan
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class ExactExecutionResult:
    execution_contract: str
    resolution: SemanticResolutionResult
    corpora: tuple[ExactCorpusExecution, ...]


@dataclass(frozen=True)
class ApproximateCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plan: ApproximateNativePlan
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class ApproximateExecutionResult:
    execution_contract: str
    resolution: ApproximateSemanticResolutionResult
    corpora: tuple[ApproximateCorpusExecution, ...]


@dataclass(frozen=True)
class ExactAuthorityCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plan: AuthorityNativePlan
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class ExactAuthorityExecutionResult:
    execution_contract: str
    resolution: AuthorityResolutionResult
    corpora: tuple[ExactAuthorityCorpusExecution, ...]


@dataclass(frozen=True)
class ApproximateAuthorityCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plan: AuthorityNativePlan
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class ApproximateAuthorityExecutionResult:
    execution_contract: str
    resolution: ApproximateAuthorityResolutionResult
    corpora: tuple[ApproximateAuthorityCorpusExecution, ...]


@dataclass(frozen=True)
class IdentityCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plan: IdentityNativePlan
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class IdentityExecutionResult:
    execution_contract: str
    resolution: IdentityResolutionResult
    corpora: tuple[IdentityCorpusExecution, ...]


@dataclass(frozen=True)
class IdentifierCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plan: IdentifierNativePlan
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class IdentifierExecutionResult:
    execution_contract: str
    resolution: IdentifierResolutionResult
    corpora: tuple[IdentifierCorpusExecution, ...]


@dataclass(frozen=True)
class ExactExecutionProblem:
    category: str
    message: str
    corpus_id: str | None = None
    component_id: str | None = None


class ExactExecutionError(ValueError):
    def __init__(self, problem: ExactExecutionProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


@dataclass(frozen=True)
class ApproximateExecutionProblem:
    category: str
    message: str
    corpus_id: str | None = None
    component_id: str | None = None


class ApproximateExecutionError(ValueError):
    def __init__(self, problem: ApproximateExecutionProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


def _approximate_fail(
    category: str,
    message: str,
    *,
    corpus_id: str | None = None,
    component_id: str | None = None,
) -> None:
    raise ApproximateExecutionError(
        ApproximateExecutionProblem(
            category=category,
            message=message,
            corpus_id=corpus_id,
            component_id=component_id,
        )
    )


def _translate_exact_execution_error(error: ExactExecutionError) -> ApproximateExecutionError:
    problem = error.problem
    return ApproximateExecutionError(
        ApproximateExecutionProblem(
            category=problem.category,
            message=problem.message,
            corpus_id=problem.corpus_id,
            component_id=problem.component_id,
        )
    )


def _fail(
    category: str,
    message: str,
    *,
    corpus_id: str | None = None,
    component_id: str | None = None,
) -> None:
    raise ExactExecutionError(
        ExactExecutionProblem(
            category=category,
            message=message,
            corpus_id=corpus_id,
            component_id=component_id,
        )
    )


def _utf16(value: str) -> bytes:
    return value.encode("utf-16be")


def _nonempty_string(value: Any) -> bool:
    return type(value) is str and bool(value)


def _normalize_contexts(
    contexts: Iterable[LoadedCorpusContext],
) -> dict[str, LoadedCorpusContext]:
    try:
        rows = tuple(contexts)
    except TypeError:
        _fail("invalid_execution_context", "contexts must be iterable")

    by_corpus: dict[str, LoadedCorpusContext] = {}
    for context in rows:
        if type(context) is not LoadedCorpusContext:
            _fail("invalid_execution_context", "context has the wrong type")
        if not _nonempty_string(context.corpus_id):
            _fail("invalid_execution_context", "corpus_id must be a non-empty string")
        if not _nonempty_string(context.parent_manifest_digest):
            _fail(
                "invalid_execution_context",
                "parent manifest digest must be a non-empty string",
                corpus_id=context.corpus_id,
            )
        if type(context.components) is not tuple or not context.components:
            _fail(
                "invalid_execution_context",
                "components must be a non-empty exact tuple",
                corpus_id=context.corpus_id,
            )
        if context.active_ontology_bundle_digest is not None and not _nonempty_string(
            context.active_ontology_bundle_digest
        ):
            _fail(
                "invalid_execution_context",
                "active ontology bundle digest must be a non-empty string or null",
                corpus_id=context.corpus_id,
            )

        seen_components: set[str] = set()
        for component in context.components:
            if type(component) is not LoadedComponentContext:
                _fail(
                    "invalid_execution_context",
                    "component context has the wrong type",
                    corpus_id=context.corpus_id,
                )
            if not _nonempty_string(component.component_id) or not _nonempty_string(
                component.content_digest
            ):
                _fail(
                    "invalid_execution_context",
                    "component identity fields must be non-empty strings",
                    corpus_id=context.corpus_id,
                )
            if component.api is None:
                _fail(
                    "invalid_execution_context",
                    "component API handle must be non-null",
                    corpus_id=context.corpus_id,
                    component_id=component.component_id,
                )
            if component.component_id in seen_components:
                _fail(
                    "invalid_execution_context",
                    "duplicate component ID in execution context",
                    corpus_id=context.corpus_id,
                    component_id=component.component_id,
                )
            seen_components.add(component.component_id)

        if context.corpus_id in by_corpus:
            _fail(
                "duplicate_execution_context",
                "duplicate execution context for corpus",
                corpus_id=context.corpus_id,
            )
        by_corpus[context.corpus_id] = context
    return by_corpus


def _requested_corpora(request: SemanticResolveRequest) -> tuple[str, ...]:
    if type(request) is not SemanticResolveRequest:
        raise TypeError("request must be SemanticResolveRequest")
    corpora = request.corpora
    if type(corpora) is not tuple or not corpora:
        # I-006 owns the full request diagnostic. This guard only makes the
        # pre-resolution executor traversal deterministic and safe.
        _fail("invalid_execution_context", "request corpora must be a non-empty tuple")
    if any(not _nonempty_string(corpus_id) for corpus_id in corpora):
        _fail("invalid_execution_context", "request corpus IDs must be non-empty strings")
    return tuple(sorted(set(corpora), key=_utf16))


def _select_variants(
    ir: CompiledSemanticIR,
    corpora: tuple[str, ...],
) -> dict[str, BundleVariantIR]:
    if type(ir) is not CompiledSemanticIR or type(ir.variants) is not tuple:
        _fail("invalid_compiled_ir", "compiled IR has an invalid variant envelope")

    by_corpus: dict[str, list[BundleVariantIR]] = {}
    for row in ir.variants:
        if type(row) is not BundleVariantIR or type(row.key) is not BundleVariantKey:
            _fail("invalid_compiled_ir", "compiled IR contains an invalid variant row")
        if not _nonempty_string(row.key.corpus_id):
            _fail("invalid_compiled_ir", "compiled IR variant corpus_id is invalid")
        by_corpus.setdefault(row.key.corpus_id, []).append(row)

    selected: dict[str, BundleVariantIR] = {}
    for corpus_id in corpora:
        rows = by_corpus.get(corpus_id, ())
        if not rows:
            _fail(
                "missing_runtime_variant",
                "requested corpus has no compiled runtime variant",
                corpus_id=corpus_id,
            )
        if len(rows) != 1:
            _fail(
                "ambiguous_runtime_variant",
                "requested corpus has multiple compiled runtime variants",
                corpus_id=corpus_id,
            )
        selected[corpus_id] = rows[0]
    return selected


def _components(context: LoadedCorpusContext) -> dict[str, LoadedComponentContext]:
    return {row.component_id: row for row in context.components}


def _observation(context: LoadedCorpusContext) -> LoadedTFObservation:
    return LoadedTFObservation(
        parent_manifest_digest=context.parent_manifest_digest,
        components={
            row.component_id: (row.content_digest, row.api)
            for row in context.components
        },
    )


def _validate_value_predicate(plan: ExactNativePlan) -> NativeBindingIR:
    binding = plan.native_execution_binding
    valid = (
        type(binding) is NativeBindingIR
        and _nonempty_string(binding.component_id)
        and _nonempty_string(binding.node_type)
        and _nonempty_string(binding.feature)
        and binding.value_present is True
        and type(binding.value) is str
        and bool(binding.value)
        and binding.execution_shape == "value-predicate"
        and binding.values is None
        and binding.closed_values is None
        and binding.edge is None
        and binding.direction is None
        and binding.steps is None
        and binding.interpretation is None
    )
    if not valid:
        _fail(
            "unsupported_native_binding",
            "v0.1 execution supports only an explicit string value-predicate binding",
            corpus_id=plan.corpus_id,
            component_id=getattr(binding, "component_id", None),
        )
    return binding


def _validate_value_set_predicate(plan: ExactNativePlan) -> NativeBindingIR:
    binding = plan.native_execution_binding
    values_valid = type(binding) is NativeBindingIR and type(binding.values) is tuple and bool(binding.values)
    encoded_values: list[bytes] = []
    if values_valid:
        for value in binding.values or ():
            if not (value is None or type(value) in {str, int, float, bool}):
                values_valid = False
                break
            try:
                encoded_values.append(canonical_json_bytes(value))
            except Exception:
                values_valid = False
                break
        if values_valid:
            values_valid = (
                len(set(encoded_values)) == len(encoded_values)
                and tuple(encoded_values) == tuple(sorted(encoded_values))
            )
    valid = (
        type(binding) is NativeBindingIR
        and _nonempty_string(binding.component_id)
        and _nonempty_string(binding.node_type)
        and _nonempty_string(binding.feature)
        and binding.value_present is False
        and binding.value is None
        and values_valid
        and binding.execution_shape == "value-set-predicate"
        and binding.closed_values is None
        and binding.edge is None
        and binding.direction is None
        and binding.steps is None
        and binding.interpretation is None
    )
    if not valid:
        _fail(
            "unsupported_native_binding",
            "v0.1 value-set execution requires one feature and a canonical finite JSON-scalar value set",
            corpus_id=plan.corpus_id,
            component_id=getattr(binding, "component_id", None),
        )
    return binding


def _validate_membership_binding(plan: Any) -> NativeBindingIR:
    binding = plan.native_execution_binding
    valid = (
        type(binding) is NativeBindingIR
        and _nonempty_string(binding.component_id)
        and _nonempty_string(binding.node_type)
        and binding.execution_shape == "membership"
        and binding.feature is None
        and binding.value_present is False
        and binding.value is None
        and binding.closed_values is None
        and binding.values is None
        and binding.edge is None
        and binding.direction is None
        and binding.steps is None
        and binding.interpretation is None
    )
    if not valid:
        _fail(
            "unsupported_native_binding",
            "membership execution requires only component_id and node_type",
            corpus_id=plan.corpus_id,
            component_id=getattr(binding, "component_id", None),
        )
    return binding


def _loaded_membership_api(
    api: Any,
    binding: NativeBindingIR,
    *,
    corpus_id: str,
) -> tuple[Any, Any]:
    try:
        otype_api = api.F.otype
        selector = otype_api.s
        lookup = otype_api.v
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded node-type API is unavailable",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        ) from error
    if not callable(selector) or not callable(lookup):
        _fail(
            "loaded_api_unavailable",
            "loaded node-type API methods are unavailable",
            corpus_id=corpus_id,
            component_id=binding.component_id,
        )
    return selector, lookup


def _execute_membership(
    plan: Any,
    component: LoadedComponentContext,
) -> tuple[int, ...]:
    binding = _validate_membership_binding(plan)
    selector, lookup = _loaded_membership_api(
        component.api,
        binding,
        corpus_id=plan.corpus_id,
    )
    try:
        raw_nodes = selector(binding.node_type)
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded node-type selector failed",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        ) from error

    nodes = _normalize_result_nodes(
        raw_nodes,
        corpus_id=plan.corpus_id,
        component_id=binding.component_id or "",
    )
    if not nodes:
        _fail(
            "invalid_result_nodes",
            "membership selector became empty after prerequisite authorization",
            corpus_id=plan.corpus_id,
            component_id=binding.component_id,
        )

    for node in nodes:
        try:
            observed_type = lookup(node)
        except Exception as error:
            raise ExactExecutionError(
                ExactExecutionProblem(
                    "loaded_api_unavailable",
                    "loaded node-type lookup failed",
                    corpus_id=plan.corpus_id,
                    component_id=binding.component_id,
                )
            ) from error
        if type(observed_type) is not str or not observed_type:
            _fail(
                "loaded_api_unavailable",
                "loaded node-type lookup returned a malformed value",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        if observed_type != binding.node_type:
            _fail(
                "invalid_result_nodes",
                "membership selector returned a node outside the reviewed node type",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
    return nodes


def _validate_edge_path_binding(plan: Any) -> NativeBindingIR:
    binding = plan.native_execution_binding
    steps_valid = (
        type(binding) is NativeBindingIR
        and type(binding.steps) is tuple
        and bool(binding.steps)
    )
    if steps_valid:
        for step in binding.steps or ():
            if (
                type(step) is not EdgeStepIR
                or not _nonempty_string(step.edge)
                or step.direction not in {"outgoing", "incoming"}
                or not _nonempty_string(step.result_node_type)
                or step.valued is not False
            ):
                steps_valid = False
                break

    valid = (
        type(binding) is NativeBindingIR
        and _nonempty_string(binding.component_id)
        and _nonempty_string(binding.node_type)
        and binding.execution_shape == "edge-path"
        and steps_valid
        and binding.feature is None
        and binding.value_present is False
        and binding.value is None
        and binding.closed_values is None
        and binding.values is None
        and binding.edge is None
        and binding.direction is None
        and binding.interpretation is None
    )
    if not valid:
        _fail(
            "unsupported_native_binding",
            "edge-path execution requires a typed non-empty unvalued step sequence",
            corpus_id=plan.corpus_id,
            component_id=getattr(binding, "component_id", None),
        )
    return binding


def _loaded_edge_path_api(
    api: Any,
    binding: NativeBindingIR,
    *,
    corpus_id: str,
) -> tuple[Any, Any, tuple[Any, ...]]:
    selector, lookup = _loaded_membership_api(
        api,
        binding,
        corpus_id=corpus_id,
    )

    try:
        loaded_value = api.Eall()
        if isinstance(loaded_value, (str, bytes, bytearray, Mapping)):
            _fail(
                "loaded_api_unavailable",
                "loaded edge inventory is malformed",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        loaded = tuple(loaded_value)
    except ExactExecutionError:
        raise
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded edge inventory is unavailable",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        ) from error

    if any(type(name) is not str or not name for name in loaded):
        _fail(
            "loaded_api_unavailable",
            "loaded edge inventory is malformed",
            corpus_id=corpus_id,
            component_id=binding.component_id,
        )
    loaded_set = set(loaded)

    methods: list[Any] = []
    for step in binding.steps or ():
        if step.edge not in loaded_set:
            _fail(
                "loaded_api_unavailable",
                "reviewed edge path references an edge that is not loaded",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        try:
            edge_api = getattr(api.E, step.edge)
            method = getattr(
                edge_api,
                "f" if step.direction == "outgoing" else "t",
            )
            valued = edge_api.doValues
        except Exception as error:
            raise ExactExecutionError(
                ExactExecutionProblem(
                    "loaded_api_unavailable",
                    "loaded edge API is unavailable",
                    corpus_id=corpus_id,
                    component_id=binding.component_id,
                )
            ) from error
        if not callable(method):
            _fail(
                "loaded_api_unavailable",
                "loaded edge traversal method is unavailable",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        if type(valued) is not bool or valued is not False:
            _fail(
                "loaded_api_unavailable",
                "I-023 executes only explicitly unvalued loaded edges",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        methods.append(method)

    return selector, lookup, tuple(methods)


def _loaded_node_type(
    lookup: Any,
    node: int,
    *,
    corpus_id: str,
    component_id: str,
) -> str:
    try:
        observed_type = lookup(node)
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded node-type lookup failed",
                corpus_id=corpus_id,
                component_id=component_id,
            )
        ) from error
    if type(observed_type) is not str or not observed_type:
        _fail(
            "loaded_api_unavailable",
            "loaded node-type lookup returned a malformed value",
            corpus_id=corpus_id,
            component_id=component_id,
        )
    return observed_type


def _execute_edge_path(
    plan: Any,
    component: LoadedComponentContext,
) -> tuple[int, ...]:
    binding = _validate_edge_path_binding(plan)
    selector, lookup, methods = _loaded_edge_path_api(
        component.api,
        binding,
        corpus_id=plan.corpus_id,
    )

    try:
        raw_start = selector(binding.node_type)
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded edge-path start selector failed",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        ) from error

    frontier = _normalize_result_nodes(
        raw_start,
        corpus_id=plan.corpus_id,
        component_id=binding.component_id or "",
    )
    if not frontier:
        _fail(
            "invalid_result_nodes",
            "edge-path start selector became empty after prerequisite authorization",
            corpus_id=plan.corpus_id,
            component_id=binding.component_id,
        )

    for node in frontier:
        observed_type = _loaded_node_type(
            lookup,
            node,
            corpus_id=plan.corpus_id,
            component_id=binding.component_id or "",
        )
        if observed_type != binding.node_type:
            _fail(
                "invalid_result_nodes",
                "edge-path start selector returned a node outside the reviewed start type",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )

    for step, method in zip(binding.steps or (), methods):
        if not frontier:
            break
        selected: list[int] = []
        selected_seen: set[int] = set()
        for source_node in frontier:
            try:
                raw_nodes = method(source_node)
            except Exception as error:
                raise ExactExecutionError(
                    ExactExecutionProblem(
                        "loaded_api_unavailable",
                        "loaded edge traversal failed",
                        corpus_id=plan.corpus_id,
                        component_id=binding.component_id,
                    )
                ) from error
            nodes = _normalize_result_nodes(
                raw_nodes,
                corpus_id=plan.corpus_id,
                component_id=binding.component_id or "",
            )
            for node in nodes:
                observed_type = _loaded_node_type(
                    lookup,
                    node,
                    corpus_id=plan.corpus_id,
                    component_id=binding.component_id or "",
                )
                if observed_type != step.result_node_type:
                    continue
                if node in selected_seen:
                    continue
                selected_seen.add(node)
                selected.append(node)
        frontier = tuple(selected)

    return frontier


def _execution_result_domain(plan: Any) -> tuple[str, str]:
    binding = plan.native_execution_binding
    if type(binding) is not NativeBindingIR:
        _fail(
            "unsupported_native_binding",
            "execution plan has an invalid native binding",
            corpus_id=plan.corpus_id,
        )
    if binding.execution_shape == "value-predicate":
        binding = _validate_value_predicate(plan)
        return binding.component_id or "", binding.node_type or ""
    if binding.execution_shape == "value-set-predicate":
        binding = _validate_value_set_predicate(plan)
        return binding.component_id or "", binding.node_type or ""
    if binding.execution_shape == "membership":
        binding = _validate_membership_binding(plan)
        return binding.component_id or "", binding.node_type or ""
    if binding.execution_shape == "edge-path":
        binding = _validate_edge_path_binding(plan)
        final_step = (binding.steps or ())[-1]
        return binding.component_id or "", final_step.result_node_type or ""
    _fail(
        "unsupported_native_binding",
        "execution shape has no reviewed result-node domain",
        corpus_id=plan.corpus_id,
        component_id=binding.component_id,
    )
    raise AssertionError("unreachable")


def _loaded_feature_api(
    api: Any,
    binding: NativeBindingIR,
    *,
    corpus_id: str,
) -> tuple[Any, Any]:
    try:
        loaded_value = api.Fall()
        if isinstance(loaded_value, (str, bytes, bytearray, Mapping)):
            _fail(
                "loaded_api_unavailable",
                "loaded feature inventory is malformed",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        loaded = tuple(loaded_value)
    except ExactExecutionError:
        raise
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded feature inventory is unavailable",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        ) from error
    if any(type(name) is not str for name in loaded):
        _fail(
            "loaded_api_unavailable",
            "loaded feature inventory is malformed",
            corpus_id=corpus_id,
            component_id=binding.component_id,
        )
    if binding.feature not in loaded:
        _fail(
            "feature_not_loaded",
            "planned node feature is not currently loaded",
            corpus_id=corpus_id,
            component_id=binding.component_id,
        )
    try:
        feature_api = getattr(api.F, binding.feature)
        otype_api = api.F.otype
        feature_selector = feature_api.s
        otype_lookup = otype_api.v
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded feature API is unavailable",
                corpus_id=corpus_id,
                component_id=binding.component_id,
            )
        ) from error
    if not callable(feature_selector) or not callable(otype_lookup):
        _fail(
            "loaded_api_unavailable",
            "loaded feature API methods are unavailable",
            corpus_id=corpus_id,
            component_id=binding.component_id,
        )
    return feature_selector, otype_lookup


def _normalize_result_nodes(
    raw_nodes: Any,
    *,
    corpus_id: str,
    component_id: str,
) -> tuple[int, ...]:
    try:
        rows = tuple(raw_nodes)
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "invalid_result_nodes",
                "feature selector returned a non-iterable result",
                corpus_id=corpus_id,
                component_id=component_id,
            )
        ) from error

    normalized: list[int] = []
    seen: set[int] = set()
    for node in rows:
        if type(node) is bool:
            _fail(
                "invalid_result_nodes",
                "boolean is not a valid node ID",
                corpus_id=corpus_id,
                component_id=component_id,
            )
        try:
            value = operator.index(node)
        except Exception as error:
            raise ExactExecutionError(
                ExactExecutionProblem(
                    "invalid_result_nodes",
                    "result node does not implement a usable integer index protocol",
                    corpus_id=corpus_id,
                    component_id=component_id,
                )
            ) from error
        value = int(value)
        if value <= 0 or value in seen:
            _fail(
                "invalid_result_nodes",
                "result node IDs must be positive and unique after normalization",
                corpus_id=corpus_id,
                component_id=component_id,
            )
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _execute_value_predicate(
    plan: ExactNativePlan,
    component: LoadedComponentContext,
) -> tuple[int, ...]:
    binding = _validate_value_predicate(plan)
    feature_selector, otype_lookup = _loaded_feature_api(
        component.api,
        binding,
        corpus_id=plan.corpus_id,
    )
    try:
        raw_nodes = feature_selector(binding.value)
    except Exception as error:
        raise ExactExecutionError(
            ExactExecutionProblem(
                "loaded_api_unavailable",
                "loaded feature selector failed",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        ) from error

    nodes = _normalize_result_nodes(
        raw_nodes,
        corpus_id=plan.corpus_id,
        component_id=binding.component_id or "",
    )
    result: list[int] = []
    for node in nodes:
        try:
            node_type = otype_lookup(node)
        except Exception as error:
            raise ExactExecutionError(
                ExactExecutionProblem(
                    "loaded_api_unavailable",
                    "loaded node-type lookup failed",
                    corpus_id=plan.corpus_id,
                    component_id=binding.component_id,
                )
            ) from error
        if type(node_type) is not str or not node_type:
            _fail(
                "loaded_api_unavailable",
                "loaded node-type lookup returned a malformed value",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        if node_type == binding.node_type:
            result.append(node)
    return tuple(result)


def _execute_value_set_predicate(
    plan: ExactNativePlan,
    component: LoadedComponentContext,
) -> tuple[int, ...]:
    binding = _validate_value_set_predicate(plan)
    feature_selector, otype_lookup = _loaded_feature_api(
        component.api,
        binding,
        corpus_id=plan.corpus_id,
    )
    selected_nodes: set[int] = set()
    for selected_value in binding.values or ():
        try:
            raw_nodes = feature_selector(selected_value)
        except Exception as error:
            raise ExactExecutionError(
                ExactExecutionProblem(
                    "loaded_api_unavailable",
                    "loaded feature selector failed",
                    corpus_id=plan.corpus_id,
                    component_id=binding.component_id,
                )
            ) from error
        nodes = _normalize_result_nodes(
            raw_nodes,
            corpus_id=plan.corpus_id,
            component_id=binding.component_id or "",
        )
        selected_nodes.update(nodes)

    result: list[int] = []
    for node in sorted(selected_nodes):
        try:
            node_type = otype_lookup(node)
        except Exception as error:
            raise ExactExecutionError(
                ExactExecutionProblem(
                    "loaded_api_unavailable",
                    "loaded node-type lookup failed",
                    corpus_id=plan.corpus_id,
                    component_id=binding.component_id,
                )
            ) from error
        if type(node_type) is not str or not node_type:
            _fail(
                "loaded_api_unavailable",
                "loaded node-type lookup returned a malformed value",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        if node_type == binding.node_type:
            result.append(node)
    return tuple(result)


def execute_exact_semantic(
    ir: CompiledSemanticIR,
    request: SemanticResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ExactExecutionResult:
    requested = _requested_corpora(request)
    normalized_contexts = _normalize_contexts(contexts)
    for corpus_id in requested:
        if corpus_id not in normalized_contexts:
            _fail(
                "missing_execution_context",
                "requested corpus has no loaded execution context",
                corpus_id=corpus_id,
            )

    variants = _select_variants(ir, requested)
    reports: dict[str, RuntimeEvaluationReport] = {}
    prerequisites = []
    for corpus_id in requested:
        context = normalized_contexts[corpus_id]
        report = evaluate_runtime_prerequisites(
            variants[corpus_id],
            _observation(context),
            source_contract=EXACT_EXECUTION_RUNTIME_SOURCE_CONTRACT,
            active_ontology_bundle_digest=context.active_ontology_bundle_digest,
        )
        reports[corpus_id] = report
        prerequisites.append(report.to_prerequisite())

    resolution = semantic_resolve(ir, request, tuple(prerequisites))
    executions: list[ExactCorpusExecution] = []
    for plan in resolution.plans:
        if plan.corpus_id not in reports or plan.corpus_id not in normalized_contexts:
            _fail(
                "plan_context_mismatch",
                "fresh resolver plan has no authorized runtime context",
                corpus_id=plan.corpus_id,
            )
        binding = plan.native_execution_binding
        if type(binding) is not NativeBindingIR:
            _fail(
                "unsupported_native_binding",
                "fresh resolver plan has an invalid native binding",
                corpus_id=plan.corpus_id,
            )
        if binding.execution_shape == "value-predicate":
            binding = _validate_value_predicate(plan)
        elif binding.execution_shape == "value-set-predicate":
            binding = _validate_value_set_predicate(plan)
        elif binding.execution_shape == "membership":
            binding = _validate_membership_binding(plan)
        elif binding.execution_shape == "edge-path":
            binding = _validate_edge_path_binding(plan)
        else:
            _fail(
                "unsupported_native_binding",
                "execution shape is not supported by the loaded runtime",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        components = _components(normalized_contexts[plan.corpus_id])
        component = components.get(binding.component_id or "")
        if component is None:
            _fail(
                "missing_execution_component",
                "fresh resolver plan references a component outside the execution context",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        if binding.execution_shape == "value-predicate":
            nodes = _execute_value_predicate(plan, component)
        elif binding.execution_shape == "value-set-predicate":
            nodes = _execute_value_set_predicate(plan, component)
        elif binding.execution_shape == "membership":
            nodes = _execute_membership(plan, component)
        else:
            nodes = _execute_edge_path(plan, component)
        executions.append(
            ExactCorpusExecution(
                corpus_id=plan.corpus_id,
                nodes=nodes,
                plan=plan,
                runtime_report=reports[plan.corpus_id],
            )
        )

    executions.sort(key=lambda row: _utf16(row.corpus_id))
    return ExactExecutionResult(
        execution_contract=EXACT_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(executions),
    )



def _execute_approximate_semantic_impl(
    ir: CompiledSemanticIR,
    request: ApproximateSemanticResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ApproximateExecutionResult:
    canonical_request = _validate_approximate_request(request)
    requested = canonical_request.corpora
    normalized_contexts = _normalize_contexts(contexts)
    for corpus_id in requested:
        if corpus_id not in normalized_contexts:
            _fail(
                "missing_execution_context",
                "requested corpus has no loaded execution context",
                corpus_id=corpus_id,
            )

    variants = _select_variants(ir, requested)
    reports: dict[str, RuntimeEvaluationReport] = {}
    prerequisites = []
    for corpus_id in requested:
        context = normalized_contexts[corpus_id]
        report = evaluate_runtime_prerequisites(
            variants[corpus_id],
            _observation(context),
            source_contract=APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT,
            active_ontology_bundle_digest=context.active_ontology_bundle_digest,
        )
        reports[corpus_id] = report
        prerequisites.append(report.to_prerequisite())

    resolution = semantic_resolve_approximate(
        ir,
        canonical_request,
        tuple(prerequisites),
    )
    executions: list[ApproximateCorpusExecution] = []
    for plan in resolution.plans:
        if plan.corpus_id not in reports or plan.corpus_id not in normalized_contexts:
            _fail(
                "plan_context_mismatch",
                "fresh approximate resolver plan has no authorized runtime context",
                corpus_id=plan.corpus_id,
            )
        binding = plan.native_execution_binding
        if type(binding) is not NativeBindingIR:
            _fail(
                "unsupported_native_binding",
                "fresh approximate resolver plan has an invalid native binding",
                corpus_id=plan.corpus_id,
            )
        if binding.execution_shape == "value-predicate":
            binding = _validate_value_predicate(plan)
        elif binding.execution_shape == "value-set-predicate":
            binding = _validate_value_set_predicate(plan)
        elif binding.execution_shape == "membership":
            binding = _validate_membership_binding(plan)
        elif binding.execution_shape == "edge-path":
            binding = _validate_edge_path_binding(plan)
        else:
            _fail(
                "unsupported_native_binding",
                "approximate execution shape is not supported by the loaded runtime",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        components = _components(normalized_contexts[plan.corpus_id])
        component = components.get(binding.component_id or "")
        if component is None:
            _fail(
                "missing_execution_component",
                "fresh approximate resolver plan references a component outside the execution context",
                corpus_id=plan.corpus_id,
                component_id=binding.component_id,
            )
        if binding.execution_shape == "value-predicate":
            nodes = _execute_value_predicate(plan, component)
        elif binding.execution_shape == "value-set-predicate":
            nodes = _execute_value_set_predicate(plan, component)
        elif binding.execution_shape == "membership":
            nodes = _execute_membership(plan, component)
        else:
            nodes = _execute_edge_path(plan, component)
        executions.append(
            ApproximateCorpusExecution(
                corpus_id=plan.corpus_id,
                nodes=nodes,
                plan=plan,
                runtime_report=reports[plan.corpus_id],
            )
        )

    executions.sort(key=lambda row: _utf16(row.corpus_id))
    return ApproximateExecutionResult(
        execution_contract=APPROXIMATE_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(executions),
    )


def execute_approximate_semantic(
    ir: CompiledSemanticIR,
    request: ApproximateSemanticResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ApproximateExecutionResult:
    try:
        return _execute_approximate_semantic_impl(ir, request, contexts)
    except ExactExecutionError as error:
        raise _translate_exact_execution_error(error) from error


EXACT_CONJUNCTION_EXECUTION_CONTRACT = "tfont-exact-semantic-conjunction-execution-v1"


@dataclass(frozen=True)
class ApproximateConjunctionCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plans: tuple[ApproximateNativePlan, ...]
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class ApproximateConjunctionExecutionResult:
    execution_contract: str
    resolution: ApproximateSemanticConjunctionResolutionResult
    corpora: tuple[ApproximateConjunctionCorpusExecution, ...]


@dataclass(frozen=True)
class ExactConjunctionCorpusExecution:
    corpus_id: str
    nodes: tuple[int, ...]
    plans: tuple[ExactNativePlan, ...]
    runtime_report: RuntimeEvaluationReport


@dataclass(frozen=True)
class ExactConjunctionExecutionResult:
    execution_contract: str
    resolution: SemanticConjunctionResolutionResult
    corpora: tuple[ExactConjunctionCorpusExecution, ...]


def _execute_exact_plan_in_context(
    plan: ExactNativePlan,
    context: LoadedCorpusContext,
) -> tuple[int, ...]:
    binding = plan.native_execution_binding
    if type(binding) is not NativeBindingIR:
        _fail(
            "unsupported_native_binding",
            "fresh resolver plan has an invalid native binding",
            corpus_id=plan.corpus_id,
        )
    if binding.execution_shape == "value-predicate":
        binding = _validate_value_predicate(plan)
    elif binding.execution_shape == "value-set-predicate":
        binding = _validate_value_set_predicate(plan)
    elif binding.execution_shape == "membership":
        binding = _validate_membership_binding(plan)
    elif binding.execution_shape == "edge-path":
        binding = _validate_edge_path_binding(plan)
    else:
        _fail(
            "unsupported_native_binding",
            "exact conjunction execution shape is not supported by the loaded runtime",
            corpus_id=plan.corpus_id,
            component_id=binding.component_id,
        )

    component = _components(context).get(binding.component_id or "")
    if component is None:
        _fail(
            "missing_execution_component",
            "fresh resolver plan references a component outside the execution context",
            corpus_id=plan.corpus_id,
            component_id=binding.component_id,
        )
    if binding.execution_shape == "value-predicate":
        return _execute_value_predicate(plan, component)
    if binding.execution_shape == "value-set-predicate":
        return _execute_value_set_predicate(plan, component)
    if binding.execution_shape == "membership":
        return _execute_membership(plan, component)
    return _execute_edge_path(plan, component)


def _validate_conjunction_node_domains(
    resolution: SemanticConjunctionResolutionResult,
) -> None:
    domains: dict[str, set[tuple[str, str]]] = {
        corpus_id: set() for corpus_id in resolution.request.corpora
    }
    for constituent in resolution.resolutions:
        for plan in constituent.plans:
            domains.setdefault(plan.corpus_id, set()).add(
                _execution_result_domain(plan)
            )

    for corpus_id in resolution.request.corpora:
        corpus_domains = domains.get(corpus_id, set())
        if len(corpus_domains) != 1:
            _fail(
                "incompatible_conjunction_node_domain",
                "exact conjunction requires one shared component and node type per corpus",
                corpus_id=corpus_id,
            )


def execute_exact_conjunction(
    ir: CompiledSemanticIR,
    request: SemanticConjunctionRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ExactConjunctionExecutionResult:
    if type(request) is not SemanticConjunctionRequest:
        raise TypeError("request must be SemanticConjunctionRequest")
    if type(request.corpora) is not tuple or not request.corpora:
        _fail(
            "invalid_execution_context",
            "request corpora must be a non-empty tuple",
        )
    if any(not _nonempty_string(corpus_id) for corpus_id in request.corpora):
        _fail(
            "invalid_execution_context",
            "request corpus IDs must be non-empty strings",
        )

    requested = tuple(sorted(set(request.corpora), key=_utf16))
    normalized_contexts = _normalize_contexts(contexts)
    for corpus_id in requested:
        if corpus_id not in normalized_contexts:
            _fail(
                "missing_execution_context",
                "requested corpus has no loaded execution context",
                corpus_id=corpus_id,
            )

    variants = _select_variants(ir, requested)
    reports: dict[str, RuntimeEvaluationReport] = {}
    prerequisites = []
    for corpus_id in requested:
        context = normalized_contexts[corpus_id]
        report = evaluate_runtime_prerequisites(
            variants[corpus_id],
            _observation(context),
            source_contract=EXACT_EXECUTION_RUNTIME_SOURCE_CONTRACT,
            active_ontology_bundle_digest=context.active_ontology_bundle_digest,
        )
        reports[corpus_id] = report
        prerequisites.append(report.to_prerequisite())

    resolution = semantic_resolve_conjunction(ir, request, tuple(prerequisites))
    _validate_conjunction_node_domains(resolution)
    by_corpus: dict[str, list[tuple[ExactNativePlan, tuple[int, ...]]]] = {
        corpus_id: [] for corpus_id in resolution.request.corpora
    }
    for constituent in resolution.resolutions:
        for plan in constituent.plans:
            context = normalized_contexts.get(plan.corpus_id)
            if context is None or plan.corpus_id not in reports:
                _fail(
                    "plan_context_mismatch",
                    "conjunction plan has no authorized runtime context",
                    corpus_id=plan.corpus_id,
                )
            nodes = _execute_exact_plan_in_context(plan, context)
            by_corpus.setdefault(plan.corpus_id, []).append((plan, nodes))

    executions: list[ExactConjunctionCorpusExecution] = []
    expected_plan_count = len(resolution.request.keys)
    for corpus_id in resolution.request.corpora:
        rows = by_corpus.get(corpus_id, [])
        if len(rows) != expected_plan_count:
            _fail(
                "plan_context_mismatch",
                "conjunction did not produce one exact plan per requested atom",
                corpus_id=corpus_id,
            )
        intersection = set(rows[0][1])
        for _plan, nodes in rows[1:]:
            intersection.intersection_update(nodes)
        executions.append(
            ExactConjunctionCorpusExecution(
                corpus_id=corpus_id,
                nodes=tuple(sorted(intersection)),
                plans=tuple(plan for plan, _nodes in rows),
                runtime_report=reports[corpus_id],
            )
        )

    executions.sort(key=lambda row: _utf16(row.corpus_id))
    return ExactConjunctionExecutionResult(
        execution_contract=EXACT_CONJUNCTION_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(executions),
    )


def _execute_approximate_conjunction_impl(
    ir: CompiledSemanticIR,
    request: ApproximateSemanticConjunctionRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ApproximateConjunctionExecutionResult:
    canonical_request = _validate_approximate_conjunction_request(request)
    requested = canonical_request.corpora
    normalized_contexts = _normalize_contexts(contexts)
    for corpus_id in requested:
        if corpus_id not in normalized_contexts:
            _fail(
                "missing_execution_context",
                "requested corpus has no loaded execution context",
                corpus_id=corpus_id,
            )

    variants = _select_variants(ir, requested)
    reports: dict[str, RuntimeEvaluationReport] = {}
    prerequisites = []
    for corpus_id in requested:
        context = normalized_contexts[corpus_id]
        report = evaluate_runtime_prerequisites(
            variants[corpus_id],
            _observation(context),
            source_contract=APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT,
            active_ontology_bundle_digest=context.active_ontology_bundle_digest,
        )
        reports[corpus_id] = report
        prerequisites.append(report.to_prerequisite())

    resolution = semantic_resolve_approximate_conjunction(
        ir,
        canonical_request,
        tuple(prerequisites),
    )
    _validate_conjunction_node_domains(resolution)

    by_corpus: dict[str, list[tuple[ApproximateNativePlan, tuple[int, ...]]]] = {
        corpus_id: [] for corpus_id in resolution.request.corpora
    }
    for constituent in resolution.resolutions:
        for plan in constituent.plans:
            context = normalized_contexts.get(plan.corpus_id)
            if context is None or plan.corpus_id not in reports:
                _fail(
                    "plan_context_mismatch",
                    "approximate conjunction plan has no authorized runtime context",
                    corpus_id=plan.corpus_id,
                )
            nodes = _execute_exact_plan_in_context(plan, context)
            by_corpus.setdefault(plan.corpus_id, []).append((plan, nodes))

    executions: list[ApproximateConjunctionCorpusExecution] = []
    expected_plan_count = len(resolution.request.keys)
    for corpus_id in resolution.request.corpora:
        rows = by_corpus.get(corpus_id, [])
        if len(rows) != expected_plan_count:
            _fail(
                "plan_context_mismatch",
                "conjunction did not produce one approximate plan per requested atom",
                corpus_id=corpus_id,
            )
        intersection = set(rows[0][1])
        for _plan, nodes in rows[1:]:
            intersection.intersection_update(nodes)
        executions.append(
            ApproximateConjunctionCorpusExecution(
                corpus_id=corpus_id,
                nodes=tuple(sorted(intersection)),
                plans=tuple(plan for plan, _nodes in rows),
                runtime_report=reports[corpus_id],
            )
        )

    executions.sort(key=lambda row: _utf16(row.corpus_id))
    return ApproximateConjunctionExecutionResult(
        execution_contract=APPROXIMATE_CONJUNCTION_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(executions),
    )


def execute_approximate_conjunction(
    ir: CompiledSemanticIR,
    request: ApproximateSemanticConjunctionRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ApproximateConjunctionExecutionResult:
    try:
        return _execute_approximate_conjunction_impl(ir, request, contexts)
    except ExactExecutionError as error:
        raise _translate_exact_execution_error(error) from error

def _reference_runtime_state(
    ir: CompiledSemanticIR,
    corpora: tuple[str, ...],
    contexts: Iterable[LoadedCorpusContext],
) -> tuple[
    dict[str, LoadedCorpusContext],
    dict[str, RuntimeEvaluationReport],
    tuple[Any, ...],
]:
    normalized_contexts = _normalize_contexts(contexts)
    for corpus_id in corpora:
        if corpus_id not in normalized_contexts:
            _fail(
                "missing_execution_context",
                "requested corpus has no loaded execution context",
                corpus_id=corpus_id,
            )

    variants = _select_variants(ir, corpora)
    reports: dict[str, RuntimeEvaluationReport] = {}
    prerequisites = []
    for corpus_id in corpora:
        context = normalized_contexts[corpus_id]
        report = evaluate_runtime_prerequisites(
            variants[corpus_id],
            _observation(context),
            source_contract=REFERENCE_EXECUTION_RUNTIME_SOURCE_CONTRACT,
            active_ontology_bundle_digest=context.active_ontology_bundle_digest,
        )
        reports[corpus_id] = report
        prerequisites.append(report.to_prerequisite())
    return normalized_contexts, reports, tuple(prerequisites)


def _execute_reference_plan(
    plan: AuthorityNativePlan | IdentityNativePlan | IdentifierNativePlan,
    context: LoadedCorpusContext,
) -> tuple[int, ...]:
    binding = plan.native_execution_binding
    if type(binding) is not NativeBindingIR:
        _fail(
            "unsupported_native_binding",
            "fresh reference resolver plan has an invalid native binding",
            corpus_id=plan.corpus_id,
        )
    if binding.execution_shape == "value-predicate":
        binding = _validate_value_predicate(plan)
    elif binding.execution_shape == "value-set-predicate":
        binding = _validate_value_set_predicate(plan)
    elif binding.execution_shape == "membership":
        binding = _validate_membership_binding(plan)
    elif binding.execution_shape == "edge-path":
        binding = _validate_edge_path_binding(plan)
    else:
        _fail(
            "unsupported_native_binding",
            "reference execution shape is not supported by the loaded runtime",
            corpus_id=plan.corpus_id,
            component_id=binding.component_id,
        )

    component = _components(context).get(binding.component_id or "")
    if component is None:
        _fail(
            "missing_execution_component",
            "fresh reference resolver plan references a component outside the execution context",
            corpus_id=plan.corpus_id,
            component_id=binding.component_id,
        )
    if binding.execution_shape == "value-predicate":
        return _execute_value_predicate(plan, component)
    if binding.execution_shape == "value-set-predicate":
        return _execute_value_set_predicate(plan, component)
    if binding.execution_shape == "membership":
        return _execute_membership(plan, component)
    return _execute_edge_path(plan, component)


def execute_exact_authority(
    ir: CompiledSemanticIR,
    request: AuthorityResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ExactAuthorityExecutionResult:
    canonical = _validate_authority_request(request)
    normalized, reports, prerequisites = _reference_runtime_state(
        ir, canonical.corpora, contexts
    )
    resolution = authority_resolve_exact(ir, canonical, prerequisites)
    rows = []
    for plan in resolution.plans:
        context = normalized.get(plan.corpus_id)
        if context is None or plan.corpus_id not in reports:
            _fail(
                "plan_context_mismatch",
                "fresh authority plan has no authorized runtime context",
                corpus_id=plan.corpus_id,
            )
        rows.append(
            ExactAuthorityCorpusExecution(
                corpus_id=plan.corpus_id,
                nodes=_execute_reference_plan(plan, context),
                plan=plan,
                runtime_report=reports[plan.corpus_id],
            )
        )
    rows.sort(key=lambda row: _utf16(row.corpus_id))
    return ExactAuthorityExecutionResult(
        execution_contract=EXACT_AUTHORITY_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(rows),
    )


def execute_approximate_authority(
    ir: CompiledSemanticIR,
    request: ApproximateAuthorityResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> ApproximateAuthorityExecutionResult:
    canonical = _validate_approximate_authority_request(request)
    normalized, reports, prerequisites = _reference_runtime_state(
        ir, canonical.corpora, contexts
    )
    resolution = authority_resolve_approximate(ir, canonical, prerequisites)
    rows = []
    for plan in resolution.plans:
        context = normalized.get(plan.corpus_id)
        if context is None or plan.corpus_id not in reports:
            _fail(
                "plan_context_mismatch",
                "fresh approximate authority plan has no authorized runtime context",
                corpus_id=plan.corpus_id,
            )
        rows.append(
            ApproximateAuthorityCorpusExecution(
                corpus_id=plan.corpus_id,
                nodes=_execute_reference_plan(plan, context),
                plan=plan,
                runtime_report=reports[plan.corpus_id],
            )
        )
    rows.sort(key=lambda row: _utf16(row.corpus_id))
    return ApproximateAuthorityExecutionResult(
        execution_contract=APPROXIMATE_AUTHORITY_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(rows),
    )


def execute_identity(
    ir: CompiledSemanticIR,
    request: IdentityResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> IdentityExecutionResult:
    canonical = _validate_identity_request(request)
    normalized, reports, prerequisites = _reference_runtime_state(
        ir, canonical.corpora, contexts
    )
    resolution = identity_resolve(ir, canonical, prerequisites)
    rows = []
    for plan in resolution.plans:
        context = normalized.get(plan.corpus_id)
        if context is None or plan.corpus_id not in reports:
            _fail(
                "plan_context_mismatch",
                "fresh identity plan has no authorized runtime context",
                corpus_id=plan.corpus_id,
            )
        rows.append(
            IdentityCorpusExecution(
                corpus_id=plan.corpus_id,
                nodes=_execute_reference_plan(plan, context),
                plan=plan,
                runtime_report=reports[plan.corpus_id],
            )
        )
    rows.sort(key=lambda row: _utf16(row.corpus_id))
    return IdentityExecutionResult(
        execution_contract=IDENTITY_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(rows),
    )


def execute_identifier(
    ir: CompiledSemanticIR,
    request: IdentifierResolveRequest,
    contexts: Iterable[LoadedCorpusContext],
) -> IdentifierExecutionResult:
    canonical = _validate_identifier_request(request)
    normalized, reports, prerequisites = _reference_runtime_state(
        ir, canonical.corpora, contexts
    )
    resolution = identifier_resolve(ir, canonical, prerequisites)
    rows = []
    for plan in resolution.plans:
        context = normalized.get(plan.corpus_id)
        if context is None or plan.corpus_id not in reports:
            _fail(
                "plan_context_mismatch",
                "fresh identifier plan has no authorized runtime context",
                corpus_id=plan.corpus_id,
            )
        rows.append(
            IdentifierCorpusExecution(
                corpus_id=plan.corpus_id,
                nodes=_execute_reference_plan(plan, context),
                plan=plan,
                runtime_report=reports[plan.corpus_id],
            )
        )
    rows.sort(key=lambda row: _utf16(row.corpus_id))
    return IdentifierExecutionResult(
        execution_contract=IDENTIFIER_EXECUTION_CONTRACT,
        resolution=resolution,
        corpora=tuple(rows),
    )

