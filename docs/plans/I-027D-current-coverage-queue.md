# I-027D implementation plan — versioned current queue selection

**Issue:** #286. **Research:** `docs/research/I-027D-current-coverage-queue.md`.

1. Freeze `docs/research/data/i027d/p004-current-manifest-selection.json` with all seven manifest paths and expected immutable source pins. Build from `p004-routing-v1` policy and the selected successor manifests; historical policy/output stay unchanged. No implicit "latest" directory scan.
2. TDD RED: new tests require opt-in `scripts/coverage/build_i027d_current_queue.py` and deterministic `docs/research/data/generated/i027d/p004-current-work-queue.json`. Negative fixtures mutate content/revision/denominator, research authority, production source IDs, previously reviewed statuses, native-only dispositions, and original technical/gap sets.
3. Implementation: load/verify selection; reconcile each selected manifest *against baseline* and intermediate required releases; check exact item IDs, kinds, research layers, source pin/digest, denominator basis, technical exclusions, accounting gaps; disallow production authority regression.
4. Reuse I-026 routing policy *in memory* to generate selected-current `build_queue(policy=...)`. Add explicit `current_view` metadata (version and selected-manifest provenance) to a **separate** output; keep original historical output byte-identical. Validate output counts and conservation.
5. Current output must embed actual `existing_accounting` for BHSA 35/219, Syriac 7/74, ExtraBiblical 8/136. Overall same 934 semantic rows, 15 exclusions, C=380 D=67 E=153 F=161 G=39 H=134.
6. Include a focused CI job Python 3.10/3.12 and full suite exact-head validation. Verify original `scripts/coverage/build_i026_work_queue.py --check` still passes and no historical files are modified.
7. Separate logically-independent skeptical review of **real corpus manifests** including 27 reviewed BHSA verbal stems and Syriac `ls="prop"` gap, production vs research authority boundary, with exact review commit.
8. Merge only on exact-head all-green CI. Then update user-facing documentation to identify `p004-current-v1` as current state and I-026 as historical reviewed baseline, without redefining the underlying P-004 denominator.

Do not proceed to the implementation stage until PR #282 (ExtraBiblical source release) is merged, or formally narrow the selector to exclude it and update expected counts.
