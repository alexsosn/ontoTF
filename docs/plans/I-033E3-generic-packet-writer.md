# I-033E3 / #303 — generic, bounded packet authoring plan

**Issue:** #303
**Research:** `docs/research/I-033E3-generic-packet-writer.md`

## RED test

Create `tests/i033e/test_generic_packet_writer.py` first. The test uses the **existing 10-row pinned-source fixture** (nine BHSA, one Syriac), writes a v2 manifest and candidate JSON into a temporary repository, and requires a reusable command to emit exactly `serialized(build_review_packet(...))` bytes in `--write` mode; `--check` must pass only for those exact bytes. Include stale/tampered evidence or packet, duplicate-key JSON, path traversal, symlink escape, foreign manifest paths, wrong event-like metadata, and overwrite rejection. The packet must remain `authority=unreviewed-proposal`, `release_authorized=false`, with all ten source-bound decision digests.

## Implementation

`scripts/mappings/build_candidate_review_packet.py` loads a **fixed** manifest path relative to `--root` and only allows strict v1/v2 shapes and relative JSON input paths already permitted by the protected gate. It rejects duplicate JSON keys using `loads_source`; caps lengths; rejects symlink components and out-of-root files; reads a bounded ledger and supplementary evidence; validates v2 candidate evidence through `CandidateEvidenceResources`; recomputes a review packet through `build_review_packet` plus `verify_review_packet` and refuses `--check` mismatch. `--write` is exclusive and cannot alter an existing reviewed request. `--stdout` merely prints the unapproved packet.

Existing four-row hardcoded scripts stay compatible. No new per-item workflow or semantic promotion.

## GREEN / skeptical review / merge

Full exact-head 3.10 and 3.12 GitHub suites and all other active checks must pass; skeptic must inspect real 10-row corpus test data, path trust, file handling, no approval confusion, and symlink/duplicate-key behavior. Post a fresh review against exact final SHA; squash merge with `expected_head_sha`. Keep #303 open until real independently approved 10+ candidate packet and published overlay are shown.

## Independent adversarial RED rework

First skeptical review at `7814221` identified two flaws:
1. The direct exclusive write could leave a partial final file on disk interruption; new contract simulates a failed atomic link and requires no final or leaked temporary file. Use same-directory tempfile + fsync + atomic no-replace hard-link + unconditional temp cleanup.
2. `set(paths.values())` evaluated unvalidated JSON arrays/dicts and leaked TypeError; validate all paths as canonical strings *before* deduplication. Negative tests now explicitly include JSON array and JSON object values.

Both failures are fixed after their negative tests were committed in RED revision `675da22`. Re-run exact-head CI and a new adversarial review on the final SHA.
