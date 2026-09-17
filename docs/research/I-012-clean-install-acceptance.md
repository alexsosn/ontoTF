# I-012 research: clean-install v0.1 end-to-end acceptance

**Issue:** #162  
**Baseline:** `main` after I-009 merge `dfc3e1669b3e31247ad52182b03084beb55a57cb`  
**Phase:** research only

## Question

What is the smallest authoritative release-acceptance artifact that proves the shipped v0.1 OLiA Noun slice works end to end from an installed wheel, without adding another execution API, downloading production corpora, or duplicating the I-009 semantic review?

## Current coverage

I-009 already provides two important but separate integration boundaries.

`tests/i009/test_runtime_red.py` loads the production BHSA/Syriac/ExtraBiblical bundles, semantically validates them, compiles one `CompiledSemanticIR`, constructs three already-loaded API contexts and calls `execute_exact_semantic()` for one OLiA Noun request. It proves heterogeneous scalar/set selectors, deterministic three-corpus nodes, exact-parent failure before native selection, and selected-value runtime authorization. Its loaded APIs, however, come from `tests.i008._fixtures`, and the test runs from the repository checkout.

`tests/i009/test_wheel_install_red.py` builds a real wheel, installs it outside the checkout, inventories the packaged resources, and loads/validates/compiles all three production bundles under isolated Python. It intentionally stops before loaded execution.

The missing release assertion is therefore not a production feature. It is the composition of these existing boundaries in one clean-install acceptance run plus explicit checks of the already-existing explanation/provenance envelope.

## Existing explanation surface is sufficient

No new explanation/result type is required. `execute_exact_semantic()` returns `ExactExecutionResult`, which already contains:

- `execution_contract`;
- the full `SemanticResolutionResult`;
- one `ExactCorpusExecution` per corpus;
- each corpus row's deterministic `nodes`;
- the exact `ExactNativePlan` selected by the resolver;
- the fresh `RuntimeEvaluationReport` established immediately before resolution/execution.

`ExactNativePlan` already carries the common semantic key, corpus/release identity, expected/observed parent state, mapping/projection identities and reviews, native execution binding and plan fingerprint. `RuntimeEvaluationReport` carries the observed parent/dependency closure used to authorize execution. The acceptance path should assert this existing surface rather than invent a parallel explanation schema or serializer.

## Public installed-wheel boundary

The top-level `tfont` package already exports every API needed by an acceptance runner:

- `load_production_noun_bundles` / `PRODUCTION_NOUN_CORPORA`;
- `validate_semantic_bundle` and `compile_semantic_ir`;
- `SemanticKey` and `SemanticResolveRequest`;
- `LoadedComponentContext` / `LoadedCorpusContext`;
- `execute_exact_semantic` and the result/problem types.

The acceptance runner should import only from installed `tfont`, not `tests.*`, source-tree modules by path, or editable-install state.

## Loaded-corpus simulation in ordinary CI

Ordinary release CI should not download or bundle BHSA, Syriac or ExtraBiblical merely to test TFont's already-loaded API handoff. The semantic/native claims are independently reviewed and pinned in I-009 evidence. For the release acceptance runner, a tiny in-script loaded-TF API double is sufficient if it implements only the production executor's documented read surface:

- `Fall()` -> names of already-loaded features;
- `F.sp.s(value)` -> selected nodes;
- `F.otype.v(node)` -> node type.

This double is transport/execution stimulus, not semantic authority. Production parent/component identities should be taken from the loaded production bundles/compiled variants wherever practical rather than copied from test fixtures. The synthetic node/value rows may be fixed, obvious acceptance data chosen to exercise `subs`, `nmpr`, nonmatching values, overlap/node-type filtering and deterministic ordering.

A real Context-Fabric smoke remains useful lower-layer coverage in I-008, but replacing this release gate with full corpus acquisition would add network, storage and upstream-availability failure modes unrelated to the v0.1 package contract.

## Clean-install shape

Recommended release gate:

1. build one non-editable wheel from the candidate checkout;
2. create a fresh virtual environment outside the checkout;
3. install exactly that wheel into the venv;
4. copy/run a repository acceptance runner from an outside-checkout working directory with isolated Python;
5. runner imports only installed `tfont` and uses shipped production resources;
6. validate/compile all three bundles;
7. create three minimal already-loaded API contexts using the production identities and local API doubles;
8. execute one exact OLiA Noun request;
9. assert nodes and the explanation/provenance chain;
10. repeat with one parent digest drifted and assert fail-closed before any selector call.

A committed runner under `scripts/acceptance/v01_noun.py` is preferable to hiding the whole release criterion inside a test function: CI can execute the same artifact used during release review, while it is clearly not a new runtime/package API. The subsequent release-polish ticket may reference or wrap it, but user-facing documentation should not present a fake-loaded-API harness as the normal user workflow.

## TDD gate for an acceptance-only ticket

There is no justified production-code RED: current APIs already appear sufficient. Creating a new public helper solely to manufacture a failing product test would be overengineering.

The TDD boundary should instead be the missing acceptance artifact itself:

- tests-only/CI RED invokes `scripts/acceptance/v01_noun.py` from a freshly installed wheel environment; it fails because that acceptance runner is absent;
- minimal GREEN adds only the runner (and, if necessary, narrow CI plumbing), not `src/tfont` behavior;
- if the runner exposes a genuine product defect, freeze that defect with a separate RED before touching production code.

This preserves the requested RED/GREEN discipline without inventing product surface for testability.

## Required assertions

The successful run should prove, through public installed-wheel objects:

1. exactly the three production corpora participate;
2. one OLiA Noun request yields deterministic corpus ordering and expected acceptance node tuples;
3. BHSA and ExtraBiblical plans are finite `value-set-predicate` bindings over canonical `{nmpr, subs}` and Syriac is scalar `value-predicate` over `subs`;
4. every plan target/key remains the requested OLiA Noun semantic tuple;
5. each plan exposes mapping ID, projection ID, mapping/projection review fingerprints and native-binding identity;
6. each corpus row exposes a fresh runtime report whose expected/observed parent is exact and whose dependency closure passed;
7. release/profile fingerprints and plan/resolution fingerprints are nonempty and consistent with the returned resolution;
8. no API double reports an autoload call;
9. changing one loaded parent digest produces `parent_incompatible` before any corpus selector is called.

The negative run must check all selector counters, not only the drifted corpus, because execution establishes prerequisites for all requested corpora before `semantic_resolve()` and should not begin native execution if the multi-corpus request is unauthorized.

## Packaging and isolation

The acceptance workflow should build/install the wheel rather than reuse `pip install -e .`. It should run from a temporary directory outside the checkout and must not add the repository root or `tests/` to `sys.path`. A fresh venv is simpler and stronger than `--target` plus path injection. The runner itself can be copied into the temporary working directory before execution; its import boundary remains the installed package.

The existing I-009 isolated-wheel resource test remains useful and should not be deleted merely because I-012 overlaps part of it. I-012 is the release-level composed path; I-009 remains targeted packaging regression coverage.

## Scope decision

I-012 should add **no production runtime code** unless the RED uncovers a real missing public capability. Expected implementation surface is:

- `scripts/acceptance/v01_noun.py`;
- focused I-012 CI/test plumbing that builds a wheel, fresh-installs it and runs the copied acceptance runner;
- optionally a small test that validates the runner's machine-readable success output, if useful for stable CI diagnostics.

Do not put a user-facing tutorial here; the release-polish ticket owns README/first-success documentation, version `0.1.0`, release notes/tagging and final release review.

## Adversarial risks for the plan/review gates

- false clean-install test caused by source checkout leaking onto `sys.path`;
- runner importing `tests.i008._fixtures` or other non-wheel code;
- copied hardcoded parent/component identities silently diverging from shipped profiles;
- asserting only result nodes while failing to prove provenance/review/runtime identity;
- negative parent test calling selectors before authorization failure;
- accidental corpus/network loading hidden in the runner;
- treating API doubles as evidence that the actual corpus encoding is correct (that authority remains I-009 evidence/review);
- turning a release acceptance script into a new supported query/CLI API without research.

## Conclusion

The smallest correct I-012 is a **clean-wheel acceptance runner and CI gate over the existing public API**, not another TFont feature. It should compose the two I-009 boundaries, assert the existing explanation/provenance envelope, and fail closed on parent drift. If this runner passes without `src/tfont` changes, that is the desired result: the remaining blocker was release-level integration evidence, not missing runtime functionality.
