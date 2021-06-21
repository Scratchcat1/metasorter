import unittest
from metasorter.main import resolve_collision
from tempfile import mkdtemp
from metasorter.test.tempfile_context import TempFileContext
import os


class TestResolveCollision(unittest.TestCase):
    def setUp(self):
        self.source_dir = mkdtemp()
        self.target_dir = mkdtemp()

    def tearDown(self):
        os.rmdir(self.source_dir)
        os.rmdir(self.target_dir)

    def test_no_files(self):
        name = "abc"
        ext = "tmp"
        with TempFileContext(self.source_dir, filename=f"{name}.{ext}") as filepath:
            self.assertEqual(
                resolve_collision(filepath, self.target_dir, name, ext), "0"
            )

    def test_different_file(self):
        name = "abc"
        ext = "tmp"
        with TempFileContext(self.source_dir, filename=f"{name}.{ext}") as filepath:
            with TempFileContext(self.target_dir, filename=f"otherfile_0.{ext}"):
                self.assertEqual(
                    resolve_collision(filepath, self.target_dir, name, ext), "0"
                )

    def test_same_file(self):
        name = "abc"
        ext = "tmp"
        with TempFileContext(
            self.source_dir, filename=f"{name}.{ext}", data="data"
        ) as filepath:
            with TempFileContext(
                self.target_dir, filename=f"{name}_0.{ext}", data="data"
            ):
                self.assertEqual(
                    resolve_collision(filepath, self.target_dir, name, ext), "0"
                )

    def test_different_content(self):
        name = "abc"
        ext = "tmp"
        with TempFileContext(
            self.source_dir, filename=f"{name}.{ext}", data="data"
        ) as filepath:
            with TempFileContext(
                self.target_dir, filename=f"{name}_0.{ext}", data="not that data"
            ):
                self.assertEqual(
                    resolve_collision(filepath, self.target_dir, name, ext), "1"
                )
