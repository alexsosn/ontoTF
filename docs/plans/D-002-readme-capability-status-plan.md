# D-002 plan: synchronize README capability/status claims

**Issue:** #76
**Research:** `docs/research/D-002-readme-capability-status.md`
**Base:** `main=fac75d5a251945653a7be585fa30eae34afd4693`

## Goal
Correct only the public README capability/status boundary so users can tell what ontoTF already ships from what is accepted architecture or still in implementation.

## RED contract
Before editing README, extend `tests/docs/test_readme_status.py` with assertions that current README must fail:

1. `Parent/component identity` (or an equally explicit heading) is present under implemented capabilities.
2. README no longer says parent-component identity is a later implementation stage.
3. README names the accepted common ontology semantic-adapter architecture and clearly marks it as architecture/design, not shipped semantic validation/runtime.
4. Cross-artifact semantic validation remains explicitly unshipped/in progress.
5. Minimal parent identity usage references current exported public API names (`directory_component_digest` and `parent_manifest_digest` or equivalent stable public functions).

Existing source-validation/digest/install regressions remain unchanged.

## Minimal GREEN README changes
- Update `Current status` to list three shipped production foundations: structural source validation, deterministic canonicalization/digests, parent/component identity.
- Move only semantic validation, compatibility evaluation, compiler/runtime resolution, and corpus mappings to future/in-progress wording.
- Add an `Accepted semantic architecture` section summarizing the P-003 native-record / typed-projection / external-reference separation and fail-closed no-target states.
- Explicitly say this accepted architecture is not yet the same as a shipped semantic validator/resolver.
- Add a short `Parent/component identity` implemented-capability section and one minimal public API example.

## Non-goals
- No code/schema/runtime changes.
- No tutorial expansion.
- No claim that semantic validation is implemented before its own merge.
- No package release claim.
- No finished-corpus-mapping claim.

## Test gate
After README edit:
- focused `python -m unittest tests.docs.test_readme_status -v`;
- full repository `python -m unittest discover -s tests -v` with packaging frontend available in CI;
- exact-head CI on supported Python versions if existing workflows trigger.

## Review gate
Fresh logically independent adversarial exact-head review must check for both stale underclaiming and accidental overclaiming. This authoring context cannot count as reviewer.
