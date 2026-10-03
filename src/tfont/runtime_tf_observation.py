from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .digests import canonical_json_bytes


_SAFE_JCS_INT_MAX = 2**53 - 1
_SAFE_JCS_INT_MIN = -_SAFE_JCS_INT_MAX


class LoadedTFObservation:
    """Narrow read-only adapter over already-loaded Text-Fabric-like APIs.

    The adapter never imports Text-Fabric and never loads features. Missing or
    unreadable loaded-API capabilities are represented as unknown observations.
    """

    def __init__(
        self,
        *,
        parent_manifest_digest: str,
        components: Mapping[str, tuple[str, Any]],
        extent_interpretations: Mapping[str, Mapping[str, str]] | None = None,
    ) -> None:
        if type(parent_manifest_digest) is not str or not parent_manifest_digest:
            raise ValueError("parent_manifest_digest must be a non-empty string")
        self.parent_manifest_digest = parent_manifest_digest
        self._components = dict(components)
        self._extent_interpretations = {
            component_id: dict(values)
            for component_id, values in (extent_interpretations or {}).items()
        }
        self._edge_value_cache: dict[
            tuple[str, str, str, str],
            tuple[str, str | None, tuple[str | int, ...], int],
        ] = {}

    def _component(self, component_id: str) -> tuple[str, Any] | None:
        value = self._components.get(component_id)
        if (
            type(value) is not tuple
            or len(value) != 2
            or type(value[0]) is not str
            or not value[0]
        ):
            return None
        return value

    def component(self, component_id: str) -> tuple[str, str | None]:
        value = self._component(component_id)
        if value is None:
            return ("absent", None) if component_id not in self._components else ("unknown", None)
        return ("present", value[0])

    def _api(self, component_id: str) -> Any | None:
        value = self._component(component_id)
        return None if value is None else value[1]

    @staticmethod
    def _loaded_names(api: Any, method_name: str) -> tuple[str, ...] | None:
        try:
            values = getattr(api, method_name)()
        except Exception:
            return None
        try:
            rows = tuple(values)
        except TypeError:
            return None
        if any(type(value) is not str for value in rows):
            return None
        return rows

    def node_type(self, component_id: str, node_type: str) -> str:
        api = self._api(component_id)
        if api is None:
            return "absent" if component_id not in self._components else "unknown"
        try:
            nodes = tuple(api.F.otype.s(node_type))
        except Exception:
            return "unknown"
        return "present" if nodes else "absent"

    def feature(self, component_id: str, node_type: str, feature: str) -> str:
        api = self._api(component_id)
        if api is None:
            return "absent" if component_id not in self._components else "unknown"
        loaded = self._loaded_names(api, "Fall")
        if loaded is None or feature not in loaded:
            return "unknown"
        try:
            nodes = tuple(api.F.otype.s(node_type))
            feature_api = getattr(api.F, feature)
        except Exception:
            return "unknown"
        if not nodes:
            return "absent"

        # A loaded node feature is corpus-global metadata. The P-002
        # feature-present assertion is narrower: it is scoped to one node type.
        # Prove that the feature has at least one defined value on that type;
        # do not treat the same feature on another node type as positive evidence.
        try:
            if any(feature_api.v(node) is not None for node in nodes):
                return "present"
        except Exception:
            return "unknown"
        return "unknown"

    def edge(self, component_id: str, edge: str, direction: str) -> str:
        api = self._api(component_id)
        if api is None:
            return "absent" if component_id not in self._components else "unknown"
        loaded = self._loaded_names(api, "Eall")
        if loaded is None or edge not in loaded:
            return "unknown"
        method = "f" if direction == "outgoing" else "t" if direction == "incoming" else None
        if method is None:
            return "unknown"
        try:
            edge_api = getattr(api.E, edge)
            getattr(edge_api, method)
        except Exception:
            return "unknown"
        return "present"

    def path(self, component_id: str, steps: tuple[tuple[str, str], ...]) -> str:
        if type(steps) is not tuple or not steps:
            return "unknown"
        results = tuple(self.edge(component_id, edge, direction) for edge, direction in steps)
        if any(result == "absent" for result in results):
            return "absent"
        if any(result != "present" for result in results):
            return "unknown"
        return "present"

    def values(
        self,
        component_id: str,
        node_type: str,
        feature: str,
    ) -> tuple[str, tuple[Any, ...]]:
        api = self._api(component_id)
        if api is None:
            return ("absent", ()) if component_id not in self._components else ("unknown", ())
        loaded = self._loaded_names(api, "Fall")
        if loaded is None or feature not in loaded:
            return ("unknown", ())
        try:
            nodes = tuple(api.F.otype.s(node_type))
            feature_api = getattr(api.F, feature)
            values = tuple(
                value
                for node in nodes
                for value in (feature_api.v(node),)
                if value is not None
            )
        except Exception:
            return ("unknown", ())
        return ("complete", values)

    def edge_values(
        self,
        component_id: str,
        edge: str,
        source_node_type: str,
        target_node_type: str,
    ) -> tuple[str, str | None, tuple[str | int, ...], int]:
        cache_key = (component_id, edge, source_node_type, target_node_type)
        cached = self._edge_value_cache.get(cache_key)
        if cached is not None:
            return cached

        api = self._api(component_id)
        if api is None:
            result = (
                ("absent", None, (), 0)
                if component_id not in self._components
                else ("unknown", None, (), 0)
            )
            self._edge_value_cache[cache_key] = result
            return result

        loaded = self._loaded_names(api, "Eall")
        if loaded is None or edge not in loaded:
            result = ("unknown", None, (), 0)
            self._edge_value_cache[cache_key] = result
            return result

        try:
            edge_api = getattr(api.E, edge)
            do_values = edge_api.doValues
            metadata = edge_api.meta
            items = edge_api.items
            otype = api.F.otype.v
        except Exception:
            result = ("unknown", None, (), 0)
            self._edge_value_cache[cache_key] = result
            return result

        if (
            do_values is not True
            or type(metadata) is not dict
            or metadata.get("valueType") not in {"str", "int"}
            or type(metadata.get("valueType")) is not str
            or not callable(items)
            or not callable(otype)
        ):
            result = ("unknown", None, (), 0)
            self._edge_value_cache[cache_key] = result
            return result

        value_type = metadata["valueType"]
        try:
            raw_items = items()
            rows = tuple(raw_items)
        except Exception:
            result = ("unknown", None, (), 0)
            self._edge_value_cache[cache_key] = result
            return result

        present: set[str | int] = set()
        missing_count = 0
        try:
            for source, targets in rows:
                if type(source) is not int or source <= 0:
                    raise ValueError("invalid edge source")
                if not isinstance(targets, Mapping):
                    raise ValueError("invalid valued edge target map")
                source_type = otype(source)
                if type(source_type) is not str or not source_type:
                    raise ValueError("invalid source node type")
                for target, value in targets.items():
                    if type(target) is not int or target <= 0:
                        raise ValueError("invalid edge target")
                    if value_type == "str":
                        if type(value) is not str:
                            raise ValueError("invalid string edge value")
                        value_present = True
                    else:
                        if value is None:
                            value_present = False
                        elif type(value) is int:
                            if value < _SAFE_JCS_INT_MIN or value > _SAFE_JCS_INT_MAX:
                                raise ValueError("unsafe integer edge value")
                            value_present = True
                        else:
                            raise ValueError("invalid integer edge value")
                    target_type = otype(target)
                    if type(target_type) is not str or not target_type:
                        raise ValueError("invalid target node type")
                    if (
                        source_type == source_node_type
                        and target_type == target_node_type
                    ):
                        if value_present:
                            present.add(value)
                        else:
                            missing_count += 1
        except Exception:
            result = ("unknown", None, (), 0)
            self._edge_value_cache[cache_key] = result
            return result

        try:
            ordered = tuple(sorted(present, key=canonical_json_bytes))
        except Exception:
            result = ("unknown", None, (), 0)
            self._edge_value_cache[cache_key] = result
            return result

        result = ("complete", value_type, ordered, missing_count)
        self._edge_value_cache[cache_key] = result
        return result

    def extent(self, component_id: str, node_type: str) -> tuple[str, str | None]:
        if component_id not in self._components:
            return ("absent", None)
        if self._component(component_id) is None:
            return ("unknown", None)
        component = self._extent_interpretations.get(component_id)
        if component is None:
            return ("unknown", None)
        value = component.get(node_type)
        if type(value) is not str or not value:
            return ("unknown", None)
        return ("known", value)
