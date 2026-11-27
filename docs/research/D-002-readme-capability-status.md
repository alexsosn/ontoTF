# D-002 research: README capability/status synchronization

## Question
What should the public README say on current `main=fac75d5a251945653a7be585fa30eae34afd4693` so that users can distinguish shipped ontoTF capabilities from accepted architecture and still-unmerged implementation work?

## Current public implementation surface
`src/ontotf/__init__.py` exports three production families:

1. source loading/structural validation: `loads_source`, `load_source`, `validate_source`, `load_and_validate`, `SourceValidationError`;
2. canonicalization/digests: JCS canonicalization plus source/evidence/mapping/profile digest helpers and `DigestError`;
3. parent/component identity: `file_component_digest`, `directory_component_digest`, `tf_payload_digest`, `parent_manifest_projection`, `parent_manifest_digest`, `IdentityError`.

Therefore the README statement that only structural validation and digest primitives are production foundations is stale, and the sentence listing parent-component identity as a future implementation stage is false on current main.

## Merged architecture that is not yet a shipped runtime API
P-003 is merged on current main and defines the common ontology semantic-adapter architecture:

- corpus-native Text-Fabric / Context-Fabric semantics remain authoritative;
- reviewed native semantic records may have zero or more approved typed target-bearing projections;
- semantic-pivot and authority-value projections are separate from identity/catalogue/provenance/locator external references;
- `ambiguous`, `native-only`, and `unsupported` remain explicit non-approved/no-target states;
- active ontology bundle/bridge closure, evidence/review binding, and explicit approximation policy are upstream prerequisites for later semantic execution;
- no generic sidecar/database/API ingestion or live ontology/network runtime is part of the baseline architecture.

This architecture is an accepted design contract, not evidence that cross-artifact semantic validation, semantic IR compilation, resolver/query execution, or corpus mappings are already shipped.

## Current README drift
The current README:

- says foundational research and P-001 plus only two production foundations are merged;
- names only structural validation and canonicalization/digests under implemented capabilities;
- explicitly says parent-component identity is a later implementation stage;
- gives no concise user-facing explanation of the accepted common ontology adapter architecture.

The installation and existing source/digest examples remain accurate.

## Documentation boundary
The README should be corrected narrowly:

- add parent/component identity to implemented capabilities and provide one minimal public-API example;
- update current status so it does not count only two shipped foundations;
- describe P-003 as accepted architecture, using wording such as “accepted architecture” / “planned semantic layer”, not “implemented semantic validation”;
- keep cross-artifact semantic validation, compatibility evaluation, semantic IR/compiler/runtime resolution, and corpus-specific mappings explicitly unshipped until merged;
- retain the experimental/proof-of-concept framing.

## Regression strategy
A focused documentation contract can pin semantic wording without coupling to issue/PR numbers. It should fail on current README because parent identity is absent from implemented sections and still named as future work. It should also guard against overclaiming semantic validation as shipped.

## Non-goals
No runtime/schema/digest changes, no tutorial expansion, no claim of a published package release, no claim that interoperability target corpora already have finished mappings.
