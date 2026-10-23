"""Головне вікно MacTools."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
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
from src.utils.file_info import get_file_info


class MainWindow(QMainWindow):
    """Головне вікно MacTools."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Шляхи зберігаються за їхнім нормалізованим представленням.
        self._files: dict[str, Path] = {}

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
        files_panel = QFrame()
        files_panel.setObjectName("filesPanel")

        files_layout = QVBoxLayout(files_panel)
        files_layout.setContentsMargins(12, 12, 12, 12)
        files_layout.setSpacing(10)

        files_header = QHBoxLayout()

        self.files_label = QLabel("Додані елементи")
        self.files_label.setObjectName("sectionLabel")

        self.files_count_label = QLabel("0")
        self.files_count_label.setObjectName("countLabel")

        files_header.addWidget(self.files_label)
        files_header.addStretch()
        files_header.addWidget(self.files_count_label)

        self.files_list = QListWidget()
        self.files_list.setObjectName("filesList")
        self.files_list.setAlternatingRowColors(True)
        self.files_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )

        self.files_list.setMinimumWidth(300)

        files_layout.addLayout(files_header)
        files_layout.addWidget(self.files_list)

        # Права частина — інформація про вибраний елемент.
        self.info_panel = QFrame()
        self.info_panel.setObjectName("infoPanel")
        self.info_panel.setMinimumWidth(250)
        self.info_panel.setMaximumWidth(340)

        info_layout = QVBoxLayout(self.info_panel)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(12)

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
        self.info_path.setWordWrap(True)
        self.info_path.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.info_labels = [
            self.info_type,
            self.info_size,
            self.info_modified,
            self.info_created,
            self.info_path,
        ]

        for label in self.info_labels:
            label.setObjectName("infoValue")
            label.setWordWrap(True)
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

        info_layout.addWidget(self.info_title)
        info_layout.addWidget(self.info_name)
        info_layout.addSpacing(4)
        info_layout.addWidget(self.info_type)
        info_layout.addWidget(self.info_size)
        info_layout.addWidget(self.info_modified)
        info_layout.addWidget(self.info_created)
        info_layout.addSpacing(4)
        info_layout.addWidget(self.info_path)
        info_layout.addStretch()

        content_layout.addWidget(files_panel, 1)
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

        added_count = 0
        skipped_count = 0

        for raw_path in paths:
            path = Path(raw_path)

            if not path.exists():
                skipped_count += 1
                continue

            try:
                key = str(path.resolve(strict=True))
            except (OSError, RuntimeError):
                skipped_count += 1
                continue

            if key in self._files:
                skipped_count += 1
                continue

            self._files[key] = path
            added_count += 1

        # Показуємо всі додані елементи, щоб користувач одразу
        # бачив результат перетягування.
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
            f"{message} Усього: {len(self._files)}."
        )

    def _clear_files(self) -> None:
        """Очищає список доданих файлів."""

        if not self._files:
            self.statusBar().showMessage("Список уже порожній.")
            return

        self._files.clear()
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

        for key, path in self._files.items():
            if not self._matches_category(path):
                continue

            item = QListWidgetItem()

            if path.is_dir():
                item.setText(f"▰  {path.name}")
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    key,
                )
            else:
                item.setText(f"   {path.name}")
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    key,
                )

            item.setToolTip(str(path))
            self.files_list.addItem(item)

        self.files_count_label.setText(
            str(self.files_list.count())
        )

        self._update_file_info(None)

    def _matches_category(self, path: Path) -> bool:
        """Перевіряє, чи належить елемент до категорії."""

        if self._active_category == "Усі":
            return True

        if path.is_dir():
            return False

        extension = path.suffix.lower()

        extensions = CATEGORIES.get(
            self._active_category,
            set(),
        )

        return extension in extensions

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
        path = self._files.get(key)

        self._update_file_info(path)

    def _update_file_info(self, path: Path | None) -> None:
        """Відображає властивості вибраного елемента."""

        if path is None:
            self.info_name.setText("Файл не вибрано")
            self.info_type.setText("Тип: —")
            self.info_size.setText("Розмір: —")
            self.info_modified.setText("Змінено: —")
            self.info_created.setText("Створено: —")
            self.info_path.setText("Шлях: —")
            return

        try:
            info = get_file_info(path)

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

        except OSError:
            self.info_name.setText(path.name or str(path))
            self.info_type.setText("Тип: недоступний")
            self.info_size.setText("Розмір: недоступний")
            self.info_modified.setText("Змінено: недоступно")
            self.info_created.setText("Створено: недоступно")
            self.info_path.setText(f"Шлях: {path}")