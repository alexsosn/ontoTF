# I-033B — generic release catalogue, historical loader parity

**Parent:** #290 (I-033 batch mapping architecture), ADR-001. **Development phase:** research → plan → RED → GREEN.

## Real-code audit

`src/tfont/production_bundles.py` hard-codes three different corpus sets, four version constants, four growing evidence dictionaries, four conditional ontology evidence switches and one wrapper per feature increment. Releasing four mappings in #289 required new Python declarations despite existing `_mapping_artifact`, `_artifact`, `SemanticSourceBundle`, `validate_semantic_bundle`, and `compile_semantic_ir` supporting arbitrary mapping sets. New version 0.4.0 also copies 0.3.0 mappings and parent manifest.

The biggest immediate high-confidence cut is to separate *release selection* from Python code. The loader should read a single **packaged versioned release catalogue** and construct the same `SemanticSourceBundle`, preserving all old wrappers. This makes a future release a catalogue data change plus genuinely new evidence/mapping data, with no hard-coded `_ADJ_ADV_...` Python edits.

## Scope and non-goals

Introduce `tfont.load_profile(corpus_id, release_id="current", models=("olia",))` and `tfont.list_profile_releases(corpus_id)`. Existing supported versions:
- BHSA: 0.1.0, 0.2.0, 0.3.0, 0.4.0 (`current`=0.4.0)
- Syriac: the same four versions (`current`=0.4.0)
- ExtraBiblical: 0.1.0, 0.2.0, 0.3.0 (`current`=0.3.0)

Catalogue entries hold **explicit immutable resource paths** (profile, parent, evidence, ontology lock). The current *alias* is intentionally explicit, not automatically inferred from semver or filenames. No source corpus checkout is needed at runtime; resources come from `importlib.resources.files("tfont")` and are portable in installed wheels.

This is **loader parity**: no new ontology mappings, term approvals, semantic digests, coverage upgrades, or schema changes. The installed catalog initially supports only OLiA as a model pack. Requests for any other model MUST fail closed rather than pretending seven ontologies are installed.

## Threat model / contracts

- Unknown corpus/version or unsupported model must raise controlled `ProductionBundleError`.
- No arbitrary path traversal: all profile/parent/evidence/ontology refs are relative, normalized, within documented packaged roots and match the selected corpus/version. Historical ExtraBiblical evidence legitimately includes BHSA sources, so cross-corpus evidence is allowed as *explicit* pins only.
- Verify catalogue closed-key shape, exact nonempty evidence lists, unique release identifiers and duplicate-free evidence bindings. Validate the loaded source artifacts and the semantic bundle; do not silently skip absent/invalid resources.
- Release-specific `ontology_lock` + ontology evidences are explicit and must remain pinned to the same OLiA ontology snapshot, not inferred from URI spelling.
- The exact `SemanticSourceBundle` produced by generic loader must be semantically and structurally identical to legacy wrapper output, including the source_name values of mapped artifacts. No hidden mutation of immutable historical mappings.
- Generic `current` is a release alias; independently report P-004 *coverage progress* from reviewed coverage manifests (not from the number of mappings).

## Measured exit

Parity for all **11** published corpus/release combinations, including ExtraBiblical evidence shared with BHSA and 0.4.0 adjectival additions. One new registry module, one small bundled catalogue and tests; **zero** per-value new workflows or profile copies. Follow-up under #290: compact overlay releases and independent review receipts; this PR only removes future hard-coded loader extensions.
