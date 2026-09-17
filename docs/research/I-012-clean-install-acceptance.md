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

This double is transport/execution stimulus, not semantic authority. The synthetic node/value rows may be fixed, obvious acceptance data chosen to exercise `subs`, `nmpr`, nonmatching values, overlap/node-type filtering and deterministic ordering.

### Acceptance identities must be independent oracles

The acceptance runner must **not** derive all expected release authority from the wheel it is testing. A self-consistent but accidentally changed profile could otherwise supply both the value under test and its own expected value.

Freeze the reviewed I-009 release identities independently in the acceptance artifact and compare the installed wheel against them:

| corpus | parent manifest digest | component digest | mapping semantic digest | projection semantic digest |
| --- | --- | --- | --- | --- |
| BHSA | `sha256:cc2c65cd79b2cb7faf1a34b94feb3cc2d3291e7064cbec942c53b0e05f1b0837` | `sha256:5178414e293a743fc98768abcab5b9cb268e14ad56fd2cfbac544ae2869d2e6f` | `sha256:1584b737cc14b14c6178a651d96e4d14c21414bcd55c216b4dbf45133ab02729` | `sha256:60b78e009d3ca5797ad090c9fb82a2a928c2b44a0a9f23c90b95f86238388c41` |
| Syriac | `sha256:afb5a826b9ebe10cdd4ca23d96e00ee7bf677d06496cfcfcee6bb37d2ecff6c4` | `sha256:54a2596d5525f3afb34db0a89d5511e6b8471ce4a93fae4825b22f0945ab62ef` | `sha256:ae7fe7e2bff7d43524b78f68afc548cdde51e20bc32ecf2d082aec2f390043a1` | `sha256:7aab23f738faa2c4fde2909a280618863284ddf8ec63c6a0e237ecb111a5d1a2` |
| ExtraBiblical | `sha256:d39fe3f4848cadb14ae5ef453a5150ea6281b2874728566198d7de10d72bec4a` | `sha256:d0ca9bdf90bfdefe19861c2c68e91071650ed511b8a79270490238b30274aee0` | `sha256:5ccd4e2648595c439c374b383e6e3f5abe747aa3997fe863918e733c5ddb0c2c` | `sha256:8827054ce6355fd05172b2dc7ed58030240637c0ba93092e518f11b9b3a24907` |

Also freeze the OLiA revision `d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6`, Noun IRI `http://purl.org/olia/olia.owl#Noun`, and exact-only release policy. These constants are deliberate release acceptance duplication, not test-fixture authority: changing them requires an explicit reviewed release decision.

The API contexts should use these frozen parent/component identities. The compiled wheel must independently report the same expected parent and semantic digests. That makes accidental resource drift a test failure rather than a self-fulfilling input.

A real Context-Fabric smoke remains useful lower-layer coverage in I-008, but replacing this release gate with full corpus acquisition would add network, storage and upstream-availability failure modes unrelated to the v0.1 package contract.

## Clean-install shape

Recommended release gate:

1. build one non-editable wheel from the candidate checkout;
2. create a fresh virtual environment outside the checkout;
3. install exactly that wheel into the venv;
4. copy/run a repository acceptance runner from an outside-checkout working directory with isolated Python;
5. runner imports only installed `tfont` and uses shipped production resources;
6. validate/compile all three bundles and compare their release identities to the frozen reviewed constants above;
7. create three minimal already-loaded API contexts using the frozen release identities and local API doubles;
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
2. installed parent/component, mapping/projection semantic, OLiA and exact-only policy identities equal the independently frozen reviewed v0.1 constants;
3. one OLiA Noun request yields deterministic corpus ordering and expected acceptance node tuples;
4. BHSA and ExtraBiblical plans are finite `value-set-predicate` bindings over canonical `{nmpr, subs}` and Syriac is scalar `value-predicate` over `subs`;
5. every plan target/key remains the requested OLiA Noun semantic tuple;
6. each plan exposes the expected mapping ID, projection ID, mapping/projection semantic digests, mapping/projection review fingerprints and native-binding identity;
7. each corpus row exposes a fresh runtime report whose expected/observed parent is exact and whose complete dependency closure passed;
8. release/profile fingerprints and plan/resolution fingerprints are nonempty and consistent with the returned resolution;
9. no API double reports an autoload call;
10. changing one loaded parent digest produces `parent_incompatible` before any corpus selector is called.

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
- self-derived parent/component/mapping identities making accidental release drift pass tautologically;
- frozen acceptance constants being changed casually instead of through an explicit reviewed release decision;
- asserting only result nodes while failing to prove provenance/review/runtime identity;
- negative parent test calling selectors before authorization failure;
- accidental corpus/ontology network loading hidden in the runner;
- treating API doubles as evidence that the actual corpus encoding is correct (that authority remains I-009 evidence/review);
- turning a release acceptance script into a new supported query/CLI API without research.

## Conclusion

The smallest correct I-012 is a **clean-wheel acceptance runner and CI gate over the existing public API**, not another TFont feature. It should compose the two I-009 boundaries, compare the installed release against independently frozen reviewed identities, assert the existing explanation/provenance envelope, and fail closed on parent drift. If this runner passes without `src/tfont` changes, that is the desired result: the remaining blocker was release-level integration evidence, not missing runtime functionality.
