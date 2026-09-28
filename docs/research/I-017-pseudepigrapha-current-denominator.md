# I-017 research — current Pseudepigrapha-TF semantic denominator

Issue: #206  
Status: evidence collection in progress

## Question

Can the current Pseudepigrapha-TF denominator be regenerated from the exact
published materialized Text-Fabric artifact, replacing the historical
40-item curated R-011 stress-profile denominator without overstating
exhaustiveness?

## Observed release identity

- Repository: `alexsosn/Pseudepigrapha-TF`.
- Current repository head is `7c4b757bb543a110ae9a252d1281835859136852`.
- Git tag `v1.0.0` resolves directly to that same commit.
- GitHub Release `v1.0.0` was published 2026-09-17 and contains
  `tf-1.0.zip` with GitHub-recorded SHA-256
  `d2dfad7e643699617a9493b9f5d724868f8027dd5f2e88bd558451e3e7819b7a`.
- The repository-owned release identity is converter `1.0.0`, TF data
  version `1.0`, built from OCP commit
  `c939dcbacad78c5d18d2c4282cad23c47e19ac07`.
- The release workflow materializes that exact OCP snapshot, validates the
  generated graph, stages the native archive, loads it with stock Text-Fabric,
  and binds the release commit/tag into the distribution manifest.

## Historical baseline limitation

The immutable I-016 historical manifest retains the R-011 40-item curated
denominator derived from Pseudepigrapha-TF commit
`d098845043897957efee7a42ae4854deddd5a1bd`. Its scope is correctly marked
`bounded-curated`; it cannot support a corpus-wide completion claim.

The current converter contract is much wider: the generated researcher
feature index exposes 96 node-feature names plus 9 edge-feature names (including
technical `oslots`). That index is not sufficient evidence of *materialized*
presence because its renderer deliberately includes converter-supported,
corpus-dependent optional features even when absent from the render graph.

## Evidence method

I-017 therefore inventories the immutable published `tf-1.0.zip` itself.
The research job:

1. downloads only the pinned release asset;
2. verifies the release SHA-256 before inspection;
3. loads the extracted archive with Text-Fabric 13.1.x;
4. records every materialized `.tf` feature/support file;
5. records the actual `otype` node-type vocabulary;
6. records observed values only for a small set of candidate features whose
   boundedness must separately be justified from converter semantics.

The inventory job is research tooling. TFont runtime must remain network-free
and must not acquire corpora.

## Exhaustiveness rule

A new denominator may be called `machine-exhaustive` only for a precisely
defined schema-level scope:

- every materialized semantic node type;
- every materialized semantic node feature;
- every materialized semantic edge feature;
- every explicitly reviewed closed/bounded semantic value family;
- every materialized technical/support feature represented as an explicit
  technical exclusion rather than silently dropped.

Open-vocabulary values (text, identifiers, languages, manuscript sigla,
citations, XML payloads, etc.) remain represented by their feature-level item;
finite observation in one release does not make them a closed vocabulary.

The release archive inventory still needs to establish the exact current
feature/node-type set and the technical/semantic split before this conclusion
can be finalized.
