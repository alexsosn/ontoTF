# I-013 research: first v0.1.0 release boundary

Issue: #166. Baseline: `main=3c5d2b52c1a738b8a31b0b3fda196eaf49c6b84b`. Research only; no version/docs/release mutation in this gate.

## Verified state and actual gaps

- `pyproject.toml` still declares `tfont` version `0.0.0`, supported Python >=3.10, setuptools wheel, and explicitly packages schemas, three profile resource trees, and OLiA snapshot/attribution/license. The current SPDX warning is already recorded in #157 and does not fail the wheel build; don't silently expand this ticket into that refactor.
- `README.md` is materially outdated: it says only I-004 validation is implemented, explicitly denies compiler, runtime prerequisite evaluation, resolver, executable mappings and native execution. It also links the old GitHub repo path. These are release-blocking documentation errors.
- I-007 prerequisite evaluation, I-008 scalar executor, I-010 finite-set executor, I-011 release-authored exact-only parent policy, I-009 production three-corpus bundles and I-012 integrated clean-wheel acceptance are all merged. The canonical v0.1 semantic request is `OLiA #Noun`, BHSA and ExtraBiblical `word.sp in {nmpr,subs}`, Syriac `word.sp=subs`. I-012 #165 verifies wheel -> production validation -> compiler -> fresh runtime report -> exact resolver -> execution/provenance and parent-drift fail-closed on Python 3.10/3.12, with independent review. It uses small already-loaded TF API doubles, not actual downloaded corpora.
- No GitHub releases currently exist (GitHub releases API returned `[]`); the connected GitHub tool supports repository file/branch/PR write actions but does not advertise `create_release`, `create_tag`, or workflow dispatch. Publication therefore needs a separately reviewed, tightly scoped, authenticated Actions path, not an invented connector action. The feature-branch write workflow in I-012 demonstrated a GitHub Actions `GITHUB_TOKEN` can push to its own branch, but **this does not prove release creation permission**. Publication success must be read back from actual GitHub release/tag endpoints; if forbidden, report a blocker and keep #142/#166 open.

## Minimum truthful release documentation

README must open with what actually works: semantic bundle validation and deterministic IR, reviewed v0.1 OLiA Noun exact resolution and loaded native TF execution for three **specific pinned upstream corpus revisions**; results contain nodes, mapping/projection/review provenance, parent and report identities. The first milestone is this narrow slice, not generic ontology inference. Correct GitHub links to `alexsosn/ontoTF`.

Explain that TFont bundles only mapping/profile metadata and a CC-BY-3.0 OLiA snapshot with its attribution, **not** corpus `.tf` or `.mql` bytes. ontoTF-authored code/profiles are MIT; source corpora retain their upstream licenses. No implicit permission to redistribute/commercialize third-party corpora.

Install instructions must distinguish `pip install <wheel downloaded from actual GitHub v0.1.0 release>` from future/unavailable PyPI (`pip install tfont` is NOT a supported release instruction until verified). Optionally `pip install .` from a local checkout for developers. Do not put an unverified download URL in a tutorial before publication; link the actual GitHub Releases landing page when published.

A copy/paste *real* first-success example can be single-corpus BHSA to minimize prerequisites, then show how the API accepts all three. It must use `tf.fabric.Fabric` to load an existing local TF directory, or clearly mark a caller-provided already-loaded TF/CF API. Verified upstream `annotation/text-fabric/tf/docs/about/usefunc.md` documents `from tf.fabric import Fabric; TF=Fabric(locations=..., modules=...); api=TF.load(features)` and notes `tf.app.use` may auto-download corpus **and app code**. Prefer the local Fabric path in the minimal example to avoid unexpected acquisition and code execution. The caller explicitly supplies the directory containing the pinned BHSA TF `2021` payload. Compute actual `tf_payload_digest(tf_dir)` from that exact folder, construct the parent manifest with the known `component_id='bhsa-tf'`, `kind='tf-payload'`, `identity_algorithm='tfont-tf-files-sha256-v1'`, `content_digest=actual_digest`, `algorithm='tfont-parent-components-sha256-v1'`, derive `parent_manifest_digest()` and check both actual digest and parent against `load_production_noun_bundle('bhsa')` expected identity *before* executing. Load the `otype` and `sp` TF features; `LoadedComponentContext.api` must be the actual loaded TF API. Validate, compile, construct exact Noun `SemanticResolveRequest` for `('bhsa',)` and call `execute_exact_semantic` with one `LoadedCorpusContext`; print node count, example nodes and mapping/projection provenance. An identity mismatch should fail with an actionable message rather than suggest bypassing exact-only policy. Correct BHSA data source is `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`, TF directory `2021`; the corpus README documents Text-Fabric loading and CC BY-NC 4.0 corpus license.

This first-success example is not the fixed fake-API `scripts/acceptance/v01_noun.py` script; that script is for the release integration test only. README must not claim that I-012 CI acquired and tested live corpora end to end. A real TF 0.5.7 smoke under I-008 tests the lower-level TF API separately.

## Release notes and version contract

Set `project.version='0.1.0'` once, keep resource profile version `0.1.0`. Add short `docs/releases/v0.1.0.md` with supported slice, installation, attribution/license boundaries, known limitations and test scope. Freeze README and release notes wording before code changes so tests can reject stale claims. Build the versioned `tfont-0.1.0-py3-none-any.whl`, check filename and wheel METADATA Version `0.1.0`, verify MIT root LICENSE and OLiA license/attribution/snapshot, no corpus bytes and no synthetic fixtures inside wheel; install in an isolated venv and run I-012 acceptance plus full suite on both supported CI versions.

## Publication mechanism options

1. GitHub connector direct tag/release action: NOT exposed by installed tool, cannot assume available.
2. Reviewed GitHub Actions workflow with `contents: write` scoped to publishing, runs only on the release-notes file's initial push to default branch, checks commit is exactly verified main and version `0.1.0`, independently reruns the clean-wheel acceptance and full suite on 3.10/3.12 as required, then creates immutable tag/release and attaches the exact built wheel using `gh release create --target <verified SHA>`; fail closed if `v0.1.0` exists with unexpected SHA; no overwrite or force. The main push workflow itself must be reviewed before merge, and cannot claim publication until GitHub confirms it. Keep workflow inert on ordinary later docs edits.
3. Manual owner action is a fallback only if Actions token cannot publish; record exact blocker and safe command. Do not use user credentials or publish PyPI.

Prefer one narrow reviewed automated publication workflow that *does not* run on PR with write permissions or publish when only one CI matrix row succeeded. A `needs` dependency must gate any publishing job on version, full-suite (both Python versions) and clean-wheel acceptance (both versions). Use `github.ref == 'refs/heads/main'` and an exact release-specific path trigger, plus one-time existing tag/release checks. Publish wheel + release notes after gates, then verify the release URL, tag SHA and downloadable asset with GitHub API. Never retag a divergent existing version.

## Scope guards and adversarial risks

- Do not convert research into generic release engineering, signing, credentials storage, auto version bump, PyPI or corpus downloader.
- Do not accidentally describe baseline `tf.app.use` as offline: it may fetch remote app code and corpus payload.
- Do not derive observed parent from the *expected* manifest without hashing real caller-owned TF data; that would make the example falsely self-authorizing.
- Do not claim exact semantic mapping universally across all versions/corpora.
- Do not cite current full-suite as evidence that real corpus acquisition succeeded.
- Do not publish a release before candidate test gates and fresh adversarial review.

Next gate: independent skeptical research review; then plan-only PR freezing exact file diff, real sample code and testing/publication implementation.