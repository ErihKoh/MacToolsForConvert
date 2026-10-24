"""Головне вікно MacTools."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabBar,
    QVBoxLayout,
    QWidget, QProgressBar,
)

from src.config import (
    APP_DISPLAY_NAME,
    APP_VERSION,
    CATEGORIES,
    OUTPUT_DIR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from src.converters.registry import ConverterRegistry
from src.converters.setup import create_default_registry
from src.services.conversion_service import ConversionService, ConversionResult
from src.services.conversion_worker import ConversionWorker
from src.ui.conversion_panel import ConversionPanel
from src.ui.drop_area import DropArea
from src.ui.file_info_panel import FileInfoPanel
from src.ui.file_list_panel import FileListPanel
from src.utils.file_manager import FileManager


class MainWindow(QMainWindow):
    """Головне вікно MacTools."""

    def __init__(
            self,
            registry: ConverterRegistry | None = None,
    ) -> None:
        super().__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.file_manager = FileManager()

        self.converter_registry = (
            registry
            if registry is not None
            else create_default_registry()
        )

        self.conversion_service = ConversionService(
            self.converter_registry
        )

        self._active_category = "Усі"

        # Стан поточної конвертації.
        self._conversion_worker: ConversionWorker | None = None
        self._conversion_results: list[ConversionResult] = []

        self._setup_ui()
        self._connect_signals()
        self._refresh_file_list()

        converter_count = len(self.converter_registry)

        self.statusBar().showMessage(
            f"MacTools {APP_VERSION} готовий до роботи. "
            f"Доступно конвертерів: {converter_count}."
        )

    def _setup_ui(self) -> None:
        """Створює структуру головного вікна."""

        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)

        main_layout.setContentsMargins(24, 20, 24, 14)
        main_layout.setSpacing(14)

        # Заголовок.
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(3)

        self.header_label = QLabel("MacTools")
        self.header_label.setObjectName("headerLabel")

        self.subtitle_label = QLabel(
            "Інструменти для роботи з файлами"
        )
        self.subtitle_label.setObjectName("subtitleLabel")

        title_layout.addWidget(self.header_label)
        title_layout.addWidget(self.subtitle_label)

        self.clear_button = QPushButton("Очистити список")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_button)

        main_layout.addLayout(header_layout)

        # Область Drag-and-Drop.
        self.drop_area = DropArea(self)
        main_layout.addWidget(self.drop_area)

        # Категорії файлів.
        self.category_tabs = QTabBar()
        self.category_tabs.setObjectName("categoryTabs")
        self.category_tabs.setExpanding(False)
        self.category_tabs.setDrawBase(False)
        self.category_tabs.setMovable(False)
        self.category_tabs.setUsesScrollButtons(True)

        self.category_names = [
            "Усі",
            *CATEGORIES.keys(),
        ]

        for category in self.category_names:
            self.category_tabs.addTab(category)

        main_layout.addWidget(self.category_tabs)

        # Список файлів та інформаційна панель.
        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        self.files_panel = FileListPanel(self)

        # Сумісність із наявними методами.
        self.files_list = self.files_panel.files_list
        self.files_count_label = self.files_panel.count_label

        self.info_panel = FileInfoPanel(self)

        content_layout.addWidget(self.files_panel, 1)
        content_layout.addWidget(self.info_panel)

        main_layout.addLayout(content_layout, 1)

        # Панель конвертації.
        self.conversion_panel = ConversionPanel(self)
        main_layout.addWidget(self.conversion_panel)

        # Індикатор прогресу.
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("conversionProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Готовність: %p%")
        self.progress_bar.hide()

        main_layout.addWidget(self.progress_bar)

        # Кнопка скасування поточної пакетної операції.
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

        self.setCentralWidget(central_widget)

    def _connect_signals(self) -> None:
        """Підключає сигнали інтерфейсу."""

        self.drop_area.files_added.connect(self._add_files)
        self.clear_button.clicked.connect(self._clear_files)

        self.category_tabs.currentChanged.connect(
            self._on_category_changed
        )

        self.files_list.currentItemChanged.connect(
            self._on_selection_changed
        )

        self.conversion_panel.convert_requested.connect(
            self._convert_files
        )

        self.cancel_conversion_button.clicked.connect(
            self._cancel_conversion
        )

    def _add_files(self, paths: list[str]) -> None:
        """Додає файли або рекурсивно обходить вибрані папки."""

        added_count = 0
        skipped_count = 0

        for raw_path in paths:
            path = Path(raw_path)

            if not path.exists():
                skipped_count += 1
                continue

            if path.is_dir():
                added, skipped = (
                    self.file_manager.add_directory_recursive(path)
                )
            elif path.is_file():
                added, skipped = self.file_manager.add_files(
                    [str(path)]
                )
            else:
                skipped_count += 1
                continue

            added_count += added
            skipped_count += skipped

        all_index = self.category_names.index("Усі")
        self.category_tabs.setCurrentIndex(all_index)

        self._refresh_file_list()

        if added_count:
            message = f"Додано файлів: {added_count}."
        else:
            message = "Нових файлів не додано."

        if skipped_count:
            message += f" Пропущено: {skipped_count}."

        self.statusBar().showMessage(
            f"{message} Усього файлів: {self.file_manager.count}."
        )

    def _clear_files(self) -> None:
        """Очищає список доданих файлів."""

        if self._conversion_worker is not None:
            self.statusBar().showMessage(
                "Не можна очистити список під час конвертації."
            )
            return

        if self.file_manager.count == 0:
            self._reset_conversion_progress()
            self.statusBar().showMessage("Список уже порожній.")
            return

        self.file_manager.clear()
        self._refresh_file_list()
        self._reset_conversion_progress()

        self.statusBar().showMessage("Список файлів очищено.")

    def _on_category_changed(self, index: int) -> None:
        """Застосовує фільтр вибраної категорії."""

        if index < 0 or index >= len(self.category_names):
            return

        self._active_category = self.category_names[index]
        self._refresh_file_list()

        self.statusBar().showMessage(
            f"Категорія: {self._active_category}. "
            f"Елементів у списку: {self.files_list.count()}."
        )

    def _refresh_file_list(self) -> None:
        """Оновлює список відповідно до вибраної категорії."""

        self.files_list.clear()

        filtered_files = self.file_manager.get_filtered_files(
            self._active_category
        )

        for key, path in filtered_files.items():
            item = QListWidgetItem()

            if path.is_dir():
                item.setText(f"▰  {path.name}")
            else:
                item.setText(f"   {path.name}")

            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setToolTip(str(path))
            self.files_list.addItem(item)

        self.files_panel.update_count()
        self._update_file_info(None)

    def _on_selection_changed(
            self,
            current: QListWidgetItem | None,
            previous: QListWidgetItem | None,
    ) -> None:
        """Оновлює інформаційну панель."""

        if current is None:
            self._update_file_info(None)
            return

        key = current.data(Qt.ItemDataRole.UserRole)
        path = self.file_manager.files.get(key)

        self._update_file_info(path)

    def _update_file_info(self, path: Path | None) -> None:
        """Передає вибраний елемент інформаційній панелі."""

        self.info_panel.update_info(path)

    def _convert_files(
            self,
            output_format: str,
            output_directory: str,
    ) -> None:
        """Запускає пакетну конвертацію у фоновому потоці."""

        if self._conversion_worker is not None:
            self.statusBar().showMessage(
                "Конвертація вже виконується."
            )
            return

        if not output_directory:
            self.statusBar().showMessage(
                "Вкажіть папку для результатів."
            )
            return

        output_path = Path(output_directory).expanduser()

        if not output_path.is_dir():
            QMessageBox.warning(
                self,
                "Папку не знайдено",
                "Виберіть наявну папку для результатів.",
            )
            return

        selected_items = self.files_list.selectedItems()

        if selected_items:
            source_paths = [
                self.file_manager.files.get(
                    item.data(Qt.ItemDataRole.UserRole)
                )
                for item in selected_items
            ]
        else:
            source_paths = list(self.file_manager.files.values())

        files_to_convert = [
            path
            for path in source_paths
            if path is not None and path.is_file()
        ]

        if not files_to_convert:
            QMessageBox.information(
                self,
                "Немає файлів",
                "Додайте файли або виберіть файли для конвертації.",
            )
            return

        self._conversion_results.clear()

        self.progress_bar.setRange(0, len(files_to_convert))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(
            f"0 із {len(files_to_convert)} файлів"
        )
        self.progress_bar.show()

        self.cancel_conversion_button.show()
        self.conversion_panel.convert_button.setEnabled(False)

        self.statusBar().showMessage(
            f"Підготовлено файлів до конвертації: "
            f"{len(files_to_convert)}."
        )

        worker = ConversionWorker(
            service=self.conversion_service,
            sources=files_to_convert,
            output_directory=output_path,
            output_format=output_format,
            parent=self,
        )

        self._conversion_worker = worker

        worker.progress_changed.connect(
            self._on_conversion_progress
        )
        worker.file_finished.connect(
            self._on_file_conversion_finished
        )
        worker.conversion_finished.connect(
            self._on_conversion_finished
        )
        worker.conversion_failed.connect(
            self._on_conversion_failed
        )
        worker.finished.connect(
            self._on_worker_stopped
        )

        worker.start()

    def _on_conversion_progress(
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

        self.statusBar().showMessage(
            f"Конвертація файла {current} із {total}: {filename}"
        )

    def _on_file_conversion_finished(
            self,
            result: ConversionResult,
    ) -> None:
        """Зберігає результат обробки одного файла."""

        self._conversion_results.append(result)

        if result.success:
            self.statusBar().showMessage(
                f"Готово: {result.source.name}"
            )
        else:
            self.statusBar().showMessage(
                f"Помилка: {result.source.name}"
            )

    def _on_conversion_finished(
            self,
            success_count: int,
            failure_count: int,
    ) -> None:
        """Показує підсумок пакетної конвертації."""

        worker = self._conversion_worker
        interrupted = (
                worker is not None
                and worker.isInterruptionRequested()
        )

        processed_count = success_count + failure_count

        if interrupted:
            message = (
                "Конвертацію скасовано. "
                f"Оброблено: {processed_count}; "
                f"успішно: {success_count}; "
                f"помилок: {failure_count}."
            )
        else:
            message = (
                "Конвертацію завершено. "
                f"Успішно: {success_count}; "
                f"помилок: {failure_count}."
            )

        self.statusBar().showMessage(message)

        if failure_count:
            errors = [
                f"{result.source.name}: {result.error}"
                for result in self._conversion_results
                if not result.success
            ]

            details = "\n".join(errors[:10])

            if len(errors) > 10:
                details += (
                    f"\n… та ще {len(errors) - 10} помилок."
                )

            QMessageBox.warning(
                self,
                "Результати конвертації",
                f"{message}\n\n{details}",
            )
        else:
            QMessageBox.information(
                self,
                "Результати конвертації",
                f"{message}\n"
                f"Папка результатів:\n"
                f"{self.conversion_panel.output_directory_edit.text()}",
            )

    def _on_conversion_failed(self, error: str) -> None:
        """Повідомляє про неочікувану помилку робочого потоку."""

        self.statusBar().showMessage(
            "Під час виконання конвертації сталася помилка."
        )

        QMessageBox.critical(
            self,
            "Помилка конвертації",
            error,
        )

    def _reset_conversion_progress(self) -> None:
        """Скидає індикатор прогресу конвертації."""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Готовність: %p%")
        self.progress_bar.hide()

    def _cancel_conversion(self) -> None:
        """Просить фоновий потік припинити пакетну обробку."""

        worker = self._conversion_worker

        if worker is None or not worker.isRunning():
            return

        worker.requestInterruption()
        self.cancel_conversion_button.setEnabled(False)

        self.statusBar().showMessage(
            "Скасування запитано. Завершується поточний файл."
        )

    def _on_worker_stopped(self) -> None:
        """Відновлює інтерфейс після зупинки потоку."""

        worker = self._conversion_worker

        if worker is not None:
            worker.deleteLater()

        self._conversion_worker = None

        self.conversion_panel.convert_button.setEnabled(True)

        self.cancel_conversion_button.setEnabled(True)
        self.cancel_conversion_button.hide()

        self._reset_conversion_progress()
