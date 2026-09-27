# I-015 legacy-loader compatibility amendment

**Issue:** #196  
**Amends:** I-015 plan and profile-release identity amendment.

## Finding from RED/GREEN boundary

Pointing the historical `load_production_noun_bundle(s)` API at the expanded 0.2.0 profile is not source-compatible in practice. Runtime prerequisite evaluation is profile-wide: a caller that loads only `sp` for the established Noun request would suddenly fail because the expanded profile also declares `gn`, `nu`, and Syriac `ls` dependencies.

The shared OLiA `lock.json` is also part of the historical v0.1 bundle surface; expanding its `terms_used` makes the old bundle metadata observably different.

## Corrected boundary

1. `load_production_noun_bundle(s)` and `PRODUCTION_NOUN_CORPORA` remain historical/current-v0.1 compatibility APIs backed by profile resources `0.1.0`.
2. `load_production_linguistic_bundle(s)` and `PRODUCTION_LINGUISTIC_CORPORA` load the new expanded profile `0.2.0`.
3. Existing `resources/profiles/*/0.1.0/**`, existing OLiA `lock.json`, and existing Noun runtime behavior remain unchanged.
4. I-015 creates a separate ontology-lock metadata artifact for the expanded profile (same exact OLiA snapshot/revision/content digest and lock ID, expanded `terms_used`). The 0.2.0 loader uses that artifact; the 0.1.0 loader keeps using `lock.json`.
5. New I-015 tests use the linguistic loader. Existing I-009 tests stay authoritative for the old noun loader and must pass unchanged.

This preserves actual runtime compatibility instead of only preserving Python symbol names.
