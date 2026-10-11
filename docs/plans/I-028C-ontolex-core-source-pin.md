# I-028C — pinned OntoLex RDF/XML pack / TDD implementation plan

**Issue:** #350. **Research:** `docs/research/I-028C-ontolex-core-source-pin.md`.

1. **RED:** Commit `tests/i028c/test_ontolex_core_snapshot.py` before adding the package artifact and lock. Require exact file and raw byte digests, original OWL namespace/class/property kinds, cardinality restrictions and licensing declaration. Validate the lock against the existing TFont ontology-lock schema; ensure its content digest is exactly the source SHA-256. The first RED condition is missing `ontolex.owl`.
2. **GREEN:** copy **unaltered** upstream `ontolex/ontolex@d6f840f` `Ontologies/ontolex.owl` to `src/tfont/resources/ontologies/ontolex/d6f840f.../ontolex.owl`; add a minimal validated `lock-core-v1.json` with that exact source URL, commit, CC0 license, byte digest and only actually verified ontology URIs. Existing `pyproject.toml` already packages `resources/ontologies/*/*/*.owl` and `*.json`; no package config change.
3. Regression tests must fail on fake target kind, altered source bytes, false class/property roles, wrong range or cardinality, changed commit pin or removal of embedded CC0 evidence. No network execution, no new runtime loader/CI workflow/schema variants.
4. Run exact-head Python 3.10 and 3.12 full-suite CI, independent review from original OWL + W3C final report (not from the authored test expectation), and expected-head merge if green.
5. Handoff: OntoLex Core class/property evidence is now **installed and source-pinned**. The #348 single BHSA class target stays unapproved until actual lexeme→Form construction is reviewed and #303 can publish model-general batches. Coverage remains unchanged.
