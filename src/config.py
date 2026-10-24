"""Централізована конфігурація MacTools."""

from pathlib import Path


# Основні параметри застосунку
APP_NAME = "MacTools"
APP_DISPLAY_NAME = "MacTools — File Tools"
APP_VERSION = "0.1.0"

# Коренева папка проєкту
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Папка для тимчасових даних
TEMP_DIR = Path.home() / "Library" / "Caches" / "MacTools"

# Папка для результатів обробки
OUTPUT_DIR = Path.home() / "Documents" / "MacTools"

# Початкові параметри головного вікна
WINDOW_WIDTH = 1120
WINDOW_HEIGHT = 760
WINDOW_MIN_WIDTH = 850
WINDOW_MIN_HEIGHT = 580

# Параметри інтерфейсу
DEFAULT_THEME = "dark"
DEFAULT_LANGUAGE = "uk"

# Категорії файлів
CATEGORIES = {
    "Зображення": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp",
        ".tiff", ".tif", ".webp", ".heic", ".svg", ".ico",
    },
    "PDF": {
        ".pdf",
    },
    "Файли": {
        ".txt", ".md", ".rtf", ".doc", ".docx",
        ".xls", ".xlsx", ".csv", ".ppt", ".pptx",
        ".json", ".xml", ".html", ".htm", ".py",
        ".js", ".css", ".log",
    },
    "Медіа": {
        ".mp3", ".wav", ".flac", ".aac", ".ogg",
        ".mp4", ".mov", ".avi", ".mkv", ".webm",
        ".m4a", ".wma",
    },
    "Архіви": {
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".bz2", ".xz",
    },
}


def ensure_app_directories() -> None:
    """Створює необхідні папки застосунку."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
