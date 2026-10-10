# I-027B1 plan — BHSA OLiA Verb production release

**Issue:** #275  
**Parent:** #274 / #264  
**Research:** `docs/research/I-027B1-bhsa-olia-verb.md`

## Research → plan gate

1. Confirm pinned native `sp=verb` documentation and exact `word` selector; confirm locally locked OLiA `Verb` is an OWL class.
2. Identify existing `0.2.0` production bundle layout and all identity/digest requirements. Maintain full historical file immutability.
3. Introduce new normalized, pinned evidence records for source and OLiA target; compute their canonical evidence digests.
4. Add a versioned `0.3.0` BHSA profile with exact `value-predicate` mapping and reviewed mapping + projection semantic digests. Inherit existing mappings byte-identically if the versioned runtime's semantic profile rules allow reusing content-bound review, otherwise issue a new reviewed release-level compatibility assertion.
5. Give new profile a versioned OLiA snapshot lock with `Verb` in `terms_used`, leaving previous lock immutable.
6. Add explicit loader for `0.3.0` instead of silently changing `load_production_linguistic_bundle()` v0.2.0 identity.
7. Add an immutable BHSA coverage successor on top of I-027A: new production accounting only for `node_value:sp="verb"`, preserving all other item accounting, pinned denominator digest and `native-only` `vs` family.
8. All generated JSON must be deterministic; reproducibility/identity tests reject drift.

## TDD RED
- New versioned resources initially absent ⇒ loader and coverage tests fail.
- Negative tests: wrong `sp` value, lexical-node leakage, Noun/Verb confusion, stale mapping/projection/review digests, missing ontology term, missing source evidence, historical resources mutated, coverage denominator changed or I-027A dispositions lost.
- Evidence review includes at least one normal corpus-specific positive and one negative source assertion.

## GREEN
- Implement reviewed 0.3.0 source bundle + exact resolver execution tests and the immutable versioned accounting successor.
- Never silently patch existing release paths; every schema source validated and packaged.
- Enforce controlled linguistic POS capability, no inferred morphology from the Verb annotation.

## TEST / REVIEW
- Focused CI on Python 3.10 and 3.12, full repository test suite, source packaging tests.
- Separate logically-independent adversarial review against BHSA docs, OLiA class definition, semantic digests and runtime behavior on actual/pinned corpus fixtures.
- Merge only on exact-head all-green CI.
- Follow-up #274 for Syriac and ExtraBiblical with independently reviewed selectors and release identities.
