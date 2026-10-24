"""Панель налаштування конвертації файлів MacTools."""

from pathlib import Path
from typing import Iterable

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
    QProgressBar,
)

from src.config import OUTPUT_DIR
from src.converters.formats import IMAGE_FORMATS, PDF_FORMATS, DOCUMENT_FORMATS, normalize_format, \
    get_format_display_name


class ConversionPanel(QFrame):
    """"Панель вибору формату та папки для конвертації."""
    convert_requested = Signal(str, str)

    ALL_FORMATS = set(IMAGE_FORMATS) | set(PDF_FORMATS) | set(DOCUMENT_FORMATS)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("conversionPanel")
        self._setup_ui()
        self._connect_signals()
        self.set_available_formats(self.ALL_FORMATS)

    def _setup_ui(self) -> None:
        """Створює елементи інтерфейсу панелі."""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        self.title_label = QLabel("Конвертація файлів")
        self.title_label.setObjectName("sectionLabel")
        main_layout.addWidget(self.title_label)

        format_layout = QHBoxLayout()
        format_layout.setSpacing(10)

        self.format_label = QLabel("Формат:")
        self.format_label.setMinimumWidth(80)

        self.format_combo = QComboBox()
        self.format_combo.setObjectName("outputFormatCombo")

        format_layout.addWidget(self.format_label)
        format_layout.addWidget(self.format_combo, 1)
        main_layout.addLayout(format_layout)

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

        self.convert_button = QPushButton("Конвертувати")
        self.convert_button.setObjectName("convertButton")
        self.convert_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        main_layout.addWidget(
            self.convert_button,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        # Індикатор прогресу конвертації.
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("conversionProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Готовність: %p%")
        self.progress_bar.hide()

        main_layout.addWidget(self.progress_bar)

        # Кнопка скасування конвертації.
        self.cancel_conversion_button = QPushButton(
            "Скасувати конвертацію"
        )
        self.cancel_conversion_button.setObjectName(
            "cancelConversionButton"
        )
        self.cancel_conversion_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.cancel_conversion_button.hide()

        main_layout.addWidget(
            self.cancel_conversion_button,
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

    def set_conversion_running(self, total: int) -> None:
        """Готує панель до виконання конвертації."""

        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"0 із {total} файлів")
        self.progress_bar.show()

        self.cancel_conversion_button.setEnabled(True)
        self.cancel_conversion_button.show()
        self.convert_button.setEnabled(False)

    def update_conversion_progress(
            self,
            current: int,
            total: int,
            filename: str,
    ) -> None:
        """Оновлює прогрес і назву поточного файла."""

        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current - 1)
        self.progress_bar.setFormat(
            f"{current} із {total}: {filename}"
        )

    def set_conversion_idle(self) -> None:
        """Відновлює початковий стан панелі."""

        self.convert_button.setEnabled(
            self.format_combo.count() > 0
        )

        self.cancel_conversion_button.setEnabled(True)
        self.cancel_conversion_button.hide()

        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Готовність: %p%")
        self.progress_bar.hide()

    def set_available_formats(
            self,
            formats: Iterable[str],
    ) -> None:
        """Встановлює список доступних вихідних форматів."""

        available = {
            normalize_format(fmt)
            for fmt in formats
            if normalize_format(fmt)
        }

        previous_format = self.format_combo.currentData()

        self.format_combo.blockSignals(True)
        self.format_combo.clear()

        for extension in sorted(available):
            self.format_combo.addItem(
                get_format_display_name(extension),
                extension,
            )

        previous_index = self.format_combo.findData(previous_format)

        if previous_index >= 0:
            self.format_combo.setCurrentIndex(previous_index)

        self.format_combo.blockSignals(False)

        has_formats = self.format_combo.count() > 0
        self.format_combo.setEnabled(has_formats)
        self.convert_button.setEnabled(has_formats)

        if not has_formats:
            self.format_combo.addItem(
                "Немає сумісних форматів",
                "",
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

        output_format = str(self.format_combo.currentData() or "")
        output_directory = self.output_directory_edit.text().strip()

        if not output_format:
            return

        self.convert_requested.emit(
            output_format,
            output_directory,
        )
