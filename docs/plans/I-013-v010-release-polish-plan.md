# I-013 plan: v0.1.0 release candidate and publication

Issue #166; research PR #167 merged as `069dfcf0b3544fd3cd6bd203b4bd54c2411b82e5`. Plan-only, no implementation in this PR.

## Release contract and boundaries

Ship exactly one supported v0.1 semantic slice: OLiA Noun over pinned BHSA, ETCBC Syriac and ETCBC ExtraBiblical, already-loaded TF/CF, deterministic exact native selectors and per-corpus provenance. Do not advertise PyPI, corpus downloader, generic mappings, MCP, live ontology evaluation or three real corpora acquired in CI. Package source remains MIT, bundled OLiA snapshot CC BY 3.0 with attribution; upstream corpora not bundled and retain their own licenses.

Expected changed files for the release candidate:
1. `pyproject.toml`: `project.version = '0.1.0'` only; keep dependency and packaging contracts otherwise unchanged. Packaging SPDX warnings are separately #157, not a failing build.
2. `README.md`: replace stale feature claims with concise up-to-date functionality, pinned corpus support, local installation, copy-paste *real* BHSA first-success code and limitations. Fix GitHub links to ontoTF.
3. `docs/releases/v0.1.0.md`: short versioned release notes, precise support and license/attribution boundaries, scope/test caveat.
4. `tests/i013/test_release_red.py`: version/documentation/release-notes and sample-code gate under `unittest`, included in authoritative full suite.
5. `.github/workflows/i013-release.yml`: narrowly gated verification and main-only publishing, no feature-code changes.

## Documentation first-success code contract

A one-corpus BHSA example is a genuine smallest win, not I-012's fake API. `python -m pip install ./tfont-0.1.0-py3-none-any.whl` is a local downloaded release wheel install; install Text-Fabric separately for a local example. Caller supplies `BHSA_TF_DIR` pointing *to exact `.tf` files* from `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da/tf/2021`; do not assume user's cache path. Code uses `from tf.fabric import Fabric`, `TF = Fabric(locations=str(tf_dir))`, `api = TF.load('sp')` (otype auto-loaded), never `tests.*` or fabricated TF API. `tf_payload_digest(tf_dir)` reads real local `.tf` bytes, checked against bundled `bhsa-tf` content digest. Build observed manifest with `algorithm='tfont-parent-components-sha256-v1'` and exactly the reviewed `bhsa-tf` component (`kind='tf-payload'`, `identity_algorithm='tfont-tf-files-sha256-v1'`, observed digest); compute `parent_manifest_digest()` and compare with `validated.expected_parent_manifest_digest`. Do not authorize using expected digest without hashing real data. `compile_semantic_ir((validated,))` must work for the single corpus. Construct `SemanticKey(profile_id='linguistic', capability_id='linguistic.part-of-speech', target='http://purl.org/olia/olia.owl#Noun', formal_kind='class', semantic_role='annotation-value')`, `SemanticResolveRequest(...,corpora=('bhsa',))`, `LoadedComponentContext('bhsa-tf',content_digest,api)`, `LoadedCorpusContext('bhsa',observed_parent,(component,))`, call `execute_exact_semantic`, print count, first five nodes, plan.mapping_id, plan.projection_id, plan.parent_state, and plan mapping/projection review IDs. Do not claim nodes from BHSA can be known without real corpus bytes. Plain empty result is valid; identity mismatch is actionable and must not be worked around by overriding the release policy. The example should be Python copy/paste, not shell with fictitious imported vars. README makes local TF directory prerequisite prominent and links Text-Fabric and upstream BHSA license. Three-corpus API pattern can be described without another huge example.

## RED and GREEN gates

Tests-only RED branch from merged plan. Write unittest `tests/i013/test_release_red.py` proving:
- `tomllib` on 3.11/3.12, `tomli` unavailable 3.10: avoid introducing tomli; read/version regex or `importlib.metadata.version('tfont')` depending editable packaging, check `pyproject` with safe regex, plus wheel metadata separate CI;
- pyproject version 0.1.0, README no claims that compiler/resolver/executor not shipped, README links current repo and real BHSA first-success path, release notes exist and identify exact boundaries;
- sample uses `tf_payload_digest`/`parent_manifest_digest` over caller dir, never `tests.i008` or fake loaded API;
- wheel metadata must declare 0.1.0, include root MIT LICENSE, OLiA CC BY 3.0 license/attribution/snapshot, production profiles and no corpus TF bytes.

RED must be the expected version/docs/release-note failures while existing I-012, I-009 and full suite remain green. Do not make new public API fail artificially.

Minimal GREEN changes metadata/docs/notes only and focused CI/release workflow. If docs example exposes actual public API defect, add targeted failing regression before production changes. Do not change source semantics merely to make doc example prettier.

## Release workflow and publishing authority

One permanent `.github/workflows/i013-release.yml` runs on `pull_request` for candidate verification and `push` to `main` only when `docs/releases/v0.1.0.md` changes. Default permissions `contents: read`. Matrix `verify` Python 3.10/3.12 runs authoritative unittest full suite, plus focused release doctest/contract. Matrix `wheel-acceptance` Python 3.10/3.12 builds wheel with `python -m build --wheel`, asserts exactly `tfont-0.1.0-py3-none-any.whl`, inspects zip wheel METADATA Version, license/attribution and no `.tf`, creates fresh venv outside checkout, installs wheel and runs copied I-012 runner with `python -I` and checkout-forbidden root. This may reuse existing I-012 workflow implementation by calling the same script, not invent a second acceptance runner. If workflow overhead problematic, limit full suite to existing `Full repository suite` status but do NOT publish before seeing both Python versions green on exact main.

`publish` job has `needs: [verify, wheel-acceptance]`, `if: github.event_name == 'push' && github.ref == 'refs/heads/main'` and the only `contents: write` permission. It checkouts exact `${{ github.sha }}`, validates version/release notes, rebuilds exact wheel for attachment (or uses an artifact uploaded from validated build), checks `gh release view v0.1.0`: if exists, never overwrite or move a tag; fail if inconsistent and otherwise skip. If absent, also check whether `refs/tags/v0.1.0` exists: if so, require it to point to THIS `github.sha`, otherwise fail closed. Create a release with `gh release create v0.1.0 <wheel> --target "$GITHUB_SHA" --title 'TFont v0.1.0' --notes-file docs/releases/v0.1.0.md`, checking `GITHUB_TOKEN` and relevant permissions. API readback must confirm tag, target commit SHA, release non-draft and wheel asset. If permission or release mechanics fail, leave issue and tracker open; no PyPI fallback. No write permission in PR jobs; no tagging or publication in tests/reviews.

Caveat: `gh release create` may create a lightweight tag if missing; tag immutability is not enforced by repo policy, but this workflow must never force/move it. The publishing path has not yet been exercised, so final status cannot be claimed until actual GitHub API readback.

## Exact-head final gate

1. Focused I-013 tests green Python 3.10/3.12, repo full suite on exact head green both, fresh-wheel acceptance both, wheel artifact and metadata inspect PASS.
2. Fresh independent adversarial reviewer checks truthful README, sample's real data identity against accidental expected-digest shortcut, native selector actual contract, license file completeness, no leaked fake API, release workflow write scope and failure handling, no premature public release.
3. PR merge with expected-head SHA only. Publication main-push workflow then independently verifies exact merged main before any GitHub tag/release. Observe readback and only then close #166 and #142.

If workflow cannot publish because GitHub Actions has insufficient contents write permission or tag rules, do not create a new unsafe backdoor/secret: provide the user the exact operational blocker and leave publication checklist open. No further feature scope.