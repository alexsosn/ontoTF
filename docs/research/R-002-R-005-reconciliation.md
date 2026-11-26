# R-002 / R-005 reconciliation: candidate relations are not approved mappings

**Status:** normative clarification for PR #9  
**Recorded:** 2026-09-05

This note reconciles R-002's reviewed mapping-assessment contract with R-005's explicit cross-corpus candidate-strength matrix. It does not change the ontology support tiers or formalization rules in `R-002-review-reconciliation.md`.

## Rule

R-005 classifications `S/C/B/N/R/U/L` are **research-stage evidence about an apparent cross-corpus relationship at the abstraction stated by the matrix row**.

They are not canonical ontology mappings and cannot be compiled directly into executable R-002/R-003 mapping assessments.

In particular:

- R-005 `S` does not automatically become ontoTF `assessment.strength: exact`;
- R-005 `C` does not automatically become `close` to any particular ontology term;
- R-005 `B/N` does not establish the direction of an RDF `rdfs:subClassOf` or SKOS mapping predicate;
- R-005 `R` is evidence that concepts are related, but it does not select a publication relation;
- `U` remains unsupported/unknown until new evidence is reviewed;
- `L` remains native/profile-local unless a later ontology-term review establishes a suitable external projection.

An approved mapping requires a separate term-level review containing at minimum:

1. exact native selector/path and parent-profile compatibility evidence;
2. exact target term URI and pinned ontology release/snapshot;
3. ontoTF mapping assessment (`exact`, `close`, `broader`, `narrower`, `related`, `ambiguous`, `native-only`, or `unsupported`);
4. applicability conditions and rationale;
5. formal publication relation/pattern, if one is safe under the target formalism;
6. regression/negative cases;
7. independent review of the mapping change.

Conceptually:

```text
R-005 candidate S/C/B/N/R/U/L
        ↓ evidence, never automatic promotion
term-level ontology research/review
        ↓
canonical ontoTF mapping assessment
        ↓
optional RDF/OWL/SKOS formalization
        ↓
R-003 runtime resolution status
```

This boundary is especially important for the census cases that deliberately use a broad comparison level: word/sign roles, lexical entities, witness-related data, physical lines, and language-specific grammatical systems. A row-level `S` says nothing by itself about logical equivalence between particular classes or values.

## Review consequence

A final independent reviewer of R-002 should reject any schema/compiler design that derives approved mapping strength or RDF predicates directly from the R-005 matrix without the intervening reviewed mapping assertion.
