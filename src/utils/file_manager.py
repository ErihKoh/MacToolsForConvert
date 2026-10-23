"""Керування колекцією файлів і папок MacTools."""

from pathlib import Path

from src.config import CATEGORIES


class FileManager:
    """Зберігає, перевіряє та фільтрує додані файли."""

    def __init__(self) -> None:
        self._files: dict[str, Path] = {}

    @property
    def files(self) -> dict[str, Path]:
        """Повертає копію колекції файлів."""

        return self._files.copy()

    @property
    def count(self) -> int:
        """Повертає кількість усіх доданих елементів."""

        return len(self._files)

    def add_files(self, paths: list[str]) -> tuple[int, int]:
        """Додає файли та папки.

        Повертає пару:
        (кількість доданих елементів, кількість пропущених).
        """

        added_count = 0
        skipped_count = 0

        for raw_path in paths:
            path = Path(raw_path)

            if not path.exists():
                skipped_count += 1
                continue

            try:
                key = str(path.resolve(strict=True))
            except (OSError, RuntimeError):
                skipped_count += 1
                continue

            if key in self._files:
                skipped_count += 1
                continue

            self._files[key] = path
            added_count += 1

        return added_count, skipped_count

    def clear(self) -> None:
        """Видаляє всі елементи з колекції."""

        self._files.clear()

    def get_filtered_files(
        self,
        category: str = "Усі",
    ) -> dict[str, Path]:
        """Повертає файли, що відповідають вибраній категорії."""

        if category == "Усі":
            return self.files

        extensions = CATEGORIES.get(category)

        if extensions is None:
            return {}

        filtered: dict[str, Path] = {}

        for key, path in self._files.items():
            if path.is_dir():
                continue

            if path.suffix.lower() in extensions:
                filtered[key] = path

        return filtered