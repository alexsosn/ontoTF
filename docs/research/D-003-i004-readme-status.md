# D-003 research — README status after shipped I-004 semantic validation

**Issue:** #101  
**Baseline:** `main` `200dcaba593d02d4d903aa424d6c7fec574f2ff2`  
**Type:** documentation accuracy / capability-status maintenance

## Question

What can the README now truthfully claim about semantic validation after I-004 landed, and which later semantic/runtime stages must still remain explicitly unshipped?

## Stale current README claims

Current README says:

- only three production foundations are merged;
- `Cross-artifact semantic validation ... [is] not yet shipped`;
- accepted semantic architecture `does not mean the validator ... is already implemented on main`;
- `This is accepted architecture, not yet shipped cross-artifact semantic validation ...`.

Those statements no longer match current main.

## Public API evidence

`src/ontotf/__init__.py` publicly exports the I-004 semantic-validation surface:

- `SemanticArtifact`;
- `SemanticSourceBundle`;
- `SemanticIndexes`;
- `SemanticValidationProblem`;
- `SemanticValidationError`;
- `ValidatedSemanticBundle`;
- `validate_semantic_bundle`.

The public package also exports the mapping-v2/digest support used by this layer, including `mapping_semantic_digest_v2`, `projection_semantic_digest_v1`, `MAPPING_SEMANTIC_ALGORITHM_V2`, and `PROJECTION_SEMANTIC_ALGORITHM`.

Therefore semantic validation is a shipped code capability, not merely an accepted design.

## Exact I-004 boundary on main

`validate_semantic_bundle()` performs deterministic cross-artifact validation over a caller-supplied `SemanticSourceBundle` and returns `ValidatedSemanticBundle` on success.

The current implementation validates, in ordered phases:

1. supported source/contract versions;
2. deterministic indexes and duplicate identifiers;
3. expected-parent component authority and required-component consistency;
4. native dependency closure and mapping/profile scope;
5. controlled semantic vocabularies;
6. mapping/native record state legality;
7. projection/candidate/ambiguity legality;
8. target/ontology-lock membership and routing requirements;
9. ontology-bundle / bridge source closure and bundle identity requirements;
10. evidence bindings and review-evidence references;
11. mapping-v2 semantic digests and review-digest binding;
12. explicit native semantic claims such as value/domain/extent semantics;
13. mapping publication/approximation/policy legality.

The validated result includes:

- the original bundle;
- deterministic expected-parent manifest digest;
- reviewed mapping semantic digests;
- active ontology-bundle digest when applicable;
- deterministic semantic indexes.

Failures use `SemanticValidationError` / `SemanticValidationProblem` with stable category, artifact kind, source name, path and optional related ID.

## What I-004 does not do

README must continue to avoid claiming any of the following as shipped:

- loading/probing a live Text-Fabric or Context-Fabric corpus to decide compatibility;
- compatibility-state evaluation/report generation against materialized parent data;
- semantic IR compilation;
- cross-corpus query compilation or runtime/native query execution;
- live ontology HTTP resolution;
- materialization from external source formats;
- finished reviewed mappings for every target corpus;
- a production package release or supported package-registry installation path.

I-004 validates authored semantic source artifacts and their internal/cross-artifact closure. It is not a resolver or runtime execution engine.

## Structural vs semantic validation distinction

The existing structural-validation section remains useful and must stay distinct:

- `load_source` / `validate_source` enforce syntax/plain-JSON/schema shape;
- `validate_semantic_bundle` operates after structurally valid artifacts have been assembled into a semantic bundle and enforces cross-artifact semantic invariants.

README should not imply that `load_and_validate()` automatically performs I-004 semantic validation.

## Minimum README change

A documentation-only repair should:

1. change current status from three to four shipped foundations;
2. add cross-artifact semantic validation as the fourth foundation;
3. remove/replace all claims that semantic validation is not implemented;
4. add an `### Cross-artifact semantic validation` subsection under implemented capabilities;
5. describe only the durable boundary above rather than enumerating every internal helper;
6. add a minimal import/assembly/validation example using public symbols;
7. keep compatibility evaluation, semantic IR/compiler, runtime resolution and corpus-specific mapping releases explicitly future work;
8. keep the accepted semantic-architecture section as architectural context, but distinguish architecture from the now-implemented validator.

## Minimal usage example shape

The public construction model is explicit artifacts, not hidden file discovery:

```python
from ontotf import SemanticArtifact, SemanticSourceBundle, validate_semantic_bundle

bundle = SemanticSourceBundle(
    profile=SemanticArtifact("profile", "profile.yaml", profile_data),
    expected_parent_manifest=SemanticArtifact(
        "expected_parent_manifest", "expected-parent.json", parent_data
    ),
    mappings=SemanticArtifact("mappings", "mappings.yaml", mappings_data),
    ontology_locks=(...),
    evidences=(...),
)
validated = validate_semantic_bundle(bundle)
```

README should keep this example schematic rather than pretending that partial placeholders are executable source data. It can use an ellipsis/comment to indicate optional/supporting artifacts and refer readers to the public bundle types.

## TDD recommendation

Before README is edited, add a static documentation test that asserts durable semantic distinctions rather than exact paragraphs. The RED should establish that current README:

- wrongly contains at least one explicit `semantic validation ... not yet shipped/not implemented` claim;
- does not list `validate_semantic_bundle` in minimal usage/capability prose;
- does not identify semantic validation as an implemented capability.

GREEN should require:

- `Cross-artifact semantic validation` in implemented capabilities;
- public `validate_semantic_bundle` surfaced;
- `SemanticSourceBundle` surfaced;
- future/unshipped status still explicitly names compatibility evaluation, semantic IR/compiler, runtime resolution and corpus-specific mappings;
- stale negation phrases about the semantic validator are absent.

Avoid brittle full-paragraph equality.

## Non-goals

- no semantic/runtime/schema/digest behavior change;
- no redesign of README information architecture;
- no full tutorial;
- no claim that all I-004 source artifacts can be inferred/discovered automatically;
- no compatibility or runtime capability inflation;
- no release/packaging claim.

## Conclusion

D-003 is implementable as a small documentation-only correction. Current main publicly ships I-004 cross-artifact semantic validation; README must present that as the fourth implemented foundation while keeping compatibility evaluation, semantic IR/compiler, runtime resolution and corpus-specific mapping releases clearly unshipped.
