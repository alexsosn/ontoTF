# I-033E14 — trusted data-driven base selection for protected handoffs

**Issue:** #359; parent #303 / #300 / #290.

## Verified source bottleneck

The installed batch handoff factory has a reviewed and tested *candidate* path, but both builder and verifier hardcode `{"bhsa","syriac"}`, version `0.4.0`, and `p004-i027c2-{corpus}-adj-adv-v1`. This encodes the two-corpus pilot into production control flow. Every additional corpus/version would otherwise need changes to two copies of a private constant, tests and another PR.

Independent source audit of installed `release_catalog/v1.json` and packaged P-004 coverage manifests:
- BHSA current `0.4.0`, `p004-i027c2-bhsa-adj-adv-v1`, 219 semantic items.
- Syriac current `0.4.0`, `p004-i027c2-syriac-adj-adv-v1`, 74 semantic items with an existing `ls="prop"` accounting gap.
- ExtraBiblical current `0.3.0`, `p004-i027b4-extrabiblical-verb-v1`, 136 semantic items.
Each corpus is independent. Same value spelling does not imply a shared OLiA target. This task changes **only source base selection**, not candidate semantics or the protected review policy.

## Narrow change

Introduce a packaged, protected `resources/batch_release_bases/v1.json` containing precisely these three release/version/coverage-set identities. Both handoff builder and verifier resolve **only** this protected registry via the package loader; candidates may not provide arbitrary base IDs, override it, select historical versions, or rely on GitHub PR checkout files. Check registry schema, stable corpus keys and exact source-labeled manifest identity via existing validated loaders. Compare actual catalog-current release to pinned version and fail closed on drift.

Do not change the `10–50` candidate-review count, mapping-v2 semantic digests, two-pass live GitHub attestation, inherited selector rules, sparse coverage preview, or historical package assets. A third corpus is *eligible* only if source evidence, candidate schema, original component, review and protected corpus policy also pass. No automatic cross-corpus ontology correspondence and **no release authorization**.

## Test gates

RED first: typed pinned selection tests require new registry/lookup and reject forged corpus version, changed release catalog, unsupported corpora or a fabricated unreviewed source. GREEN: replace builder/verifier hardcoded selectors with one registry lookup, expand corpus-count bound only to registry length, add positive verification against actual packaged releases. Full suite must protect existing synthetic 10-row reviewed handoff fixture.

The protected signed handoff still needs a trusted versioned installed release writer (#303). Avoid describing this slice as full production activation.
