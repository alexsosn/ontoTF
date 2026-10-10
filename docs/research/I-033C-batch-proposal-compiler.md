# I-033C — batch proposal compiler from independently pinned POS evidence

**Issue:** #296; parent #290. This is the next *bounded implementation* after I-033A parity (#293) and I-033B registry loader (#294).

## Source evidence and diagnosis
Real released BHSA/Syriac `0.4.0/mappings/adj-adv.json` contain **four** separately reviewed word-level POS mappings to pinned OLiA Adjective and Adverb classes. Each repeats a 30-field native binding / projection / evidence / review skeleton. The reviewed corpus source evidence is already consolidated at `native-adj-adv-pos.json` per corpus, and the ontology evidence at `adjective-evidence.json`, `adverb-evidence.json` and `lock-linguistic-0.4.0.json`. Re-entering full Mapping v2 by hand invited stale digests and excessive CI.

The I-033A pilot only reproduces `olia:Verb` mappings after importing review metadata from already published mapping files. To make batch authoring useful for *new* decisions, proposal generation must work without reading any existing published mapping or inventing an approval.

## Scope / trust boundary
One compact ledger describes a cohort of source-pinned native `value-predicate` categories and ontology class targets with rationale. A deterministic compiler reads **only packaged pinned source evidence and ontology evidence/lock**; verifies record canonical digests, source revision, native category and node type, ontology target/OWL type and lock membership; emits complete Mapping v2 **semantic fields** and independently calculated V2 mapping / V1 projection digest values.

**The result is a proposal, never a release.** It intentionally contains no `review` fields, is rejected by production Mapping v2 schema and carries a top-level `release_authorized=false`. A future phase attaches **independently verified per-row review receipts** and writes an immutable batch release / profile, with GitHub branch protection enforcing review. This step does not treat the label `adjv` as a proof of ontology exactness; its source and target binding checks ensure identity, while genuine equivalence requires independent semantic review.

## Real-data parity control
Generate four candidates from one ledger for BHSA/Syriac `word.sp=adjv/advb` with OLiA Adjective/Adverb. Compare the canonical semantic digests to those published in the actual v0.4.0 releases. Exact parity is proof of mechanical generation fidelity **only**, not a new semantic approval. Other terms/models become valid only if their evidence and lock are separately installed, reviewed, and registered.

## Required negative tests
- Wrong original revision, modified reviewed evidence content without digest update, wrong ontology term, ontology RDF type or lock membership, foreign-corpus evidence, unknown node/category, corpus/code duplication, path traversal / external source.
- No user-supplied `review`, `reviewed`, or fake approval metadata in ledger. Generated candidate cannot pass `validate_source(mapping, "mapping")` without a separate review.
- Deterministic output independent of input row order, byte-checkable offline, never mutable installed historic v0.1.0-v0.4.0 artifacts.

## Boundary with general architecture
This is deliberately a *value-predicate + class* template, not a universal OWL/CRM/FRBR mapper. The data/input structure separates native source evidence from target ontology evidence, so future compilers can add property, relation and SKOS templates without changing trusted digest or review contracts.
