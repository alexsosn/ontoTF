# I-033F — source-bound Text-Fabric native selector smoke for attested overlay candidates

**Parent:** #303 / #300 / #290. **Base:** `16c13d9c53d2efd9d84615dc1aecfcbeb5ede0e2`.

## Facts inspected

- A real protected `pull_request_target` workflow run [38149670546](https://github.com/alexsosn/ontoTF/actions/runs/38149670546) generated an attested 10-native-only BHSA/Syriac compact pack from candidate #324. This is a **handoff**, not a registered installed release; shared-target exact count is zero. The current `verify_overlay_handoff_integrity` checks its immutable original source, ontology lock, per-corpus base release, dependencies, evidence, sparse coverage assignments and decision subset integrity without giving release authority.
- Each accepted source-backed selector is a TF `word.sp=value` native binding (BHSA art/prep/conj/prps/prde/prin/intj/nega/inrg; Syriac pron). Original ETCBC/BHSA source `docs/features/sp.md` at `4db00e...` lines 17 and 22–29, ETCBC/linksyr word_grammar at `3ba424...` line 91. These original definitions do not guarantee observed node counts in an installed TF dataset.
- `load_profile('bhsa'|'syriac')` returns historical v0.4.0 source components with exact `parent_manifest_digest` and `content_digest` commitments. `LoadedCorpusContext` and `LoadedComponentContext` in `semantic_execution.py` already describe a *loaded* TF API plus component digest without importing TF or fetching data.
- Native-only mapping rows intentionally have **no projections**. They must not be injected into `semantic_index` or reported as OLiA exact mappings. We need a way to verify that accepted native selectors operate on an exact pinned loaded TF component **before** registry installation.

## Design and limits

Add one read-only `inspect_native_overlay(pack, loaded_context)` function under `tfont`. It first calls `verify_overlay_handoff_integrity`, requires **native-only only** (zero exact and zero projections), matches corpus identity, exact parent manifest digest and every required TF component content digest to the shipped immutable v0.4.0 original, and requires preloaded `Fall()` to include `sp`. Then it **streams once** over `api.F.otype.s('word')`, calling `api.F.sp.v(node)`, counting the accepted native code values and keeping at most five node samples per value. Reject invalid, out-of-order and repeated node IDs, missing/exceptional feature access, wrong component, malicious API metadata or misleading corpus context. Output is a small deterministic **diagnostic-only** report bound to the pack content digest, with `shared_target_count=0`, no installed state or release authorization.

Alternatives rejected: running proposed/PR-head code with a privileged token; auto-loading or re-downloading TF in validator; treating source glosses as instance counts; adding shared OLiA targets; manufacturing semantically reviewed bundles out of unsealed mappings; one per-feature script/CI workflow.

**Evidence limit:** Unit regressions use a strict TF-like in-memory API to prove gate and selector semantics. Passing such tests is **not** real multi-million-node BHSA/Syriac observation. An external exact TF component must still be supplied to demonstrate live counts before #303 closes; the function cannot attest package release status, GitHub signature or ontology equivalence.
