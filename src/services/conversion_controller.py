"""Керування життєвим циклом пакетної конвертації."""

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from src.services.conversion_service import (
    ConversionResult,
    ConversionService,
)
from src.services.conversion_worker import ConversionWorker


class ConversionController(QObject):
    """Запускає worker і збирає результати конвертації."""

    progress_changed = Signal(int, int, str)
    file_finished = Signal(object)
    conversion_finished = Signal(int, int)
    conversion_failed = Signal(str)
    worker_stopped = Signal()

    def __init__(
        self,
        service: ConversionService,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._service = service
        self._worker: ConversionWorker | None = None
        self._results: list[ConversionResult] = []
        self._error: str | None = None

    @property
    def results(self) -> list[ConversionResult]:
        """Повертає результати поточної або останньої операції."""

        return list(self._results)

    @property
    def error(self) -> str | None:
        """Повертає критичну помилку, якщо вона виникла."""

        return self._error

    @property
    def worker(self) -> ConversionWorker | None:
        """Повертає поточний робочий потік."""

        return self._worker

    def is_running(self) -> bool:
        """Перевіряє, чи виконується робочий потік."""

        return (
            self._worker is not None
            and self._worker.isRunning()
        )

    def start(
        self,
        sources: list[Path],
        output_directory: Path,
        output_format: str,
    ) -> bool:
        """Запускає пакетну конвертацію."""

        if self._worker is not None:
            return False

        if not sources:
            return False

        if not output_directory.is_dir():
            return False

        self._results.clear()
        self._error = None

        worker = ConversionWorker(
            service=self._service,
            sources=sources,
            output_directory=output_directory,
            output_format=output_format,
            parent=self,
        )

        self._worker = worker

        worker.progress_changed.connect(
            self.progress_changed
        )
        worker.file_finished.connect(
            self._on_file_finished
        )
        worker.conversion_finished.connect(
            self.conversion_finished
        )
        worker.conversion_failed.connect(
            self._on_conversion_failed
        )
        worker.finished.connect(
            self._on_worker_stopped
        )

        worker.start()
        return True

    def cancel(self) -> None:
        """Просить worker зупинитися після поточного файла."""

        if self.is_running() and self._worker is not None:
            self._worker.requestInterruption()

    def _on_file_finished(
        self,
        result: ConversionResult,
    ) -> None:
        """Зберігає результат і передає його інтерфейсу."""

        self._results.append(result)
        self.file_finished.emit(result)

    def _on_conversion_failed(self, error: str) -> None:
        """Зберігає критичну помилку та передає її інтерфейсу."""

        self._error = error
        self.conversion_failed.emit(error)

    def _on_worker_stopped(self) -> None:
        """Очищає посилання після завершення робочого потоку."""

        worker = self._worker

        if worker is not None:
            worker.deleteLater()

        self._worker = None
        self.worker_stopped.emit()
