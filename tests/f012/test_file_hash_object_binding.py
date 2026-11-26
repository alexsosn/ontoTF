from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import ontotf.parent_identity as parent_identity
from ontotf.parent_identity import (
    IdentityError,
    directory_component_digest,
    file_component_digest,
    tf_payload_digest,
)


FILE_ALPHA_DIGEST = "sha256:b6a98d9ce9a2d9149288fa3df42d377c3e42737afdcdaf714e33c0a100b51060"
DIRECTORY_VECTOR_DIGEST = "sha256:d5d2ddbdccc7d67378836747af134ad681996ed0e0c63ec20f0e9e0ae259a323"
TF_VECTOR_DIGEST = "sha256:a3b28b34637f2a2bdba591ed2020c94a2991e4e64643741c804ca4621bd7f83f"


class FileObjectBindingTests(unittest.TestCase):
    def assert_category(self, category: str, func, *args, **kwargs) -> IdentityError:
        with self.assertRaises(IdentityError) as raised:
            func(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception

    def make_directory_vector(self, root: Path) -> None:
        (root / "a.txt").write_bytes(b"alpha\n")
        nested = root / "nested"
        nested.mkdir()
        (nested / "b.bin").write_bytes(b"\x00\x01\xff")

    def make_tf_vector(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / "oslots.tf").write_bytes(b"@edge\n1\t1\n")
        (root / "otext.tf").write_bytes(b"@config\n@sectionTypes=book,chapter,verse\n")
        (root / "otype.tf").write_bytes(b"@node\n1\tword\n")

    def test_standalone_regular_replacement_after_inspection_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            victim = base / "component.bin"
            replacement = base / "replacement.bin"
            victim.write_bytes(b"original-object")
            replacement.write_bytes(b"replacement-object")

            real_lstat = parent_identity._lstat
            fired = False

            def raced_lstat(path: str):
                nonlocal fired
                st = real_lstat(path)
                if not fired and path == str(victim):
                    fired = True
                    os.replace(replacement, victim)
                return st

            with patch.object(parent_identity, "_lstat", side_effect=raced_lstat):
                exc = self.assert_category("filesystem_error", file_component_digest, victim)
            self.assertTrue(fired)
            self.assertEqual(exc.problem.path, str(victim))

    def test_standalone_symlink_replacement_after_inspection_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            victim = base / "component.bin"
            target = base / "outside.bin"
            victim.write_bytes(b"original-object")
            target.write_bytes(b"outside-target")

            probe = base / "symlink-probe"
            try:
                probe.symlink_to(target)
                probe.unlink()
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            real_lstat = parent_identity._lstat
            fired = False

            def raced_lstat(path: str):
                nonlocal fired
                st = real_lstat(path)
                if not fired and path == str(victim):
                    fired = True
                    victim.unlink()
                    victim.symlink_to(target)
                return st

            with patch.object(parent_identity, "_lstat", side_effect=raced_lstat):
                exc = self.assert_category("filesystem_error", file_component_digest, victim)
            self.assertTrue(fired)
            self.assertEqual(exc.problem.path, str(victim))

    def test_recursive_file_replacement_after_entry_inspection_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "component"
            root.mkdir()
            victim = root / "victim.bin"
            victim.write_bytes(b"original-object")
            replacement = base / "replacement.bin"
            replacement.write_bytes(b"replacement-object")

            real_file_record = parent_identity._file_record
            fired = False

            def raced_file_record(*args, **kwargs):
                nonlocal fired
                filesystem_path = args[1]
                if not fired and filesystem_path == str(victim):
                    fired = True
                    os.replace(replacement, victim)
                return real_file_record(*args, **kwargs)

            with patch.object(parent_identity, "_file_record", side_effect=raced_file_record):
                exc = self.assert_category("filesystem_error", directory_component_digest, root)
            self.assertTrue(fired)
            self.assertEqual(exc.problem.path, str(victim))

    def test_tf_file_replacement_after_entry_inspection_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "tf"
            root.mkdir()
            victim = root / "otype.tf"
            victim.write_bytes(b"@node\n1\tword\n")
            replacement = base / "replacement.tf"
            replacement.write_bytes(b"@node\n1\treplacement\n")

            real_file_record = parent_identity._file_record
            fired = False

            def raced_file_record(*args, **kwargs):
                nonlocal fired
                filesystem_path = args[1]
                if not fired and filesystem_path == str(victim):
                    fired = True
                    os.replace(replacement, victim)
                return real_file_record(*args, **kwargs)

            with patch.object(parent_identity, "_file_record", side_effect=raced_file_record):
                exc = self.assert_category("filesystem_error", tf_payload_digest, root)
            self.assertTrue(fired)
            self.assertEqual(exc.problem.path, str(victim))

    def test_fstat_failure_is_filesystem_error_before_any_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"payload")
            with (
                patch.object(parent_identity.os, "fstat", side_effect=OSError("injected fstat failure")),
                patch.object(parent_identity.os, "read") as read_mock,
            ):
                exc = self.assert_category("filesystem_error", file_component_digest, path)
            read_mock.assert_not_called()
            self.assertEqual(exc.problem.path, str(path))

    def test_zero_file_identity_fails_closed_without_opening_or_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"payload")
            real = parent_identity._lstat(str(path))
            no_identity = SimpleNamespace(
                st_mode=real.st_mode,
                st_ino=0,
                st_dev=real.st_dev,
                st_file_attributes=getattr(real, "st_file_attributes", 0),
            )
            with (
                patch.object(parent_identity, "_lstat", return_value=no_identity),
                patch.object(parent_identity.os, "open") as open_mock,
                patch.object(parent_identity.os, "read") as read_mock,
            ):
                exc = self.assert_category("filesystem_error", file_component_digest, path)
            open_mock.assert_not_called()
            read_mock.assert_not_called()
            self.assertEqual(exc.problem.path, str(path))

    def test_unchanged_file_vector_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"alpha\n")
            self.assertEqual(file_component_digest(path), FILE_ALPHA_DIGEST)

    def test_unchanged_directory_vector_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_directory_vector(root)
            self.assertEqual(directory_component_digest(root), DIRECTORY_VECTOR_DIGEST)

    def test_unchanged_tf_vector_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tf_vector(root)
            self.assertEqual(tf_payload_digest(root), TF_VECTOR_DIGEST)

    def test_preexisting_symlinks_remain_symlink_not_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target.bin"
            target.write_bytes(b"payload")
            standalone = base / "standalone.bin"
            try:
                standalone.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assert_category("symlink_not_allowed", file_component_digest, standalone)

            directory = base / "directory"
            directory.mkdir()
            (directory / "link.bin").symlink_to(target)
            self.assert_category("symlink_not_allowed", directory_component_digest, directory)

            tf_root = base / "tf"
            tf_root.mkdir()
            (tf_root / "linked.tf").symlink_to(target)
            self.assert_category("symlink_not_allowed", tf_payload_digest, tf_root)


if __name__ == "__main__":
    unittest.main()
