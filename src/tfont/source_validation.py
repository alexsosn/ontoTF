from __future__ import annotations

import json
import math
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.error import YAMLError

JSONValue = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]

MAX_SOURCE_NESTING = 128

SCHEMA_FILES = {
    "profile": "profile.schema.json",
    "parent-component-manifest": "parent-component-manifest.schema.json",
    "ontology-lock": "ontology-lock.schema.json",
    "evidence": "evidence.schema.json",
    "review": "review.schema.json",
    "mapping": "mapping.schema.json",
    "compatibility-report": "compatibility-report.schema.json",
    "coverage-manifest": "coverage-manifest.schema.json",
}


@dataclass(frozen=True)
class ValidationProblem:
    category: str
    message: str
    source_name: str
    instance_path: tuple[str | int, ...] = ()
    schema_path: tuple[str | int, ...] = ()


class SourceValidationError(ValueError):
    def __init__(self, problem: ValidationProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


def _raise(category: str, message: str, source_name: str) -> None:
    raise SourceValidationError(
        ValidationProblem(category=category, message=message, source_name=source_name)
    )


def _raise_source_depth(source_name: str) -> None:
    _raise(
        "decode_error",
        f"source nesting exceeds maximum depth {MAX_SOURCE_NESTING}",
        source_name,
    )


def _raise_schema_recursion(source_name: str) -> None:
    _raise(
        "invalid_schema",
        "schema validation exceeded recursion capacity",
        source_name,
    )


def _plain_json(
    value: Any,
    *,
    source_name: str,
    active: set[int] | None = None,
    depth: int = 0,
) -> JSONValue:
    if active is None:
        active = set()

    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            _raise("non_json_value", "non-finite numeric value", source_name)
        return value
    if isinstance(value, list):
        identity = id(value)
        if identity in active:
            _raise("non_json_value", "recursive container alias", source_name)
        container_depth = depth + 1
        if container_depth > MAX_SOURCE_NESTING:
            _raise_source_depth(source_name)
        active.add(identity)
        try:
            return [
                _plain_json(
                    item,
                    source_name=source_name,
                    active=active,
                    depth=container_depth,
                )
                for item in value
            ]
        finally:
            active.remove(identity)
    if isinstance(value, dict):
        identity = id(value)
        if identity in active:
            _raise("non_json_value", "recursive container alias", source_name)
        container_depth = depth + 1
        if container_depth > MAX_SOURCE_NESTING:
            _raise_source_depth(source_name)
        active.add(identity)
        try:
            result: dict[str, JSONValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    _raise("non_json_value", "mapping keys must be strings", source_name)
                result[key] = _plain_json(
                    item,
                    source_name=source_name,
                    active=active,
                    depth=container_depth,
                )
            return result
        finally:
            active.remove(identity)

    _raise("non_json_value", f"unsupported value type: {type(value).__name__}", source_name)


class _JSONDuplicateKey(ValueError):
    pass


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _JSONDuplicateKey(key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON numeric constant: {value}")


def loads_source(
    text: str,
    *,
    format: Literal["yaml", "json"],
    source_name: str = "<memory>",
) -> JSONValue:
    if format == "json":
        try:
            parsed = json.loads(
                text,
                object_pairs_hook=_json_pairs,
                parse_constant=_reject_json_constant,
            )
        except _JSONDuplicateKey as exc:
            _raise("duplicate_key", f"duplicate mapping key: {exc}", source_name)
        except RecursionError:
            _raise_source_depth(source_name)
        except (json.JSONDecodeError, ValueError) as exc:
            _raise("decode_error", str(exc), source_name)
        return _plain_json(parsed, source_name=source_name)

    if format == "yaml":
        parser = YAML(typ="safe", pure=True)
        parser.allow_duplicate_keys = False
        try:
            parsed = parser.load(text)
        except DuplicateKeyError as exc:
            _raise("duplicate_key", str(exc), source_name)
        except RecursionError:
            _raise_source_depth(source_name)
        except YAMLError as exc:
            _raise("decode_error", str(exc), source_name)
        return _plain_json(parsed, source_name=source_name)

    _raise("decode_error", f"unsupported source format: {format}", source_name)


def load_source(path: str | Path) -> JSONValue:
    source_path = Path(path)
    source_name = str(source_path)
    try:
        text = source_path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        _raise("decode_error", str(exc), source_name)

    suffix = source_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        format: Literal["yaml", "json"] = "yaml"
    elif suffix == ".json":
        format = "json"
    else:
        _raise("decode_error", f"unsupported source suffix: {suffix or '<none>'}", source_name)
    return loads_source(text, format=format, source_name=source_name)


def _problem_path(path: Any) -> tuple[str | int, ...]:
    return tuple(path)


def _read_schema_bytes(
    filename: str,
    *,
    schema_root: str | Path | None,
) -> tuple[bytes, str]:
    if schema_root is not None:
        schema_path = Path(schema_root) / filename
        source_name = str(schema_path)
        try:
            return schema_path.read_bytes(), source_name
        except (OSError, ValueError) as exc:
            _raise("invalid_schema", str(exc), source_name)

    source_name = f"tfont:schemas/{filename}"
    try:
        return files("tfont").joinpath("schemas", filename).read_bytes(), source_name
    except OSError as exc:
        _raise("invalid_schema", str(exc), source_name)


def validate_source(
    data: JSONValue,
    schema_name: str,
    *,
    schema_root: str | Path | None = None,
    source_name: str | None = None,
) -> None:
    filename = SCHEMA_FILES.get(schema_name)
    if filename is None:
        _raise("unknown_schema", f"unknown schema: {schema_name}", schema_name)

    schema_bytes, schema_source_name = _read_schema_bytes(
        filename,
        schema_root=schema_root,
    )
    try:
        schema_text = schema_bytes.decode("utf-8-sig")
        schema = json.loads(
            schema_text,
            object_pairs_hook=_json_pairs,
            parse_constant=_reject_json_constant,
        )
    except RecursionError:
        _raise_schema_recursion(schema_source_name)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        _raise("invalid_schema", str(exc), schema_source_name)

    if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        _raise(
            "invalid_schema",
            "schema must declare JSON Schema Draft 2020-12",
            schema_source_name,
        )

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise SourceValidationError(
            ValidationProblem(
                category="invalid_schema",
                message=exc.message,
                source_name=schema_source_name,
                instance_path=_problem_path(exc.path),
                schema_path=_problem_path(exc.schema_path),
            )
        ) from exc
    except RecursionError:
        _raise_schema_recursion(schema_source_name)

    effective_source_name = schema_name if source_name is None else source_name
    normalized_data = _plain_json(data, source_name=effective_source_name)

    validator = Draft202012Validator(schema)
    try:
        errors = sorted(
            validator.iter_errors(normalized_data),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                tuple(str(part) for part in error.absolute_schema_path),
                error.message,
            ),
        )
    except RecursionError:
        _raise_schema_recursion(schema_source_name)

    if errors:
        error = errors[0]
        raise SourceValidationError(
            ValidationProblem(
                category="schema_validation",
                message=error.message,
                source_name=effective_source_name,
                instance_path=_problem_path(error.absolute_path),
                schema_path=_problem_path(error.absolute_schema_path),
            )
        )


def load_and_validate(
    path: str | Path,
    schema_name: str,
    *,
    schema_root: str | Path | None = None,
) -> JSONValue:
    source_path = Path(path)
    data = load_source(source_path)
    validate_source(
        data,
        schema_name,
        schema_root=schema_root,
        source_name=str(source_path),
    )
    return data
