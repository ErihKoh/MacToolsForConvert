"""Панель зі списком доданих файлів і папок."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
)


class FileListPanel(QFrame):
    """Відображає список файлів і лічильник елементів."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("filesPanel")

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Створює інтерфейс панелі."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()

        self.files_label = QLabel("Додані елементи")
        self.files_label.setObjectName("sectionLabel")

        self.count_label = QLabel("0")
        self.count_label.setObjectName("countLabel")

        header_layout.addWidget(self.files_label)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)

        self.files_list = QListWidget()
        self.files_list.setObjectName("filesList")
        self.files_list.setAlternatingRowColors(True)
        self.files_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )
        self.files_list.setMinimumWidth(300)

        layout.addLayout(header_layout)
        layout.addWidget(self.files_list)

    def update_count(self) -> None:
        """Оновлює лічильник видимих елементів."""

        self.count_label.setText(
            str(self.files_list.count())
        )
