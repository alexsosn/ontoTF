# R-017 post-review normative amendment

**Status:** normative correction to `R-017-external-authority-semantics.md` for P-003 integration  
**Scope:** supersedes the execution, no-target, and publication-validation handling described below; the corpus evidence and six-role separation in R-017 remain unchanged.

## 1. R-017 classifies references; it does not authorize execution by itself

R-017 selects the semantic role and reverse-index family for an external reference. It consumes, but does not derive or replace, the fail-closed execution prerequisites established by R-003 and R-015.

For every queryable reference role, **including `exact` mappings**, a non-empty reviewed native selector is necessary but insufficient. Execution additionally requires a derived **upstream execution prerequisite** showing that the active parent/profile compatibility and required R-015 semantic bundle/ontology locks/bridges/dependency closure are executable. This prerequisite is produced by the surrounding validated runtime/profile state; it is not a caller-controlled opt-in switch.

Consequences:

- `exact` semantic-pivot and authority-value bindings resolve only when a reviewed non-empty native selector exists **and** the R-003/R-015 upstream execution prerequisite is satisfied;
- same-entity identity filters and queryable catalogue identifiers consume the same upstream prerequisite before producing a native plan;
- a missing, false, malformed, or unvalidated prerequisite fails closed to informative/non-executable behavior;
- R-017 never turns URI presence, local reference validation, or selector presence into an independent execution path.

## 2. R-017 does not authorize approximate execution

For `semantic-pivot` and `authority-value` references:

- `close`, `broader`, and `narrower` are **policy-deferred / informative-only in R-017** even when a native selector exists;
- any future execution of those non-exact mappings must pass the separate R-016 approximation contract, including its reviewed approximation eligibility, closed loss contract, non-empty native plan, explicit approximate mode, caller loss acceptance, and the same upstream R-003/R-015 execution prerequisites;
- `related` and `ambiguous` remain non-substitutable/informative-only.

R-017 therefore cannot bypass R-016 merely because an AAT/PeriodO binding or ontology target has a known reference kind and native selector.

## 3. `native-only` and `unsupported` are no-target states, not external-reference targets

Accepted ontoTF architecture treats reviewed `native-only` as a legitimate native semantic state with no defensible common target. `unsupported` likewise represents absence of a usable target for the requested semantics.

Consequently:

- do **not** fabricate an `external` URI/value for either state;
- `semantic-pivot` or `authority-value` records carrying `assessment=native-only|unsupported` are invalid as external-target records;
- such states remain available in native/profile diagnostics and capability reporting, but stay outside semantic→native and authority→native reverse indexes;
- coverage metrics preserve these states rather than deleting or weakening them to increase mapped coverage.

## 4. External-reference records require an actual reference

`provenance-source` and `locator` records are non-semantic by default, but they still represent external references. Their `external` reference value is required. An empty provenance/locator record is invalid rather than a silent placeholder.

This does not authorize network access. Dereferenceability, URI shape, hostname, or the presence of a URL never creates runtime fetch capability. A-001's TF-native execution boundary remains authoritative.

## 5. Publication relations fail closed to R-013 formal-kind validation

Reference role is not sufficient evidence that an RDF/RDFS/OWL/SKOS publication relation is legal. Accepted R-013 separates formal target/operand kind from semantic/reference role.

R-017 therefore uses this boundary:

- `owl:sameAs` is the only publication relation R-017 can validate locally, and only for a reviewed `entity-identity` record with `identity_strength=same-entity`;
- compact and canonical full-IRI spellings of `owl:sameAs` have the same validation semantics;
- SKOS mapping predicates require R-013/P-003 formal-kind validation proving the relevant operands are legitimate SKOS concepts; `semantic-pivot` or `authority-value` role alone never authorizes them;
- all other non-empty publication relations, including RDFS/OWL predicates such as `rdfs:subClassOf` or `owl:equivalentClass`, are **deferred/fail-closed** until the R-013 formal-kind-aware publication validator establishes legality;
- unknown/custom relation spellings are not an escape hatch;
- URI spelling must not change policy: a full IRI cannot bypass a compact-name restriction.

R-017 deliberately does not duplicate the R-013 relation/type matrix. Its prototype rejects/delegates positive publication claims it cannot prove from local identity information.

## 6. P-003 integration rule

P-003 should compose the research contracts in this order:

1. R-017 classifies reference role and chooses a separate index family;
2. target-negative/native-only states remain outside target indexes;
3. R-013 validates any requested publication relation against formal operand kinds; R-017 contributes only the locally provable same-entity `owl:sameAs` case;
4. R-003 parent/profile compatibility and the active R-015 semantic bundle/locks/bridges/dependency closure derive the upstream execution prerequisite;
5. exact semantic/authority/identity/identifier bindings may compile only when their reviewed native binding is present **and the upstream execution prerequisite is satisfied, including `exact`**;
6. non-exact semantic/authority execution additionally delegates to R-016 and cannot be authorized by R-017;
7. resulting native query plans execute only through the TF-native boundary defined by A-001.

The regression contract is encoded in `tests/research/test_r017_reference_policy.py` and `tests/research/test_r017_post_r016_contract.py`; the non-production prototype is `scripts/research/r017_reference_policy.py`.
