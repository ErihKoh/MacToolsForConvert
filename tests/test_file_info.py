"""Тести для утиліт інформації про файли."""

import tempfile
import unittest
from pathlib import Path

from src.utils.file_info import (
    format_size,
    get_directory_size,
    get_file_info,
)


class TestFormatSize(unittest.TestCase):
    """Перевіряє форматування розміру файлів."""

    def test_zero_bytes(self) -> None:
        self.assertEqual(format_size(0), "0 Б")

    def test_bytes(self) -> None:
        self.assertEqual(format_size(512), "512 Б")

    def test_kilobytes(self) -> None:
        self.assertEqual(format_size(1024), "1.00 КБ")

    def test_megabytes(self) -> None:
        self.assertEqual(format_size(1048576), "1.00 МБ")

    def test_gigabytes(self) -> None:
        self.assertEqual(format_size(1073741824), "1.00 ГБ")

    def test_negative_size(self) -> None:
        with self.assertRaises(ValueError):
            format_size(-1)


class TestGetFileInfo(unittest.TestCase):
    """Перевіряє отримання метаданих файлів і папок."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_regular_file(self) -> None:
        file_path = self.root / "example.txt"
        file_path.write_text("Hello", encoding="utf-8")

        info = get_file_info(file_path)

        self.assertEqual(info["name"], "example.txt")
        self.assertEqual(info["item_type"], "TXT")
        self.assertEqual(info["size"], "5 Б")
        self.assertEqual(info["path"], str(file_path.resolve()))
        self.assertTrue(info["modified"])
        self.assertTrue(info["created"])

    def test_file_without_extension(self) -> None:
        file_path = self.root / "README"
        file_path.write_text("Test", encoding="utf-8")

        info = get_file_info(file_path)

        self.assertEqual(info["item_type"], "Файл без розширення")

    def test_directory(self) -> None:
        directory = self.root / "documents"
        directory.mkdir()

        info = get_file_info(directory)

        self.assertEqual(info["name"], "documents")
        self.assertEqual(info["item_type"], "Папка")
        self.assertEqual(info["size"], "0 Б")
        self.assertEqual(info["path"], str(directory.resolve()))

    def test_missing_file(self) -> None:
        file_path = self.root / "missing.txt"

        with self.assertRaises(OSError):
            get_file_info(file_path)

    def test_directory_size_includes_nested_files(self) -> None:
        """Розмір папки включає файли з підпапок."""

        (self.root / "first.txt").write_bytes(b"12345")

        nested = self.root / "nested"
        nested.mkdir()
        (nested / "second.txt").write_bytes(b"1234567")

        self.assertEqual(get_directory_size(self.root), 12)

        info = get_file_info(self.root)
        self.assertEqual(info["size"], "12 Б")

    def test_empty_directory_size(self) -> None:
        """Порожня папка має нульовий розмір."""

        directory = self.root / "empty"
        directory.mkdir()

        self.assertEqual(get_directory_size(directory), 0)


if __name__ == "__main__":
    unittest.main()