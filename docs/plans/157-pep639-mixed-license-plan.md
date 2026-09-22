# #157 — PEP 639 mixed-license distribution metadata plan

Accepted research prerequisite: `docs/research/157-pep639-mixed-license.md` (merged via PR #171); source main `2be24cc571923c27d31c6251fb86f850e5daec64`. This plan changes packaging metadata only, not file-level licenses or existing v0.1.0 release.

## Public and compatibility contract

- Current distribution version stays `0.1.0` on `main` as development source metadata after v0.1 tag. Do **not** overwrite v0.1.0 GitHub Release, retag, upload a replacement asset or claim a new release. No PyPI.
- `[build-system].requires`: replace `setuptools>=75` with `setuptools>=77.0.3` (keep `wheel`); runtime `requires-python` and dependencies unchanged.
- `[project]`: replace legacy `license = {file = "LICENSE"}` and remove old `License :: OSI Approved :: MIT License` classifier; add `license = "MIT AND CC-BY-3.0"`, `license-files = ["LICENSE", "src/tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/LICENSE.data", "src/tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/ATTRIBUTION.txt"]`. These entries denote the archive's distinct license obligations and legal notices, not double-licensing each file.
- Preserve original root MIT `LICENSE`; OLiA `olia.owl`, `LICENSE.data`, `ATTRIBUTION.txt`, lock and profile resources byte-for-byte and in `tfont/resources/...` package paths. No corpus TF/MQL payload. Release notes/README already explain file-level licensing; change them only if contract test proves materially inaccurate.

## TDD test design (write tests only, demonstrate RED on exact head)

New `tests/packaging/test_pep639_mixed_license.py` uses unittest, standard library, built distributions. A cheap contract test checks pyproject license metadata/absence of legacy fields (Python 3.10 text/regex is sufficient). Heavy distribution test is enabled via `I157_PACKAGING_TEST=1` in dedicated CI to avoid doubling builds for every full-suite job.

With `python -m build --wheel --sdist --outdir <temp>` in an isolated outside-checkout directory, assert one wheel and sdist, version `0.1.0`; inspect wheel `dist-info/METADATA` via email parser and sdist `PKG-INFO` from tarfile. Both must emit exact `License-Expression: MIT AND CC-BY-3.0` and three `License-File` paths matching actual files; no legacy `License` metadata or obsolete MIT Trove license classifier. Confirm LICENSE/OLiA notice/attribution **bytes** in both archives at metadata-declared paths (for wheel `.dist-info/licenses/<License-File>`; for sdist relative project root). Confirm original OLiA package resources still present separately and corpus `.tf`/`.mql` files absent. Capture build combined output and reject `SetuptoolsDeprecationWarning` about legacy license table/classifier or `project.license` warning; do not assert zero unrelated warnings. Smoke-import package/resource from a fresh `pip install` of built wheel outside checkout and verify `importlib.resources` legal text/attribution bytes.

RED expectation on current main: old `license = {file = "LICENSE"}` and classifier, missing `License-Expression`, no OLiA `License-File` rows; existing I-009 wheel and I-012 acceptance remain green. Assert focused CI demonstrates the *expected* failures before metadata mutation; new tests cannot be silently skipped on dedicated gate.

## GREEN implementation and CI

Change only `pyproject.toml` for production. Add one read-only focused `.github/workflows/i157-pep639-license.yml` with push/PR matching pyproject, test, workflow and docs; Python 3.10/3.12, `python -m pip install -e . build`, run `I157_PACKAGING_TEST=1 python -m unittest tests.packaging.test_pep639_mixed_license -v`, then `python -m unittest discover -s tests/i009 -v` and the small packaging control. Reuse existing authoritative full-suite on PR; do not add a second workflow that runs full `unittest discover -s tests -v`. Avoid writes, releases and tags in CI.

## Final gates

Inspect exact-head focused CI both versions and independent full suite both versions; existing I-013 release metadata/resource and I-009 tests must pass. Adversarial final review must inspect generated archive bytes/metadata, `AND` semantics, build warnings, no corpus/ontology semantic mutation, no release workflow trigger on this PR/merge, no duplicate full-suite ownership, and any accidentally included legal material. Merge only after PASS and close #157. Historical v0.1 release remains tied to `dcab3a473f3a4347554194ec9a5e34238b7c0769` throughout.
