"""Панель налаштування конвертації файлів MacTools."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.config import OUTPUT_DIR


class ConversionPanel(QFrame):
    """"Панель вибору формату та папки для конвертації."""
    convert_requested = Signal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("conversionPanel")

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Створює елементи інтерфейсу панелі."""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Заголовок панелі.
        self.title_label = QLabel("Конвертація файлів")
        self.title_label.setObjectName("sectionLabel")

        main_layout.addWidget(self.title_label)

        # Вибір вихідного формату.
        format_layout = QHBoxLayout()
        format_layout.setSpacing(10)

        self.format_label = QLabel("Формат:")
        self.format_label.setMinimumWidth(80)

        self.format_combo = QComboBox()
        self.format_combo.setObjectName("outputFormatCombo")
        self.format_combo.addItem("JPEG (.jpg)", "jpg")
        self.format_combo.addItem("PNG (.png)", "png")
        self.format_combo.addItem("WebP (.webp)", "webp")
        self.format_combo.addItem("TIFF (.tiff)", "tiff")
        self.format_combo.addItem("BMP (.bmp)", "bmp")

        format_layout.addWidget(self.format_label)
        format_layout.addWidget(self.format_combo, 1)

        main_layout.addLayout(format_layout)

        # Вибір папки для результатів.
        directory_label = QLabel("Папка для результатів:")
        directory_label.setObjectName("fieldLabel")

        main_layout.addWidget(directory_label)

        directory_layout = QHBoxLayout()
        directory_layout.setSpacing(8)

        self.output_directory_edit = QLineEdit(str(OUTPUT_DIR))
        self.output_directory_edit.setObjectName(
            "outputDirectoryEdit"
        )
        self.output_directory_edit.setClearButtonEnabled(True)
        self.output_directory_edit.setPlaceholderText(
            "Вкажіть папку для збереження результатів"
        )

        self.browse_directory_button = QPushButton("Огляд…")
        self.browse_directory_button.setObjectName(
            "browseDirectoryButton"
        )
        self.browse_directory_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        directory_layout.addWidget(self.output_directory_edit, 1)
        directory_layout.addWidget(self.browse_directory_button)

        main_layout.addLayout(directory_layout)

        # Кнопка запуску.
        self.convert_button = QPushButton("Конвертувати")
        self.convert_button.setObjectName("convertButton")
        self.convert_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        main_layout.addWidget(
            self.convert_button,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

    def _connect_signals(self) -> None:
        """Підключає обробники натискання кнопок."""

        self.browse_directory_button.clicked.connect(
            self._browse_output_directory
        )

        self.convert_button.clicked.connect(
            self._request_conversion
        )

    def _browse_output_directory(self) -> None:
        """Відкриває діалог вибору папки результатів."""

        current_directory = self.output_directory_edit.text().strip()

        if not current_directory:
            current_directory = str(Path.home())

        selected_directory = QFileDialog.getExistingDirectory(
            self,
            "Виберіть папку для результатів",
            current_directory,
        )

        if selected_directory:
            self.output_directory_edit.setText(selected_directory)

    def _request_conversion(self) -> None:
        """Передає параметри конвертації головному вікну."""

        output_format = str(self.format_combo.currentData())
        output_directory = self.output_directory_edit.text().strip()

        self.convert_requested.emit(
            output_format,
            output_directory,
        )
