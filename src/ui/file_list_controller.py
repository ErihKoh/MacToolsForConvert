"""Керування файлами для головного вікна MacTools."""

from pathlib import Path

from src.utils.file_manager import FileManager


class FileListController:
    """Керує додаванням, очищенням і вибором файлів."""

    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager = file_manager

    def add_paths(self, paths: list[str]) -> tuple[int, int]:
        """Додає файли та рекурсивно обробляє вибрані папки."""

        added_count = 0
        skipped_count = 0

        for raw_path in paths:
            path = Path(raw_path)

            if not path.exists():
                skipped_count += 1
                continue

            if path.is_dir():
                added, skipped = (
                    self.file_manager.add_directory_recursive(path)
                )
            elif path.is_file():
                added, skipped = self.file_manager.add_files(
                    [str(path)]
                )
            else:
                skipped_count += 1
                continue

            added_count += added
            skipped_count += skipped

        return added_count, skipped_count

    def clear(self) -> None:
        """Очищає колекцію файлів."""

        self.file_manager.clear()

    def get_source_files(
            self,
            selected_keys: list[str] | None = None,
    ) -> list[Path]:
        """Повертає вибрані файли або всі додані файли.

        Якщо передано ключі вибраних елементів, використовує їх.
        Якщо вибір порожній, повертає всі додані файли.
        Папки не включає.
        """

        files = self.file_manager.files

        if selected_keys:
            source_paths = [
                files.get(key)
                for key in selected_keys
            ]
        else:
            source_paths = list(files.values())

        return [
            path
            for path in source_paths
            if path is not None and path.is_file()
        ]
