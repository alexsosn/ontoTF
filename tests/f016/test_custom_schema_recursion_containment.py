from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ontotf.source_validation as source_validation
from ontotf.source_validation import SCHEMA_FILES, SourceValidationError, validate_source

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_RECURSION_MESSAGE = "schema validation exceeded recursion capacity"


def write_schema(root: Path, schema: dict, schema_name: str = "profile") -> Path:
    path = root / SCHEMA_FILES[schema_name]
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


def simple_object_schema(*, required: list[str] | None = None) -> dict:
    schema: dict = {"$schema": DRAFT_2020_12, "type": "object"}
    if required is not None:
        schema["required"] = required
    return schema


def is_schema_self_validation(instance) -> bool:  # noqa: ANN001
    return isinstance(instance, dict) and instance.get("$schema") == DRAFT_2020_12


class CustomSchemaRecursionControls(unittest.TestCase):
    def test_invalid_utf8_custom_schema_remains_invalid_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / SCHEMA_FILES["profile"]
            path.write_bytes(b"\xff")
            with self.assertRaises(SourceValidationError) as raised:
                validate_source({}, "profile", schema_root=root)
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(raised.exception.problem.source_name, str(path))

    def test_malformed_json_custom_schema_remains_invalid_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / SCHEMA_FILES["profile"]
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(SourceValidationError) as raised:
                validate_source({}, "profile", schema_root=root)
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(raised.exception.problem.source_name, str(path))

    def test_ordinary_schema_error_keeps_paths_and_schema_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_schema(
                root,
                {"$schema": DRAFT_2020_12, "type": 42},
            )
            with self.assertRaises(SourceValidationError) as raised:
                validate_source({}, "profile", schema_root=root)
        problem = raised.exception.problem
        self.assertEqual(problem.category, "invalid_schema")
        self.assertEqual(problem.source_name, str(path))
        self.assertTrue(problem.schema_path)

    def test_valid_custom_schema_invalid_instance_keeps_instance_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_schema(root, simple_object_schema(required=["required_field"]))
            with self.assertRaises(SourceValidationError) as raised:
                validate_source(
                    {},
                    "profile",
                    schema_root=root,
                    source_name="instance.json",
                )
        self.assertEqual(raised.exception.problem.category, "schema_validation")
        self.assertEqual(raised.exception.problem.source_name, "instance.json")

    def test_source_preflight_wins_before_validator_traversal(self):
        recursive: dict = {}
        recursive["self"] = recursive
        original_iter_errors = source_validation.Draft202012Validator.iter_errors

        def must_not_run_for_source(self, instance):  # noqa: ANN001
            if is_schema_self_validation(instance):
                return original_iter_errors(self, instance)
            raise AssertionError("source iter_errors must not run before source preflight")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_schema(root, simple_object_schema())
            with mock.patch.object(
                source_validation.Draft202012Validator,
                "iter_errors",
                new=must_not_run_for_source,
            ):
                with self.assertRaises(SourceValidationError) as raised:
                    validate_source(
                        recursive,  # type: ignore[arg-type]
                        "profile",
                        schema_root=root,
                        source_name="recursive-instance.json",
                    )
        self.assertEqual(raised.exception.problem.category, "non_json_value")
        self.assertEqual(raised.exception.problem.source_name, "recursive-instance.json")

    def test_packaged_schema_loading_remains_unchanged(self):
        with self.assertRaises(SourceValidationError) as raised:
            validate_source({}, "profile")
        self.assertEqual(raised.exception.problem.category, "schema_validation")
        self.assertEqual(raised.exception.problem.source_name, "profile")


class CustomSchemaRecursionREDTests(unittest.TestCase):
    def assert_schema_recursion(self, callable_) -> SourceValidationError:
        with self.assertRaises(SourceValidationError) as raised:
            callable_()
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(raised.exception.problem.message, SCHEMA_RECURSION_MESSAGE)
        return raised.exception

    def test_schema_json_parser_recursion_is_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_schema(root, simple_object_schema())
            with mock.patch.object(
                source_validation.json,
                "loads",
                side_effect=RecursionError("injected parser recursion"),
            ):
                error = self.assert_schema_recursion(
                    lambda: validate_source({}, "profile", schema_root=root)
                )
        self.assertEqual(error.problem.source_name, str(path))

    def test_check_schema_recursion_is_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_schema(root, simple_object_schema())
            with mock.patch.object(
                source_validation.Draft202012Validator,
                "check_schema",
                side_effect=RecursionError("injected check recursion"),
            ):
                error = self.assert_schema_recursion(
                    lambda: validate_source({}, "profile", schema_root=root)
                )
        self.assertEqual(error.problem.source_name, str(path))

    def test_lazy_iter_errors_recursion_is_contained_after_preflight(self):
        state = {"called": False, "advanced": False}
        original_iter_errors = source_validation.Draft202012Validator.iter_errors

        def lazy_iter_errors(self, instance):  # noqa: ANN001
            if is_schema_self_validation(instance):
                return original_iter_errors(self, instance)
            state["called"] = True

            def recurse_on_advance():
                state["advanced"] = True
                raise RecursionError("injected traversal recursion")
                yield None

            return recurse_on_advance()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_schema(root, simple_object_schema())
            with mock.patch.object(
                source_validation.Draft202012Validator,
                "iter_errors",
                new=lazy_iter_errors,
            ):
                error = self.assert_schema_recursion(
                    lambda: validate_source(
                        {},
                        "profile",
                        schema_root=root,
                        source_name="shallow-instance.json",
                    )
                )
        self.assertTrue(state["called"])
        self.assertTrue(state["advanced"])
        self.assertEqual(error.problem.source_name, str(path))


if __name__ == "__main__":
    unittest.main()
