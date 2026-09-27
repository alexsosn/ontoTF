# I-015 profile-release identity amendment

**Issue:** #196  
**Amends:** `docs/plans/I-015-noun-morphology-expansion-plan.md`

## Finding

The merged plan correctly keeps the published v0.1.1 wheel historically Noun-only, but it did not explicitly protect the identity of the production semantic profile itself.

Current production resources are authored as profile release `0.1.0`. Adding six mappings, morphology capability, dependencies, ontology terms, and review authority while retaining `profile_version=0.1.0` would assign two different semantic release signatures to the same `(corpus_id, profile_id, profile_version)` identity. The compiler already treats conflicting signatures under one profile release as an error.

## Amendment

I-015 MUST create a new production profile release **0.2.0** for each supported corpus.

- Copy the existing reviewed v0.1.0 profile resources into `resources/profiles/<corpus>/0.2.0/` as the starting point.
- Apply the I-015 mapping/dependency/evidence expansion only under `0.2.0`.
- Keep every `0.1.0` resource byte-for-byte unchanged.
- Set the production linguistic loader to `_PROFILE_VERSION = "0.2.0"`.
- Legacy `load_production_noun_bundle(s)` remains an API compatibility alias to the current production linguistic profile; it is not a historical v0.1.0 resource loader.
- Published GitHub v0.1.1 remains immutable and still contains the old package/profile resources.

The pinned corpus parent identities and pinned OLiA snapshot do not change.

## Additional tests

GREEN must verify:

1. all packaged `resources/profiles/*/0.1.0/**` bytes are unchanged relative to the I-015 baseline;
2. current production loader returns profile version `0.2.0`;
3. the expanded release signature differs from the historical v0.1.0 signature for semantic reasons rather than parent/ontology-byte changes;
4. the old v0.1.1 release artifact is not modified by this source change.

This amendment is required before GREEN implementation.
