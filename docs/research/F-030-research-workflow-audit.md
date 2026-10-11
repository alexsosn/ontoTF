# F-030 / #291: retire redundant historical research test workflows

**Issue:** #291
**Base:** `bea8fc30d1d5b24c42ab114f0dd801868eefe4ff` (merged #320, 66 workflow YAMLs).
**Method:** Inspect each retired YAML body and the exact existing test modules; do not infer equivalence from names alone.

## Real workflow command audit

| Retire (8 workflow YAML files) | Unique executable command | Existing canonical owner |
| --- | --- | --- |
| `r001-report-validation.yml` | `python -m unittest tests.research.test_r001_report -v` | `unittest discover -s tests -v` |
| `r002-report-validation.yml` | `python -m unittest tests.research.test_r002_report -v` | `unittest discover -s tests -v` |
| `r003-report-validation.yml` | `python -m unittest tests.research.test_r003_report -v` | `unittest discover -s tests -v` |
| `r004-report-validation.yml` | `python -m unittest tests.research.test_r004_report -v` | `unittest discover -s tests -v` |
| `r005-generated-validation.yml` | `python -m unittest tests.research.test_r005_generated -v` | `unittest discover -s tests -v` |
| `r015-bundle-research.yml` | `python -m pytest -q` for five explicit `test_r015_*.py` modules | `python -m pytest tests/research -q` |
| `r016-approximate-policy.yml` | `python -m pytest -q tests/research/test_r016_policy.py` | `python -m pytest tests/research -q` |
| `r017-reference-policy.yml` | `python -m pytest -q` for two `test_r017_*.py` modules | `python -m pytest tests/research -q` |

All eight retired workflows only set up Python and invoke the test commands above. R-001–R-005 are only triggered by historical research branch pushes/manual dispatch; R-015–R-017 also have targeted pull_request triggers. Canonical `full-suite.yml` already runs **unconditionally on every PR head and main**, in both Python 3.10 and 3.12, with these two test commands, immutable coverage `--check` commands, wheel build and installed package smoke. `tests/research/__init__.py` is present. Inspected all fourteen relevant `tests/research/test_r*.py` files and found direct test functions (including 4+13+14+13+14 unittest tests for R001–R005 and 121 pytest test functions across R015–R017). No executable research generator is run by the eight removed workflows.

## Adversarial exclusions

- `r005-research-inventory.yml`: intentionally **retained**. Fetches seven pinned external TF corpora, computes source inventories and compares committed outputs byte-for-byte; not covered by offline tests.
- `r011-report-validation.yml`: retained. Runs R-011 measurement script and targeted pytest under **Python 3.11**, outside main's 3.10/3.12 matrix.
- `r020-denotational-semantics.yml`: retained. Re-runs source-based denotational report on Python 3.10 and 3.12 and byte-compares a stored JSON artifact.
- `i027b3-extrabiblical-source.yml`, `i027c1-native-pos.yml`: original source provenance checks; retain.
- `i033e3-protected-batch-review.yml`: separate privileged reviewer and approval authority; retain.
- Existing F-/D-series metadata and reviewed release checks remain unaffected.

## Safety and limits

Eliminating eight workflow YAMLs does not eliminate their tests; an always-discovered new regression test must prove all fourteen test modules and both unconditional owners are present. No source, mapping, snapshot or trust boundary modifications. Historical workflows' manual dispatch capability disappears, but all preserved tests remain runnable by `workflow_dispatch` on the canonical full suite. Existing workflow-name branch protection could be configured externally; connector cannot assert exact names are or are not required. This is an incremental #291 slice, not proof of measured runner-time savings or completion of the single-workflow redesign.
