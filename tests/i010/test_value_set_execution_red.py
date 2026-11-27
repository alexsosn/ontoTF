from __future__ import annotations

import copy
import unittest

from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import noun_semantic_key
from ontotf.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1
from ontotf.semantic_execution import (
    ExactExecutionError,
    LoadedComponentContext,
    LoadedCorpusContext,
    execute_exact_semantic,
)
from ontotf.semantic_ir import compile_semantic_ir
from ontotf.semantic_resolver import SemanticResolveRequest, SemanticResolutionError
from ontotf.semantic_validation import SemanticValidationError, validate_semantic_bundle


def _refresh_mapping(mapping):
    for projection in mapping["projections"]:
        projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
        projection["review"]["reviewed_mapping_digest"] = projection[
            "projection_semantic_digest"
        ]
    mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
    mapping["review"]["reviewed_mapping_digest"] = mapping["mapping_semantic_digest"]


def _value_set_sources(
    values=("subs", "nmpr"),
    dependency_values=("subs", "nmpr"),
):
    sources = noun_sources("bhsa", parent_char="a")
    original = sources["profile"]["dependencies"][0]
    dependencies = []
    for value in dependency_values:
        dependency = copy.deepcopy(original)
        dependency["dependency_id"] = f"dep:bhsa:word-sp:{value}"
        dependency["assertion"]["value"] = value
        dependencies.append(dependency)
    sources["profile"]["dependencies"] = dependencies

    mapping = sources["mappings"]["mappings"][0]
    mapping["native_dependencies"] = [row["dependency_id"] for row in dependencies]
    for binding in (
        mapping["native_binding"],
        mapping["projections"][0]["native_execution_binding"],
    ):
        binding.pop("value")
        binding["values"] = list(values)
        binding["execution_shape"] = "value-set-predicate"
    _refresh_mapping(mapping)
    return sources


def _value_set_bundle(values=("subs", "nmpr")):
    sources = _value_set_sources(values)
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


class _Feature:
    def __init__(self, values, selectors):
        self._values = values
        self._selectors = selectors

    def v(self, node):
        return self._values.get(node)

    def s(self, value):
        return self._selectors.get(value, ())


class _Otype:
    def __init__(self, types):
        self._types = types

    def v(self, node):
        return self._types.get(node)

    def s(self, node_type):
        return tuple(node for node, value in self._types.items() if value == node_type)


class _API:
    def __init__(self, *, duplicate_single_selector=False, missing_nmpr=False):
        values = {1: "subs", 2: "nmpr", 3: "subs", 4: "verb", 5: "nmpr"}
        if missing_nmpr:
            values[2] = "verb"
        selectors = {
            "subs": (1, 1) if duplicate_single_selector else (3, 1),
            "nmpr": (5, 2, 3),
        }
        self.F = type(
            "Features",
            (),
            {
                "sp": _Feature(values, selectors),
                "otype": _Otype({1: "word", 2: "word", 3: "word", 4: "word", 5: "lex"}),
            },
        )()

    def Fall(self):
        return ("otype", "sp")


def _compiled(values=("subs", "nmpr")):
    return compile_semantic_ir((_value_set_bundle(values),))


def _context(ir, api):
    variant = ir.variants[0]
    return LoadedCorpusContext(
        corpus_id="bhsa",
        parent_manifest_digest=variant.key.expected_parent_manifest_digest,
        components=(
            LoadedComponentContext(
                component_id="bhsa-tf",
                content_digest="sha256:" + "a" * 64,
                api=api,
            ),
        ),
    )


def _request():
    return SemanticResolveRequest(key=noun_semantic_key(), corpora=("bhsa",))


class I010ValueSetExecutionTests(unittest.TestCase):
    def test_mapping_semantic_digest_is_invariant_to_selected_value_order(self):
        left = _value_set_bundle(("subs", "nmpr"))
        right = _value_set_bundle(("nmpr", "subs"))
        self.assertEqual(left.mapping_semantic_digests, right.mapping_semantic_digests)

    def test_selected_value_order_does_not_change_plan_or_resolution_identity(self):
        left_ir = _compiled(("subs", "nmpr"))
        right_ir = _compiled(("nmpr", "subs"))
        left = execute_exact_semantic(
            left_ir,
            _request(),
            (_context(left_ir, _API()),),
        )
        right = execute_exact_semantic(
            right_ir,
            _request(),
            (_context(right_ir, _API()),),
        )
        self.assertEqual(
            left.resolution.plans[0].plan_fingerprint,
            right.resolution.plans[0].plan_fingerprint,
        )
        self.assertEqual(
            left.resolution.resolution_fingerprint,
            right.resolution.resolution_fingerprint,
        )
        self.assertEqual(left.corpora[0].nodes, right.corpora[0].nodes)

    def test_value_set_requires_dependency_for_every_selected_value(self):
        sources = _value_set_sources(dependency_values=("subs",))
        validate_structural_sources(sources)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(sources))
        self.assertEqual(raised.exception.problem.category, "native_semantics_unproven")

    def test_projection_value_set_cannot_execute_value_outside_authorized_dependencies(self):
        sources = _value_set_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["native_execution_binding"]["values"] = ["subs", "verb"]
        _refresh_mapping(sources["mappings"]["mappings"][0])
        validate_structural_sources(sources)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(sources))
        self.assertEqual(raised.exception.problem.category, "native_semantics_unproven")

    def test_value_set_resolves_as_one_plan_and_executes_deterministic_union(self):
        ir = _compiled()
        result = execute_exact_semantic(ir, _request(), (_context(ir, _API()),))
        self.assertEqual(len(result.resolution.plans), 1)
        binding = result.resolution.plans[0].native_execution_binding
        self.assertEqual(binding.values, ("nmpr", "subs"))
        self.assertEqual(result.corpora[0].nodes, (1, 2, 3))

    def test_missing_selected_native_value_fails_runtime_authorization(self):
        ir = _compiled()
        with self.assertRaises(SemanticResolutionError) as raised:
            execute_exact_semantic(
                ir,
                _request(),
                (_context(ir, _API(missing_nmpr=True)),),
            )
        # I-007 treats any failed declared dependency as an incompatible loaded
        # parent before I-006 can authorize a plan. Preserve that fail-closed
        # precedence rather than weakening runtime state for this new predicate.
        self.assertEqual(raised.exception.problem.category, "parent_incompatible")

    def test_duplicate_inside_one_selector_still_fails_before_union(self):
        ir = _compiled()
        with self.assertRaises(ExactExecutionError) as raised:
            execute_exact_semantic(
                ir,
                _request(),
                (_context(ir, _API(duplicate_single_selector=True)),),
            )
        self.assertEqual(raised.exception.problem.category, "invalid_result_nodes")
