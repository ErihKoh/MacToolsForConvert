"""Тести для FileManager."""

import tempfile
import unittest
from pathlib import Path

from src.utils.file_manager import FileManager


class TestFileManager(unittest.TestCase):
    """Перевіряє керування колекцією файлів."""

    def setUp(self) -> None:
        """Створює тимчасову папку для кожного тесту."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.manager = FileManager()

    def tearDown(self) -> None:
        """Видаляє тимчасові файли."""

        self.temp_dir.cleanup()

    def test_empty_manager(self) -> None:
        """Нова колекція має бути порожньою."""

        self.assertEqual(self.manager.count, 0)
        self.assertEqual(self.manager.files, {})

    def test_add_file(self) -> None:
        """Перевіряє додавання наявного файлу."""

        file_path = self.root / "example.txt"
        file_path.write_text("Тест", encoding="utf-8")

        added, skipped = self.manager.add_files([str(file_path)])

        self.assertEqual(added, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(self.manager.count, 1)

    def test_add_duplicate(self) -> None:
        """Повторне додавання файлу не створює дубліката."""

        file_path = self.root / "example.txt"
        file_path.write_text("Тест", encoding="utf-8")

        added, skipped = self.manager.add_files(
            [str(file_path), str(file_path)]
        )

        self.assertEqual(added, 1)
        self.assertEqual(skipped, 1)
        self.assertEqual(self.manager.count, 1)

    def test_skip_missing_file(self) -> None:
        """Неіснуючий шлях має бути пропущений."""

        missing_path = self.root / "missing.txt"

        added, skipped = self.manager.add_files([str(missing_path)])

        self.assertEqual(added, 0)
        self.assertEqual(skipped, 1)
        self.assertEqual(self.manager.count, 0)

    def test_add_directory(self) -> None:
        """Перевіряє додавання папки."""

        directory = self.root / "documents"
        directory.mkdir()

        added, skipped = self.manager.add_files([str(directory)])

        self.assertEqual(added, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(self.manager.count, 1)

    def test_clear(self) -> None:
        """Очищення видаляє всі елементи."""

        file_path = self.root / "example.txt"
        file_path.write_text("Тест", encoding="utf-8")

        self.manager.add_files([str(file_path)])
        self.manager.clear()

        self.assertEqual(self.manager.count, 0)
        self.assertEqual(self.manager.files, {})

    def test_files_returns_copy(self) -> None:
        """Зміна поверненої колекції не змінює внутрішню."""

        file_path = self.root / "example.txt"
        file_path.write_text("Тест", encoding="utf-8")

        self.manager.add_files([str(file_path)])
        files = self.manager.files
        files.clear()

        self.assertEqual(self.manager.count, 1)

    def test_filter_by_category(self) -> None:
        """Фільтр повертає файли вибраної категорії."""

        image = self.root / "photo.png"
        document = self.root / "notes.txt"

        image.write_bytes(b"image")
        document.write_text("Тест", encoding="utf-8")

        self.manager.add_files([str(image), str(document)])

        result = self.manager.get_filtered_files("Зображення")

        self.assertEqual(len(result), 1)
        self.assertEqual(
            next(iter(result.values())).name,
            "photo.png",
        )

    def test_filter_all(self) -> None:
        """Категорія «Усі» повертає всі елементи."""

        first = self.root / "one.txt"
        second = self.root / "two.png"

        first.write_text("1", encoding="utf-8")
        second.write_bytes(b"2")

        self.manager.add_files([str(first), str(second)])

        self.assertEqual(
            len(self.manager.get_filtered_files("Усі")),
            2,
        )

    def test_unknown_category(self) -> None:
        """Невідома категорія повертає порожню колекцію."""

        file_path = self.root / "example.txt"
        file_path.write_text("Тест", encoding="utf-8")

        self.manager.add_files([str(file_path)])

        self.assertEqual(
            self.manager.get_filtered_files("Невідома категорія"),
            {},
        )


if __name__ == "__main__":
    unittest.main()