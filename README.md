# TFont

TFont is a Python semantic interoperability layer for Text-Fabric / Context-Fabric corpora. The current package release is **v0.1.1**, a metadata-only packaging patch over the first semantic release, **v0.1.0**. The supported semantic contract remains one reviewed common ontology concept across three pinned corpus versions without guessing semantics from similar-looking feature names.

## What is shipped

One exact shared target: [OLiA Noun](http://purl.org/olia/olia.owl#Noun). Reviewed production profiles exist for:

| Corpus | Pinned upstream source | Native Noun selector |
| --- | --- | --- |
| [ETCBC BHSA](https://github.com/ETCBC/bhsa/tree/4db00e2157915495e1a4d3d57e41223df24775da) | revision `4db00e2…`, TF `2021` | `word.sp in {nmpr,subs}` |
| [ETCBC Syriac](https://github.com/ETCBC/syriac/tree/bb0eaa7e21b020a26b7566d2e495da9b1f84a919) | revision `bb0eaa7…`, TF `0.9` | `word.sp=subs` |
| [ETCBC ExtraBiblical](https://github.com/ETCBC/extrabiblical/tree/9a56288e6777bad6328856acf055c780e65dd5d9) | revision `9a56288…`, TF `0.2` | `word.sp in {nmpr,subs}` |

The differences are intentional: the reviewed Syriac encoding keeps proper nouns under `sp=subs`; BHSA and ExtraBiblical distinguish `nmpr` from `subs`. This is one selected feature value or finite set per corpus, **not** generic Boolean composition.

Public library APIs include source and cross-artifact validation (`validate_semantic_bundle`), deterministic parent/component and semantic digests, compilation (`compile_semantic_ir`), capability discovery, fresh runtime prerequisite evaluation, exact semantic resolution and execution (`execute_exact_semantic`). `load_production_noun_bundle` and `load_production_noun_bundles` expose installed production resources. Each executed corpus result contains node IDs, the exact mapping and projection, their reviews and evidence, expected/observed parent identity, prerequisite report and deterministic fingerprints.

**Trust boundary:** a production profile is authorized only for its exact reviewed parent manifest. The executor uses a current compiled IR, evaluates dependencies from the already-loaded TF API and resolves the request afresh before native selection; a caller-supplied plan or public hash cannot authorize execution on its own. Mismatched or unverified corpus data fail closed.

## Installation

Python 3.10 or newer. Download `tfont-0.1.1-py3-none-any.whl` from the [GitHub v0.1.1 release](https://github.com/alexsosn/ontoTF/releases/tag/v0.1.1), then install the **downloaded local wheel**:

```bash
python -m pip install ./tfont-0.1.1-py3-none-any.whl
```

For the local-corpus example below, separately install [Text-Fabric](https://github.com/annotation/text-fabric) (`python -m pip install text-fabric`). A development checkout may instead use `python -m pip install -e .`. v0.1.1 changes package license metadata only; it does not expand the v0.1 semantic/runtime scope. This GitHub wheel is the current v0.1 distribution; `pip install tfont` is **not** a supported PyPI installation claim.

Corpus files are **not bundled**. TFont does not download, load or update BHSA, Syriac or ExtraBiblical; you must obtain source corpora independently and respect their licenses. The separately bundled pinned OLiA ontology is CC BY 3.0 with its `ATTRIBUTION.txt` and `LICENSE.data`; ontoTF-authored code and mapping/profile metadata are MIT. BHSA corpus data have distinct CC BY-NC 4.0 terms.

## First success with real BHSA data

Prerequisite: obtain the `.tf` files in the `tf/2021` directory from the **pinned** [ETCBC BHSA revision `4db00e2157915495e1a4d3d57e41223df24775da`](https://github.com/ETCBC/bhsa/tree/4db00e2157915495e1a4d3d57e41223df24775da/tf/2021). Set `BHSA_TF_DIR` to the local directory *containing `otype.tf`, `sp.tf`, and the other original `.tf` files*, not its parent. Do not edit these files. This workflow uses the local `tf.fabric.Fabric` API and does not ask Text-Fabric to download an app or corpus.

```bash
export BHSA_TF_DIR=/absolute/path/to/bhsa/tf/2021
python - <<'PY'
import os
from pathlib import Path
from tf.fabric import Fabric
from tfont import (
    LoadedComponentContext, LoadedCorpusContext,
    SemanticKey, SemanticResolveRequest,
    load_production_noun_bundle, validate_semantic_bundle,
    compile_semantic_ir, execute_exact_semantic,
    tf_payload_digest, parent_manifest_digest,
)

# Observe actual local TF bytes; never pass the expected digest as an observation.
tf_dir = Path(os.environ["BHSA_TF_DIR"]).expanduser()
observed_component = tf_payload_digest(tf_dir)
bundle = load_production_noun_bundle("bhsa")
validated = validate_semantic_bundle(bundle)
expected_component = bundle.expected_parent_manifest.data["components"][0]
if observed_component != expected_component["content_digest"]:
    raise SystemExit("BHSA TF payload is not the pinned 2021 release; check BHSA_TF_DIR and revision")
observed_manifest = {
    "algorithm": "tfont-parent-components-sha256-v1",
    "components": [{
        "component_id": "bhsa-tf",
        "kind": "tf-payload",
        "identity_algorithm": "tfont-tf-files-sha256-v1",
        "content_digest": observed_component,
    }],
}
observed_parent = parent_manifest_digest(observed_manifest)
if observed_parent != validated.expected_parent_manifest_digest:
    raise SystemExit("BHSA parent identity differs from the reviewed production profile")

TF = Fabric(locations=str(tf_dir), silent="deep")
api = TF.load("sp")  # otype is a standard loaded TF feature
if api is None or api is False:
    raise SystemExit("Text-Fabric could not load the local BHSA sp feature")
component = LoadedComponentContext(
    component_id="bhsa-tf", content_digest=observed_component, api=api,
)
context = LoadedCorpusContext(
    corpus_id="bhsa", parent_manifest_digest=observed_parent,
    components=(component,),
)
ir = compile_semantic_ir((validated,))
request = SemanticResolveRequest(
    key=SemanticKey(
        profile_id="linguistic", capability_id="linguistic.part-of-speech",
        target="http://purl.org/olia/olia.owl#Noun",
        formal_kind="class", semantic_role="annotation-value",
    ),
    corpora=("bhsa",),
)
result = execute_exact_semantic(ir, request, (context,))
row = result.corpora[0]
print("BHSA noun nodes:", len(row.nodes), "first five:", row.nodes[:5])
print("Native mapping:", row.plan.mapping_id, "projection:", row.plan.projection_id)
print("Reviews:", row.plan.mapping_review.review_id, row.plan.projection_review.review_id)
print("Parent state:", row.plan.parent_state, "resolution:", result.resolution.resolution_fingerprint)
PY
```

To query all three corpora, load the other two **pinned** local TF APIs, separately hash their actual payloads and parent manifests, call `load_production_noun_bundles()`, validate/compile all three, then supply three `LoadedCorpusContext` objects and `corpora=("bhsa", "syriac", "extrabiblical")`. The installed profiles determine each corpus's native selector; the caller does not translate `Noun` into `sp` values manually.

## Supported boundaries and verification

This release supports the exact OLiA Noun slice only. It does **not** implement approximate alignment, a broad POS ontology, same-corpus multi-binding composition, generic query-language planning, MCP, remote ontology dereferencing, corpus acquisition or universal cross-corpus compatibility. Different corpus revisions require independently reviewed profiles, not an override flag.

The [clean-wheel acceptance runner](scripts/acceptance/v01_noun.py) tests the complete public three-corpus path and provenance using **API doubles** (not actual downloaded corpora) under Python 3.10/3.12. A separate Context-Fabric integration smoke uses a small genuine loaded CF corpus. Native corpus semantics are based on independently reviewed pinned source evidence; CI is not a claim of live real-three-corpus execution. See [v0.1.1 patch notes](docs/releases/v0.1.1.md), the historical [v0.1.0 release notes](docs/releases/v0.1.0.md), and [release tracker](https://github.com/alexsosn/ontoTF/issues/142).

## Development and architecture

The foundation also provides strict JSON/YAML source loading, JSON Schema contracts, RFC 8785/JCS canonicalization, semantic/evidence/review digest validation, and exact parent identity for files, directories and `.tf` payloads. Common ontology mapping authority is explicitly reviewed rather than inferred from labels. [AGENTS.md](AGENTS.md) defines the research/plan/TDD/adversarial-review loop; [P-003 architecture](docs/plans/P-003-common-ontology-semantic-adapter.md) documents the broader design. [GitHub Issues](https://github.com/alexsosn/ontoTF/issues) tracks remaining work.
