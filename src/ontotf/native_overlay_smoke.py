"""Read-only TF-native smoke checks for accepted, UNINSTALLED overlay candidates.

This module cannot install mappings, attest a workflow, or grant any shared
ontology target. A returned count means a preloaded TF API had nodes whose
native word feature matched a *source-bound* native-only selector.
"""
from __future__ import annotations

from typing import Any

from .overlay_handoff import verify_overlay_handoff_integrity
from .parent_identity import parent_manifest_digest
from .release_registry import load_profile
from .semantic_execution import LoadedComponentContext, LoadedCorpusContext

CONTRACT = "tfont-native-overlay-smoke-v1"
SAMPLE_LIMIT = 5


class NativeOverlaySmokeError(ValueError):
    """Untrusted, mismatched or unavailable loaded TF observations."""


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise NativeOverlaySmokeError(message)


def inspect_native_overlay(pack: dict[str, Any], loaded: LoadedCorpusContext) -> dict[str, Any]:
    """Observe one corpus' accepted native-only selectors in ONE word scan.

    No TF import, no feature loading, no PR Python execution, no network and no
    inference of an OLiA equivalence. The caller supplies an already loaded
    TF-like API whose content digest has independently been checked.
    """
    try:
        verify_overlay_handoff_integrity(pack)
    except (ValueError, TypeError, KeyError) as exc:
        raise NativeOverlaySmokeError("unsealed candidate pack failed structural verification") from exc
    _need(type(loaded) is LoadedCorpusContext, "loaded TF context has the wrong type")
    _need(type(pack["counts"]) is dict and pack["counts"]["exact"] == 0,
          "native smoke cannot execute exact ontology projections")
    corpus = loaded.corpus_id
    _need(type(corpus) is str and corpus in {"bhsa", "syriac"},
          "only source-pinned BHSA/Syriac pilot corpora supported")
    candidates = [c for c in pack["corpora"] if c["corpus_id"] == corpus]
    _need(len(candidates) == 1, "candidate pack does not contain requested corpus")
    candidate = candidates[0]
    _need(candidate["base_release"] == "0.4.0", "pilot release differs from installed base")

    base = load_profile(corpus, release_id="0.4.0")
    parent = base.expected_parent_manifest.data
    _need(loaded.parent_manifest_digest == parent_manifest_digest(parent),
          "loaded TF parent manifest does not match frozen source")
    expected = {row["component_id"]: row["content_digest"] for row in parent["components"]}
    _need(len(expected) == len(parent["components"])
          and type(loaded.components) is tuple
          and len(loaded.components) == len(expected),
          "TF components missing, duplicated or unexpected")
    component_by_id = {}
    for component in loaded.components:
        _need(type(component) is LoadedComponentContext
              and component.component_id in expected
              and component.component_id not in component_by_id
              and component.content_digest == expected[component.component_id],
              "loaded TF component identity does not match pinned original")
        component_by_id[component.component_id] = component
    _need(set(component_by_id) == set(expected), "TF component identity mismatch")

    rows = sorted(candidate["mappings"], key=lambda x: x["mapping_id"])
    _need(bool(rows), "candidate corpus has no accepted native selectors")
    selected: dict[str, dict[str, Any]] = {}
    component_ids = set()
    for row in rows:
        _need(row["native_state"] == "native-only"
              and not row["projections"],
              "positive/shared-target mapping is not a native-only selector")
        selector = row["native_binding"]
        component_id = selector["component_id"]
        _need(component_id in component_by_id
              and selector["node_type"] == "word"
              and selector["feature"] == "sp"
              and selector["execution_shape"] == "value-predicate"
              and type(selector["value"]) is str,
              "non-native or unsupported selector is not executable")
        value = selector["value"]
        _need(value not in selected, "duplicate native selector value")
        component_ids.add(component_id)
        selected[value] = {
            "mapping_id": row["mapping_id"],
            "native_state": "native-only",
            "value": value,
            "count": 0,
            "sample_nodes": [],
        }
    _need(len(component_ids) == 1, "pilot native selectors span multiple TF components")
    api = component_by_id[next(iter(component_ids))].api
    try:
        loaded_features = api.Fall()
        _need(type(loaded_features) in (tuple, list, set)
              and "sp" in loaded_features
              and "otype" in loaded_features,
              "TF sp/otype features must already be loaded")
        word_nodes = api.F.otype.s("word")
        _need(word_nodes is not None, "loaded TF word nodes unavailable")
    except NativeOverlaySmokeError:
        raise
    except Exception as exc:
        raise NativeOverlaySmokeError("cannot read loaded TF word/sp features") from exc

    scanned = 0
    previous = 0
    try:
        for node in word_nodes:
            _need(type(node) is int and node > previous,
                  "TF word nodes must be strictly increasing positive IDs")
            previous = node
            scanned += 1
            value = api.F.sp.v(node)
            _need(value is None or type(value) is str,
                  "TF sp feature values must be strings or undefined")
            if value in selected:
                result = selected[value]
                result["count"] += 1
                if len(result["sample_nodes"]) < SAMPLE_LIMIT:
                    result["sample_nodes"].append(node)
    except NativeOverlaySmokeError:
        raise
    except Exception as exc:
        raise NativeOverlaySmokeError("unreadable or incomplete preloaded TF word/sp data") from exc
    _need(scanned > 0, "no loaded TF word nodes to inspect")
    return {
        "contract": CONTRACT,
        "authority": "diagnostic-only-not-a-release",
        "corpus_id": corpus,
        "pack_digest": pack["content_digest"],
        "parent_manifest_digest": loaded.parent_manifest_digest,
        "scanned_words": scanned,
        "shared_target_count": 0,
        "selectors": list(selected.values()),
    }


__all__ = ["NativeOverlaySmokeError", "inspect_native_overlay"]
