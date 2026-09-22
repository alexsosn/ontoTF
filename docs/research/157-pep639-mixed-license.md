# #157 — PEP 639 packaging metadata for mixed-license TFont distributions

Date: 2026-09-22. Research only; no runtime, packaging or published-release changes in this gate.

## Observed at `main` `dcab3a473f3a4347554194ec9a5e34238b7c0769`

- `pyproject.toml`: `setuptools>=75`, `license = {file = "LICENSE"}` and `License :: OSI Approved :: MIT License` classifier. The existing v0.1 wheel's root `LICENSE` is MIT; setuptools 84 issued license-table/classifier deprecation warnings (#157).
- The repository source paths `src/tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/{olia.owl,LICENSE.data,ATTRIBUTION.txt}` are bundled in the wheel at `tfont/resources/...` (without the repository's `src/` prefix). `LICENSE.data` is the full Creative Commons Attribution 3.0 Unported legal code. `ATTRIBUTION.txt` explicitly identifies pinned upstream OLiA revision, CC BY 3.0, and keeps ontoTF-authored mappings under MIT. Third-party TF/MQL corpus data are **not** bundled.
- I-013 release CI verifies the root MIT `dist-info/licenses/LICENSE` and separate package-resource OLiA notices, but does not require the combined license expression or enumerate both licenses in `License-File` metadata. Its v0.1 release is already published: this migration must not rewrite/relabel that historical wheel or tag.

## Standards and independent evidence

- PyPA PEP 639 specifications: `project.license` is an SPDX license expression applying to the **distribution archive**. `project.license-files` lists relative source paths; the backend must include every matched file and emit `License-File` core-metadata entries. Deprecated TOML license table and license Trove classifiers should be removed. https://packaging.python.org/en/latest/specifications/pyproject-toml/ ; https://peps.python.org/pep-0639/
- PyPA's explicit *mixed-licensed bundled code* scenario: `License-1 AND License-2` indicates both apply to the archive or parts of it; `OR` means the recipient may choose either. Corresponding full license texts must be packaged and listed. https://packaging.python.org/en/latest/guides/licensing-examples-and-user-scenarios/
- SPDX's canonical identifier for this exact OLiA notice is `CC-BY-3.0`, not `CC-BY-3.0-IGO`, `CC-BY-4.0` or `CC-BY-NC-4.0`. https://spdx.org/licenses/CC-BY-3.0.html
- Setuptools supports SPDX expression plus `project.license-files` from v77.0.0; PyPA's compatibility guide names v77.0.3 as its known-good first release. Set a conservative build minimum `setuptools>=77.0.3` and remove the old classifier. https://setuptools.pypa.io/en/stable/userguide/license_migration.html ; https://packaging.python.org/en/latest/guides/writing-pyproject-toml/

## Alternatives assessed

1. **`license = "MIT"` alone — reject.** It incorrectly presents the mixed MIT + bundled OLiA CC BY 3.0 archive as solely MIT. The repository's source-code MIT license is still correct; the archive-level field has different scope.
2. **`MIT OR CC-BY-3.0` — reject.** That would misleadingly suggest recipient can choose either license for the whole distribution.
3. **Leave license expression unset and include license files only — permissible fallback, but loses machine-readable archive-level license specificity.** Not preferred if the compound expression builds cleanly.
4. **`license = "MIT AND CC-BY-3.0"` plus explicit root/OLiA license files and attribution — recommended.** The conjunction represents separately licensed parts, not relicensing all ontoTF code CC BY or all OLiA bytes MIT. Keep human-facing README/ATTRIBUTION distinction unchanged.

## Proposed minimal implementation contract for subsequent plan/TDD

- Bump only *build-time* minimum to `setuptools>=77.0.3` (runtime Python range unchanged), remove obsolete classifier; use `[project] license = "MIT AND CC-BY-3.0"` and `license-files = ["LICENSE", "src/tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/LICENSE.data", "src/tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/ATTRIBUTION.txt"]`.
- Build both wheel and sdist in isolation. Assert metadata `License-Expression: MIT AND CC-BY-3.0`, corresponding `License-File` rows, correct license-file bytes present under `.dist-info/licenses/`, original resource OLiA legal text/attribution still accessible via package loader, unchanged `0.1.0` version and no added TF/MQL corpus data. Ensure no setuptools deprecation warnings about `project.license` table/classifier/legacy `tool.setuptools.license-files`.
- Test from clean outside-checkout installation and relevant existing I-009/I-012/full CI; no changes to semantic data or mapping digests. Do not republish v0.1.0 from a post-tag commit: this work is post-release maintenance and must not mutate the published release. No PyPI release or more automation.

## Residual uncertainty and review challenge

- Confirm the build backend preserves exact nested paths in `License-File` entries and the wheel's `dist-info/licenses/` layout; test observed archive bytes rather than assuming packaging path behavior. If setuptools rejects nested license path glob or warns on an unmatched file, resolve it via a minimal packaging change, never by dropping CC BY from metadata.
- The archive-level conjunction is a *metadata summary*, not a claim that the two licenses apply to every constituent file. Keep per-component licensing notices as authoritative. This is a packaging interpretation, not a legal determination about redistribution beyond the existing reviewed upstream license evidence.
