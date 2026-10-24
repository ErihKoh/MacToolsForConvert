"""Ініціалізація та запуск MacTools."""

import sys

from PySide6.QtWidgets import QApplication

from src.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_THEME,
    ensure_app_directories,
)
from src.converters.setup import create_default_registry
from src.ui.main_window import MainWindow
from src.ui.styles import THEMES


def run() -> int:
    """Запускає графічний застосунок."""

    ensure_app_directories()

    app = QApplication(sys.argv)
    app.setStyleSheet(THEMES[DEFAULT_THEME])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Створюємо реєстр доступних конвертерів.
    converter_registry = create_default_registry()

    # Передаємо реєстр головному вікну.
    window = MainWindow(registry=converter_registry)
    window.show()

    return app.exec()