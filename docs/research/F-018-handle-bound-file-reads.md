# F-018 research — handle-bound file inspection and hashing

**Issue:** #90  
**Supersedes:** the obsolete F-015 namespace on the pre-correction branch; F-015 belongs to issue #87.  
**Baseline:** current `main` `01a2099a242178db004363f9cc1baf8272f446ee`; research-only gate after namespace repair, no F-018 plan/RED/production artifacts in this tree.

## Question

Can ontoTF strengthen regular-file digesting so that the object which passes final no-follow/reparse/type inspection is exactly the open object from which digest bytes are read, across supported Python 3.10/3.12 on POSIX and Windows, without treating `(st_dev, st_ino)` equality as an unconditional temporal proof?

## Why this is a separate F-018 ticket

F-012 removed the old `stat(path) -> reopen path -> hash whatever is there` race by comparing an expected no-follow `(st_dev, st_ino)` tuple with `fstat()` on the opened descriptor. That mismatch detector is useful, but equality of two temporally separated identity representations is not a universal object capability:

- Python 3.12 expanded Windows `st_ino` to support up to 128-bit file identifiers; earlier Python versions exposed a narrower representation on some filesystems;
- Microsoft documents file-ID reuse over time and warns that the legacy 64-bit identifier is not guaranteed unique on ReFS;
- Unix inode/device identity is filesystem-local and may be reused after deletion.

Therefore F-018 retains tuple mismatch as defense in depth but does not use tuple equality as the authority for inspection-to-read continuity.

Primary references retained from the reviewed predecessor research:

- Python `os.stat_result`, `os.open`, `os.fstat`, open-flag documentation, and `msvcrt.open_osfhandle` for Python 3.10/3.12;
- Microsoft `BY_HANDLE_FILE_INFORMATION`, `FILE_ID_INFO`, `CreateFileW`, reparse-point operations, `GetFileInformationByHandleEx`, and `_open_osfhandle` ownership documentation;
- POSIX `open()` semantics for `O_NOFOLLOW` and `O_NONBLOCK`.

Additional authoritative references used by this corrected review:

- POSIX `open()` (`O_NOFOLLOW`; FIFO `O_NONBLOCK` behavior): https://man7.org/linux/man-pages/man3/open.3p.html
- Python open-flag constants (`O_NONBLOCK`, `O_NOFOLLOW` availability): https://docs.python.org/3/library/os.html
- Microsoft `CreateFileW` / `FILE_FLAG_OPEN_REPARSE_POINT`: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew

## Strong invariant

The authoritative invariant is:

> The same trusted no-follow descriptor/Win32 handle that passes final-object link/reparse/type inspection supplies every byte accepted by the digest.

Layered sequence:

1. keep the existing pre-open no-follow stat where callers already have it;
2. obtain a trusted final-component no-follow descriptor/handle;
3. inspect that opened object for link/reparse and file type;
4. compare expected/opened platform identity as a one-way mismatch detector;
5. read every digest byte from the already-inspected descriptor/handle;
6. never reopen the pathname for hashing.

A pathname rename/replacement after trusted acquisition cannot redirect reads. The contract deliberately does not claim a filesystem snapshot before acquisition or immutability of the same opened object while it is being read.

The acquisition itself must also remain bounded for a raced final object. A path that was inspected as a regular file can be replaced with a FIFO before `open()`. A blocking read-only FIFO open would hang before `fstat()` can reject the non-regular object. F-018 therefore treats nonblocking final acquisition as part of the same final-component trust boundary on POSIX.

## POSIX feasibility

On POSIX-like supported runners, use `os.open(path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK | optional O_CLOEXEC)` with real nonzero `O_NOFOLLOW` and `O_NONBLOCK` primitives. Then:

- `O_NOFOLLOW` makes final symbolic-link acquisition fail rather than follow the target;
- `O_NONBLOCK` makes a read-only FIFO open return without delay, allowing handle-bound type inspection instead of hanging on an adversarial regular-to-FIFO replacement;
- `os.fstat(fd)` validates the opened object;
- require regular-file type before any digest read;
- reject expected/opened identity mismatch;
- stream bytes with `os.read` from that descriptor only;
- close it exactly once in `finally`.

For the supported regular-file path, nonblocking acquisition does not change digest bytes. A final symbolic-link failure attributable to no-follow open must preserve `symlink_not_allowed`. If trustworthy no-follow or nonblocking acquisition primitives are unavailable, F-018 fails closed as `filesystem_error`; it does not silently fall back to ordinary blocking/following `open()` plus tuple equality.

This protects only the final component. Ancestor-directory traversal remains F-013's distinct boundary.

## Windows feasibility with the standard library

Python's ordinary `os.open()` does not expose the required final reparse-point semantics, but `ctypes` and `msvcrt` are sufficient.

### Trusted Win32 acquisition

Use `CreateFileW` with:

- `GENERIC_READ`;
- `FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE`;
- `OPEN_EXISTING`;
- `FILE_FLAG_OPEN_REPARSE_POINT`.

Pin ctypes prototypes and handle widths explicitly and load Kernel32 with last-error support.

Before ownership transfer, query `GetFileInformationByHandleEx(... FileAttributeTagInfo ...)`. If `FILE_ATTRIBUTE_REPARSE_POINT` is set, close the raw handle once and report `symlink_not_allowed`. Query/open failures remain `filesystem_error` with correct one-owner cleanup.

Microsoft documents that `FILE_FLAG_OPEN_REPARSE_POINT` suppresses normal reparse processing and returns a handle to an existing symbolic link itself rather than its target. This flag is therefore part of the authority boundary, not an optional diagnostic detail.

### Handle to descriptor

After the raw handle is accepted:

1. call `msvcrt.open_osfhandle(raw_handle, os.O_RDONLY)`;
2. successful conversion transfers ownership to the CRT descriptor;
3. never manually `CloseHandle` after successful transfer;
4. if conversion fails before transfer, close the raw handle exactly once;
5. call `msvcrt.setmode(fd, os.O_BINARY)` before reads;
6. on setmode failure close the descriptor exactly once;
7. use common `os.fstat`, mismatch check and `os.read` logic;
8. close the descriptor exactly once.

The retained handle/descriptor—not file-ID equality—is the continuity primitive, so the primary guarantee is not dependent on Python 3.10 versus 3.12 `st_ino` width.

## ontoTF call paths

The same helper boundary applies to all byte-bearing parent identity paths:

- `file_component_digest()`;
- recursive regular files in `directory_component_digest()`;
- direct `.tf` payload files in `tf_payload_digest()`.

F-014 lexical exact-file checks stay before filesystem inspection. F-012 ordinary regular-to-different-regular replacement mismatch remains a required defense-in-depth regression.

## Error compatibility

Preserve existing public categories:

- final link/reparse through trusted acquisition -> `symlink_not_allowed`;
- standalone non-regular file -> existing `wrong_path_type` behavior;
- trusted open/query/conversion/setmode/fstat/mismatch/read, missing no-follow/nonblocking primitive, or raced non-regular final object after an expected regular-file inspection -> `filesystem_error` unless an existing caller contract is more specific;
- recursive unsupported entry types discovered during ordinary directory enumeration -> existing `unsupported_entry` behavior.

No filesystem identity metadata enters digest projection bytes. Existing algorithm identifiers and fixed digest vectors remain unchanged.

## Required future plan/RED coverage

A later implementation plan may be added only after this research-only head is independently approved. Its tests must prove at least:

1. trusted descriptor helpers are absent on pre-GREEN production, giving a deliberate RED;
2. POSIX missing/zero `O_NOFOLLOW` or `O_NONBLOCK` fails closed with zero reads;
3. the POSIX kernel open call actually carries both `O_NOFOLLOW` and `O_NONBLOCK`, so an implementation cannot substitute `lstat()` plus a following/blocking open;
4. after expected regular-file stat, replacing the final path with a symlink before trusted acquisition is rejected as `symlink_not_allowed` with zero digest reads;
5. a regular-to-FIFO race cannot block acquisition and fails before digest reads;
6. ordinary expected/opened regular-file mismatch still fails before read;
7. pathname replacement after trusted descriptor acquisition cannot redirect reads;
8. descriptor hashing performs no pathname reopen;
9. actual Windows 3.10/3.12 exercises normal-file `CreateFileW -> open_osfhandle -> binary descriptor -> read` behavior;
10. RED pins that `CreateFileW` receives `FILE_FLAG_OPEN_REPARSE_POINT`, independently of whether real Windows symlink creation is permitted on the runner;
11. Win32 raw-handle/descriptor ownership failure paths close exactly one owner;
12. common post-acquisition `fstat`, mismatch and read failures close the descriptor exactly once;
13. F-012, F-014, I-003 and fixed digest controls remain green.

Use Ubuntu 24.04 and Windows latest, each on Python 3.10 and 3.12. Windows normal-file handle conversion must be exercised for real; mocks are limited to difficult ABI/ownership/failure seams and deterministic flag assertions.

## Non-goals

F-018 does not claim or implement:

- ancestor-directory handle binding (F-013);
- filesystem snapshot or locking semantics;
- detection/prevention of in-place writes to the same open object (F-017 research);
- proof of which object occupied a pathname before trusted acquisition when a colliding/reused identity defeats the mismatch detector;
- stable object identity across process restarts;
- third-party native extensions.

## Research conclusion

Implementation is feasible and justified with a layered contract. Retain tuple mismatch as useful evidence, but make a single trusted no-follow descriptor/handle authoritative from final-object inspection through every digest read. POSIX requires real no-follow and nonblocking acquisition so a raced symlink cannot be followed and a raced FIFO cannot hang before type rejection. Windows uses standard-library ctypes for a no-follow/reparse-aware handle, then transfers ownership exactly once to a binary CRT descriptor. Existing digest bytes and public categories remain compatible.

This exact tree is intentionally research-only after the material F-018 namespace correction. It does not authorize a plan, RED artifacts, workflow, or production code until a fresh logically-independent review approves this research head.