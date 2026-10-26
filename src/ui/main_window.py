"""Головне вікно MacTools."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from src.config import (
    APP_DISPLAY_NAME,
    APP_VERSION,
    CATEGORIES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from src.converters.registry import ConverterRegistry
from src.converters.setup import create_default_registry
from src.services.conversion_service import (
    ConversionResult,
    ConversionService,
)
from src.services.conversion_controller import ConversionController
from src.ui.conversion_panel import ConversionPanel
from src.ui.drop_area import DropArea
from src.ui.file_info_panel import FileInfoPanel
from src.ui.file_list_panel import FileListPanel
from src.ui.file_list_controller import FileListController
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
        self.file_list_controller = FileListController(
            self.file_manager
        )

        self.converter_registry = (
            registry
            if registry is not None
            else create_default_registry()
        )

        self.conversion_service = ConversionService(
            self.converter_registry
        )

        self.conversion_controller = ConversionController(
            self.conversion_service,
            parent=self,
        )

        self._active_category = "Усі"

        # Стан поточної конвертації.

        # Стан закриття вікна.
        self._close_after_conversion = False

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

        self.files_list = self.files_panel.files_list
        self.files_count_label = self.files_panel.count_label

        self.info_panel = FileInfoPanel(self)

        content_layout.addWidget(self.files_panel, 1)
        content_layout.addWidget(self.info_panel)

        main_layout.addLayout(content_layout, 1)

        # Панель конвертації.
        self.conversion_panel = ConversionPanel(self)
        main_layout.addWidget(self.conversion_panel)

        # Посилання на елементи керування конвертацією.
        self.progress_bar = self.conversion_panel.progress_bar
        self.cancel_conversion_button = (
            self.conversion_panel.cancel_conversion_button
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

        self.files_list.itemSelectionChanged.connect(
            self._update_available_output_formats
        )

        self.conversion_panel.convert_requested.connect(
            self._convert_files
        )

        self.cancel_conversion_button.clicked.connect(
            self._cancel_conversion
        )

        self.conversion_controller.progress_changed.connect(
            self._on_conversion_progress
        )
        self.conversion_controller.file_finished.connect(
            self._on_file_conversion_finished
        )
        self.conversion_controller.conversion_finished.connect(
            self._on_conversion_finished
        )
        self.conversion_controller.conversion_failed.connect(
            self._on_conversion_failed
        )
        self.conversion_controller.worker_stopped.connect(
            self._on_worker_stopped
        )

    def _add_files(self, paths: list[str]) -> None:
        """Додає файли або рекурсивно обходить вибрані папки."""

        added_count, skipped_count = (
            self.file_list_controller.add_paths(paths)
        )

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

        if self.conversion_controller.worker is not None:
            self.statusBar().showMessage(
                "Не можна очистити список під час конвертації."
            )
            return

        if self.file_manager.count == 0:
            self._reset_conversion_progress()
            self.statusBar().showMessage("Список уже порожній.")
            return

        self.file_list_controller.clear()
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
        filtered_files = self.file_manager.get_filtered_files(
            self._active_category
        )

        self.files_panel.set_files(filtered_files)
        self.info_panel.update_info(None)
        self._update_available_output_formats()


    def _on_selection_changed(
            self,
            current: QListWidgetItem | None,
            previous: QListWidgetItem | None,
    ) -> None:
        """Оновлює інформаційну панель."""

        if current is None:
            self.info_panel.update_info(None)
            return

        key = current.data(Qt.ItemDataRole.UserRole)
        path = self.file_manager.files.get(key)

        self.info_panel.update_info(path)

    def _get_source_files(self) -> list[Path]:
        """Повертає файли, вибрані для конвертації."""

        selected_keys = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.files_list.selectedItems()
        ]

        return self.file_list_controller.get_source_files(
            selected_keys
        )

    def _update_available_output_formats(self) -> None:
        """Оновлює вихідні формати відповідно до вибраних файлів."""

        source_paths = self._get_source_files()

        compatible_formats = self.conversion_service.get_available_formats(
            sources=source_paths,
            output_formats=self.conversion_panel.ALL_FORMATS,
        )

        self.conversion_panel.set_available_formats(
            compatible_formats
        )

    def _prepare_conversion_ui(self, total: int) -> None:

        """Готує інтерфейс до пакетної конвертації."""

        self.conversion_panel.set_conversion_running(total)

    def _convert_files(
            self,
            output_format: str,
            output_directory: str,
    ) -> None:
        """Запускає пакетну конвертацію через контролер."""

        if self.conversion_controller.worker is not None:
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

        files_to_convert = self._get_source_files()

        if not files_to_convert:
            QMessageBox.information(
                self,
                "Немає файлів",
                "Додайте файли або виберіть файли для конвертації.",
            )
            return

        self._close_after_conversion = False

        total = len(files_to_convert)
        self._prepare_conversion_ui(total)

        self.statusBar().showMessage(
            f"Підготовлено файлів до конвертації: {total}."
        )

        started = self.conversion_controller.start(
            sources=files_to_convert,
            output_directory=output_path,
            output_format=output_format,
        )

        if not started:
            self._restore_conversion_ui()
            self.statusBar().showMessage(
                "Не вдалося запустити конвертацію."
            )

    def _on_conversion_progress(
            self,
            current: int,
            total: int,
            filename: str,
    ) -> None:
        """Оновлює прогрес конвертації."""

        self.conversion_panel.update_conversion_progress(
            current,
            total,
            filename,
        )

        self.statusBar().showMessage(
            f"Конвертація файла {current} із {total}: {filename}"
        )

    def _on_file_conversion_finished(
            self,
            result: ConversionResult,
    ) -> None:
        """Зберігає результат обробки одного файла."""


        if result.success:
            self.statusBar().showMessage(
                f"Готово: {result.source.name}"
            )
        else:
            self.statusBar().showMessage(
                f"Помилка: {result.source.name}"
            )

    def _get_conversion_error_details(self) -> str:
        """Формує текст зі списком помилок конвертації."""

        errors = [
            f"{result.source.name}: {result.error}"
            for result in self.conversion_controller.results
            if not result.success
        ]

        details = "\n".join(errors[:10])

        if len(errors) > 10:
            details += f"\n… та ще {len(errors) - 10} помилок."

        return details

    def _build_conversion_summary(
            self,
            success_count: int,
            failure_count: int,
    ) -> str:
        """Формує підсумкове повідомлення про конвертацію."""

        worker = self.conversion_controller.worker
        interrupted = (
                worker is not None
                and worker.isInterruptionRequested()
        )

        processed_count = success_count + failure_count

        if interrupted:
            return (
                "Конвертацію скасовано. "
                f"Оброблено: {processed_count}; "
                f"успішно: {success_count}; "
                f"помилок: {failure_count}."
            )

        if self.conversion_controller.error is not None:
            return (
                "Конвертацію перервано через критичну помилку. "
                f"Оброблено: {processed_count}; "
                f"успішно: {success_count}; "
                f"помилок: {failure_count}."
            )

        return (
            "Конвертацію завершено. "
            f"Успішно: {success_count}; "
            f"помилок: {failure_count}."
        )

    def _on_conversion_finished(
            self,
            success_count: int,
            failure_count: int,
    ) -> None:
        """Формує підсумок пакетної конвертації."""

        message = self._build_conversion_summary(
            success_count,
            failure_count,
        )

        self.statusBar().showMessage(message)

        # Під час закриття вікна не показуємо модальні діалоги.
        if self._close_after_conversion:
            return

        # Критичну помилку показуємо лише в одному діалозі.
        if self.conversion_controller.error is not None:
            QMessageBox.critical(
                self,
                "Критична помилка конвертації",
                f"{message}\n\n{self.conversion_controller.error}",
            )
            return

        if failure_count:
            details = self._get_conversion_error_details()

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
        """Зберігає текст критичної помилки для підсумкового діалогу."""


        self.statusBar().showMessage(
            "Під час виконання конвертації сталася критична помилка."
        )

    def _cancel_conversion(self) -> None:
        """Просить контролер зупинити пакетну обробку."""
        if not self.conversion_controller.is_running():
            return
        self.conversion_controller.cancel()
        self.cancel_conversion_button.setEnabled(False)
        self.statusBar().showMessage(
            "Скасування запитано. Завершується поточний файл."
        )

    def _restore_conversion_ui(self) -> None:
        """Відновлює інтерфейс після завершення конвертації."""

        self.conversion_panel.set_conversion_idle()

    def _reset_conversion_progress(self) -> None:
        """Скидає індикатор прогресу конвертації."""

        self.conversion_panel.set_conversion_idle()

    def _on_worker_stopped(self) -> None:
        """Відновлює інтерфейс після завершення фонового потоку."""

        self._restore_conversion_ui()

        # Якщо закриття було відкладене до завершення потоку,
        # повторно закриваємо вікно після очищення worker контролером.
        if self._close_after_conversion:
            self._close_after_conversion = False
            self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Безпечно обробляє закриття вікна."""

        worker = self.conversion_controller.worker

        if worker is None or not worker.isRunning():
            event.accept()
            return

        answer = QMessageBox.question(
            self,
            "Конвертація виконується",
            (
                "Конвертація ще триває.\n\n"
                "Скасувати пакетну операцію та закрити MacTools?\n"
                "Поточний файл спочатку завершить обробку."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        self._close_after_conversion = True
        self.setEnabled(False)

        self.conversion_controller.cancel()

        self.statusBar().showMessage(
            "Завершення поточної операції перед закриттям…"
        )

        # Не блокуємо GUI через worker.wait().
        # Вікно закриється після завершення потоку.
        event.ignore()
