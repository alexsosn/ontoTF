# I-033E5 — protected evidence ingestion plan

Parent #310 / #303 / #290. Research: `docs/research/I-033E5-candidate-evidence.md`.

1. Commit research/design before implementation. Write RED tests using actual
   installed BHSA/Syriac POS and OLiA records under new candidate resource IDs.
   Require new evidence to reproduce an unreviewed packet with injected loader;
   default packet output stays byte-identical. Fail on forged pins, digests,
   source URI, RDF kind/declaration, citation changes, resource shadowing and
   extras. Confirm intended failures before implementing.
2. Add an authoring-only, in-memory evidence loader. Inputs are the existing
   ledger and already parsed bounded evidence objects; outputs are validated
   deep copies or unchanged installed resources. Validate installed releases as
   source anchors. Keep lock reading installed-only. No storage/query adapter.
3. Add keyword-only loader parameters to packet build/verify. Generated packet
   schema and digest wire formats stay unchanged. Errors fail closed; no reviewer
   authority is created. Review bindings cover all eligible evidence fields.
4. Add manifest v2 `{schema_version, ledger, packet, evidence_resources}` where
   evidence_resources maps compiler resource names to allowlisted PR JSON paths.
   Retain v1. Protected context fetch returns packet/ledger/validated loader;
   legacy two-value fetch remains valid for v1 and rejects contexts it cannot
   carry. CLI uses the full context through live second verification. Local-file
   invocation retains installed-only loading. Reuse one protected workflow.
5. Test manifest/data limits, unknown/unused resources, path traversal, duplicates,
   stale blob/SHA, PR source-pin drift and full mocked fetch→packet→live review.
   No mocked result counts as authenticated production review. Verify honest
   provenance and existing revoked/self/stale-review controls remain effective.
6. Focused compiler/packet/live gate tests, full Python 3.10/3.12 exact-head
   regression, frozen checks and wheel packaging. Use independent skeptical
   review grounded in original corpus text, installed RDF, actual code and parent
   criteria. Revise and re-review any material changes before expected-head merge.

Uncertainty: native record contents are still proposed assertions; schema/hash
validation cannot authenticate scholarly truth. Original-source review is a
publication prerequisite. Candidate locks, source revisions, models and enum-only
gloss inference fail closed in this bounded pilot. No released data are mutated.
