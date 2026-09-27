# I-015 plan — production noun morphology and exact conjunctions

**Issue:** #196  
**Research:** `docs/research/I-015-noun-morphology-expansion.md`  
**Baseline:** `7e0c39854659222fc1a8545c8e10c680cbda969c`

## Exit condition

On current source `main`, a caller with verified pinned BHSA, Syriac, and ExtraBiblical TF contexts can execute reviewed exact requests for:

- OLiA Noun;
- ProperNoun;
- Masculine / Feminine;
- Singular / Plural / Dual;

and can explicitly conjoin different semantic atoms, including `Noun AND Plural`, `Noun AND Feminine`, `Noun AND Dual`, and `ProperNoun AND Feminine`. Conjunction returns the deterministic per-corpus node intersection and complete constituent plan/review/evidence provenance.

Published v0.1.1 remains historically Noun-only; this ticket does not republish or rewrite that GitHub release.

## Compatibility

Preserve all existing single-atom contracts:

- `SemanticResolveRequest`, `semantic_resolve`;
- `execute_exact_semantic`;
- `PRODUCTION_NOUN_CORPORA`;
- `load_production_noun_bundle(s)`.

Add new APIs rather than making existing request/result fields polymorphic.

Introduce general production-loader aliases:

- `PRODUCTION_LINGUISTIC_CORPORA`;
- `load_production_linguistic_bundle`;
- `load_production_linguistic_bundles`.

The legacy noun loader delegates to the same expanded linguistic bundle and remains source-compatible.

## Production resources

### OLiA

Update the existing pinned lock only; do not change ontology bytes/revision.

Extend `terms_used` with:

- Noun;
- ProperNoun;
- Masculine;
- Feminine;
- Singular;
- Plural;
- Dual.

Add one normalized OLiA evidence artifact covering the six new classes and their exact hierarchy/category relations in the already pinned snapshot. Retain the existing Noun hierarchy evidence.

### BHSA

Add normalized source evidence for exact `gn` and `nu` definitions from the pinned BHSA feature documentation.

Extend profile dependencies with:

- `word.gn=m`, `word.gn=f`;
- `word.nu=sg`, `word.nu=pl`, `word.nu=du`.

The existing `word.sp=nmpr` dependency owns ProperNoun.

Add six exact mapping rows to the existing mapping artifact with scalar `value-predicate` bindings.

### Syriac

Add normalized grammar evidence from pinned `linksyr` `word_grammar` for:

- `ls=prop` proper noun;
- `gn=m/f`;
- `nu=sg/pl/du`.

Extend profile dependencies for those values. Add six exact mapping rows. ProperNoun uses `word.ls=prop`; morphology uses `gn` / `nu`.

### ExtraBiblical

Retain the explicit BHSA-family feature-authority evidence. Add exact pinned TF-value evidence for `gn` and `nu`; bind it together with BHSA feature-definition evidence when authorizing semantics.

Extend dependencies with `gn=m/f` and `nu=sg/pl/du`; `sp=nmpr` already exists. Add six exact mappings.

### Capabilities

Add `linguistic.morphology` to all three profile capability lists. ProperNoun remains `linguistic.part-of-speech`.

## Conjunction resolver

Add a separate exact-only contract in `semantic_resolver.py`:

- `EXACT_CONJUNCTION_RESOLVER_CONTRACT = "tfont-exact-semantic-conjunction-resolver-v1"`;
- `EXACT_CONJUNCTION_RESOLUTION_FINGERPRINT_ALGORITHM`;
- `SemanticConjunctionRequest(keys, corpora, semantic_mode="exact")`;
- `SemanticConjunctionResolutionResult`;
- `semantic_resolve_conjunction(ir, request, prerequisites)`.

Validation:

1. request must contain at least two exact `SemanticKey` objects;
2. duplicate keys are invalid rather than silently deduplicated;
3. corpora use the existing exact corpus-selection contract;
4. semantic mode remains exact-only;
5. keys are canonicalized by the same semantic-key field order/UTF-16 rule used by compiled IR.

Resolution:

1. materialize prerequisites once;
2. call existing `semantic_resolve` independently for every canonical key against the same corpora/prerequisites;
3. any atom failure fails the entire conjunction;
4. retain constituent `SemanticResolutionResult` objects and all `ExactNativePlan` provenance;
5. fingerprint includes canonical request keys and constituent resolution fingerprints;
6. input key order cannot change the result/fingerprint.

Do not change `multiple_exact_bindings`: same-key multiplicity still fails.

## Conjunction execution

Add an explicit exact conjunction execution contract in `semantic_execution.py`:

- `EXACT_CONJUNCTION_EXECUTION_CONTRACT`;
- `ExactConjunctionCorpusExecution(corpus_id, nodes, plans, runtime_report)`;
- `ExactConjunctionExecutionResult`;
- `execute_exact_conjunction(ir, request, contexts)`.

Refactor only enough common code to execute a fresh exact plan without duplicating selector semantics.

Execution requirements:

1. validate contexts and select variants once;
2. evaluate fresh runtime prerequisites once per requested corpus;
3. resolve all atoms with `semantic_resolve_conjunction`;
4. execute each exact constituent plan through the existing scalar/value-set binding machinery;
5. per corpus, intersect atom node sets and sort ascending;
6. return all constituent plans in canonical semantic-key order;
7. never synthesize a TF query string, OR, NOT, hierarchy substitution, or caller-authored native plan.

An empty intersection is a valid exact result, not an error.

## Public surface

Export all new loader/conjunction constants, dataclasses, and functions through `tfont.__init__`.

Document current development-source capability separately from the immutable published v0.1.1 wheel. Do not imply that the already published wheel contains I-015.

## TDD

Create `tests/i015/` first.

RED must prove at least:

1. general linguistic loader/API is absent;
2. six new production SemanticKeys are absent;
3. profiles do not yet expose `linguistic.morphology`;
4. exact conjunction API is absent.

The RED head may not change production code/resources.

GREEN tests must cover:

- all three expanded production bundles validate/compile together;
- exact native selector for every new atom/corpus;
- OLiA lock contains exactly the new used terms while retaining the same snapshot digest;
- new evidence/review bindings validate;
- legacy noun loader remains compatible;
- each new atom resolves across all three corpora;
- conjunction request validation (<2 keys, duplicate keys, unknown/non-exact atom);
- key-order invariance of conjunction resolution fingerprint;
- same-key `multiple_exact_bindings` failure remains unchanged;
- exact node intersection with API doubles;
- `Noun AND Plural` across BHSA/Syriac/ExtraBiblical;
- `ProperNoun AND Feminine`;
- empty intersection;
- constituent plan/review/evidence provenance retained;
- execution result/order invariance;
- single-atom v0.1 tests remain green.

## CI

Add a narrow `.github/workflows/i015-noun-morphology.yml` exact-head PR gate for `tests/i015` plus directly affected production semantic modules/resources on Python 3.10 and 3.12.

The authoritative full repository suite must also pass on the exact GREEN head.

## Review gates

Before merge, independent adversarial review must challenge:

- every native value against pinned source evidence, especially ExtraBiblical authority inheritance;
- Syriac `ls=prop` exactness;
- OLiA target identities;
- distinction between conjunction of different SemanticKeys and R-018 same-key multi-binding composition;
- no atom dropping on failure;
- order-independent fingerprints;
- provenance survival;
- legacy single-atom behavior and loaders;
- user-facing claims about published v0.1.1 vs development main.

Merge only with expected exact head SHA. After merge, rerun/verify the authoritative full suite on main and close #196 only after successful readback.
