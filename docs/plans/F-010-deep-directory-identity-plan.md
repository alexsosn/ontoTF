# F-010 plan: iterative recursive-directory identity traversal

**Issue:** #71  
**Research:** `docs/research/F-010-deep-directory-identity.md` at `8eaf0357b2c54fe680b1ee61a0f1cc83e5f70635`  
**Current integration baseline:** `main` `c38d77a35fd7f6d4e06b3d27d2b0bc298f85de62`

## 1. Scope

Remove Python call-stack recursion from `directory_component_digest()` while preserving the accepted `ontotf-directory-files-sha256-v1` identity contract exactly.

Production scope is limited to recursive directory traversal internals in `src/ontotf/parent_identity.py`. No schema, digest algorithm identifier, mapping/profile contract, TF payload behavior, parent-manifest behavior, or semantic/runtime behavior changes.

## 2. Design decision

Use an explicit iterative depth-first traversal with stack frames. Do **not** add a ontoTF directory-depth limit and do not read or modify Python's recursion limit in production.

Each frame records:

- the scanned directory's entries as a concrete list;
- the next entry index;
- the component-relative path segments for that directory.

Operational sequence:

1. validate the root exactly as I-003 does today;
2. scan the root into the initial frame using the same `os.scandir()` error translation;
3. inspect the next entry in the top frame;
4. validate its name and call `entry.stat(follow_symlinks=False)`;
5. reject link-like entries before type dispatch;
6. for a real directory, advance the parent frame and immediately push a scanned child frame;
7. for a regular file, emit the same logical-path/file-digest record and advance the frame;
8. reject other entry types exactly as today;
9. pop exhausted frames;
10. sort/hash the completed records through the existing `_hash_file_records()` unchanged.

This mirrors the current recursive depth-first control flow while eliminating Python stack growth.

## 3. Error and identity compatibility

The implementation must preserve:

- child `os.scandir()` failures -> `IdentityError(category="filesystem_error", path=<child directory>)`;
- `DirEntry.stat(follow_symlinks=False)` failures -> `filesystem_error` at the entry path;
- link-like/reparse entries -> `symlink_not_allowed`;
- non-file/non-directory entries -> `unsupported_entry`;
- file read failures -> existing `filesystem_error` from `_sha256_file()`;
- invalid/unicode logical path diagnostics;
- empty-directory digest semantics;
- UTF-16 final record ordering;
- all existing fixed `ontotf-directory-files-sha256-v1` vectors.

No `RecursionError` catch is required in the final iterative traversal because traversal itself must not recurse. Do not mask unrelated programming errors with broad exception handling.

## 4. RED test gate

Before production edits add `tests/f010/` with focused tests and a workflow.

### Deep virtual hierarchy

Exercise the public `directory_component_digest()` API while patching only filesystem primitives needed to avoid host path-depth limits:

- patch `_require_real_directory()` to accept a synthetic root;
- patch `os.scandir()` to return a context-manager-like sequence;
- each synthetic directory contains one fake directory entry until a chosen depth greater than the current interpreter recursion limit;
- fake `DirEntry.stat(follow_symlinks=False)` returns an exact directory mode;
- the final directory is empty.

The **test fixture** may use `sys.getrecursionlimit()` only to choose a depth that reliably makes the old recursive implementation fail. Production code must never consult it.

Required RED:

- current implementation leaks raw `RecursionError` for the deep virtual hierarchy.

Required GREEN:

- the same hierarchy succeeds and returns the same digest as an empty directory record set.

### Diagnostic controls

Add deep virtual cases proving:

- link-like child -> `symlink_not_allowed`;
- special child -> `unsupported_entry`;
- child scan `OSError` -> `filesystem_error` with the child path;
- entry stat `OSError` -> `filesystem_error` with the entry path.

### Compatibility controls

Reuse or explicitly exercise existing I-003 tests proving:

- ordinary recursive directory fixed vector unchanged;
- enumeration/creation order does not affect identity;
- empty real directory unchanged;
- existing root/link/path diagnostics remain unchanged.

RED must fail because traversal still uses recursive Python calls, not because mocks violate the public filesystem contract.

## 5. Minimal GREEN implementation

Prefer one private helper such as `_scan_directory(path)` that returns `list[os.DirEntry[str]]` while preserving current `OSError -> filesystem_error` translation.

Replace only the nested recursive `walk()` with a frame loop. A small private dataclass/tuple for frames is acceptable if it reduces mutation ambiguity; it must not become public API.

Do not change:

- `_file_record()`;
- `_hash_file_records()`;
- `_validate_segment()`;
- `_is_link_like()`;
- `_sha256_file()`;
- public function signatures or algorithm constants.

## 6. CI gate

Add `.github/workflows/f010-deep-directory-identity.yml` with Python 3.10/3.12 and exact source-head checkout.

Before F-007 is merged, each job may run:

1. editable install plus `build`;
2. focused `tests/f010`;
3. full `tests/i003` regressions;
4. full repository suite.

If F-007 #35 merges before F-010 finalization, re-integrate on current main and remove F-010's generic repository-suite step so `full-suite.yml` remains the sole canonical owner. Retain focused F-010 + I-003 coverage and let the authoritative workflow provide repository-wide coverage.

## 7. Integration gate

Before final review:

- integrate current `main` without losing F-010 history;
- verify the PR is zero behind its base or otherwise demonstrate an equivalent current-base tree;
- inspect current CI workflow ownership, especially F-007;
- run exact-head Python 3.10/3.12 focused and repository-wide gates with packaging enabled;
- verify no `*-v1` identity constant or fixed vector changed.

Any material integration change invalidates earlier final review.

## 8. Non-goals

F-010 does not:

- introduce a directory depth quota;
- raise or alter `sys.setrecursionlimit()`;
- follow symlinks/reparse points;
- redesign TOCTOU behavior or add hostile-filesystem sandboxing;
- change TF direct-`.tf` traversal semantics;
- change canonical JSON or F-009 depth behavior;
- change schemas, mapping semantics, compatibility inference, or P-003 work.

## 9. Independent review gate

After exact-head GREEN, require a logically independent adversarial review from a context/person that did not author the final implementation head.

Review must attack:

- recursive-vs-iterative file-record equivalence;
- depth-first error timing where multiple bad entries exist;
- symlink/reparse handling at deep levels;
- special/stat/scandir/read error paths;
- traversal-order independence and fixed digest vectors;
- hidden production dependence on recursion limits;
- accidental depth ceilings;
- TOCTOU scope drift;
- F-007 full-suite ownership on the final base.

Do not merge without that exact-head independent review.
