"""Тести фонового потоку конвертації."""

import tempfile
import unittest

from pathlib import Path
from unittest.mock import Mock

from PySide6.QtCore import QCoreApplication

from src.services.conversion_service import ConversionResult
from src.services.conversion_worker import ConversionWorker


class TestConversionWorker(unittest.TestCase):
    """Перевіряє поведінку ConversionWorker."""

    @classmethod
    def setUpClass(cls):
        """Створює застосунок Qt для тестування сигналів."""

        cls.app = QCoreApplication.instance()

        if cls.app is None:
            cls.app = QCoreApplication([])

    def setUp(self):
        """Готує тимчасову директорію та тестові файли."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)

        self.source_1 = self.directory / "image1.png"
        self.source_2 = self.directory / "image2.png"

        self.source_1.touch()
        self.source_2.touch()

        self.output_directory = self.directory / "output"
        self.output_directory.mkdir()

        self.service = Mock()

    def tearDown(self):
        """Видаляє тимчасові файли."""

        self.temp_dir.cleanup()

    def _create_worker(self, sources=None):
        """Створює фоновий потік із тестовим сервісом."""

        if sources is None:
            sources = [self.source_1, self.source_2]

        return ConversionWorker(
            service=self.service,
            sources=sources,
            output_directory=self.output_directory,
            output_format="JPEG",
        )

    def _wait_for_worker(self, worker):
        """Очікує завершення потоку та обробляє сигнали Qt."""

        self.assertTrue(
            worker.wait(5000),
            "Фоновий потік не завершився за 5 секунд.",
        )

        self.app.processEvents()

    def test_successful_conversion(self):
        """Успішна конвертація обробляє всі файли."""

        results = [
            ConversionResult(
                source=self.source_1,
                destination=self.output_directory / "image1_converted.jpg",
                success=True,
                error=None,
            ),
            ConversionResult(
                source=self.source_2,
                destination=self.output_directory / "image2_converted.jpg",
                success=True,
                error=None,
            ),
        ]

        self.service.convert_file.side_effect = results

        worker = self._create_worker()

        progress_events = []
        file_events = []
        finished_events = []

        worker.progress_changed.connect(
            lambda current, total, name: progress_events.append(
                (current, total, name)
            )
        )
        worker.file_finished.connect(file_events.append)
        worker.conversion_finished.connect(
            lambda success, failure: finished_events.append(
                (success, failure)
            )
        )

        worker.start()
        self._wait_for_worker(worker)

        self.assertEqual(self.service.convert_file.call_count, 2)

        self.assertEqual(
            progress_events,
            [
                (1, 2, "image1.png"),
                (2, 2, "image2.png"),
            ],
        )

        self.assertEqual(file_events, results)
        self.assertEqual(finished_events, [(2, 0)])

    def test_failed_file_does_not_stop_remaining_files(self):
        """Помилка одного файлу не зупиняє обробку наступного."""

        failed_result = ConversionResult(
            source=self.source_1,
            destination=None,
            success=False,
            error="Помилка тестової конвертації",
        )

        successful_result = ConversionResult(
            source=self.source_2,
            destination=self.output_directory / "image2_converted.jpg",
            success=True,
            error=None,
        )

        self.service.convert_file.side_effect = [
            failed_result,
            successful_result,
        ]

        worker = self._create_worker()

        file_events = []
        finished_events = []

        worker.file_finished.connect(file_events.append)
        worker.conversion_finished.connect(
            lambda success, failure: finished_events.append(
                (success, failure)
            )
        )

        worker.start()
        self._wait_for_worker(worker)

        self.assertEqual(self.service.convert_file.call_count, 2)
        self.assertEqual(file_events, [failed_result, successful_result])
        self.assertEqual(finished_events, [(1, 1)])

    def test_unexpected_exception_emits_error_signal(self):
        """Непередбачена помилка повідомляється через сигнал."""

        self.service.convert_file.side_effect = RuntimeError(
            "Тестова критична помилка"
        )

        worker = self._create_worker(sources=[self.source_1])

        errors = []
        finished_events = []

        worker.conversion_failed.connect(errors.append)
        worker.conversion_finished.connect(
            lambda success, failure: finished_events.append(
                (success, failure)
            )
        )

        worker.start()
        self._wait_for_worker(worker)

        self.assertEqual(
            errors,
            ["Тестова критична помилка"],
        )

        self.assertEqual(finished_events, [(0, 0)])

    def test_cancellation_stops_before_next_file(self):
        """Запит на скасування зупиняє обробку наступних файлів."""

        worker = self._create_worker()

        first_result = ConversionResult(
            source=self.source_1,
            destination=self.output_directory / "image1_converted.jpg",
            success=True,
            error=None,
        )

        self.service.convert_file.return_value = first_result

        def convert_and_request_cancellation(**kwargs):
            """Скасовує роботу після першого файлу."""

            worker.requestInterruption()
            return first_result

        self.service.convert_file.side_effect = (
            convert_and_request_cancellation
        )

        file_events = []
        finished_events = []

        worker.file_finished.connect(file_events.append)
        worker.conversion_finished.connect(
            lambda success, failure: finished_events.append(
                (success, failure)
            )
        )

        worker.start()
        self._wait_for_worker(worker)

        self.assertEqual(self.service.convert_file.call_count, 1)
        self.assertEqual(file_events, [first_result])
        self.assertEqual(finished_events, [(1, 0)])
