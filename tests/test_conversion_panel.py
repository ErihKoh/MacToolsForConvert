"""Тести панелі налаштування конвертації."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.ui.conversion_panel import ConversionPanel


class TestConversionPanel(unittest.TestCase):
    """Перевіряє поведінку ConversionPanel."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.panel = ConversionPanel()

    def tearDown(self) -> None:
        self.panel.close()
        self.panel.deleteLater()
        self.app.processEvents()

    def test_sets_available_formats(self) -> None:
        self.panel.set_available_formats({"png", "pdf"})

        actual_formats = {
            self.panel.format_combo.itemData(index)
            for index in range(self.panel.format_combo.count())
        }

        self.assertEqual(actual_formats, {"png", "pdf"})
        self.assertTrue(self.panel.format_combo.isEnabled())
        self.assertTrue(self.panel.convert_button.isEnabled())

    def test_normalizes_format_extensions(self) -> None:
        self.panel.set_available_formats({".PNG", " JPG ", "pdf"})

        actual_formats = {
            self.panel.format_combo.itemData(index)
            for index in range(self.panel.format_combo.count())
        }

        self.assertEqual(actual_formats, {"png", "jpg", "pdf"})

    def test_preserves_previous_format_when_available(self) -> None:
        self.panel.set_available_formats({"png", "pdf"})
        self.panel.format_combo.setCurrentIndex(
            self.panel.format_combo.findData("png")
        )

        self.panel.set_available_formats({"jpg", "png"})

        self.assertEqual(self.panel.format_combo.currentData(), "png")

    def test_disables_conversion_when_no_formats_available(self) -> None:
        self.panel.set_available_formats(set())

        self.assertFalse(self.panel.convert_button.isEnabled())
        self.assertFalse(self.panel.format_combo.isEnabled())
        self.assertEqual(self.panel.format_combo.currentData(), "")

    def test_emits_conversion_request(self) -> None:
        self.panel.set_available_formats({"png"})
        self.panel.output_directory_edit.setText("/tmp")

        received = []

        self.panel.convert_requested.connect(
            lambda output_format, output_directory: received.append(
                (output_format, output_directory)
            )
        )

        self.panel._request_conversion()

        self.assertEqual(
            received,
            [("png", "/tmp")],
        )

    def test_does_not_emit_request_without_format(self) -> None:
        self.panel.set_available_formats(set())

        received = []

        self.panel.convert_requested.connect(
            lambda output_format, output_directory: received.append(
                (output_format, output_directory)
            )
        )

        self.panel._request_conversion()

        self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
