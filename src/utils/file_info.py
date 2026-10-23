"""Утиліти для отримання інформації про файли та папки."""

from datetime import datetime
from pathlib import Path
from typing import TypedDict


class FileInfo(TypedDict):
    """Структура метаданих файлу або папки."""

    name: str
    item_type: str
    size: str
    modified: str
    created: str
    path: str


def format_size(size: int) -> str:
    """Перетворює розмір у байтах на читабельний формат."""

    if size < 0:
        raise ValueError("Розмір не може бути від'ємним.")

    units = ("Б", "КБ", "МБ", "ГБ", "ТБ")
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "Б":
                return f"{int(value)} {unit}"

            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{size} Б"


def get_file_info(path: str | Path) -> FileInfo:
    """Повертає метадані файлу або папки."""

    file_path = Path(path)
    stat = file_path.stat()

    if file_path.is_dir():
        item_type = "Папка"
        size_text = "—"
    else:
        item_type = file_path.suffix.upper().lstrip(".")

        if not item_type:
            item_type = "Файл без розширення"

        size_text = format_size(stat.st_size)

    modified = datetime.fromtimestamp(
        stat.st_mtime
    ).strftime("%d.%m.%Y %H:%M:%S")

    # На macOS st_birthtime зазвичай містить час створення.
    birth_time = getattr(stat, "st_birthtime", None)

    if birth_time is not None:
        created = datetime.fromtimestamp(
            birth_time
        ).strftime("%d.%m.%Y %H:%M:%S")
    else:
        created = "Недоступно"

    return {
        "name": file_path.name or str(file_path),
        "item_type": item_type,
        "size": size_text,
        "modified": modified,
        "created": created,
        "path": str(file_path.resolve()),
    }