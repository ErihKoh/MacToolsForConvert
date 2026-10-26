"""Тести головного вікна MacTools."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


class TestMainWindow(unittest.TestCase):
    """Перевіряє обробку запитів на конвертацію."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_rejects_empty_output_directory(self) -> None:
        self.window._convert_files("png", "")

        self.assertIsNone(self.window.conversion_controller.worker)
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Вкажіть папку для результатів.",
        )

    def test_rejects_nonexistent_output_directory(self) -> None:
        with patch(
            "src.ui.main_window.QMessageBox.warning"
        ) as warning_mock:
            self.window._convert_files(
                "png",
                "/nonexistent_mactools_test_directory",
            )

        warning_mock.assert_called_once()
        self.assertIsNone(self.window.conversion_controller.worker)

    def test_rejects_conversion_when_no_files_exist(self) -> None:
        with TemporaryDirectory() as output_directory:
            with patch(
                "src.ui.main_window.QMessageBox.information"
            ) as information_mock:
                self.window._convert_files(
                    "png",
                    output_directory,
                )

        information_mock.assert_called_once()
        self.assertIsNone(self.window.conversion_controller.worker)

    def test_updates_formats_after_selecting_png(self) -> None:
        """Після вибору PNG серед форматів доступний PDF."""

        with TemporaryDirectory() as directory:
            source = Path(directory) / "sample.png"
            source.touch()

            self.window._add_files([str(source)])

            item = self.window.files_list.item(0)
            item.setSelected(True)

            available_formats = {
                self.window.conversion_panel.format_combo.itemData(index)
                for index in range(
                    self.window.conversion_panel.format_combo.count()
                )
            }

            self.assertIn("pdf", available_formats)
            self.assertTrue(
                self.window.conversion_panel.convert_button.isEnabled()
            )

    def test_clearing_files_removes_available_formats(self) -> None:
        """Після очищення списку доступних форматів немає."""

        with TemporaryDirectory() as directory:
            source = Path(directory) / "sample.png"
            source.touch()

            self.window._add_files([str(source)])

            item = self.window.files_list.item(0)
            item.setSelected(True)

            self.assertEqual(self.window.files_list.count(), 1)

            self.window._clear_files()

            self.assertEqual(self.window.files_list.count(), 0)
            self.assertEqual(
                self.window.conversion_panel.format_combo.currentData(),
                "",
            )
            self.assertFalse(
                self.window.conversion_panel.convert_button.isEnabled()
            )


if __name__ == "__main__":
    unittest.main()