from copy import deepcopy
import hashlib
import re

import pytest

from scripts.research.r015_bundle_id import bridge_content_digest, bundle_digest
from ontotf.digests import canonical_json_bytes


DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _lock(lock_id: str, *, release: str, terms_used: list[str]) -> dict:
    return {
        "lock_id": lock_id,
        "ontology_id": lock_id,
        "support_tier": "core",
        "term_namespace": f"{lock_id}:",
        "release": release,
        "source_uri": f"https://example.org/{lock_id}/{release}",
        "content_digest": _digest(lock_id),
        "license": "test-license",
        "terms_used": list(terms_used),
    }


def _scope():
    # U+10000 sorts before U+E000 under RFC 8785 UTF-16 ordering, while Python
    # code-point ordering does the opposite. The extra keys force a real JCS check.
    return {
        "source_term": "old:F28",
        "target_term": "new:F28",
        "relation": "reviewed-continuity",
        "\ue000": "bmp-private-use",
        "\U00010000": "astral",
    }


def _bridge():
    return {
        "bridge_id": "f28",
        "source_lock_id": "old",
        "source_lock_release": "1.0",
        "source_lock_digest": _digest("old"),
        "target_lock_id": "new",
        "target_lock_release": "2.0",
        "target_lock_digest": _digest("new"),
        "scope": _scope(),
        "compatibility": "compatible",
        "evidence_id": "evidence:f28",
        "evidence_digest": _digest("evidence"),
        "runtime_strength": "exact",
        "runtime_limitations": ["term scoped"],
        "review_status": "reviewed",
        "review_id": "review:f28",
        "reviewer_id": "github:reviewer",
        "reviewed_at": "2026-09-07T15:00:00Z",
    }


def _semantic_bridge_payload(bridge):
    fields = (
        "source_lock_id",
        "source_lock_release",
        "source_lock_digest",
        "target_lock_id",
        "target_lock_release",
        "target_lock_digest",
        "assertion_kind",
        "scope",
        "compatibility",
        "evidence_id",
        "evidence_digest",
        "runtime_strength",
        "runtime_limitations",
    )
    return {key: bridge[key] for key in fields if key in bridge}


def _bundle():
    bridge = _bridge()
    bridge["digest"] = bridge_content_digest(bridge)
    bridge["reviewed_content_digest"] = bridge["digest"]
    return {
        "schema_version": 1,
        "profile_contracts": ["written-text@1"],
        "ontology_locks": [
            _lock("consumer", release="1.0", terms_used=["consumer:TX1"]),
            _lock("old", release="1.0", terms_used=["old:F28"]),
            _lock("new", release="2.0", terms_used=["new:F28"]),
        ],
        "bridge_locks": [bridge],
        "dependency_edges": [
            {
                "id": "edge",
                "consumer": "consumer",
                "requires": "old",
                "satisfied_by": "bridge:f28",
                "required_bridge_scope": _scope(),
                "active": True,
            }
        ],
    }


def test_bridge_digest_is_sha256_of_i002_jcs_bytes():
    bridge = _bridge()
    expected = "sha256:" + hashlib.sha256(
        canonical_json_bytes(_semantic_bridge_payload(bridge))
    ).hexdigest()
    assert bridge_content_digest(bridge) == expected
    assert DIGEST_RE.fullmatch(expected)


def test_bundle_digest_uses_i002_jcs_and_has_canonical_digest_shape():
    result = bundle_digest(_bundle())
    assert DIGEST_RE.fullmatch(result)


def test_profile_contract_set_order_uses_i002_utf16_semantics():
    a = _bundle()
    a["profile_contracts"] = ["\ue000", "\U00010000"]
    b = deepcopy(a)
    b["profile_contracts"].reverse()
    assert bundle_digest(a) == bundle_digest(b)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_lock_digest", "sha256:not-hex"),
        ("target_lock_digest", "sha256:ABCDEF"),
        ("evidence_digest", "not-a-digest"),
    ],
)
def test_bridge_digest_fields_must_use_i002_sha256_representation(field, value):
    bundle = _bundle()
    bridge = bundle["bridge_locks"][0]
    bridge[field] = value
    bridge["digest"] = bridge_content_digest(bridge)
    bridge["reviewed_content_digest"] = bridge["digest"]
    with pytest.raises(ValueError, match="digest"):
        bundle_digest(bundle)


def test_ontology_lock_content_digest_must_use_i002_sha256_representation():
    bundle = {
        "schema_version": 1,
        "profile_contracts": ["linguistic@1"],
        "ontology_locks": [
            {
                "lock_id": "olia",
                "ontology_id": "olia",
                "support_tier": "core",
                "term_namespace": "http://purl.org/olia/olia.owl#",
                "release": "current-pinned",
                "source_uri": "http://purl.org/olia/olia.owl",
                "content_digest": "sha256:fake",
                "license": "CC-BY-3.0",
                "terms_used": ["http://purl.org/olia/olia.owl#Noun"],
            }
        ],
        "bridge_locks": [],
        "dependency_edges": [],
    }
    with pytest.raises(ValueError, match="content_digest|digest"):
        bundle_digest(bundle)
