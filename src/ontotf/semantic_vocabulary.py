from __future__ import annotations

SEMANTIC_VALIDATION_CATEGORIES = frozenset(
    {
        "unsupported_contract_version",
        "duplicate_id",
        "missing_reference",
        "component_authority",
        "unknown_vocabulary",
        "invalid_record_state",
        "invalid_projection",
        "invalid_candidate",
        "invalid_reference_routing",
        "kind_role_conflict",
        "unknown_ontology_target",
        "bundle_closure",
        "bridge_closure",
        "evidence_digest_mismatch",
        "stale_semantic_digest",
        "stale_review_binding",
        "native_semantics_unproven",
        "invalid_approximation",
        "invalid_publication_relation",
    }
)

FORMAL_KINDS = frozenset({"class", "property", "skos-concept", "named-resource"})

SEMANTIC_ROLES = frozenset(
    {
        "entity-type",
        "annotation-category",
        "annotation-value",
        "relation",
        "attribute",
        "lexical-entry-identity",
        "lexical-form-identity",
        "lexical-sense-identity",
        "lexical-concept-identity",
        "authority-reference",
        "claim-proposition",
        "inference-activity",
    }
)

TARGET_ROUTING = frozenset(
    {
        ("semantic-pivot", "semantic-constraint"),
        ("authority-value", "authority-value-filter"),
    }
)

EXTERNAL_REFERENCE_ROUTING = frozenset(
    {
        ("entity-identity", "identity-filter"),
        ("catalogue-identifier", "identifier-filter"),
        ("provenance-source", "metadata-filter"),
        ("provenance-source", "explanation-only"),
        ("locator", "explanation-only"),
    }
)

PROJECTION_ASSESSMENTS = frozenset({"exact", "close", "broader", "narrower", "related"})
NATIVE_STATES = frozenset({"positive", "ambiguous", "native-only", "unsupported"})
CANDIDATE_ASSESSMENTS = PROJECTION_ASSESSMENTS

PROFILE_STATES = frozenset({"active", "absent", "unavailable"})
PROFILE_IDS = frozenset(
    {
        "structural",
        "linguistic",
        "lexical",
        "written-text",
        "textology",
        "heritage",
        "scholarly-inference",
        "archaeology",
        "scientific-analysis",
        "lexicography",
    }
)

CAPABILITY_IDS = frozenset(
    {
        "structural.entity-kind",
        "structural.slot-coverage",
        "structural.edge-traversal",
        "structural.section-navigation",
        "linguistic.part-of-speech",
        "linguistic.morphology",
        "linguistic.syntax",
        "linguistic.discourse",
        "lexical.entry",
        "lexical.form",
        "lexical.sense",
        "lexical.concept",
        "lexical.relation",
        "written-text.segment",
        "written-text.sign",
        "written-text.writing-system",
        "written-text.transcription-recognition",
        "textology.textual-version",
        "textology.witness",
        "textology.fragment-transmission",
        "textology.apparatus-reading",
        "textology.witness-attestation",
        "textology.explicit-omission",
        "heritage.physical-object",
        "heritage.physical-part",
        "heritage.identifier",
        "heritage.material",
        "heritage.place-provenance",
        "heritage.custody-location",
        "scholarly-inference.claim",
        "scholarly-inference.inference",
        "scholarly-inference.meaning-comprehension",
        "scholarly-inference.provenance-assessment",
    }
)

IDENTITY_STRENGTHS = frozenset(
    {"same-entity", "probable-same-entity", "related-record", "ambiguous-identity"}
)

SEMANTIC_MODES = frozenset({"exact", "approximate"})
LOSS_TOKENS = frozenset({"undercoverage", "overcoverage"})
