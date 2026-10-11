# F-030 / #291: exact-head CI POS-pilot plan

**Issue:** #291

Research: `docs/research/F-030-pos-ci-pilot.md`.

## Contract
1. Preserve `full-suite.yml` as the single unconditional PR regression owner on the exact SHA for Python 3.10 and 3.12, `unittest`, `pytest`, both existing frozen generator checks, wheel and wheel-install checks.
2. Move seven additional offline pinned-source successor/coverage commands from the old POS workflows into a single named `--check` step in `full-suite.yml`, with no runtime code change.
3. Remove precisely seven redundant workflows. Preserve external pinned-source checkout workflows `i027b3` and `i027c1`, as well as `i033e3` protected-review release trust boundary.
4. Add an automated ownership test that fails if an offline check is missing/duplicated, the associated script or regression test package disappears, any retired workflow returns, the exact-head checkout or cross-version matrix is lost, or external-source workflows are accidentally removed.
5. The existing F-007 tests still require some legacy workflow owners; leave all of those in this pilot.

## TDD + review gates
- RED: commit the ownership test before changing workflow files. The original seven workflow files still exist and their moved commands are absent from full-suite; both conditions trigger explicit failures.
- GREEN: consolidate one fixed step and retire old workflows, then run local static guard and full exact-head CI (Python 3.10/3.12, wheel).
- Independent adversarial review: inspect the real full-suite diff and all seven deleted workflow scripts against published source/coverage; check for omitted commands, lost source checkouts, unsafe PR token scope, or a coverage regression.
- Only expected-head merge after the final-head checks pass and skeptical review has no blocking findings.

## Compatibility
This phase changes only workflow ownership, never source/ontology evidence, the Text-Fabric runtime, review authority or artifacts. Branch protection may still list obsolete check names; assess and coordinate migration before broad removal. The seven targeted workflows are a bounded pilot, not closure of all #291.
