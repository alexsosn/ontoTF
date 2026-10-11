# I-034E — install the first 12 attested OLiA POS mappings

**Issues:** #303, #264, #283. **Baseline:** `4056f60eecb2de67058d707d307870ccfaa36aeb`.

## Actual source and positive GitHub review, not synthetic approval

- Immutable BHSA nine/Syriac six source POS decisions were published as protected GitHub source-bound candidate packet `i034a-bhsa-syriac-olia-full-pos` (PR #343).
- Protected publish run [38172147473](https://github.com/alexsosn/ontoTF/actions/runs/38172147473) produced the actual artifact `ontology-overlay-handoff-343-38172147473` (artifact ID `11714296834`). Inspected the **76,395-byte** `batch-review-pack.json` inside the 9.2 KB GitHub artifact ZIP. Its content digest is **`sha256:9379981e174ef080468aa0e6f9c1b87b4fa06432effcd907e3973f3328eee308`**, `batch_id=i034a-bhsa-syriac-olia-full-pos`; review observation PR #343, immutable head `b6168a6602ab546446d4101b2029207d840f2076`, author `alexsosn`, GitHub review ID `5484742668`, challenge event ID `5484742495`; outcome **12 exact, 3 reviewed native-only**. This is the sole-agent two-pass review, not a second human.
- BHSA original feature source ETCBC/BHSA SHA `4db00e2157915495e1a4d3d57e41223df24775da`, pinned `docs/features/sp.md`; Syriac ETCBC/linksyr `word_grammar` SHA `3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6` targeting Syriac corpus SHA `bb0eaa7e21b020a26b7566d2e495da9b1f84a919`. Nine OLiA class evidence records and expanded lock `lock-linguistic-i034a-pos.json` are already installed in protected main against original `olia.owl` SHA-256 `5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd`.
- Scope = eight positive BHSA and four positive Syriac POS categories. BHSA `prps`, Syriac `inrg` and `nega` remain native-only. These are lexical **class-level** mappings, not OWL same-as assertions, not a claim that parent corpus nodes have been observed in a local TF directory.

## Installation design

- Immutable opt-in **0.5.0** releases for BHSA and Syriac with **all** existing reviewed 0.4.0 mappings and dependencies retained; add the 15 attested native word.sp mappings and their two source-evidence resources.
- Keep `current=0.4.0` in registry until end-to-end real TF verification; `load_profile(corpus, "0.5.0")` opts in.
- Existing `ontology_lock` is insufficient: older mappings reference `olia-reference-model` and new ones refer to `olia-reference-model-i034a-pos`. `SemanticSourceBundle.ontology_locks` already supports **multiple locks**; registry loader must support an optional second lock for this release without altering historic release schema.
- Include exact source evidence in packaged 0.5 resources, old source records and original immutable ontology evidence. No existing profile version or corpus pin may be rewritten.
- Every new Mapping v2 review must be traceable to exact real #343 two-pass GitHub review, contain correct original mapping/projection semantic digests, and retain explicit category semantics. The attested artifact is provenance; a committed copy of a JSON digest is **not** itself a cryptographic signature. We must not claim the runtime independently contacted GitHub or revalidated SLSA attestation.
- Bundle schema, semantic IR and wheel must load this release, making **12 actual shared-target** mappings available as an opt-in installed profile. Sparse coverage accounting / real loaded TF observation remain separate audited release gates.

**Adversarial risks:** fabricated review event, copied review semantically not bound to accepted IDs, two lock collisions, duplicate native mappings, coverage inferred from source gloss, copied old profiles drifting, no TF actual runtime. Tests fail closed where possible and must separate these limits.
