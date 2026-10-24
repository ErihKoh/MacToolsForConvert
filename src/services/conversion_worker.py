"""Фонове виконання конвертації файлів MacTools."""
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.services.conversion_service import (
    ConversionResult,
    ConversionService,
)


class ConversionWorker(QThread):
    """Виконує пакетну конвертацію у фоновому потоці."""
    progress_changed = Signal(int, int, str)
    file_finished = Signal(object)
    conversion_finished = Signal(int, int)
    conversion_failed = Signal(str)

    def __init__(
            self,
            service: ConversionService,
            sources: list[Path],
            output_directory: Path,
            output_format: str,
            parent=None,
    ) -> None:
        super().__init__(parent)

        self._service = service
        self._sources = list(sources)
        self._output_directory = output_directory
        self._output_format = output_format

    def run(self) -> None:
        """Послідовно конвертує файли у фоновому потоці."""

        total = len(self._sources)
        success_count = 0
        failure_count = 0

        try:
            for index, source in enumerate(self._sources, start=1):
                if self.isInterruptionRequested():
                    break

                self.progress_changed.emit(
                    index,
                    total,
                    source.name,
                )

                result: ConversionResult = (
                    self._service.convert_file(
                        source=source,
                        output_directory=self._output_directory,
                        output_format=self._output_format,
                    )
                )

                if result.success:
                    success_count += 1
                else:
                    failure_count += 1

                self.file_finished.emit(result)

        except Exception as exc:
            self.conversion_failed.emit(str(exc))

        finally:
            self.conversion_finished.emit(
                success_count,
                failure_count,
            )