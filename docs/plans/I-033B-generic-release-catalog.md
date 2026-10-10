# I-033B plan — data-selected loader without breaking historical APIs

1. RED: tests import `load_profile`/`list_profile_releases` and verify 11 corpus/release parity cases against existing explicitly versioned legacy bundles. Validate target corpus, selected version, mapped IDs, evidence/ontology locks and `validate_semantic_bundle` IR; explicit current alias.
2. RED adversarial: unknown corpus, release, model, malformed alias, duplicate evidence, path traversal, cross-corpus spoofing, swapped ontology lock/source, stale ontology or malformed catalogue must fail closed (not treated as empty mappings).
3. GREEN: package `src/tfont/resources/release_catalog/v1.json` with explicit exact path arrays and controlled `models=["olia"]`; new `src/tfont/release_registry.py` loads/validates catalogue and reuses existing `SemanticArtifact`+mapping merge machinery. Do NOT edit legacy loaders.
4. Export new public API from `src/tfont/__init__.py`; retain full existing historical load functions and package metadata.
5. A single generic parametrized Python 3.10/3.12 regression matrix for 11 cases and adversarial negative fixtures. Full exact-head repository suite, wheel inclusion check and no bespoke CI YAML for a single mapping.
6. Fresh logically independent skeptical review, compare each real corpus/release bundle and generated indexes, inspect path trust boundary, materialized wheel resource presence and ontology constraints; merge expected head only after all tests green.
7. Next phase: catalogue supports compact inherited releases compiled from decision ledger. Do not claim this phase replaces per-item Mapping v2/profile authoring or establishes independently signed review authority.
