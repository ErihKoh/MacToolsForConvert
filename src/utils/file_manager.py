"""Керування колекцією файлів і папок MacTools."""

import os
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
        """Додає файли та папки без рекурсивного обходу.

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

    def add_directory_recursive(
        self,
        directory: str | Path,
        include_directories: bool = False,
    ) -> tuple[int, int]:
        """Рекурсивно додає файли з папки та всіх її підпапок.

        За замовчуванням додаються лише файли.
        Якщо include_directories=True, додаються також підпапки.

        Символічні посилання не обходяться, щоб уникнути циклів.
        Повертає кількість доданих і пропущених елементів.
        """

        root = Path(directory)

        if not root.is_dir():
            return 0, 1

        added_count = 0
        skipped_count = 0

        def on_walk_error(_error: OSError) -> None:
            nonlocal skipped_count
            skipped_count += 1

        for current_root, dir_names, file_names in os.walk(
            root,
            topdown=True,
            followlinks=False,
            onerror=on_walk_error,
        ):
            current_path = Path(current_root)

            # Символічні посилання на папки не обходяться.
            dir_names[:] = [
                name
                for name in dir_names
                if not (current_path / name).is_symlink()
            ]

            candidates = [current_path / name for name in file_names]

            if include_directories:
                candidates.extend(
                    current_path / name for name in dir_names
                )

            for path in candidates:
                if path.is_symlink():
                    skipped_count += 1
                    continue

                try:
                    if not path.is_file() and not (
                        include_directories and path.is_dir()
                    ):
                        skipped_count += 1
                        continue

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