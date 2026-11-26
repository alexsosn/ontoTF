from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ontotf.source_validation import validate_source  # noqa: E402

SCHEMA_ROOT = ROOT / "src" / "ontotf" / "schemas"


def reviewed_record() -> dict:
    return {
        "review_id": "review:with-audit-fields",
        "status": "reviewed",
        "reviewed_mapping_digest": "sha256:mapping",
        "reviewer_id": "reviewer:test",
        "reviewed_at": "2026-09-05T21:00:00Z",
        "review_source": "offline:test",
        "review_method": "independent-skeptical",
        "notes": ["audit note"],
        "evidence": ["review-evidence:test"],
    }


def mapping_with_review(review: dict) -> dict:
    projection_review = dict(review)
    projection_review["review_id"] = "review:projection"
    projection_review["reviewed_mapping_digest"] = "sha256:projection"
    return {
        "schema_version": 2,
        "mappings": [
            {
                "mapping_id": "mapping:test",
                "corpus_id": "corpus:test",
                "native_binding": {
                    "component_id": "test-tf",
                    "feature": "gn",
                    "value": "m",
                },
                "native_dependencies": ["dep:test"],
                "profiles": ["linguistic"],
                "capabilities": ["linguistic.morphology"],
                "native_state": "positive",
                "projections": [
                    {
                        "projection_id": "projection:test",
                        "target": "https://example.org/term",
                        "reference_kind": "semantic-pivot",
                        "query_role": "semantic-constraint",
                        "formal_kind": "class",
                        "semantic_role": "annotation-value",
                        "profile_id": "linguistic",
                        "capability_id": "linguistic.morphology",
                        "assessment": "exact",
                        "ontology_lock": "lock:test",
                        "native_execution_binding": {"component_id": "test-tf", "feature": "gn", "value": "m"},
                        "evidence": [{"evidence_id": "evidence:test", "content_digest": "sha256:evidence"}],
                        "review": projection_review,
                        "projection_semantic_digest": "sha256:projection",
                    }
                ],
                "ambiguous_candidates": [],
                "external_references": [],
                "evidence": [{"evidence_id": "evidence:test", "content_digest": "sha256:evidence"}],
                "review": review,
                "mapping_semantic_digest": "sha256:mapping",
                "rationale": "fixture",
            }
        ],
    }


class ReviewSchemaConsistencyTests(unittest.TestCase):
    def test_standalone_review_shape_is_valid_when_embedded_in_mapping(self):
        review = reviewed_record()
        validate_source(review, "review", schema_root=SCHEMA_ROOT)
        validate_source(mapping_with_review(review), "mapping", schema_root=SCHEMA_ROOT)


if __name__ == "__main__":
    unittest.main()
