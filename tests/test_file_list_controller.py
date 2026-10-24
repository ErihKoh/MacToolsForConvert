"""Тести контролера списку файлів MacTools."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.ui.file_list_controller import FileListController
from src.utils.file_manager import FileManager


class TestFileListController(unittest.TestCase):
    """Перевіряє керування файлами."""

    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.file_manager = FileManager()
        self.controller = FileListController(self.file_manager)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_paths_adds_file(self) -> None:
        source = self.root / "example.txt"
        source.write_text("test", encoding="utf-8")

        added, skipped = self.controller.add_paths([str(source)])

        self.assertEqual(added, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(self.file_manager.count, 1)

    def test_add_paths_skips_missing_path(self) -> None:
        missing = self.root / "missing.txt"

        added, skipped = self.controller.add_paths([str(missing)])

        self.assertEqual(added, 0)
        self.assertEqual(skipped, 1)
        self.assertEqual(self.file_manager.count, 0)

    def test_add_paths_adds_files_from_directory(self) -> None:
        directory = self.root / "documents"
        directory.mkdir()

        first_file = directory / "first.txt"
        second_file = directory / "second.txt"

        first_file.write_text("first", encoding="utf-8")
        second_file.write_text("second", encoding="utf-8")

        added, skipped = self.controller.add_paths([str(directory)])

        self.assertEqual(added, 2)
        self.assertEqual(skipped, 0)
        self.assertEqual(self.file_manager.count, 2)

    def test_clear_removes_all_files(self) -> None:
        source = self.root / "example.txt"
        source.write_text("test", encoding="utf-8")

        self.controller.add_paths([str(source)])
        self.controller.clear()

        self.assertEqual(self.file_manager.count, 0)

    def test_get_source_files_returns_selected_files(self) -> None:
        first_file = self.root / "first.txt"
        second_file = self.root / "second.txt"

        first_file.write_text("first", encoding="utf-8")
        second_file.write_text("second", encoding="utf-8")

        self.controller.add_paths([
            str(first_file),
            str(second_file),
        ])

        selected_keys = [str(first_file.resolve())]

        result = self.controller.get_source_files(selected_keys)

        self.assertEqual(result, [first_file])

    def test_get_source_files_returns_all_when_selection_is_empty(
        self,
    ) -> None:
        first_file = self.root / "first.txt"
        second_file = self.root / "second.txt"

        first_file.write_text("first", encoding="utf-8")
        second_file.write_text("second", encoding="utf-8")

        self.controller.add_paths([
            str(first_file),
            str(second_file),
        ])

        result = self.controller.get_source_files([])

        self.assertEqual(result, [first_file, second_file])

    def test_get_source_files_excludes_directories(self) -> None:
        directory = self.root / "documents"
        directory.mkdir()

        source = self.root / "example.txt"
        source.write_text("test", encoding="utf-8")

        self.file_manager.add_files([
            str(directory),
            str(source),
        ])

        result = self.controller.get_source_files()

        self.assertEqual(result, [source])


if __name__ == "__main__":
    unittest.main()