# Contributing to ontoTF

The target is a researcher-friendly XML mapping catalog. Read the [XML contract](docs/architecture/researcher-first-xml-contract.xml) and [removal plan](docs/architecture/researcher-first-removal-plan.xml). The XML reader has not yet shipped; the old JSON runtime is transitional.

## Mapping contribution (target workflow)

Edit `src/tfont/mappings/<corpus>.xml`, or create it for a new corpus. Add or revise as many mappings as needed. Use the shared `src/tfont/mappings/schema.xsd` syntax; do not edit the schema for ordinary new values, nor write a registry entry or per-corpus Python adapter. Add an evidence URL and short note when the assertion needs explanation.

Open one PR. The review checks the native definition, target meaning, direction/strength of the relation and at least one plausible false equivalence. A logically independent adversarial pass can be done by the same agent. One CI workflow parses the XML, checks selectors and bidirectional lookup and tests wheel packaging. No signed receipts, protected review handoffs, per-row versioning or external reviewer identity.

A new runtime capability may require Python and test edits with research/plan/TDD in that same PR. Ordinary mapping data additions do not. Never fabricate target mappings to improve coverage counts. Approximate results must remain clearly qualified. Native-only is a legitimate result.

This policy supersedes the old ticket ownership and separate research/design/release PR ritual for new mapping contributions. During migration, keep historical APIs usable where needed but do not copy old release machinery.
