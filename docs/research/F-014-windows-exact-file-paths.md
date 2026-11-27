# F-014 research — portable exact-file path spelling boundary

**Issue:** #84  

## Trigger

Cross-platform F-012 CI exposed an existing I-003 portability defect. On Windows, `file_component_digest(<regular-file> + os.sep + ".")` can reach `os.lstat()` as the underlying regular file, while POSIX rejects the same conceptual spelling. ontoTF therefore currently lets host pathname normalization decide whether an exact-file component spelling is accepted.

The F-012 object-binding tests themselves pass on Windows. This research is independent of F-012 production code.

## Existing contract

`file_component_digest()` represents one exact regular file. Unlike directory and TF roots, it does not strip terminal directory-root spellings. Existing I-003 coverage requires a terminal directory spelling such as `<file>/.` to fail.

At the same time, ordinary nonterminal relative traversal (`./file`, `dir/../dir/file`) was previously delegated to the host and is not the portability defect that triggered this work. F-014 should not remove that behavior without separate evidence.

## Host behavior

Windows path parsing can normalize spelling before the final filesystem object is inspected. Microsoft documents that ordinary Win32 path handling strips trailing ASCII periods and ASCII spaces from file/directory name components before opening; this can make a spelling resolve to a different stored name.

Primary evidence:

- Microsoft, **Naming Files, Paths, and Namespaces**: period as current-directory component; do not end a file/directory name with space or period.
- Microsoft Windows support, **Whitespace characters in file and folder names**: trailing ASCII space/period are removed by ordinary Windows naming behavior.
- Microsoft Windows Server support, **Can't delete files on NTFS file system**: typical Win32 syntax strips trailing spaces/periods before opening, potentially opening a different file; `\\?\` is a special namespace escape hatch.

The risk is not confined to the basename. An ancestor spelling such as `directory.\file.tf` can be normalized at the directory component before lookup reaches the final file. Checking only the last component leaves the same alias problem in an ancestor.

ontoTF does not define a separate extended-namespace identity mode. Accepting these stored-name spellings on POSIX while ordinary Windows APIs can alias another object would make identity input platform-dependent.

## Chosen contract

For `file_component_digest()` only, reject before filesystem inspection when:

1. the supplied path ends in a native path separator;
2. the **final** non-empty component is exactly `.`, preserving the existing `<file>/.` rejection; or
3. any native path component other than the navigation tokens `.` and `..` ends in ASCII period (`.`) or ASCII space (` `).

Rule 3 covers final and ancestor stored-name components. It is cross-platform on purpose: POSIX names ending in these characters are outside ontoTF's portable exact-file identity input domain because ordinary Win32 handling can reinterpret them.

Nonterminal `.` and `..` navigation tokens remain accepted as before. Leading periods (`.hidden`) and internal periods (`a.b`) remain valid. Non-native separator characters retain existing host semantics. Extended Win32 `\\?\` namespace semantics are not introduced.

Directory and TF roots retain their current `_root_inspection_path()` behavior; changing their naming domain requires separate research.

## Error category

Use existing `wrong_path_type` for rejected non-portable exact-file spellings. The original supplied path is retained in `IdentityProblem.path`.

Embedded NUL remains `filesystem_error` through `_lstat()` and is not intercepted by this lexical check.

## RED strategy and review history

The initial tests-only RED pinned terminal separators and terminal dot-segment rejection. Existing I-003 coverage reproduced `<file>/.` on Windows.

Independent adversarial passes then found three edge classes, each converted into deterministic RED before production hardening:

1. final stored-name components ending in ASCII period/space;
2. ancestor stored-name components with the same Win32 alias risk;
3. over-rejection of nonterminal `.` / `..` navigation tokens introduced by the second hardening.

Focused controls also pin `.hidden`, `a.b`, unchanged fixed digest, directory/TF root behavior, and embedded-NUL category preservation.

## Non-goals

- no generic path canonicalizer;
- no change to directory/TF root equivalence;
- no Windows reserved-device-name policy;
- no drive/UNC canonicalization project;
- no case-folding or Unicode filesystem normalization;
- no extended `\\?\` identity mode;
- no digest projection change;
- no F-012 descriptor-binding change.

## Conclusion

Reject Win32-ambiguous trailing ASCII period/space in stored-name components and terminal directory syntax before `lstat()`, while preserving existing nonterminal relative-navigation semantics.