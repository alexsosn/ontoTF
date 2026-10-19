# ontoTF development guidance

**Binding target architecture:** [Researcher-first XML contract](docs/architecture/researcher-first-xml-contract.xml) and [removal plan](docs/architecture/researcher-first-removal-plan.xml). The prior ADR-001 registry, attestation, profile-version and coverage-publication plans are superseded. The XML path is a migration target; do not claim it is implemented until tests demonstrate the actual loader.

## Product

Researchers need correct and quick corpus-to-corpus mapping discovery. A mapped CATEGORY is not necessarily a mapped TOKEN or a shared entity identity. Preserve the original corpus semantics, evidence and mapping relation (`exact`, `close`, `broader`, `narrower`, `related`, `ambiguous`, `native-only`, `unsupported`). Never infer semantic identity from identical labels.

## TF-native runtime boundary

ontoTF resolves annotations on already materialized Text-Fabric / Context-Fabric
nodes, features, and edges. Corpus-specific ingestion and conversion of upstream
formats belongs to the corpus materializer; a URI in a mapping is a semantic
identifier or evidence link, not an instruction to dereference it. Do not add
a generic sidecar, file-record adapter, external database or network-fetching
runtime for ordinary XML correspondence queries. Any genuinely needed new
carrier or runtime behavior must be justified by an actual corpus example,
a user-facing query, and tests, not by an arbitrary required number of corpora.

## Contribution invariant

A new or extended corpus must require editing **one XML file at `src/tfont/mappings/<corpus>.xml`**, optionally a second source-evidence file; no new Python file, manifest, registry, release snapshot, ontology lock or CI workflow. XML in this repository is the source of truth. No intermediary YAML/JSON mapping ledger or external database.

One cohesive PR, one counterexample-driven adversarial semantic review, one nonduplicated CI check path. Same agent may conduct a genuinely logically independent review. Research/plan/TDD apply to genuinely new behavior, not to repeating an already-supported mapping row. Do not build review receipts, handoff signatures, certificates, cryptographic provenance protocols or per-batch immutable releases. Keep published historical wheels working during migration.

## Priority

1. Make two real corpus XML files resolve both directions and work from an installed wheel.
2. Migrate actual semantic mappings and keep uncertainty explicit; expand useful corpus-to-corpus coverage.
3. Delete old publication bureaucracy and duplicate CI after migrating the unique user-facing checks.
4. Test a new contributor adding a corpus with one XML file.

Do not expand infrastructure without a concrete observed need from real mapping data. Git history and ordinary PR reviews are sufficient process provenance. Existing deprecated design documents and their prior ticket sequencing are not controlling requirements.
