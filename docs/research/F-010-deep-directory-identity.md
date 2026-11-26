# F-010 research: deep recursive directory identity without interpreter recursion

**Issue:** #71  
**Recorded:** 2026-09-07  
**Baseline:** `main` `9e644f57ab5b5a019f6a4a9384e5bee897c62003`  
**Type:** I-003 stability / filesystem identity hardening

## Question

How should `directory_component_digest()` preserve the accepted `ontotf-directory-files-sha256-v1` identity semantics for arbitrarily deep filesystem trees without leaking Python `RecursionError` or inventing a semantic directory-depth limit?

## Existing I-003 contract

Accepted `docs/plans/I-003-parent-component-identity-plan.md` defines:

- deterministic **recursive** directory identity over every regular file below the declared component root;
- exact-byte per-file SHA-256;
- portable component-relative logical paths;
- final UTF-16 path ordering followed by I-002 canonical JSON;
- explicit fail-closed symlink/reparse and special-entry policy;
- stable `IdentityError` categories including `filesystem_error`;
- fixed directory digest vectors and enumeration-order independence.

The production implementation currently realizes recursion literally:

```python
def walk(directory, relative_segments):
    ...
    if stat.S_ISDIR(st.st_mode):
        walk(entry_path, segments)
```

No `RecursionError` boundary exists around that Python call recursion. Therefore directory hierarchy depth can become an accidental dependency on the interpreter stack even though depth is not part of the versioned directory identity algorithm.

## Python evidence

Python documents the recursion limit as protection against overflowing the C stack. The highest safe recursion limit is platform-dependent, and exceeding interpreter recursion raises `RecursionError`.

Authoritative source:
<https://docs.python.org/3/library/sys.html#sys.setrecursionlimit>

This is an implementation/runtime property, not a filesystem identity property. Raising the recursion limit is explicitly unsafe as a general fix, and defining the directory identity domain relative to `sys.getrecursionlimit()` would make the same tree acceptable on one interpreter configuration and rejected on another.

## Filesystem traversal evidence

Python's `os.scandir()` supplies directory entries, and `DirEntry.stat(follow_symlinks=False)` obtains metadata without following a final symbolic link. Those are the primitives already used by I-003 and remain available without recursive Python calls.

Authoritative source:
<https://docs.python.org/3/library/os.html#os.scandir>

The accepted implementation also explicitly checks `stat.S_ISLNK` and Windows reparse attributes after `follow_symlinks=False`; F-010 should preserve that policy rather than switch to a higher-level walker whose error/link semantics would need to be re-derived.

## Decision: iterative traversal, no ontoTF depth ceiling

Prefer an explicit iterative depth-first traversal over adding a maximum directory depth.

Reasons:

1. **Depth has no semantic role in the v1 identity algorithm.** The digest is defined by sorted logical path + file-byte records, not by traversal call depth.
2. **A fixed ontoTF ceiling would be new rejection semantics.** There is no research or corpus requirement for such a bound.
3. **Interpreter-derived limits are non-deterministic.** Python says safe recursion depth is platform-dependent.
4. **Iteration preserves the complete accepted domain.** It removes Python stack usage while letting real filesystem constraints surface through the same OS calls already translated to `filesystem_error`.
5. **Digest bytes need not change.** The implementation already sorts completed file records by logical path before canonicalization, so traversal order cannot affect the successful digest.

No algorithm identifier bump is justified if every successfully addressed tree produces the same record set and canonical bytes.

## Preserve depth-first operational behavior where practical

Although successful digest identity is traversal-order independent, error timing can be observable when a tree contains more than one invalid entry. The current recursive implementation is depth-first in the enumeration order returned by each `os.scandir()` call.

The minimal iterative replacement should therefore model recursive frames rather than merely push all subdirectories onto a flat LIFO worklist.

A frame can contain:

```text
entries: list[DirEntry]
next_index: int
relative_segments: tuple[str, ...]
```

Algorithm:

1. scan root into the first frame;
2. inspect the next entry in the top frame;
3. for a real subdirectory, increment the parent frame index and push a newly scanned child frame immediately;
4. for a regular file, emit its record and advance the frame;
5. for link-like/special entries, fail exactly as today;
6. pop an exhausted frame.

This reproduces recursive depth-first control flow without consuming Python call-stack depth.

## `os.scandir()` / stat error boundary

Keep the existing behavior exactly:

- failure to scan a directory -> `IdentityError(category="filesystem_error", path=<directory>)`;
- failure to stat an entry -> `filesystem_error` at the entry path;
- link-like entry -> `symlink_not_allowed`;
- regular file -> exact-byte hash;
- directory -> descend;
- other type -> `unsupported_entry`.

Do not broaden to `except Exception` and do not translate unrelated programming errors.

## TOCTOU considerations

I-003 explicitly states that the POC assumes the local tree is stable during one digest operation; it is not a hostile-filesystem sandbox. Iteration does not change that threat model.

As today, an entry may change between directory enumeration, `stat`, and file read. F-010 should not attempt inode pinning, openat-based sandboxing, or retry semantics; those would be separate architecture/security work and could change identity/error behavior.

## Test strategy

### Reproduce recursion without host path-length dependence

A real >1000-level path is unsuitable as the primary RED fixture because OS/filesystem path limits differ. Instead exercise the **public** `directory_component_digest()` against a controlled virtual directory hierarchy by patching only filesystem primitives:

- `_require_real_directory(root)` is controlled as a successful root check;
- `os.scandir(path)` returns a context-manager-like object containing one fake real-directory `DirEntry` until the chosen virtual depth, then an empty directory;
- each fake `DirEntry.stat(follow_symlinks=False)` returns an `S_IFDIR` mode;
- no files are needed, so successful identity remains the accepted empty-record digest.

Size the virtual hierarchy above `sys.getrecursionlimit()` solely to guarantee that the **old implementation** exhausts interpreter recursion. The product must not read or compare `sys.getrecursionlimit()`.

RED expectation:

```text
current recursive implementation -> raw RecursionError
```

GREEN expectation:

```text
iterative implementation -> EMPTY_DIRECTORY_DIGEST
```

This makes the fixture portable across Python 3.10/3.12 while proving the product no longer depends on interpreter recursion depth.

### Controls

Mandatory controls:

- existing fixed recursive directory vector unchanged;
- reversed file creation/enumeration remains same identity;
- deep virtual link-like entry still yields `symlink_not_allowed`;
- deep virtual special entry still yields `unsupported_entry`;
- virtual child scan `OSError` still yields `filesystem_error` with child path;
- existing real filesystem tests remain unchanged;
- empty real directory remains the canonical empty-record digest.

## Interaction with F-009

F-009 #69 guards recursive **JSON value** validation/canonicalization. F-010 does not depend on F-009 for traversal correctness.

After directory traversal produces a flat `records` list, `_hash_file_records()` still delegates to `canonical_json_bytes(records)`. Each file record is shallow; directory hierarchy depth is encoded in the `relative_logical_path` string rather than nested JSON containers. Therefore F-009's JSON nesting policy does not impose a directory-depth limit.

## Interaction with F-007

F-007 #34 may centralize repository-wide CI before F-010 is finalized. F-010 should retain a focused I-003 regression workflow but must not become a second owner of the canonical full-suite command after F-007 merges. Final integration must inspect current workflow ownership.

## Implementation recommendation

Refactor only `directory_component_digest()` traversal internals, preferably by introducing one private helper to scan a directory into a list while retaining current error translation.

Do not change:

- public identity functions;
- algorithm constants;
- logical path construction;
- record shape/order/canonicalization;
- symlink/reparse policy;
- special-entry policy;
- empty-directory behavior;
- TF direct-`.tf` traversal semantics;
- parent-manifest projection.

## Review attack surface

Independent review should challenge:

- whether iterative frames exactly preserve recursive entry processing/error timing;
- accidental symlink following or reparse regression;
- special-entry handling in deep children;
- failure-path preservation for child `scandir`/stat/read errors;
- file record/path equivalence and fixed digest vectors;
- artificial directory-depth limits creeping back in;
- dependence on `sys.getrecursionlimit()` anywhere in production;
- TOCTOU scope expansion;
- duplicate full-suite ownership if F-007 lands concurrently.

## Conclusion

F-010 should replace Python-call recursion in `directory_component_digest()` with explicit iterative depth-first frames. This removes an interpreter-dependent raw failure while preserving the complete accepted v1 filesystem identity domain and every successful digest byte.
