# F-013 research — bind recursive traversal to inspected directory objects

**Issue:** #81  
**Type:** filesystem identity integrity / portability research  
**Baseline:** `main` `43907d497209019e4fb12bc5ca05f68e68448b40`

## Question

Can ontoTF guarantee that recursive directory enumeration remains attached to the exact directory objects that passed no-link inspection, on both POSIX and Windows, using Python 3.10+ standard-library facilities only?

F-012 closes the analogous race for **regular files** by comparing a fresh no-follow stat identity with `fstat()` on the opened descriptor before reading bytes. The residual directory race is different: current traversal inspects a child directory pathname and later calls `os.scandir(path)`. If the pathname is replaced between those operations, enumeration may occur in a different directory object.

## Accepted constraints

Any solution must preserve:

- Windows and POSIX support;
- no symlink/junction/reparse traversal;
- exact existing `tfont-directory-files-sha256-v1` bytes for stable trees;
- iterative traversal with no ontoTF depth ceiling;
- deterministic `filesystem_error`, `symlink_not_allowed`, and `unsupported_entry` behavior;
- Python standard library only;
- no claim of full filesystem snapshots or concurrent in-place mutation protection.

## Python 3.10+ POSIX capabilities

Python documents three primitives that make descriptor-bound traversal practical on Unix:

1. `os.scandir(path)` may take an open directory file descriptor, but **file-descriptor support was added on Unix** in Python 3.7. When a descriptor is supplied, `DirEntry.path` is only the entry name, which is suitable for operations relative to the directory handle rather than reconstructed absolute pathnames.
2. `dir_fd` parameters permit path operations relative to an already-open directory descriptor. Python describes these as POSIX `*at`/`f*at` style operations and exposes platform support through `os.supports_dir_fd`.
3. `os.fwalk()` yields a live directory descriptor for each traversed directory, defaults to `follow_symlinks=False`, supports relative directory descriptors, and is an explicitly descriptor-oriented traversal primitive. Python 3.10 documents `fwalk()` as Unix-only.

Relevant documentation:

- https://docs.python.org/3.10/library/os.html#os.scandir
- https://docs.python.org/3.10/library/os.html#files-and-directories
- https://docs.python.org/3.10/library/os.html#os.fwalk

A POSIX-only implementation could therefore open/verify each directory, enumerate with `scandir(fd)` or `fwalk`, and use `dir_fd`-relative no-follow stat/open operations for children. That can avoid re-resolving already-inspected ancestor pathname components.

## Windows capability gap in the same API

The same documented Python API is not symmetric on Windows:

- `os.scandir(fd)` file-descriptor support is documented as **Unix-only**.
- Python's descriptor-relative path mechanism maps to POSIX `*at`/`f*at` style operations and is exposed per-platform via `os.supports_dir_fd`; it does not supply a documented Windows directory-enumeration-by-handle equivalent.
- `os.fwalk()` is Unix-only in Python 3.10.
- `os.scandir()` documents distinct implementations: `opendir()`/`readdir()` on Unix versus Win32 `FindFirstFileW`/`FindNextFileW` on Windows. The Windows API exposed by `os.scandir()` is pathname-based rather than bound to an already-open parent-directory handle.
- `O_DIRECTORY` / `O_NOFOLLOW` are optional C-library extensions rather than portable Windows guarantees.

Relevant documentation:

- https://docs.python.org/3.10/library/os.html#os.scandir
- https://docs.python.org/3.10/library/os.html#os.supports-fd
- https://docs.python.org/3.10/library/os.html#os.supports-dir-fd
- https://docs.python.org/3.10/library/os.html#open-flag-constants
- https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-findfirstfilew

Therefore a single implementation built only from documented high-level `os` descriptor APIs cannot provide the same ancestor-handle binding guarantee on both supported platform families.

## Could `ctypes` close the Windows gap?

`ctypes` is technically part of the Python standard library, but using it to call Windows native handle/enumeration APIs would be a materially different portability and maintenance contract, not a transparent use of the existing `os` interface.

A robust Windows solution would need all of the following to be proven against documented Win32/NT behavior:

- opening directory handles without following name-surrogate reparse points;
- obtaining stable directory file IDs from handles;
- enumerating entries *from the opened directory handle*, not by a reconstructed pathname;
- opening child objects relative to the already-verified parent handle so ancestor pathname substitution cannot redirect lookup;
- retaining correct junction/reparse classification;
- lifetime and sharing semantics compatible with ordinary user corpora;
- error normalization matching POSIX behavior.

The documented Win32 directory enumeration used by Python (`FindFirstFileW` / `FindNextFileW`) takes a pathname. Merely holding a verified parent handle and then enumerating `parent_path` again does **not** close the race: the pathname may now name another directory. Similarly, verifying the final child handle after opening through a re-resolved ancestor pathname cannot prove that lookup remained within the previously verified parent object.

Closing that gap appears to require lower-level Windows relative-handle/object-manager functionality or a carefully designed native layer. That is far beyond a narrow I-003 stability patch and should not be inferred from the existence of `ctypes`.

## Decision: design-blocked for a uniform v1 runtime guarantee

**Do not proceed to an F-013 implementation plan yet.**

The research proves a clean descriptor-bound design for Unix, but it does not prove an equivalent implementation on Windows using the same documented Python standard-library abstraction. Shipping the POSIX implementation while silently leaving Windows pathname traversal weaker would create platform-dependent identity integrity under one algorithm/API contract.

That violates ontoTF's explicit/fail-closed design principles more than the current documented residual race does.

## What can be stated today

After F-012:

- final regular-file bytes can be bound to the exact inspected file object before hashing;
- directory hierarchy depth no longer depends on Python recursion after F-010;
- pre-existing symlinks/reparse points remain rejected;
- **directory enumeration itself is still pathname-bound**, so hostile or concurrent replacement of an inspected directory pathname is outside the current integrity guarantee.

This limitation should be explicit in implementation/review documentation until a portable design exists.

## Plausible future paths

### Path A — raise the minimum platform/runtime contract

If ontoTF eventually permits a stronger POSIX-only identity backend or platform-specific capability tiers, a descriptor walk can be implemented with `scandir(fd)` / `dir_fd` / `fwalk`, while Windows uses a separately specified backend. This requires an explicit compatibility/capability contract rather than pretending both backends are identical.

### Path B — research a documented Windows native-handle backend

A dedicated follow-up research ticket may evaluate documented Windows APIs and whether they can be safely exposed through `ctypes` while retaining relative-to-parent-handle lookup and reparse safety. Do not start implementation until the parent-relative lookup property is demonstrated, not merely final-handle identity verification.

### Path C — filesystem snapshot/stability precondition

A later architecture could make “tree remains stable for the duration of identity materialization” an explicit operational precondition rather than attempting hostile-filesystem safety. That would need to be stated as part of the identity contract and should not be silently introduced by F-013.

## Testing implications

No RED implementation test should be committed yet because there is no accepted cross-platform production strategy. A future plan must include deterministic directory-swap tests that replace a verified directory pathname before enumeration and prove the implementation cannot enumerate the replacement tree.

Tests must cover both:

- replacement with another real directory;
- replacement with symlink/junction/reparse forms where supported.

On Windows, a valid implementation test must demonstrate that child enumeration/open operations are parent-handle-relative; merely comparing directory IDs before and after path-based `scandir()` is still vulnerable to a replace-after-second-check race.

## Relationship to F-012

F-012 #80 remains valid and independently useful. Binding the file descriptor before byte reads closes a concrete final-file substitution hole even though ancestor-directory substitution remains outside its scope.

F-013 must not delay F-012, and F-012 must not claim that directory traversal is now hostile-filesystem safe.

## Conclusion

Python 3.10+ provides enough documented standard-library machinery for descriptor-bound recursive traversal on Unix, but not through the same `os` abstraction on Windows. F-013 is therefore **design-blocked after research**: no plan or implementation should be created until a documented Windows parent-handle-relative traversal design, or an explicit platform-capability architecture, is accepted.