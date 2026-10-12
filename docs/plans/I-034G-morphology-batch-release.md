# I-034G — batch-install BHSA/Syriac OLiA morphology from primary-source decisions

Research basis: merged PRs #353 (BHSA, 29 native selectors) and #355 (Syriac, 22 native selectors), frozen R-005 denominators and pinned OLiA OWL at acolirepo/olia@d3bd4f1. No new mappings are inferred from similar spellings.

## Semantic decisions
- BHSA: 12 proposed positive exact class projections and 17 native-only decisions. Host person (ps) remains distinct from pronominal suffix person/gender/number (prs_*). Only attested suffix values may be selected.
- Syriac: nine proposed positive class projections and thirteen native-only. R-005-observed st=c, vpm, unknown categories remain native-only; never silently equate c with source-grammar cst.
- All 51 source-feature/value identities must be in their immutable 219/74-item denominators and absent from the preceding released profile. No changes to historical 0.1–0.5 records.
- New OLiA targets require pinned class-declaration evidence; use older pinned noun morphology evidence for Masculine/Feminine/Singular/Plural. Distinct ontology lock, additional immutable opt-in 0.6 releases, default/current aliases unchanged.
- Distinguish **reviewed source proposals** from released, reviewed production mappings. A review in this PR must independently check the first source and OLiA declarations; do not claim a cryptographic approval or another human reviewer.

## Research → plan → RED → GREEN gates
1. Commit this plan and failing contract tests **before** profile resources exist.
2. Add only source-bound evidence, extra OLiA class lock/evidence, one shared new mapping file per corpus, immutable versioned 0.6 resources and release entries; keep all existing 0.5 resources untouched.
3. Run exact-head Python 3.10 and 3.12 CI, wheel acceptance and real corpus smoke where available. Fix actual failures, not tests to match invalid mappings.
4. Separate adversarial review on all 51 feature/value rows, with especially hostile checks for host/suffix conflation, unverifiable Syriac labels, Hebrew perfect-as-past, nominal emphatic-as-emphasis and unobserved categories. GitHub review must identify counterexamples and final head.
5. Publication/coverage: review-backed production counts are 29 + 22 only if all rows become installed and manifest accounting is reconciled. Do not count an unreviewed proposal as production.

## Constraints
No ticket-specific CI workflow, no change to historical default loaders, no forged protected handoff signature, no ontology claims from arbitrary node names, no cross-ontology scope creep.
