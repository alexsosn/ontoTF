# I-033E3 / #303 — generic batch review-packet authoring

**Issue:** #303
**Baseline:** `326081ed02bd12d12f0f46765b4790b5d96fecec`

## Inspected code and real evidence

- The protected review gate `scripts/mappings/check_external_review.py` reads a fixed manifest `docs/research/data/batch_review/inputs.json`, fetches a ledger below `src/tfont/resources/batch_pilots/`, packet below `docs/research/data/generated/i033d/`, and for v2 candidates evidence JSON below `docs/research/data/batch_review/evidence/`. It verifies Git blobs, evidence normalization and locked source/ontology pins via `CandidateEvidenceResources`, and recomputes the packet with `verify_review_packet`.
- Current authoring scripts `scripts/mappings/build_proposals.py` and `scripts/mappings/build_review_packet.py` hard-code the **old four** adjective/adverb proposals. There is no reusable local writer to generate/check a new packet from the same protected review manifest. This encourages hand-copying large digests or writing a per-cohort generator.
- `tests/i033e/test_overlay_handoff.py::cohort()` already builds **ten** genuine pinned-source candidate selectors (nine BHSA word.sp values, one Syriac word.sp=pron) with supplementary digest-bound source evidence. Their provenance is grounded in pinned ETCBC BHSA `docs/features/sp.md` and ETCBC/linksyr `word_grammar`. The fixture is **not** a GitHub-approved release.
- Actual pinned BHSA sp.md at `4db00e2157915495e1a4d3d57e41223df24775da` defines art, prep, conj, prps, prde, prin, intj, nega, inrg at lines 17, 22–29. Actual linksyr `3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6` word_grammar defines pron at line 91. Both are source definitions, not automatic OLiA exact equivalences.

## Chosen migration

Add one **generic local authoring command** (no new workflow) accepting a repository root containing the same fixed v1/v2 input manifest. It reads only bounded canonical JSON paths, rejects symlink/path traversal, verifies source digests/ontology lock with existing trusted compiler, and produces byte-deterministic unreviewed packet using `build_review_packet`. `--check` compares committed bytes without writes; `--write` creates the packet exclusively and refuses overwrite; `--stdout` is diagnostic. Explicit root is for temporary tests only, not authority. This is **never** an approval and cannot substitute for `check_external_review.py --from-pr-head`.

Alternatives rejected: one hard-coded script per cohort (per-entity bureaucracy), manual JCS digest reproduction (error-prone), accepting absolute or unbounded candidate file paths, promoting a generated local packet to `release_authorized` or reviewer identity (security flaw).

Risks: offline candidate JSON can be self-authored, even when digest-correct; only protected independently attested GitHub reviewer and pinned real sources can authorize releases. Cross-repository candidate manifests must not be loaded as executable code. The existing `i033e3-protected-batch-review.yml` stays unchanged. No new mappings, corpus feature assertions or release are asserted by this tooling PR.
