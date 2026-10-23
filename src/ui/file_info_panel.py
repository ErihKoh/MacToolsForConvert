"""Інформаційна панель MacTools."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from src.utils.file_info import get_file_info


class FileInfoPanel(QFrame):
    """Показує інформацію про вибраний файл або папку."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("infoPanel")
        self.setMinimumWidth(250)
        self.setMaximumWidth(340)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Створює інтерфейс інформаційної панелі."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.info_title = QLabel("Інформація")
        self.info_title.setObjectName("sectionLabel")

        self.info_name = QLabel("Файл не вибрано")
        self.info_name.setObjectName("infoName")
        self.info_name.setWordWrap(True)
        self.info_name.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.info_type = QLabel("Тип: —")
        self.info_size = QLabel("Розмір: —")
        self.info_modified = QLabel("Змінено: —")
        self.info_created = QLabel("Створено: —")
        self.info_path = QLabel("Шлях: —")

        self.info_path.setObjectName("infoPath")

        self.info_labels = [
            self.info_type,
            self.info_size,
            self.info_modified,
            self.info_created,
            self.info_path,
        ]

        for label in self.info_labels:
            if label is not self.info_path:
                label.setObjectName("infoValue")

            label.setWordWrap(True)
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

        layout.addWidget(self.info_title)
        layout.addWidget(self.info_name)
        layout.addSpacing(4)
        layout.addWidget(self.info_type)
        layout.addWidget(self.info_size)
        layout.addWidget(self.info_modified)
        layout.addWidget(self.info_created)
        layout.addSpacing(4)
        layout.addWidget(self.info_path)
        layout.addStretch()

    def update_info(self, path: Path | None) -> None:
        """Оновлює інформацію про вибраний елемент."""

        if path is None:
            self._show_empty()
            return

        try:
            info = get_file_info(path)
        except OSError:
            self._show_unavailable(path)
            return

        self.info_name.setText(info["name"])
        self.info_type.setText(f"Тип: {info['item_type']}")
        self.info_size.setText(f"Розмір: {info['size']}")
        self.info_modified.setText(
            f"Змінено: {info['modified']}"
        )
        self.info_created.setText(
            f"Створено: {info['created']}"
        )
        self.info_path.setText(f"Шлях: {info['path']}")

    def _show_empty(self) -> None:
        """Показує панель без вибраного елемента."""

        self.info_name.setText("Файл не вибрано")
        self.info_type.setText("Тип: —")
        self.info_size.setText("Розмір: —")
        self.info_modified.setText("Змінено: —")
        self.info_created.setText("Створено: —")
        self.info_path.setText("Шлях: —")

    def _show_unavailable(self, path: Path) -> None:
        """Показує панель, якщо метадані недоступні."""

        self.info_name.setText(path.name or str(path))
        self.info_type.setText("Тип: недоступний")
        self.info_size.setText("Розмір: недоступний")
        self.info_modified.setText("Змінено: недоступно")
        self.info_created.setText("Створено: недоступно")
        self.info_path.setText(f"Шлях: {path}")