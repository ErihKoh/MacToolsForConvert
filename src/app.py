"""Ініціалізація та запуск MacTools."""

import sys

from PySide6.QtWidgets import QApplication

from src.config import (
    APP_NAME,
    APP_VERSION,
    ensure_app_directories,
)
from src.ui.main_window import MainWindow
from src.config import DEFAULT_THEME
from src.ui.styles import THEMES


def run() -> int:
    """Запускає графічний застосунок."""

    ensure_app_directories()

    app = QApplication(sys.argv)
    app.setStyleSheet(THEMES[DEFAULT_THEME])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow()
    window.show()

    return app.exec()