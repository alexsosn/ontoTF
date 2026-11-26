from __future__ import annotations

import unittest

import ontotf.runtime_prerequisites as runtime


class NodeFeature:
    def __init__(self, values):
        self.values = dict(values)

    def v(self, node):
        return self.values.get(node)


class OtypeFeature:
    def __init__(self, by_type):
        self.by_type = {key: tuple(value) for key, value in by_type.items()}

    def s(self, node_type):
        return self.by_type.get(node_type, ())


class EdgeFeature:
    def f(self, node):
        return ()

    def t(self, node):
        return ()


class Namespace:
    pass


class FakeLoadedApi:
    def __init__(self):
        self.F = Namespace()
        self.E = Namespace()
        self.F.otype = OtypeFeature({"word": (1, 2, 3)})
        self.F.sp = NodeFeature({1: "subs", 2: "verb", 3: None})
        self.E.mother = EdgeFeature()
        self.loaded_nodes = ("otype", "sp")
        self.loaded_edges = ("oslots", "mother")
        self.load_calls = 0

    def Fall(self):
        return self.loaded_nodes

    def Eall(self):
        return self.loaded_edges

    def load(self, *args, **kwargs):
        self.load_calls += 1
        raise AssertionError("I-007 adapter must never load features")


class BrokenLoadedApi(FakeLoadedApi):
    def Fall(self):
        raise RuntimeError("loaded API unavailable")


class I007LoadedTFAdapterRedTests(unittest.TestCase):
    def make_adapter(self, api=None, *, extent=None):
        api = api or FakeLoadedApi()
        adapter = runtime.LoadedTFObservation(
            parent_manifest_digest="sha256:" + "a" * 64,
            components={"bhsa-tf": ("sha256:" + "b" * 64, api)},
            extent_interpretations=extent or {},
        )
        return adapter, api

    def test_component_identity_comes_from_supplied_observed_manifest(self):
        adapter, _ = self.make_adapter()
        self.assertEqual(
            adapter.component("bhsa-tf"),
            ("present", "sha256:" + "b" * 64),
        )
        self.assertEqual(adapter.component("missing"), ("absent", None))

    def test_node_type_and_loaded_feature_are_observed_without_loading(self):
        adapter, api = self.make_adapter()
        self.assertEqual(adapter.node_type("bhsa-tf", "word"), "present")
        self.assertEqual(adapter.node_type("bhsa-tf", "phrase"), "absent")
        self.assertEqual(adapter.feature("bhsa-tf", "word", "sp"), "present")
        self.assertEqual(api.load_calls, 0)

    def test_feature_absent_from_loaded_api_is_unknown_not_autoloaded(self):
        adapter, api = self.make_adapter()
        self.assertEqual(adapter.feature("bhsa-tf", "word", "lemma"), "unknown")
        self.assertEqual(adapter.values("bhsa-tf", "word", "lemma"), ("unknown", ()))
        self.assertEqual(api.load_calls, 0)

    def test_loaded_feature_does_not_count_for_unrelated_node_type(self):
        api = FakeLoadedApi()
        api.F.otype = OtypeFeature({"word": (1,), "phrase": (2,)})
        api.F.sp = NodeFeature({2: "phrase-only"})
        adapter, _ = self.make_adapter(api)
        self.assertEqual(adapter.feature("bhsa-tf", "phrase", "sp"), "present")
        self.assertEqual(adapter.feature("bhsa-tf", "word", "sp"), "unknown")
        self.assertEqual(api.load_calls, 0)

    def test_missing_component_is_known_absent_for_value_and_extent_observation(self):
        adapter, _ = self.make_adapter()
        self.assertEqual(adapter.values("missing", "word", "sp"), ("absent", ()))
        self.assertEqual(adapter.extent("missing", "word"), ("absent", None))

    def test_values_enumerate_nonmissing_values_for_declared_node_type(self):
        adapter, _ = self.make_adapter()
        state, values = adapter.values("bhsa-tf", "word", "sp")
        self.assertEqual(state, "complete")
        self.assertEqual(values, ("subs", "verb"))

    def test_edge_direction_and_path_are_execution_shape_availability(self):
        adapter, _ = self.make_adapter()
        self.assertEqual(adapter.edge("bhsa-tf", "mother", "outgoing"), "present")
        self.assertEqual(adapter.edge("bhsa-tf", "mother", "incoming"), "present")
        self.assertEqual(adapter.edge("bhsa-tf", "missing", "outgoing"), "unknown")
        self.assertEqual(
            adapter.path("bhsa-tf", (("mother", "outgoing"), ("mother", "incoming"))),
            "present",
        )
        self.assertEqual(
            adapter.path("bhsa-tf", (("mother", "outgoing"), ("missing", "incoming"))),
            "unknown",
        )

    def test_extent_uses_only_explicit_local_metadata(self):
        adapter, _ = self.make_adapter(extent={"bhsa-tf": {"word": "occurrenceSet"}})
        self.assertEqual(adapter.extent("bhsa-tf", "word"), ("known", "occurrenceSet"))
        self.assertEqual(adapter.extent("bhsa-tf", "phrase"), ("unknown", None))

    def test_api_failure_becomes_unknown_and_never_triggers_loading(self):
        adapter, api = self.make_adapter(BrokenLoadedApi())
        self.assertEqual(adapter.feature("bhsa-tf", "word", "sp"), "unknown")
        self.assertEqual(adapter.values("bhsa-tf", "word", "sp"), ("unknown", ()))
        self.assertEqual(api.load_calls, 0)

    def test_adapter_does_not_import_or_require_text_fabric_package(self):
        adapter, _ = self.make_adapter()
        self.assertEqual(adapter.node_type("bhsa-tf", "word"), "present")


if __name__ == "__main__":
    unittest.main()
