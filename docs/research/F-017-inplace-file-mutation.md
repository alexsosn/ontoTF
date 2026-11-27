# F-017 research — in-place mutation during identity hashing

**Issue:** #91  

## Question

F-012 now binds reads to the exact file object accepted by ontoTF: after a no-follow inspection, the opened descriptor is `fstat()`-verified against `(st_dev, st_ino)` before any byte is read. That closes pathname substitution.

It does not prove that the bytes of the same opened object remain unchanged while the descriptor is being streamed. This research asks whether Python 3.10+ standard-library facilities can provide a uniform POSIX/Windows content-snapshot guarantee without changing the existing digest algorithms.

## Distinct integrity properties

Three properties must not be conflated:

1. **pathname binding** — the opened descriptor refers to the same filesystem object that passed inspection; F-012 provides this;
2. **same-object mutation detection** — notice at least some writes to that object while hashing;
3. **content snapshot semantics** — every byte contributing to the digest comes from one immutable logical file state.

Property 2 can be approximated with metadata. Property 3 is the stronger guarantee required before ontoTF could honestly call the hash an atomic snapshot.

## Metadata before/after hashing is not a snapshot proof

Python exposes `st_size`, `st_mtime_ns`, and `st_ctime_ns`, but explicitly documents platform/filesystem-dependent timestamp meaning and resolution. In Python 3.10, `st_ctime`/`st_ctime_ns` is metadata-change time on Unix but creation time on Windows. The docs also note that even `*_ns` fields do not imply nanosecond filesystem precision and give FAT/FAT32 as coarse-resolution examples.

Therefore a pre/post tuple such as `(size, mtime_ns, ctime_ns)` is not a portable proof that bytes were unchanged:

- a writer can change bytes without changing file size;
- mtime can be restored by ordinary metadata-setting APIs;
- Windows `ctime` is not the Unix metadata-change clock;
- filesystem timestamp granularity can collapse multiple changes into one observable value;
- a writer can complete a mutation/restore cycle between the two observations.

A second `fstat()` after hashing would detect many ordinary concurrent writes, but it is a best-effort race detector, not a cryptographic or snapshot guarantee.

## POSIX locking is not a uniform guarantee

Python's `fcntl` module is Unix-only. `fcntl.flock()` / `lockf()` expose shared/exclusive locking, with platform-specific implementation details. These interfaces do not establish a cross-platform ontoTF contract, and conventional POSIX file locks are coordination mechanisms rather than a guarantee against every writer that does not participate in the locking protocol.

Even if ontoTF acquired a Unix lock, treating that as immutable-content proof would require stronger filesystem/OS assumptions than the current portable identity API states.

## Windows has different primitives and semantics

Python exposes `msvcrt.locking()` on Windows for byte-range locks, while Win32 `CreateFile` has an independent sharing-mode model. Microsoft documents that a `CreateFile` handle opened without write sharing can prevent later incompatible write opens for the handle lifetime.

However ontoTF's F-012 code uses portable `os.open()`, whose interface does not expose the Win32 `CreateFile` sharing-mode parameter. Achieving deliberate no-write sharing would require a Windows-specific opening path (for example a CRT sharing API or native Win32 handle code), while Unix would still use different advisory-lock semantics.

A Windows-only exclusive-open backend therefore cannot be silently presented as a uniform Python-stdlib guarantee.

Existing writers or mappings also complicate locking claims: a lock/open policy that prevents subsequent incompatible opens does not automatically prove that no already-open writer or writable mapping can affect the file unless the platform contract explicitly guarantees that interaction.

## Copying to a temporary file does not solve source atomicity

ontoTF could copy an opened source into private storage and hash the copy, but if the source changes while the copy is being made the copied bytes can still represent a mixed read. The private copy stabilizes bytes only **after** the potentially inconsistent acquisition step.

Filesystem snapshots, copy-on-write clones, leases, transaction APIs, or file seals can provide stronger properties on particular platforms/filesystems, but Python 3.10 does not expose one portable primitive that gives this guarantee for arbitrary addressed files on both Windows and POSIX.

## Digest-version implication

The current identity algorithms describe byte digests of addressed files/directories/TF payloads; runtime validation metadata is not part of their projections. Adding a best-effort pre/post metadata comparison could fail additional concurrent cases without changing successful digest bytes, but it would still not justify changing the documented semantic guarantee to “snapshot”.

A real snapshot-capable backend would introduce platform capability and acquisition semantics significant enough to require separate architecture/versioning review rather than being smuggled into the existing portable algorithm contract.

## Decision

Do **not** add an F-017 production change under the claim of solving in-place mutation.

The uniform v1 guarantee remains:

- ontoTF binds hashed bytes to the exact inspected filesystem object;
- callers/producers must provide quiescent file contents while identity is being computed;
- ontoTF does not claim atomic snapshot semantics against concurrent same-object writers.

Do not add pre/post timestamp checks as a security guarantee. If a future operational use case values best-effort mutation diagnostics, that should be a separately named non-authoritative diagnostic feature whose documentation explicitly permits false negatives. It must not affect compatibility claims as if immutability had been proven.

## Future capability path

Revisit only if there is a concrete requirement for hostile/concurrent-writer snapshot semantics. Research should then be platform-capability based, for example:

- Windows deliberate `CreateFile` sharing modes / native handles;
- filesystem snapshot or clone APIs where available;
- Linux-specific seals or stronger file-description capabilities where applicable;
- producer-side immutable/content-addressed staging.

The likely architecture is a capability-qualified acquisition backend, not one hidden branch inside the current portable hasher.

## Primary evidence

- Python 3.10 `os.stat_result`: timestamp meanings and filesystem-dependent resolution; `st_ctime` differs between Unix and Windows.
- Python 3.10 `fcntl`: Unix-only descriptor locking (`flock`, `lockf`).
- Python 3.10 `msvcrt.locking`: Windows byte-range locking.
- Microsoft Win32 `CreateFile`: access and sharing modes remain attached to an open handle and can reject incompatible subsequent opens.
- Microsoft CRT sharing APIs: explicit modes distinguish deny-write/deny-read-write from permissive sharing.

## Gate result

Research finds no uniform Python-3.10-stdlib mechanism that proves one immutable content snapshot for arbitrary regular files across supported Windows and POSIX environments. Stop before plan/RED/implementation. F-012's object-binding guarantee remains valid and deliberately narrower.