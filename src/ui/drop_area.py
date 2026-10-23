"""Область перетягування файлів у MacTools."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from src.ui.styles import DARK_THEME


class DropArea(QFrame):
    """Компонент для додавання файлів через Drag-and-Drop."""

    files_added = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("dropArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(220)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Створює інтерфейс області перетягування."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(12)

        self.icon_label = QLabel("＋")
        self.icon_label.setObjectName("dropIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("Перетягніть файли сюди")
        self.title_label.setObjectName("dropTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.description_label = QLabel(
            "Файли та папки з Finder можна додавати групами"
        )
        self.description_label.setObjectName("dropDescription")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)

        self.browse_button = QPushButton("Вибрати файли")
        self.browse_button.setObjectName("browseButton")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.clicked.connect(self._browse_files)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addSpacing(8)
        layout.addWidget(
            self.browse_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        layout.addStretch()
        self.setStyleSheet(DARK_THEME)

    def dragEnterEvent(self, event) -> None:
        """Приймає перетягування, якщо воно містить файли або папки."""

        if self._has_local_urls(event):
            self._set_drag_active(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Дозволяє переміщення файлів над областю."""

        if self._has_local_urls(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """Відновлює звичайне оформлення після виходу з області."""

        self._set_drag_active(False)
        event.accept()

    def dropEvent(self, event) -> None:
        """Обробляє відпускання перетягнутих файлів."""

        self._set_drag_active(False)

        if not self._has_local_urls(event):
            event.ignore()
            return

        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]

        self._emit_valid_paths(paths)
        event.acceptProposedAction()

    def _browse_files(self) -> None:
        """Відкриває системний діалог вибору файлів."""

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Виберіть файли",
            str(Path.home()),
            "Усі файли (*)",
        )

        if paths:
            self._emit_valid_paths([Path(path) for path in paths])

    def _emit_valid_paths(self, paths: list[Path]) -> None:
        """Перевіряє шляхи та передає унікальні файли й папки."""

        valid_paths: list[str] = []
        seen: set[str] = set()

        for path in paths:
            if not path.exists():
                continue

            normalized_path = str(path.resolve())

            if normalized_path in seen:
                continue

            seen.add(normalized_path)
            valid_paths.append(normalized_path)

        if valid_paths:
            self.files_added.emit(valid_paths)

    @staticmethod
    def _has_local_urls(event) -> bool:
        """Перевіряє, чи містить подія локальні файли або папки."""

        return (
                event.mimeData().hasUrls()
                and any(
            url.isLocalFile()
            for url in event.mimeData().urls()
        )
        )

    def _set_drag_active(self, active: bool) -> None:
        """Перемикає оформлення під час перетягування."""

        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
