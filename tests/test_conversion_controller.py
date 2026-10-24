"""Тести контролера конвертації."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QSignalSpy

from src.services.conversion_service import ConversionResult
from src.services.conversion_controller import ConversionController


class TestConversionController(unittest.TestCase):
    """Перевіряє керування процесом конвертації."""

    @classmethod
    def setUpClass(cls) -> None:
        """Створює застосунок Qt для тестування сигналів."""

        cls.app = QApplication.instance()

        if cls.app is None:
            cls.app = QApplication([])

    def setUp(self) -> None:
        """Готує тестові файли та сервіс."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)

        self.source = self.directory / "image.png"
        self.source.touch()

        self.output_directory = self.directory / "output"
        self.output_directory.mkdir()

        self.destination = (
                self.output_directory / "image_converted.jpg"
        )

        self.service = Mock()
        self.result = ConversionResult(
            source=self.source,
            destination=self.destination,
            success=True,
        )
        self.service.convert_file.return_value = self.result

    def tearDown(self) -> None:
        """Прибирає тимчасові файли."""

        self.temp_dir.cleanup()

    def test_start_collects_successful_conversion_result(self) -> None:
        """Перевіряє запуск конвертації та збереження результату."""

        controller = ConversionController(self.service)
        stopped_spy = QSignalSpy(controller.worker_stopped)

        started = controller.start(
            sources=[self.source],
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertTrue(started)
        deadline = time.monotonic() + 5

        while stopped_spy.count() == 0 and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)

        self.app.processEvents()

        self.assertGreater(
            stopped_spy.count(),
            0,
            "Фоновий потік не завершився за 5 секунд.",
        )

        self.service.convert_file.assert_called_once_with(
            source=self.source,
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertEqual(controller.results, [self.result])
        self.assertIsNone(controller.error)
        self.assertIsNone(controller.worker)

    def test_start_rejects_empty_sources(self) -> None:
        """Не запускає конвертацію, якщо список файлів порожній."""

        controller = ConversionController(self.service)

        started = controller.start(
            sources=[],
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertFalse(started)
        self.assertIsNone(controller.worker)
        self.service.convert_file.assert_not_called()

    def test_start_rejects_missing_output_directory(self) -> None:
        """Не запускає конвертацію в неіснуючу папку."""

        controller = ConversionController(self.service)
        missing_directory = self.directory / "missing"

        started = controller.start(
            sources=[self.source],
            output_directory=missing_directory,
            output_format="jpg",
        )

        self.assertFalse(started)
        self.assertIsNone(controller.worker)
        self.service.convert_file.assert_not_called()

    def test_critical_error_is_saved_by_controller(self) -> None:
        """Контролер зберігає критичну помилку worker."""

        self.service.convert_file.side_effect = RuntimeError(
            "Критична помилка тесту"
        )

        controller = ConversionController(self.service)
        stopped_spy = QSignalSpy(controller.worker_stopped)

        started = controller.start(
            sources=[self.source],
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertTrue(started)

        deadline = time.monotonic() + 5

        while (
            stopped_spy.count() == 0
            and time.monotonic() < deadline
        ):
            self.app.processEvents()
            time.sleep(0.01)

        self.app.processEvents()

        self.assertGreater(
            stopped_spy.count(),
            0,
            "Worker не завершився за 5 секунд.",
        )
        self.assertEqual(
            controller.error,
            "Критична помилка тесту",
        )
        self.assertEqual(controller.results, [])
        self.assertIsNone(controller.worker)
