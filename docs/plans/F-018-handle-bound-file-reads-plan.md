# F-018 implementation plan — handle-bound exact-file inspection

**Issue:** #90  
**Research:** `docs/research/F-018-handle-bound-file-reads.md`  
**Reviewed research head:** `e3a746a7e6cf81c9a1014c5a27147d9b3f2cd285`

## 1. Goal

Strengthen every regular-file byte read used by ontoTF parent/component identity so the same trusted final-component descriptor/Win32 handle that passes link/reparse/type inspection supplies every digest byte.

Keep the existing expected/opened `(st_dev, st_ino)` comparison only as defense in depth: mismatch fails, equality never authorizes continuity.

Trusted acquisition must also be bounded. On POSIX, a raced regular-to-FIFO replacement must not block before type inspection.

No public API or digest algorithm identifier changes.

## 2. Production scope

Only `src/ontotf/parent_identity.py` after the corrected RED is independently reviewed and observed.

Public functions remain:

- `file_component_digest(path)`;
- `directory_component_digest(path)`;
- `tf_payload_digest(path)`.

Existing fixed file/directory/TF digest vectors must remain byte-identical.

No F-013 ancestor-directory binding and no F-017 in-place mutation/snapshot semantics.

## 3. Private helper boundary

Target internal responsibilities:

```python
def _open_trusted_file_descriptor(path: str) -> int:
    """Return an owned binary/read descriptor using the platform's trusted final-object acquisition primitive."""


def _sha256_descriptor(fd: int, path: str) -> str:
    """Hash an already-authorized descriptor without reopening path."""


def _sha256_file(path: str, expected: os.stat_result) -> str:
    fd = _open_trusted_file_descriptor(path)
    try:
        opened = os.fstat(fd)
        require regular file
        reject expected/opened identity mismatch
        return _sha256_descriptor(fd, path)
    finally:
        os.close(fd)
```

Exact private names may vary only if the RED contract pins equivalent behavior. No second pathname open after trusted acquisition is allowed. No `os.read` before final-object/type/mismatch authorization.

The helper may perform platform-specific acquisition/inspection work but must return exactly one owned descriptor or raise after cleaning up every resource it acquired.

## 4. POSIX implementation

On non-Windows:

1. require real nonzero `os.O_NOFOLLOW` and `os.O_NONBLOCK` primitives;
2. build flags `os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | optional os.O_CLOEXEC`;
3. call `os.open(path, flags)` directly with those flags; do not emulate no-follow with a separate `lstat()` followed by ordinary `open()`;
4. preserve final-link rejection as `symlink_not_allowed` only when the no-follow failure is attributable to link-like resolution; do not blindly treat every unrelated path-resolution `ELOOP` as proof about the final component;
5. return the descriptor to common `fstat`/regular-file/mismatch/read logic;
6. missing/unusable required primitives fail closed as `filesystem_error` before reads.

`O_NONBLOCK` is part of trusted acquisition because a path inspected as regular may be replaced by a FIFO before `os.open()`. The descriptor must be acquired without waiting for a FIFO peer so `fstat()` can reject the raced non-regular object. For ordinary regular files the digest bytes remain unchanged.

Ancestor path traversal is unchanged and remains outside F-018.

## 5. Windows implementation

Use only stdlib `ctypes`, `msvcrt`, and `os`.

Pin Kernel32 prototypes/handle widths and use last-error support for:

- `CreateFileW`;
- `GetFileInformationByHandleEx` with `FileAttributeTagInfo`;
- `CloseHandle`.

Define the required ABI structures/constants locally, including `FILE_ATTRIBUTE_TAG_INFO`, `FILE_ATTRIBUTE_REPARSE_POINT`, `FILE_FLAG_OPEN_REPARSE_POINT`, `OPEN_EXISTING`, share flags, and invalid-handle representation.

Trusted acquisition sequence:

1. `CreateFileW(path, GENERIC_READ, FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE, ..., OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT, ...)`;
2. `FILE_FLAG_OPEN_REPARSE_POINT` is mandatory and must be RED-pinned as an actual call flag;
3. query `FileAttributeTagInfo` before ownership transfer;
4. reparse -> close raw handle exactly once and `symlink_not_allowed`;
5. query failure -> close raw handle exactly once and `filesystem_error`;
6. `msvcrt.open_osfhandle(raw_handle, os.O_RDONLY)`;
7. successful conversion transfers ownership; never `CloseHandle` that raw handle afterward;
8. conversion failure before transfer -> close raw handle exactly once;
9. `msvcrt.setmode(fd, os.O_BINARY)` before reads;
10. setmode failure -> close descriptor exactly once, with no raw-handle double-close;
11. return descriptor to common `fstat`/mismatch/read logic.

Common caller closes a successfully returned descriptor exactly once on success or later failure.

## 6. Common authorization/read precedence

For standalone, recursive-directory, and direct `.tf` files:

1. preserve current caller-side expected no-follow stat and lexical/object classification;
2. trusted final-component acquisition;
3. platform-specific final link/reparse inspection;
4. `os.fstat(fd)`;
5. require regular file;
6. expected/opened identity mismatch -> `filesystem_error`;
7. only then first `os.read`;
8. stream all digest bytes from the same descriptor;
9. close the descriptor exactly once on success, `fstat` failure, type failure, identity mismatch, or read failure.

Path replacement after step 2 cannot redirect reads. The contract does not claim a pre-open pathname snapshot or in-place mutation protection.

## 7. RED gate construction

Only after this implementation plan is independently approved, restore/create `tests/f018/` and `.github/workflows/f018-handle-bound-file-reads.yml` as tests/workflow-only commits. No production file may change during RED.

### POSIX acquisition contract

Pin all of the following:

- trusted helper(s) absent on pre-GREEN production -> intended RED;
- zero/missing `O_NOFOLLOW` -> `filesystem_error`, zero reads;
- zero/missing `O_NONBLOCK` -> `filesystem_error`, zero reads;
- spy the actual POSIX `os.open` call and assert both `O_NOFOLLOW` and `O_NONBLOCK` are present;
- this flag test must fail an implementation that performs an internal `lstat()` and then calls ordinary following/blocking `os.open()`;
- expected ordinary file replaced by a symlink before trusted acquisition -> `symlink_not_allowed`, zero digest reads;
- expected ordinary file replaced by a FIFO before trusted acquisition -> call returns/fails boundedly and rejects before digest reads; do not use a test shape that can hang CI if `O_NONBLOCK` is omitted—use deterministic instrumentation/timeout-safe process isolation where necessary;
- ordinary expected/opened regular-file mismatch remains fail-closed before read;
- pathname replacement after trusted acquisition does not redirect subsequent reads;
- descriptor hashing never reopens the pathname.

The symlink/reparse test must prove the trusted opener's kernel-level acquisition behavior, not only pre-open `_lstat` compatibility. Pre-existing-link rejection remains a separate compatibility control.

### Windows acquisition contract

On Windows latest, Python 3.10 and 3.12:

- ordinary files exercise the real `CreateFileW -> handle inspection -> open_osfhandle -> setmode(O_BINARY) -> os.read` path;
- digest bytes match the existing fixed value;
- binary mode is established before the first digest read;
- deterministic instrumentation asserts `CreateFileW` receives `FILE_FLAG_OPEN_REPARSE_POINT` even when runner permissions prevent a real symlink/reparse fixture;
- where real symlink creation is permitted, regular->link replacement before trusted acquisition is rejected by the trusted opener;
- pathname replacement after trusted acquisition cannot redirect descriptor reads where portable on the runner.

### Ownership/failure seams

Mock only difficult resource/ABI seams and assert exact ownership:

- reparse result -> raw handle closed once, no conversion/read;
- handle query failure -> raw handle closed once;
- conversion failure -> raw handle closed once;
- conversion success -> no manual raw close, binary mode set;
- setmode failure -> descriptor closed once, raw handle not double-closed;
- common `fstat` failure -> returned descriptor closed once, zero reads;
- common type/mismatch failure -> returned descriptor closed once, zero reads;
- common `os.read` failure -> returned descriptor closed once;
- success -> returned descriptor closed once.

### Regression controls

Under `if: always()` run:

- `tests/f012`;
- `tests/f014`;
- `tests/i003`.

Central `full-suite.yml` owns repository-wide tests; the focused workflow must not duplicate that command.

## 8. RED acceptance

Before production changes, exact F-018 RED head must run Ubuntu 24.04 + Windows latest × Python 3.10/3.12 and show:

- focused F-018 contract fails only because trusted acquisition/descriptor hashing is not implemented;
- all applicable platform-specific flag/ownership tests reach their intended assertions rather than failing on import/namespace/setup mistakes;
- F-012/F-014/I-003 regressions remain green under `if: always()`;
- the obsolete F-015 RED evidence is not reused.

If a test is skipped because the operating system cannot create a real symlink/reparse point, deterministic acquisition-flag and ownership tests must still cover that authority boundary. A whole Windows matrix cell may not be waived.

## 9. Minimal GREEN order

Only after exact RED evidence:

1. add POSIX trusted descriptor opener with required `O_NOFOLLOW|O_NONBLOCK`;
2. add Windows trusted handle helpers and explicit ctypes ABI;
3. add descriptor-stream SHA-256 helper;
4. route existing `_sha256_file(path, expected)` through trusted acquisition -> common `fstat` -> regular-file check -> mismatch check -> descriptor hashing;
5. preserve caller/projection behavior and digest algorithms unchanged.

No opportunistic refactor outside `parent_identity.py`.

## 10. Error compatibility

Preserve public categories:

- trusted final link/reparse -> `symlink_not_allowed` when attribution is justified;
- standalone pre-inspection non-regular file -> existing `wrong_path_type` behavior;
- trusted-open/query/conversion/setmode/fstat/mismatch/read/missing required primitive or raced non-regular opened object -> `filesystem_error` unless an existing caller path is more specific;
- recursive unsupported entries discovered during ordinary enumeration -> existing `unsupported_entry`.

No file-ID metadata enters digest bytes. Algorithm constants remain unchanged.

## 11. CI before final review

Require exact-head:

- focused F-018 Ubuntu/Windows × Python 3.10/3.12 GREEN;
- F-012 GREEN;
- F-014 GREEN;
- I-003 GREEN;
- authoritative full repository suite GREEN;
- current action-major/CI-ownership policy checks GREEN;
- compare against current main contains only F-018 research/plan/tests/workflow plus the narrow `src/ontotf/parent_identity.py` production delta.

If main moves materially, integrate current main and rerun exact-head CI before final review.

## 12. Independent adversarial review

Fresh exact-head logically-independent review is mandatory after GREEN. It must attack:

- accidental pathname reopen;
- tuple equality used as authorization;
- read-before-inspection ordering;
- POSIX `os.open` missing `O_NOFOLLOW` or `O_NONBLOCK`;
- regular->FIFO blocking/hang behavior;
- overbroad `ELOOP` -> `symlink_not_allowed` attribution;
- Windows `CreateFileW` missing `FILE_FLAG_OPEN_REPARSE_POINT`;
- ctypes handle width, prototypes, and last-error ABI;
- raw-handle/descriptor leaks or double-close;
- binary-mode placement;
- real Windows Python 3.10 behavior;
- digest-vector/error-category changes;
- scope creep into F-013/F-017.

Any material repair invalidates prior final review and returns through the appropriate RED/GREEN/CI gate.

## 13. Exit condition

F-018 is complete only when trusted acquisition and all digest reads use one retained descriptor/handle; POSIX acquisition cannot follow a raced final symlink or block on a raced FIFO; Windows acquisition is reparse-aware; tuple mismatch remains defense in depth without equality overclaim; resource ownership is single and deterministic on every failure path; exact Linux/Windows matrix and full suite are green; existing digest bytes/categories remain compatible; and fresh independent review reports no blocker.
