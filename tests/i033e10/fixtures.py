"""Real immutable BHSA POS/OLiA evidence with a SYNTHETIC prior native-only release.

Never treat the hypothetical predecessor's review as a GitHub attestation.
This exercises transition semantics without manufacturing installed history.
"""
from __future__ import annotations

import copy

from tfont.release_registry import load_profile
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2


def synthetic_transition():
    bundle = load_profile("bhsa", release_id="0.3.0")
    published = next(
        x for x in bundle.mappings.data["mappings"]
        if x["mapping_id"] == "mapping:bhsa:olia-verb"
    )
    old = copy.deepcopy(published)
    old["mapping_id"] = "mapping:bhsa:native-sp-verb"
    old["native_state"] = "native-only"
    old["projections"] = []
    old["evidence"] = [
        x for x in old["evidence"] if x["evidence_id"].startswith("evidence:bhsa:")
    ]
    old["rationale"] = (
        "SYNTHETIC predecessor fixture: unprojected word.sp=verb native annotation;"
        " NEVER a historically installed or independently approved mapping."
    )
    old["mapping_semantic_digest"] = mapping_semantic_digest_v2(old)
    old["review"]["reviewed_mapping_digest"] = old["mapping_semantic_digest"]
    candidate = copy.deepcopy(published)
    candidate["mapping_id"] = "mapping:bhsa:olia-verb-after-native"
    del candidate["review"]
    del candidate["projections"][0]["review"]
    candidate["mapping_semantic_digest"] = mapping_semantic_digest_v2(candidate)
    evidence = {item.data["evidence_id"]: copy.deepcopy(item.data)
                for item in bundle.evidences}
    source = evidence["evidence:bhsa:word-sp-verb-code"]
    ontology = evidence["evidence:olia:verb-class"]
    lock = copy.deepcopy(bundle.ontology_locks[0].data)
    return old, candidate, source, ontology, lock
