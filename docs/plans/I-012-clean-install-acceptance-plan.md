# I-012 plan: clean-install v0.1 end-to-end acceptance

**Issue:** #162  
**Research:** merged PR #163; `docs/research/I-012-clean-install-acceptance.md` plus normative `I-012-adversarial-amendment.md`.  
**Baseline:** `main=65f5ef6171ea8a011e283c0be1492c5b213b76ea`.

## Frozen scope

I-012 is a release-acceptance integration ticket, not a new TFont feature. The expected GREEN changes are limited to:

- `scripts/acceptance/v01_noun.py` — one repository-owned acceptance runner, deliberately outside the importable package;
- `.github/workflows/i012-v01-acceptance.yml` — read-only focused CI that builds a wheel and runs the copied runner from a fresh outside-checkout venv;
- `tests/i012/` only for a small RED/control contract if needed to prove the workflow/runner interface deterministically.

Do not modify `src/tfont`, the production profile/mapping/evidence resources, package version, README, release notes, or release/tag workflow unless the acceptance RED demonstrates a genuine product defect. Any such defect requires a new explicit RED before a production-code change.

## Frozen release oracle

The acceptance runner owns independent reviewed v0.1 constants; it must never derive its expected authority solely from the wheel under test.

```text
OLiA revision = d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6
OLiA Noun IRI = http://purl.org/olia/olia.owl#Noun
parent_compatibility = exact-only
```

Per corpus:

| corpus | component | parent digest | component digest | mapping ID | mapping digest | projection ID | projection digest |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `bhsa` | `bhsa-tf` | `sha256:cc2c65cd79b2cb7faf1a34b94feb3cc2d3291e7064cbec942c53b0e05f1b0837` | `sha256:5178414e293a743fc98768abcab5b9cb268e14ad56fd2cfbac544ae2869d2e6f` | `mapping:bhsa:olia-noun` | `sha256:1584b737cc14b14c6178a651d96e4d14c21414bcd55c216b4dbf45133ab02729` | `projection:bhsa:olia-noun` | `sha256:60b78e009d3ca5797ad090c9fb82a2a928c2b44a0a9f23c90b95f86238388c41` |
| `syriac` | `syriac-tf` | `sha256:afb5a826b9ebe10cdd4ca23d96e00ee7bf677d06496cfcfcee6bb37d2ecff6c4` | `sha256:54a2596d5525f3afb34db0a89d5511e6b8471ce4a93fae4825b22f0945ab62ef` | `mapping:syriac:olia-noun` | `sha256:ae7fe7e2bff7d43524b78f68afc548cdde51e20bc32ecf2d082aec2f390043a1` | `projection:syriac:olia-noun` | `sha256:7aab23f738faa2c4fde2909a280618863284ddf8ec63c6a0e237ecb111a5d1a2` |
| `extrabiblical` | `extrabiblical-tf` | `sha256:d39fe3f4848cadb14ae5ef453a5150ea6281b2874728566198d7de10d72bec4a` | `sha256:d0ca9bdf90bfdefe19861c2c68e91071650ed511b8a79270490238b30274aee0` | `mapping:extrabiblical:olia-noun` | `sha256:5ccd4e2648595c439c374b383e6e3f5abe747aa3997fe863918e733c5ddb0c2c` | `projection:extrabiblical:olia-noun` | `sha256:8827054ce6355fd05172b2dc7ed58030240637c0ba93092e518f11b9b3a24907` |

Review IDs are likewise frozen:

```text
review:bhsa:olia-noun:mapping
review:bhsa:olia-noun:projection
review:syriac:olia-noun:mapping
review:syriac:olia-noun:projection
review:extrabiblical:olia-noun:mapping
review:extrabiblical:olia-noun:projection
```

Every review must remain `status=reviewed`; its reviewed digest must match the corresponding frozen semantic digest. The runner may verify review source is nonempty and HTTPS; it should not freeze timestamp or reviewer software as execution authority.

## Acceptance API double

The runner defines a tiny local Text-Fabric-like API implementation. It is test stimulus only and must not be imported from `tests.*`.

Required read surface:

- `api.Fall()` -> `("otype", "sp")` or another deterministic iterable containing `sp`;
- `api.F.otype.s("word")` -> all word nodes for I-007 observation;
- `api.F.otype.v(node)` -> native node type for execution filtering;
- `api.F.sp.v(node)` -> native `sp` value for I-007 complete-value observation;
- `api.F.sp.s(value)` -> native selector used only after successful authorization;
- a `load(...)`/autoload sentinel which increments/fails if touched; ordinary execution must leave it unused.

Frozen stimulus rows:

```text
bhsa:
  node 1 word subs
  node 2 word nmpr
  node 3 word verb
  node 4 lex  nmpr
  expected result (1, 2)

syriac:
  node 11 word subs
  node 12 word subs
  node 13 word verb
  expected result (11, 12)

extrabiblical:
  node 21 word nmpr
  node 22 word subs
  node 23 word verb
  node 24 lex  subs
  expected result (21, 22)
```

The double should count `sp.s` execution-selector calls separately from `otype.s`/`sp.v` observation calls.

## Runner algorithm

`scripts/acceptance/v01_noun.py` performs only public installed-package operations:

1. import required objects from top-level `tfont` only;
2. verify the imported `tfont` package path is not inside the source checkout if an optional `TFONT_ACCEPTANCE_FORBID_ROOT` environment value is supplied by CI; fail if it is;
3. call `load_production_noun_bundles()` and require exactly `PRODUCTION_NOUN_CORPORA == ("bhsa", "syriac", "extrabiblical")`;
4. `validate_semantic_bundle()` each shipped bundle and `compile_semantic_ir()` the three validated bundles;
5. inspect the compiled variants and exact target bindings/plans to compare installed release authority with the frozen oracle: exact parent, component identity from the shipped parent manifest/validated source, exact-only policy, mapping/projection semantic digests, OLiA lock/revision/Noun target and review identities;
6. create three `LoadedCorpusContext`s using the independently frozen parent/component digests and local loaded APIs;
7. construct one exact `SemanticResolveRequest` for profile `linguistic`, capability `linguistic.part-of-speech`, formal kind `class`, semantic role `annotation-value`, target OLiA Noun and all three corpora;
8. call `execute_exact_semantic()` once;
9. assert deterministic corpus order and node results, binding shapes, mapping/projection/review identities, exact parent states, fresh runtime dependency passes, and stable nonempty release/prerequisite/plan/resolution/report fingerprints;
10. assert zero autoload calls;
11. create fresh API doubles/contexts, drift only BHSA parent digest to a deterministic invalid SHA-256 value, run the same request and require `SemanticResolutionError.problem.category == "parent_incompatible"`;
12. after the failed multi-corpus request require every API double's `sp.s` execution-selector count is zero, while observation counters are allowed to be nonzero;
13. print exactly one final machine-readable JSON object and return zero.

Suggested success envelope:

```json
{
  "contract": "tfont-v01-noun-acceptance-v1",
  "corpora": {
    "bhsa": [1, 2],
    "extrabiblical": [21, 22],
    "syriac": [11, 12]
  },
  "resolution_fingerprint": "sha256:...",
  "status": "pass"
}
```

Keys should be serialized deterministically. The exact fingerprint value is not frozen across future reviewed releases; only its shape/nonemptiness and internal equality with the returned result are asserted.

## Provenance assertions

For every successful `ExactCorpusExecution`:

- `row.plan` must be the corresponding plan in `result.resolution.plans` by corpus and `plan_fingerprint`;
- `plan.semantic_key` equals the exact requested key;
- `plan.mapping_id`, `projection_id`, mapping/projection semantic digests equal the frozen oracle;
- mapping/projection reviews use the frozen review IDs, `status == "reviewed"`, and each `reviewed_mapping_digest` equals the expected semantic digest;
- `plan.expected_parent_manifest_digest == plan.observed_parent_manifest_digest == frozen parent`;
- `plan.parent_state == "verified-exact"`;
- `row.runtime_report.variant == plan.variant`;
- runtime report compatibility is `verified-exact` and every dependency result is `pass`;
- runtime report/profile release/prerequisite/plan/report/resolution fingerprints are nonempty `sha256:` identities where applicable;
- native binding is `word.sp`, with BHSA/Extra `execution_shape=value-set-predicate` + `values=("nmpr","subs")`, Syriac `execution_shape=value-predicate` + `value="subs"`;
- OLiA lock URL/revision/content digest in the plan equals the frozen shipped lock authority.

The runner must use exact dataclass/public fields rather than serializing and re-parsing a caller-controlled lookalike plan.

## Clean-install CI contract

`.github/workflows/i012-v01-acceptance.yml` is permanent and read-only (`permissions: contents: read`). It has two jobs:

### `acceptance`

Run at least Python 3.10 and 3.12. For each:

1. checkout exact PR/head;
2. set up the matrix Python only for **building** the wheel;
3. install `build` in the builder interpreter;
4. build exactly one wheel into a temporary artifact directory;
5. create a fresh venv in `${RUNNER_TEMP}` (outside checkout);
6. install that wheel into the venv, not `-e .`;
7. copy `scripts/acceptance/v01_noun.py` to another `${RUNNER_TEMP}` working directory;
8. `cd` there, unset `PYTHONPATH`/`PYTHONHOME`, and invoke the venv Python with `-I` on the copied script;
9. set `TFONT_ACCEPTANCE_FORBID_ROOT=$GITHUB_WORKSPACE`; runner must reject source-tree import leakage;
10. capture the final JSON line and validate `contract/status/corpora` using the venv Python or stdlib only.

The installed wheel may resolve Python package dependencies from PyPI during CI. The **acceptance runner itself** must perform no corpus loading, ontology dereference or network access. If strict offline wheel dependency installation is later required, that belongs to release polish unless it reveals a package defect.

### `regressions`

Run the authoritative repository suite or rely on the repository's existing full-suite workflow; do not create another duplicate full-suite implementation if F-007 already triggers it. The I-012 workflow may run a narrow checkout-side control (`tests/i009`, if useful), but finalization still requires the separate existing `Full repository suite` green on the exact head.

## TDD sequence

### RED

Implementation branch begins from the merged plan. First commit contains only:

- `.github/workflows/i012-v01-acceptance.yml` configured to build/install and require `scripts/acceptance/v01_noun.py`;
- optionally `tests/i012/test_acceptance_contract.py` that statically checks permanent workflow invariants or invokes a helper only if that adds independent value.

Do **not** add the runner yet. Hosted acceptance must fail specifically because the required runner is absent. Existing full-suite/regression workflows must remain green. A packaging/dependency failure or YAML syntax error is not an acceptable RED.

### GREEN

Add `scripts/acceptance/v01_noun.py` only. If this passes without `src/tfont` changes, that is the intended implementation.

If GREEN exposes a genuine package/runtime defect, stop: add a focused failing regression for that defect before changing production code. Do not silently broaden I-012.

## Exact-head gates

Before finalization require on one unchanged exact head:

- I-012 clean-wheel acceptance green on Python 3.10 and 3.12;
- existing I-009 focused/wheel contracts green where triggered;
- authoritative `Full repository suite` green on Python 3.10 and 3.12;
- no temporary write-enabled workflow/helper remains in the diff;
- PR diff contains no `src/tfont` changes unless separately justified by a recorded RED;
- fresh logically independent adversarial review PASS anchored to the exact head.

Merge only with `expected_head_sha`.

## Adversarial review checklist

Review the final implementation as a release auditor, not as the implementer:

1. Can source checkout leak onto `sys.path` and produce a false clean-install pass?
2. Does the runner import any `tests.*`, relative source file or editable package state?
3. Are the expected parent/component/mapping/projection identities independent constants, or copied dynamically from the wheel?
4. Does the double exercise I-007 `otype.s/sp.v` observation as well as I-008/I-010 `sp.s/otype.v` execution?
5. Does parent drift prevent *all* native `sp.s` execution calls, not merely the drifted corpus's call?
6. Are API observation calls correctly distinguished from forbidden execution calls in the negative case?
7. Does successful output prove provenance/review/runtime identity rather than only result nodes?
8. Are exact selector semantics still heterogeneous and canonical per reviewed I-009 evidence?
9. Does any new code download/load a corpus, dereference OLiA, invent a query language, or turn the script into a supported runtime API?
10. Can changing a frozen reviewed release identity make acceptance pass without an explicit code review of the oracle change?
11. Is CI read-only and are temporary bootstrap workflows absent?

## Handoff

After I-012 merges, update #142. The only remaining v0.1 blocker should be release polish: version `0.1.0`, truthful README/first-success workflow, known limitations/release notes, clean release-candidate verification, fresh independent release review, then `v0.1.0` tag/GitHub Release if publishing mechanics are available and proven.
