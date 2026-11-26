# I-003 parent component identity research

**Issue:** #20  
**Recorded:** 2026-09-06  
**Baseline:** `67f55b52cc75eb3704357e4ed70851c5d7db6ad2`  
**Scope:** research only; no production identity implementation in this commit.

## 1. Question

I-003 must turn concrete parent bytes into deterministic component identities and then into the transport-independent parent component-manifest identity accepted by R-001/P-001. It must not decide whether a different component set is compatible; that is I-004/I-005 territory.

The implementation must distinguish three byte-addressing shapes:

1. one exact regular file;
2. a recursive directory-like native component;
3. a Text-Fabric payload directory, whose addressed file boundary is defined by the TF loader rather than by arbitrary repository recursion.

## 2. Accepted ontoTF contract

### R-001 component-aware exact identity

Accepted `docs/research/R-001-distribution-architecture.md` requires exact compatibility to bind a transport-independent component manifest covering **every semantically addressable native component** used by the profile: TF payload plus any external sidecar, catalogue, zero-span store, or native-adapter artifact.

The important negative invariant is explicit: unchanged TF bytes do **not** preserve `verified-exact` when a required non-TF component changes.

R-001's example names:

- `ontotf-parent-components-sha256-v1` for the parent component-manifest identity contract;
- `ontotf-tf-files-sha256-v1` for the TF payload file-set identity.

### P-001 byte projections

Accepted `docs/plans/P-001-foundation-poc-design.md` section 6 says:

- component records contain `component_id`, `kind`, `identity_algorithm`, `content_digest`, plus optional `logical_locator` and `license_ref`;
- component records are sorted by `component_id`;
- parent identity is SHA-256 of canonical JSON over **semantic identity fields**;
- absolute machine paths are excluded;
- `ontotf-tf-files-sha256-v1` hashes a sorted list of `{relative_logical_path, sha256}` records for addressed TF payload files;
- directory-like sidecars use the same sorted-path/per-file-digest pattern;
- a single-file sidecar uses SHA-256 of exact bytes.

For I-003, the semantic component identity fields are therefore exactly:

```text
component_id
kind
identity_algorithm
content_digest
```

`logical_locator` is acquisition/runtime metadata, not semantic identity. `license_ref` governs redistribution/usage but does not alter the parent bytes or mapping behavior, so it is also excluded from the parent semantic digest. Both remain preserved in the manifest source and source integrity.

## 3. Current structural schema

`schemas/parent-component-manifest.schema.json` on baseline `67f55b52...` requires:

```text
algorithm = ontotf-parent-components-sha256-v1
components[]:
  component_id
  kind
  identity_algorithm
  content_digest
```

Allowed kinds are:

```text
tf-payload
sidecar
catalogue
zero-span
native-adapter
```

Optional component fields are `logical_locator` and `license_ref`; additional fields are rejected structurally.

I-003 should not duplicate all I-001 schema semantics, but its digest projection must fail closed on missing/unknown projection fields so a future semantic field cannot be silently omitted from a reused v1 algorithm.

## 4. Current I-002 primitives

Merged I-002 at `67f55b52...` provides:

- strict RFC 8785/JCS canonical JSON bytes;
- SHA-256 conventions `sha256:<64 lowercase hex>`;
- stable JSON/Unicode error behavior;
- UTF-16 code-unit ordering for semantic string sets/IDs;
- exact source/evidence/mapping/profile digest patterns.

I-003 should reuse `ontotf.digests.canonical_json_bytes` rather than add a second canonical JSON implementation.

The project currently supports Python `>=3.10`.

## 5. Actual Text-Fabric payload boundary

Text-Fabric current `master` is still `annotation/text-fabric@1079c68e051947efd955b61ad499e3a9beb03b09`, the same revision accepted by R-001.

In `tf/core/fabric.py::_makeIndex`, for each selected `location/module`, TF:

1. scans that module directory with `scanDir`;
2. selects entries for which `e.is_file()` is true and `e.name.endswith(".tf")`;
3. indexes those **direct** `.tf` files by feature name;
4. does not recursively treat arbitrary repository descendants as TF feature files.

`Fabric.load()` also documents feature names as `.tf` filenames without directories/extensions. Config features such as `otext.tf` are ordinary `.tf` files in that same scanned set.

### Consequence for I-003

`ontotf-tf-files-sha256-v1` should hash every direct regular `.tf` file in the addressed TF module directory, including config `.tf` files. It should **not** recursively hash README files, generated caches, VCS metadata, sibling source material, or `.tf` files in nested directories that the addressed TF module would not scan.

A TF directory with no direct `.tf` files cannot establish a TF payload identity and should fail closed rather than produce a plausible empty corpus identity.

## 6. TF symlink mismatch and ontoTF policy

TF's `DirEntry.is_file()` default follows symlinks. If `feature.tf` is a symlink, the effective bytes can therefore depend on a host-specific target outside the module directory.

ontoTF exact identity must be transport-independent, so I-003 should be stricter than the loader: a selected `.tf` entry that is a symlink/reparse-link must fail with a stable identity error rather than silently hashing the target.

Non-`.tf` entries are outside the TF payload boundary and are ignored by the TF-specific helper. A nested directory is also outside that direct TF payload boundary.

## 7. Recursive native-directory identity

A directory-like sidecar is different from a TF module. Its addressed byte boundary is the entire recursive tree of regular files under the declared root.

The deterministic projection is a list of:

```json
{
  "relative_logical_path": "path/with/forward/slashes",
  "sha256": "sha256:<file-byte-digest>"
}
```

Rules:

- hash exact regular-file bytes; no newline/BOM/text normalization;
- derive the logical path relative to the component root;
- represent separators as `/` regardless of host OS;
- reject backslash-bearing path components because the same spelling is a separator on Windows and a filename character on POSIX;
- require path strings to be Unicode scalar/UTF-8 representable; undecodable surrogate-escaped host filenames are not portable identity inputs;
- sort records by UTF-16 code-unit order of `relative_logical_path`, matching I-002's language-neutral string ordering rule;
- include hidden files because the recursive component boundary is explicit;
- reject symbolic links or Windows reparse-point link-like entries anywhere inside the addressed recursive tree;
- reject special entries such as sockets, FIFOs and devices rather than silently omitting them;
- ordinary empty subdirectories are topology/packaging only and do not contribute records;
- an entirely empty recursive directory therefore hashes canonical JSON `[]`, explicitly distinguishing directory-tree identity from exact empty-file identity through both bytes and `identity_algorithm`.

Hard links are regular files. If two logical paths address the same inode, both path/file records participate because logical path is part of component identity.

## 8. Filesystem API constraints on Python >=3.10

Python's current `pathlib.Path.is_file(follow_symlinks=False)` interface was added later than the project's minimum Python. I-003 should not raise the minimum version merely for scanning.

Python 3.10 `os.scandir()` / `os.DirEntry` already provides:

- `is_symlink()`;
- `is_file(follow_symlinks=False)`;
- `is_dir(follow_symlinks=False)`;
- `stat(follow_symlinks=False)`.

These are sufficient for a non-following recursive scanner on the supported floor.

On Windows, link-like directory junctions/reparse points are not all ordinary POSIX symlinks. A portable fail-closed check can additionally reject entries whose `stat_result.st_file_attributes` contains `stat.FILE_ATTRIBUTE_REPARSE_POINT` when those attributes/constants are available.

Primary references:

- https://docs.python.org/3.10/library/os.html#os.scandir
- https://docs.python.org/3.10/library/os.html#os.DirEntry.is_file
- https://docs.python.org/3.10/library/os.html#os.DirEntry.is_symlink

## 9. Root and filesystem failure policy

All filesystem helpers should fail with stable ontoTF categories rather than leak host-specific `OSError` classes as their public contract.

Recommended categories:

```text
missing_path
wrong_path_type
symlink_not_allowed
unsupported_entry
invalid_logical_path
empty_component
filesystem_error
projection_error
unicode_domain
```

The diagnostic message may contain the underlying OS error text; callers should branch on category/path metadata.

Root rules:

- file helper requires a real regular file and rejects a symlink/reparse point;
- directory helper requires a real directory and rejects a symlink/reparse point;
- TF helper requires a real directory and at least one direct regular `.tf` file;
- permission/read/stat/scandir failures become `filesystem_error`.

The POC assumes the local component tree is not concurrently mutated during one digest operation. This is a reproducibility primitive, not a hostile-filesystem sandbox. Later acquisition/build code should compute identity against immutable/staged artifacts when stronger snapshot guarantees are required.

## 10. Algorithm identifiers

P-001 already fixes:

```text
ontotf-tf-files-sha256-v1
ontotf-parent-components-sha256-v1
```

P-001 specifies but does not name the generic single-file and recursive-directory algorithms. I-003 should define names before production code rather than overload the TF identifier:

```text
ontotf-file-bytes-sha256-v1
ontotf-directory-files-sha256-v1
```

Semantics:

- `ontotf-file-bytes-sha256-v1`: SHA-256 of exact file bytes;
- `ontotf-directory-files-sha256-v1`: SHA-256 of RFC 8785 canonical JSON over the sorted recursive file-record list;
- `ontotf-tf-files-sha256-v1`: SHA-256 of the same record shape, but over only direct regular `.tf` files in the addressed TF module root;
- `ontotf-parent-components-sha256-v1`: SHA-256 of RFC 8785 canonical JSON over an object containing the sorted semantic component identity records.

Keeping directory and TF algorithm identifiers distinct preserves the addressed-file-boundary contract even when two specific file sets happen to produce the same record list.

## 11. Parent manifest projection

Input is the structurally valid parent manifest shape.

The v1 digest projection is:

```json
{
  "components": [
    {
      "component_id": "...",
      "kind": "...",
      "identity_algorithm": "...",
      "content_digest": "sha256:..."
    }
  ]
}
```

Components are unique by `component_id` and sorted with the I-002 UTF-16 code-unit comparator.

The top-level `algorithm` must equal `ontotf-parent-components-sha256-v1` but is not duplicated inside its own digest projection; the algorithm name and digest are separate identity metadata, matching I-002's versioned-digest pattern.

Changing `logical_locator` or `license_ref` alone does not change parent semantic identity. Changing any of the four semantic component fields does.

I-003 computes this identity only. Equality/difference does not itself produce `verified-exact`, `verified-compatible`, `unverified`, or `incompatible`.

## 12. Fixed-vector strategy

RED tests should contain literal expected hashes, computed independently from the production helper, for at least:

- one exact file;
- a two-file recursive directory with nested path;
- a direct TF payload containing `otype.tf`, `oslots.tf`, and `otext.tf` plus ignored non-TF/nested files;
- a parent manifest with TF + sidecar components.

Mutation tests must prove:

- byte change changes component digest;
- recursive path rename changes directory digest;
- input enumeration order does not matter;
- parent component ordering does not matter;
- unchanged TF digest plus changed sidecar digest changes parent digest.

## 13. Scope boundary

I-003 must **not**:

- check that manifest component IDs are referenced by a profile;
- check that a component kind uses the expected identity algorithm;
- decide whether a changed component is semantically compatible;
- validate dependency closure;
- inspect ontology/evidence/review bindings;
- create compatibility reports;
- compile IR or runtime indexes.

Those are later semantic/compiler stages.

## 14. Research conclusion

Proceed with four explicit identity primitives:

```text
file component exact-byte identity
recursive directory-file-set identity
TF direct-.tf-file-set identity
parent component-manifest semantic identity
```

Use `os.scandir` with no-follow classification on Python >=3.10, reject selected/link-like entries, normalize logical paths to portable `/` strings, reuse I-002 JCS, and keep compatibility-state inference completely outside I-003.
