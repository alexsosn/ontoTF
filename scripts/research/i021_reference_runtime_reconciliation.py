"""I-021 research reconciliation for authority/identity/identifier runtime.

Non-production probe. It demonstrates the current compiled index boundary and
the execution-authority gap for ExternalReferenceIR rows.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.i005._fixtures import (
    AUTHORITY_NOUN,
    catalogue_reference,
    entity_identity_reference,
    locator_reference,
    noun_sources,
    provenance_reference,
    source_bundle,
    validate_structural_sources,
)
from tests.i006._fixtures import _refresh_mapping
from tfont.digests import canonical_json_bytes
from tfont.semantic_digest_v2 import mapping_semantic_projection_v2
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


BASELINE_MAIN = "45b4584f7a8ab8ce5d5c3920fa144819a88fdfbe"


def validated(sources):
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))


def external_reference_ir():
    refs = [
        entity_identity_reference("refs"),
        catalogue_reference("refs"),
        provenance_reference("refs"),
        locator_reference("refs"),
    ]
    sources = noun_sources(
        "refs",
        parent_char="a",
        external_references=refs,
    )
    return compile_semantic_ir((validated(sources),)), sources


def authority_ir():
    sources = noun_sources(
        "authority",
        parent_char="a",
        projection_route="authority",
    )
    return compile_semantic_ir((validated(sources),)), sources


def executable_reference_ir():
    refs = [
        entity_identity_reference("exec"),
        catalogue_reference("exec"),
    ]
    for ref in refs:
        ref["native_binding"]["execution_shape"] = "value-predicate"
    sources = noun_sources(
        "exec",
        parent_char="a",
        external_references=refs,
    )
    mapping = sources["mappings"]["mappings"][0]
    _refresh_mapping(mapping)
    return compile_semantic_ir((validated(sources),))


def mapping_payload(mapping):
    projected = mapping_semantic_projection_v2(mapping)
    payload = canonical_json_bytes(projected).decode("utf-8")
    digest = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return payload, digest


def main() -> int:
    refs_ir, refs_sources = external_reference_ir()
    authority, authority_sources = authority_ir()
    executable = executable_reference_ir()

    mapping = refs_sources["mappings"]["mappings"][0]
    payload, payload_digest = mapping_payload(mapping)
    if payload_digest != mapping["mapping_semantic_digest"]:
        raise SystemExit("mapping payload does not reproduce reviewed mapping digest")

    identity_key, identity_rows = refs_ir.identity_index[0]
    identifier_key, identifier_rows = refs_ir.identifier_index[0]
    authority_key, authority_rows = authority.authority_index[0]

    identity = identity_rows[0]
    forged_identity = replace(
        identity,
        external="https://example.org/entity/forged",
        identity_strength="same-entity",
    )
    forged_ir = replace(
        refs_ir,
        identity_index=((identity_key, (forged_identity,)),),
    )

    # This is the threat boundary, not a production validator assertion:
    # CompiledSemanticIR is a public dataclass and replacement succeeds while
    # the selected release still carries the original reviewed mapping digest.
    if forged_ir.variants[0].release_signature.mapping_digests != refs_ir.variants[0].release_signature.mapping_digests:
        raise SystemExit("forged IR unexpectedly changed release mapping digest")

    executable_identity = executable.identity_index[0][1][0]
    executable_identifier = executable.identifier_index[0][1][0]

    result = {
        "baseline_main": BASELINE_MAIN,
        "current_ir": {
            "authority_key": {
                "authority_system": authority_key.authority_system,
                "authority_resource": authority_key.authority_resource,
                "formal_kind": authority_key.formal_kind,
                "semantic_role": authority_key.semantic_role,
            },
            "authority_route": [
                authority_rows[0].reference_kind,
                authority_rows[0].query_role,
            ],
            "authority_assessment": authority_rows[0].assessment,
            "authority_has_reviewed_projection_payload": bool(
                authority_rows[0].projection_semantic_payload
            ),
            "identity_key": {
                "authority_system": identity_key.authority_system,
                "external_entity_id": identity_key.external_entity_id,
                "identity_strength": identity_key.identity_strength,
            },
            "identity_route": [
                identity.reference_kind,
                identity.query_role,
            ],
            "identifier_key": {
                "issuer_or_namespace": identifier_key.issuer_or_namespace,
                "literal_id": identifier_key.literal_id,
            },
            "identifier_route": [
                identifier_rows[0].reference_kind,
                identifier_rows[0].query_role,
            ],
            "provenance_locator_not_reverse_indexed": (
                len(refs_ir.identity_index) == 1
                and len(refs_ir.identifier_index) == 1
                and {
                    row.reference_kind
                    for _, rows in refs_ir.native_index
                    for native in rows
                    for row in native.external_references
                }
                == {
                    "entity-identity",
                    "catalogue-identifier",
                    "provenance-source",
                    "locator",
                }
            ),
        },
        "review_authority": {
            "mapping_digest_reproduced_from_source_payload": payload_digest,
            "native_record_has_mapping_semantic_payload": (
                refs_ir.native_index[0][1][0].mapping_semantic_payload == payload
            ),
            "external_reference_has_own_review": hasattr(identity, "review"),
            "external_reference_has_own_semantic_digest": hasattr(
                identity, "semantic_digest"
            ),
            "forged_external_reference_replace_succeeds": (
                forged_ir.identity_index[0][1][0].external
                == "https://example.org/entity/forged"
            ),
            "forged_row_keeps_original_release_mapping_digest": (
                forged_ir.variants[0].release_signature.mapping_digests
                == refs_ir.variants[0].release_signature.mapping_digests
            ),
        },
        "execution_boundary": {
            "legacy_identity_execution_shape": identity.native_binding.execution_shape,
            "legacy_identifier_execution_shape": identifier_rows[0].native_binding.execution_shape,
            "explicit_identity_execution_shape": executable_identity.native_binding.execution_shape,
            "explicit_identifier_execution_shape": executable_identifier.native_binding.execution_shape,
            "explicit_shapes_validate_without_schema_change": (
                executable_identity.native_binding.execution_shape == "value-predicate"
                and executable_identifier.native_binding.execution_shape == "value-predicate"
            ),
        },
        "policy": {
            "authority_exact_resource": AUTHORITY_NOUN,
            "identity_strengths": [
                "same-entity",
                "probable-same-entity",
                "related-record",
                "ambiguous-identity",
            ],
            "first_slice_executable_identity_strength": "same-entity",
            "probable_related_ambiguous_are_not_exact_identity_authority": True,
        },
        "conclusion": {
            "source_schema_change_required": False,
            "index_schema_change_required": False,
            "external_reference_runtime_payload_binding_required": True,
            "recommended_binding": "canonical reviewed parent mapping semantic payload on NativeRecordIR",
            "execution_requires_explicit_execution_shape": True,
        },
    }

    if authority_rows[0].reference_kind != "authority-value":
        raise SystemExit("authority route drifted")
    if identity.reference_kind != "entity-identity":
        raise SystemExit("identity route drifted")
    if identifier_rows[0].reference_kind != "catalogue-identifier":
        raise SystemExit("identifier route drifted")
    if identity_key.identity_strength != "same-entity":
        raise SystemExit("identity fixture strength drifted")
    if not result["current_ir"]["provenance_locator_not_reverse_indexed"]:
        raise SystemExit("reference-family index isolation drifted")
    if not result["review_authority"]["native_record_has_mapping_semantic_payload"]:
        raise SystemExit("I-021 runtime payload binding is missing")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
