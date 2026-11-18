# Product goals — ontoTF / TFont

## Users and purpose

Text-Fabric researchers should be able to discover defensible cross-corpus correspondences between native linguistic features and established ontology concepts, search their already-loaded corpora, and understand the exact limits of each mapping. The mapping must not invent lexical or token identity between corpora.

## Representative research journeys

1. Ask which reviewed native feature/value represents an OLiA or other ontology category in each supported corpus, with its exact source and ontology evidence.
2. Given one BHSA, Syriac, ExtraBiblical or other supported native feature/value, find explicitly reviewed exact, broader, narrower, approximate or native-only dispositions across other corpora.
3. Find actual nodes in a loaded, supported TF/Context-Fabric corpus by a reviewed ontology category, retaining parent version, category-versus-token distinction and source evidence.
4. Clearly distinguish exact semantic correspondence from missing evidence, native-only values, ambiguity and unsupported categories.
5. Add a new corpus or mapping by editing a single reviewed XML mapping file and verify that installed package lookup discovers it without new Python adapters, per-mapping workflow or release ledger.

## Minimum usable next release

Publish a verified installed-wheel version of the current researcher-first XML catalog API; demonstrate real corpus loading, category lookup, reverse lookup, exact node selection and negative native-only behavior outside the source checkout. Published v0.1.1 remains a historical narrower contract until an actual new release is available. Expanded seven-model coverage is progressive research, not a precondition to shipping the useful existing XML capability.

## Non-goals and immediate priorities

Do not reconstruct a signed-review packet system, JCS attestation ledger, XML release certification, per-row profiles, corpus-specific Python adapter or separate CI workflow for each mapping. Retire superseded machinery (issue #290) and consolidate the documented 82 overlapping CI workflows (issue #291) without weakening real semantic checks. Prefer source-supported mapping coverage and actual downstream searches over architecture expansion.

## Autonomous-development decision rules

- Select work by the researcher journeys above, not issue count or the ease of adding tests. Prefer finishing active PRs and releases over opening new tickets.
- Before introducing a new adapter, workflow, registry, protocol, or validation layer, demonstrate that an existing mechanism cannot meet a concrete acceptance need.
- Preserve source fidelity, access controls, security, and applicable upstream rights. Do not invent inferred text or silently weaken correctness gates.
- Batch repetitive data changes and reuse parameterized tests. Keep independent adversarial review proportional to risk, and validate the actual researcher path.
- If two successive cycles do not advance a journey or remove an observed blocker, reconsider the approach. Stop when the scoped deliverable works instead of generating optional infrastructure work.
