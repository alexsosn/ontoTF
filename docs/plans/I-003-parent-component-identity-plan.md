# I-003 parent component identity implementation plan

**Issue:** #20  
**Recorded:** 2026-09-06  
**Research dependency:** `docs/research/I-003-parent-component-identity-research.md` at `6297a073829f23bd0abb2e75ec2c0ed3854d091e`  
**Baseline:** I-002 merged main `67f55b52cc75eb3704357e4ed70851c5d7db6ad2`

## 1. Scope

I-003 implements deterministic parent **identity computation only**.

It creates:

- exact single-file component hashing;
- recursive directory-like component hashing;
- Text-Fabric direct-`.tf` payload hashing;
- parent component-manifest semantic projection/digest;
- stable identity/filesystem errors;
- fixed vectors and CI.

It does not decide compatibility, validate dependency closure, resolve profile references, inspect ontology/evidence/review semantics, compile IR, or generate runtime artifacts.

## 2. Production layout

```text
src/ontotf/
  parent_identity.py
  __init__.py               # export common public identity API

tests/i003/
  __init__.py
  test_parent_identity.py
.github/workflows/i003-validation.yml
```

No schema change is required.

## 3. Versioned algorithm constants

```python
FILE_BYTES_ALGORITHM = "ontotf-file-bytes-sha256-v1"
DIRECTORY_FILES_ALGORITHM = "ontotf-directory-files-sha256-v1"
TF_FILES_ALGORITHM = "ontotf-tf-files-sha256-v1"
PARENT_COMPONENTS_ALGORITHM = "ontotf-parent-components-sha256-v1"
```

Digest values use the I-002 representation:

```text
sha256:<64 lowercase hexadecimal digits>
```

The two generic algorithm names are fixed here because P-001 specified their byte semantics but did not assign names. Reusing a `v1` name with different addressing/projection semantics is prohibited.

## 4. Public API

```python
@dataclass(frozen=True)
class IdentityProblem:
    category: str
    message: str
    path: str | None = None

class IdentityError(ValueError):
    problem: IdentityProblem

file_component_digest(path: str | os.PathLike[str]) -> str
directory_component_digest(path: str | os.PathLike[str]) -> str
tf_payload_digest(path: str | os.PathLike[str]) -> str
parent_manifest_projection(manifest: dict[str, JSONValue]) -> dict[str, JSONValue]
parent_manifest_digest(manifest: dict[str, JSONValue]) -> str
```

Common functions/errors are exported from `ontotf.__init__`. Algorithm constants remain available from `ontotf.parent_identity`.

## 5. Stable error categories

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

`problem.path` is the relevant filesystem path when one exists. JSON/projection failures may leave it `None` and identify the offending field in the message.

Underlying OS exception text is diagnostic only.

## 6. Link-like detection

Project Python floor remains `>=3.10`, so implementation uses `os.lstat` / `os.scandir` / `os.DirEntry.stat(follow_symlinks=False)` rather than `pathlib` APIs whose `follow_symlinks` options require newer Python.

An entry is link-like when either:

- `stat.S_ISLNK(st_mode)` is true; or
- Windows `st_file_attributes` has `stat.FILE_ATTRIBUTE_REPARSE_POINT`, when those attributes/constants exist.

Link-like roots or addressed entries fail with `symlink_not_allowed`.

The POC assumes the local tree is stable during one digest operation; it is not a hostile-filesystem sandbox.

## 7. Exact single-file identity

`file_component_digest(path)`:

1. `lstat` the root;
2. reject missing/link-like/non-regular root;
3. read exact bytes with no text normalization;
4. SHA-256 exact bytes;
5. return `sha256:<hex>`.

Fixed vector:

```text
b"alpha\n"
-> sha256:b6a98d9ce9a2d9149288fa3df42d377c3e42737afdcdaf714e33c0a100b51060
```

Empty regular files are valid exact-byte components:

```text
b""
-> sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

## 8. Portable logical paths

Filesystem-derived component-relative logical paths:

- are relative to the declared component root;
- use `/` separators;
- never contain empty, `.` or `..` segments;
- reject a filesystem name containing literal `\\` to avoid POSIX/Windows ambiguity;
- require every segment to be UTF-8 representable Unicode scalar text;
- preserve case and authored Unicode; no normalization/case-folding.

Record ordering uses lexicographic UTF-16 code-unit order, consistent with I-002 semantic string ordering.

## 9. File-set record projection

Directory-like and TF file-set algorithms hash this exact record shape:

```json
[
  {
    "relative_logical_path": "a.txt",
    "sha256": "sha256:..."
  }
]
```

Each per-file digest is SHA-256 of exact bytes.

After sorting by logical path, the list is encoded with I-002 `canonical_json_bytes()` and SHA-256 hashed.

No mtime, inode, permissions, owner, absolute root, host separator, repository revision, or acquisition URL participates.

## 10. Recursive directory identity

`directory_component_digest(root)` addresses all recursive regular files.

Scanner rules:

- root must be a real directory, not link-like;
- recurse through real directories;
- include every regular file, including hidden files;
- reject any link-like entry anywhere in the addressed tree;
- reject sockets/FIFOs/devices/other special entries;
- ordinary empty subdirectories emit no records;
- traversal/scandir/stat/read errors become `filesystem_error`.

An entirely empty directory is a valid explicit directory-tree identity: SHA-256 of canonical JSON `[]`:

```text
sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
```

This is distinct from an empty regular file by both digest value and algorithm ID.

Fixed recursive vector:

```text
a.txt         = b"alpha\n"
nested/b.bin  = b"\x00\x01\xff"

-> sha256:d5d2ddbdccc7d67378836747af134ad681996ed0e0c63ec20f0e9e0ae259a323
```

Renaming `nested/b.bin` while preserving bytes must change the digest because logical path is part of the projection.

## 11. Text-Fabric payload identity

`tf_payload_digest(root)` mirrors the accepted TF loader's addressed module boundary:

- root must be a real directory, not link-like;
- scan only direct children;
- include direct regular files whose names end in `.tf`;
- include config `.tf` files such as `otext.tf`;
- ignore direct non-`.tf` files;
- ignore nested directories and therefore nested `.tf` files;
- reject a selected `.tf` symlink/reparse entry rather than follow it;
- fail `empty_component` if no direct regular `.tf` file is addressed.

A non-`.tf` symlink or nested directory is outside this TF component boundary and does not affect the TF digest.

Fixed TF vector:

```text
oslots.tf = b"@edge\n1\t1\n"
otext.tf  = b"@config\n@sectionTypes=book,chapter,verse\n"
otype.tf  = b"@node\n1\tword\n"

-> sha256:a3b28b34637f2a2bdba591ed2020c94a2991e4e64643741c804ca4621bd7f83f
```

A `README.md` and `nested/ignored.tf` fixture must not change that digest.

## 12. Parent manifest semantic projection

Input source shape is the I-001 parent component manifest:

```text
algorithm
components[]
```

`algorithm` must equal `ontotf-parent-components-sha256-v1`.

Each component source may contain:

```text
component_id             semantic, required
kind                     semantic, required
identity_algorithm       semantic, required
content_digest           semantic, required
logical_locator          non-semantic, optional
license_ref              non-semantic, optional
```

Unknown fields fail `projection_error` rather than being silently omitted from v1.

The digest projection is exactly:

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

Rules:

- at least one component is required;
- all four semantic fields are non-empty exact strings;
- duplicate `component_id` fails;
- components sort by UTF-16 code-unit order of `component_id`;
- `logical_locator` and `license_ref` are validated as optional non-empty strings when present but excluded from projection;
- structural kind/algorithm cross-validity is not reimplemented here; I-001/I-004 own it.

Fixed parent vector with the TF and recursive directory vectors above:

```text
bhsa-tf       tf-payload / ontotf-tf-files-sha256-v1
oracc-sidecar sidecar    / ontotf-directory-files-sha256-v1

-> sha256:c8427586f094ade21411843a55a89f88161ab42a7462564905e94599eea57fa9
```

## 13. Mandatory TDD regressions

RED tests are committed before `src/ontotf/parent_identity.py` exists and must fail for that missing-production reason.

The test suite pins:

1. versioned algorithm constants;
2. exact file fixed vector and byte mutation;
3. empty-file identity;
4. recursive directory fixed vector;
5. empty-directory explicit identity;
6. recursive creation/enumeration order invariance;
7. nested path rename changes identity;
8. recursive symlink rejection;
9. recursive special-entry rejection where supported;
10. invalid/non-portable filesystem logical name rejection where constructible;
11. TF direct `.tf` fixed vector;
12. TF ignores README/nested `.tf`;
13. TF selected `.tf` symlink rejection;
14. TF empty payload rejection;
15. parent fixed vector;
16. parent component order invariance;
17. locator/license metadata exclusion;
18. each semantic component field affects parent digest;
19. duplicate component ID rejection;
20. unchanged TF digest + changed sidecar digest changes parent digest;
21. no compatibility-state API or inference introduced.

## 14. Workflow

`.github/workflows/i003-validation.yml` triggers on:

```text
pyproject.toml
src/ontotf/**
tests/i003/**
docs/research/I-003-parent-component-identity-research.md
docs/plans/I-003-parent-component-identity-plan.md
.github/workflows/i003-validation.yml
```

It installs editable package, then runs:

```text
python -m unittest discover -s tests/i003 -v
python -m unittest discover -s tests -v
```

Exact-head success is mandatory before review/merge.

## 15. Independent-review attack surface

Fresh adversarial review must try to falsify:

- TF direct-file boundary versus accidental recursive/repository hashing;
- symlink/reparse target leakage;
- special-file omission;
- path separator/Unicode ordering portability;
- file path rename identity;
- empty file versus empty directory behavior;
- accidental source newline/BOM normalization;
- locator/license leakage into semantic parent identity;
- missing/duplicate/unknown component projection fields;
- unchanged TF + changed required sidecar negative invariant;
- accidental compatibility-state inference;
- exact-head CI and scope.
