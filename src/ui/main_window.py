"""Головне вікно MacTools."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
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
from src.ui.drop_area import DropArea
from src.ui.file_info_panel import FileInfoPanel
from src.ui.file_list_panel import FileListPanel
from src.utils.file_manager import FileManager


class MainWindow(QMainWindow):
    """Головне вікно MacTools."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Менеджер відповідає за колекцію файлів.

        self.file_manager = FileManager()

        self._active_category = "Усі"

        self._setup_ui()
        self._connect_signals()
        self._refresh_file_list()

        self.statusBar().showMessage(
            f"MacTools {APP_VERSION} готовий до роботи"
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

        # Основна область: список та інформація.
        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        # Ліва частина — список.
        # Ліва частина — список файлів.
        self.files_panel = FileListPanel(self)

        # Зберігаємо сумісність з наявними методами MainWindow.
        self.files_list = self.files_panel.files_list
        self.files_count_label = self.files_panel.count_label

        # Права частина — інформація про вибраний елемент.
        self.info_panel = FileInfoPanel(self)

        content_layout.addWidget(self.files_panel, 1)

        content_layout.addWidget(self.info_panel)

        main_layout.addLayout(content_layout, 1)

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

    def _add_files(self, paths: list[str]) -> None:
        """Додає нові файли та папки до колекції."""

        added_count, skipped_count = self.file_manager.add_files(paths)

        # Показуємо всі додані елементи.
        all_index = self.category_names.index("Усі")
        self.category_tabs.setCurrentIndex(all_index)

        self._refresh_file_list()

        if added_count:
            message = f"Додано елементів: {added_count}."
        else:
            message = "Нових елементів не додано."

        if skipped_count:
            message += f" Пропущено: {skipped_count}."

        self.statusBar().showMessage(
            f"{message} Усього: {self.file_manager.count}."
        )

    def _clear_files(self) -> None:
        """Очищає список доданих файлів."""

        if self.file_manager.count == 0:
            self.statusBar().showMessage("Список уже порожній.")
            return

        self.file_manager.clear()
        self._refresh_file_list()

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
        """Оновлює видимий список відповідно до категорії."""

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

            item.setData(
                Qt.ItemDataRole.UserRole,
                key,
            )
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
