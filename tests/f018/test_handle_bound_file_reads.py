from __future__ import annotations

import hashlib
import multiprocessing
import os
from pathlib import Path
from queue import Empty
import stat
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ontotf.parent_identity as parent_identity
from ontotf.parent_identity import IdentityError, file_component_digest


FILE_ALPHA_DIGEST = "sha256:b6a98d9ce9a2d9149288fa3df42d377c3e42737afdcdaf714e33c0a100b51060"


def _fifo_race_worker(directory: str, result_queue) -> None:
    victim = Path(directory) / "component.bin"
    victim.write_bytes(b"ordinary-before-race")
    real_lstat = parent_identity._lstat
    fired = False

    def raced_lstat(path: str):
        nonlocal fired
        opened = real_lstat(path)
        if not fired and path == str(victim):
            fired = True
            victim.unlink()
            os.mkfifo(victim)
        return opened

    try:
        with (
            patch.object(parent_identity, "_lstat", side_effect=raced_lstat),
            patch.object(parent_identity.os, "read", side_effect=AssertionError("digest read before FIFO rejection")),
        ):
            file_component_digest(victim)
    except IdentityError as exc:
        result_queue.put(("identity", exc.problem.category, fired))
    except BaseException as exc:  # pragma: no cover - returned to parent for diagnosis
        result_queue.put(("other", f"{type(exc).__name__}: {exc}", fired))
    else:
        result_queue.put(("success", None, fired))


class HandleBoundFileReadControls(unittest.TestCase):
    def assert_category(self, category: str, func, *args, **kwargs) -> IdentityError:
        with self.assertRaises(IdentityError) as raised:
            func(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception

    def test_existing_file_digest_vector_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"alpha\n")
            self.assertEqual(file_component_digest(path), FILE_ALPHA_DIGEST)

    def test_preexisting_final_symlink_remains_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target.bin"
            link = base / "component.bin"
            target.write_bytes(b"payload")
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assert_category("symlink_not_allowed", file_component_digest, link)


class HandleBoundFileReadREDTests(unittest.TestCase):
    def assert_category(self, category: str, func, *args, **kwargs) -> IdentityError:
        with self.assertRaises(IdentityError) as raised:
            func(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception

    def helper(self):
        helper = getattr(parent_identity, "_open_trusted_file_descriptor", None)
        self.assertTrue(callable(helper), "trusted descriptor helper is required")
        return helper

    def descriptor_hasher(self):
        helper = getattr(parent_identity, "_sha256_descriptor", None)
        self.assertTrue(callable(helper), "descriptor hashing helper is required")
        return helper

    def fake_stat(self, *, inode: int = 101):
        return SimpleNamespace(st_mode=stat.S_IFREG | 0o644, st_dev=7, st_ino=inode)

    def test_trusted_descriptor_helpers_exist(self):
        self.helper()
        self.descriptor_hasher()

    @unittest.skipIf(os.name == "nt", "POSIX no-follow/nonblocking contract")
    def test_posix_zero_nofollow_fails_closed_without_read(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"payload")
            with (
                patch.object(parent_identity.os, "O_NOFOLLOW", 0, create=True),
                patch.object(parent_identity.os, "read") as read_mock,
            ):
                exc = self.assert_category("filesystem_error", helper, str(path))
            read_mock.assert_not_called()
            self.assertEqual(exc.problem.path, str(path))

    @unittest.skipIf(os.name == "nt", "POSIX no-follow/nonblocking contract")
    def test_posix_zero_nonblock_fails_closed_without_read(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"payload")
            with (
                patch.object(parent_identity.os, "O_NONBLOCK", 0, create=True),
                patch.object(parent_identity.os, "read") as read_mock,
            ):
                exc = self.assert_category("filesystem_error", helper, str(path))
            read_mock.assert_not_called()
            self.assertEqual(exc.problem.path, str(path))

    @unittest.skipIf(os.name == "nt", "POSIX acquisition flag contract")
    def test_posix_kernel_open_receives_nofollow_and_nonblock(self):
        helper = self.helper()
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        nonblock = getattr(os, "O_NONBLOCK", 0)
        self.assertNotEqual(nofollow, 0, "runner must expose O_NOFOLLOW")
        self.assertNotEqual(nonblock, 0, "runner must expose O_NONBLOCK")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"payload")
            real_open = os.open
            calls: list[int] = []

            def tracked_open(target, flags, *args, **kwargs):
                calls.append(flags)
                return real_open(target, flags, *args, **kwargs)

            with patch.object(parent_identity.os, "open", side_effect=tracked_open):
                descriptor = helper(str(path))
            try:
                self.assertEqual(len(calls), 1, "trusted POSIX acquisition must use one kernel pathname open")
                self.assertTrue(calls[0] & nofollow, "trusted open is missing O_NOFOLLOW")
                self.assertTrue(calls[0] & nonblock, "trusted open is missing O_NONBLOCK")
            finally:
                os.close(descriptor)

    def test_trusted_opener_rejects_final_symlink_before_any_read(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target.bin"
            link = base / "component.bin"
            target.write_bytes(b"target")
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            with patch.object(parent_identity.os, "read") as read_mock:
                exc = self.assert_category("symlink_not_allowed", helper, str(link))
            read_mock.assert_not_called()
            self.assertEqual(exc.problem.path, str(link))

    @unittest.skipIf(os.name == "nt", "POSIX FIFO acquisition contract")
    def test_regular_to_fifo_race_is_bounded_and_rejected_before_read(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("mkfifo unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            context = multiprocessing.get_context("fork")
            result_queue = context.Queue()
            process = context.Process(target=_fifo_race_worker, args=(tmp, result_queue))
            process.start()
            process.join(timeout=3.0)
            if process.is_alive():
                process.terminate()
                process.join(timeout=1.0)
                self.fail("trusted acquisition blocked on a raced FIFO")

            self.assertEqual(process.exitcode, 0)
            try:
                outcome = result_queue.get(timeout=1.0)
            except Empty:
                self.fail("FIFO race worker exited without reporting an outcome")
            self.assertEqual(outcome, ("identity", "filesystem_error", True))

    def test_replacing_path_after_trusted_acquisition_does_not_redirect_reads(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            victim = base / "component.bin"
            replacement = base / "replacement.bin"
            original_bytes = b"original-open-object"
            victim.write_bytes(original_bytes)
            replacement.write_bytes(b"replacement-path-object")

            real_helper = helper
            fired = False

            def acquire_then_replace(path: str):
                nonlocal fired
                descriptor = real_helper(path)
                if not fired:
                    fired = True
                    os.replace(replacement, victim)
                return descriptor

            with patch.object(parent_identity, "_open_trusted_file_descriptor", side_effect=acquire_then_replace):
                digest = file_component_digest(victim)

            self.assertTrue(fired)
            self.assertEqual(digest, "sha256:" + hashlib.sha256(original_bytes).hexdigest())

    def test_descriptor_hashing_never_reopens_path(self):
        descriptor_hasher = self.descriptor_hasher()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            payload = b"descriptor-only"
            path.write_bytes(payload)
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
            try:
                with patch.object(parent_identity.os, "open", side_effect=AssertionError("pathname reopen")):
                    digest = descriptor_hasher(descriptor, str(path))
            finally:
                os.close(descriptor)
            self.assertEqual(digest, "sha256:" + hashlib.sha256(payload).hexdigest())

    def test_common_fstat_failure_closes_returned_descriptor_once_without_read(self):
        expected = self.fake_stat()
        with (
            patch.object(parent_identity, "_open_trusted_file_descriptor", return_value=41, create=True),
            patch.object(parent_identity.os, "fstat", side_effect=OSError("injected fstat failure")),
            patch.object(parent_identity.os, "read") as read_mock,
            patch.object(parent_identity.os, "close") as close_mock,
        ):
            self.assert_category("filesystem_error", parent_identity._sha256_file, "synthetic.bin", expected)
        read_mock.assert_not_called()
        close_mock.assert_called_once_with(41)

    def test_common_identity_mismatch_closes_returned_descriptor_once_without_read(self):
        expected = self.fake_stat(inode=101)
        opened = self.fake_stat(inode=202)
        with (
            patch.object(parent_identity, "_open_trusted_file_descriptor", return_value=42, create=True),
            patch.object(parent_identity.os, "fstat", return_value=opened),
            patch.object(parent_identity.os, "read") as read_mock,
            patch.object(parent_identity.os, "close") as close_mock,
        ):
            self.assert_category("filesystem_error", parent_identity._sha256_file, "synthetic.bin", expected)
        read_mock.assert_not_called()
        close_mock.assert_called_once_with(42)

    def test_common_read_failure_closes_returned_descriptor_once(self):
        expected = self.fake_stat()
        opened = self.fake_stat()
        with (
            patch.object(parent_identity, "_open_trusted_file_descriptor", return_value=43, create=True),
            patch.object(parent_identity.os, "fstat", return_value=opened),
            patch.object(parent_identity.os, "read", side_effect=OSError("injected read failure")),
            patch.object(parent_identity.os, "close") as close_mock,
        ):
            self.assert_category("filesystem_error", parent_identity._sha256_file, "synthetic.bin", expected)
        close_mock.assert_called_once_with(43)

    def test_common_success_closes_returned_descriptor_once(self):
        expected = self.fake_stat()
        opened = self.fake_stat()
        payload = b"owned-descriptor"
        with (
            patch.object(parent_identity, "_open_trusted_file_descriptor", return_value=44, create=True),
            patch.object(parent_identity.os, "fstat", return_value=opened),
            patch.object(parent_identity.os, "read", side_effect=[payload, b""]),
            patch.object(parent_identity.os, "close") as close_mock,
        ):
            digest = parent_identity._sha256_file("synthetic.bin", expected)
        self.assertEqual(digest, "sha256:" + hashlib.sha256(payload).hexdigest())
        close_mock.assert_called_once_with(44)


if __name__ == "__main__":
    unittest.main()
