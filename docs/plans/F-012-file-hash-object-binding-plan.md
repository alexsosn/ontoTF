# F-012 plan — bind file hashing to expected file identity
**Issue:** #80

## Preconditions

Research is committed first in `docs/research/F-012-file-hash-object-binding.md`. This branch is rebuilt directly on current `main`, including merged F-014 portable exact-file path spelling behavior.

## Public behavior

No public function signatures or digest algorithm identifiers change. Pre-existing symlink/reparse classification remains `symlink_not_allowed`; wrong standalone component type remains `wrong_path_type`; unsupported recursive entries remain `unsupported_entry`.

New fail-closed behavior uses existing `filesystem_error` for unavailable expected identity, descriptor open/fstat/read failure, non-regular opened descriptor, or `(st_dev, st_ino)` mismatch. The exact filesystem path is preserved in `IdentityProblem.path`.

## Production change

In `src/ontotf/parent_identity.py`:

1. add `_stat_no_follow(path)` using `os.stat(path, follow_symlinks=False)` with stable `filesystem_error` translation;
2. add `_file_identity(st, path)` requiring exact integer `st_dev` and non-zero exact integer `st_ino`;
3. change `_sha256_file(path, expected)` to validate expected identity, `os.open()` the pathname with `O_RDONLY`, optional `O_BINARY`, optional `O_NOFOLLOW`, immediately `os.fstat()` before reads, require regular file and matching identity, then hash via 1 MiB `os.read()` chunks, closing the descriptor on every path;
4. propagate expected stat through `_file_record()`;
5. use fresh no-follow `os.stat()` for recursive directory and TF entries that contribute bytes;
6. preserve merged F-014 `_reject_nonportable_file_path()` before standalone file inspection.

Filesystem metadata is validation-only and never enters digest projection bytes.

## TDD evidence

The original F-012 sequence already recorded a tests/workflow-only RED before production implementation. Deterministic RED cases cover standalone regular→different-regular replacement, regular→symlink replacement where supported, recursive file replacement, TF file replacement, injected fstat failure before any read, and unavailable/zero identity before opening or reading. Fixed file/directory/TF digest vectors and pre-existing symlink classification are controls.

Reintegration onto current main does not invent a new feature contract; it replays the accepted production delta on top of F-014 and requires fresh exact-head GREEN plus fresh independent review.

## F-010 seam

Because F-012 intentionally stops using cached `DirEntry.stat()` as the authoritative identity source, `tests/f010/test_deep_directory_identity.py` uses a virtual `os.stat(..., follow_symlinks=False)` seam while preserving all existing F-010 behavioral assertions.

## CI

Focused matrix: Ubuntu + Windows, Python 3.10 + 3.12, exact-head checkout, actions/checkout@v5, setup-python@v6, editable install + build, then `tests/f012`, `tests/f010`, and `tests/i003`.

Repository-wide discovery remains solely in `.github/workflows/full-suite.yml`.

## GREEN acceptance

- replacement races fail closed before replacement bytes are read;
- fstat failure and unavailable identity fail before `os.read()`; unavailable expected identity also fails before `os.open()`;
- fixed file/directory/TF digest vectors remain byte-identical;
- F-014 path spelling behavior remains green on Windows and POSIX;
- F-010 and I-003 regressions remain green;
- focused Ubuntu/Windows × Python 3.10/3.12 matrix is green;
- authoritative full suite is green on exact final head.

## Independent review

Fresh exact-head review must attack read-before-verification, O_NOFOLLOW portability, Windows identity availability, descriptor cleanup, regular→regular replacement, digest compatibility, F-014 preservation, F-010 behavior, F-007 sole full-suite ownership, and accidental scope creep into directory-handle or in-place-mutation semantics.

Any material head change invalidates CI and review.