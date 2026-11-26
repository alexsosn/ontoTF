# F-014 plan — portable exact-file spelling boundary
**Issue:** #84

## Gate order

Research preceded implementation. Initial production edits followed tests-only RED. Adversarial review identified additional alias and compatibility cases; each was converted into deterministic RED coverage before production was changed again.

## Production change

`src/ontotf/parent_identity.py` has one private lexical helper for exact-file spellings. It rejects before `_lstat()` when:

- the path ends in a native separator;
- the final non-empty component is `.`; or
- any stored-name component other than navigation tokens `.` / `..` ends in ASCII period or ASCII space.

This covers Win32 aliases in ancestors and the basename without removing existing nonterminal `.` / `..` relative traversal.

No directory/TF root code changes. No digest projection or algorithm identifiers change.

## RED evidence

The gate history contains four explicit RED stages:

1. tests-only terminal separator/dot-segment contract before any production change;
2. final ASCII period/space aliases against the first GREEN;
3. ancestor ASCII period/space aliases against the second GREEN;
4. preservation of nonterminal `.` / `..` relative traversal against the over-broad third implementation.

Existing I-003 coverage separately reproduces the original `<file>/.` Windows defect.

Focused controls cover leading/internal periods, unchanged exact-file digest, directory/TF equivalent-root spellings, and embedded-NUL category preservation.

## CI

Focused workflow matrix:

- Ubuntu + Windows;
- Python 3.10 + 3.12;
- `tests/f014`;
- `tests/i003`.

Repository-wide discovery remains owned only by `full-suite.yml`.

## GREEN acceptance

- all focused tests green on all four matrix cells;
- full suite green on exact head;
- exact-file fixed digest unchanged;
- nonterminal relative-navigation behavior preserved;
- directory/TF root spellings unchanged;
- no F-012 production code included in this PR.

## Independent review

Fresh review over exact final SHA must attack over-rejection, Windows drive/UNC and `\\?\` implications, leading/internal dots, POSIX filenames intentionally excluded for portability, ancestor aliases, `.` / `..` compatibility, non-native separators, error category/path preservation, embedded-NUL behavior, and accidental changes to directory/TF root semantics.