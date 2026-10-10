# I-033E2 research-plan-TDD-release

1. Research: compare already source-reviewed BHSA + Syriac 0.3.0/0.4.0 catalogue releases and `semantic_validation` contracts. No new runtime semantic authority.
2. RED: require `tfont.published_deltas.build_published_delta` and `load_published_delta`. Tests for two positive mapped values/corpus, exact base-to-target parity (SemanticSourceBundle, SemanticIndexes, SemanticIR), deterministic small delta, no copied inherited mapping records or full coverage snapshot, old loader unchanged.
3. Adversarial RED: reject a fake target release not in registry, altered source revision, changed mapping semantic digest, removed inherited mapping, mapping replacement, different corpus, or owner-foreign evidence.
4. GREEN: declarative diff between validated *installed releases*, pin source/target resource identities and semantic mapping hashes, append only new mapping IDs/dependencies and evidence references, validate full reconstructed source bundle.
5. Keep resulting delta marked `authority: "published-registry-parity-only"` and make it impossible to use it as a live approval receipt for new candidate batches. Runtime base + overlay resolver must not trust unregistered target identities.
6. Focused Python 3.10/3.12 and full 3.10/3.12 suite on exact head; independent adversarial review grounded in actual catalog mappings and negative tests; merge expected head only on green.

Phase 3 of #300 will link trusted live GitHub per-row decisions to new signed/attested release publication; don't confuse this mechanical parity slice with authority issuance.
