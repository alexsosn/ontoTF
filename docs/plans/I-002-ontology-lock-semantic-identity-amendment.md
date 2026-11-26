# I-002 plan amendment: ontology-lock semantic identity

**Issue:** #16  
**Parent plan:** `docs/plans/I-002-canonicalization-digest-plan.md`  
**Reason:** adversarial review `5123175033` found that `{lock_id, content_digest}` binds only the ontology payload bytes and does not bind the target-pin semantics required by P-001 §16.3.

This amendment is normative for I-002 and is recorded before the production fix.

## Decision

Every `ontology_locks` entry supplied to `profile_semantic_digest()` is an already-assembled **v1 ontology-lock semantic identity record**, not a raw I-001 lock record and not a payload-only identity.

Required fields:

- `lock_id`;
- `ontology_id`;
- `support_tier`;
- `term_namespace`;
- `release`;
- `source_uri`;
- `content_digest`;
- `license`;
- `terms_used`.

Optional semantic/pinning fields, included when present:

- `upstream_release_status`;
- `source_revision`;
- `redistribution_policy`.

Explicitly excluded from this semantic identity:

- `retrieved_at` — retrieval/audit timestamp;
- `snapshot_artifact` — storage/locator metadata that may be machine- or bundle-layout-specific;
- any future field not explicitly added through a reviewed algorithm/version change.

Unknown fields fail with `projection_error`; the implementation must not recursively blacklist names from an arbitrary raw lock object.

## Normalization

- lock records are unique by `lock_id` and sorted by `lock_id` in the profile semantic projection;
- `terms_used` is a set-like collection: entries must be unique non-empty exact strings and are sorted before JCS canonicalization;
- other scalar fields are preserved exactly and must satisfy the accepted ontoTF JSON/JCS domain;
- changing any required/optional semantic field changes profile semantic identity even when `content_digest` is unchanged;
- reordering `terms_used` alone does not change profile semantic identity;
- changing the set of `terms_used` does change profile semantic identity.

## Boundary

I-002 does not derive this record from a raw ontology-lock file and does not decide whether the declared terms actually exist in the pinned ontology. I-004/I-006 own cross-artifact assembly and truth validation. I-002 only defines and hashes the deterministic semantic identity record.

The mapping entry remains `{mapping_id, mapping_semantic_digest}` because `mapping_semantic_digest` is already a dedicated semantic digest that binds the full mapping projection. The ontology payload `content_digest` is not an analogous lock-semantic digest, hence the richer lock identity above.
