
"""Конвертер електронних книг FB2, EPUB і PDF через Calibre."""

import os
import signal
import subprocess
import tempfile
from pathlib import Path

from src.config import (
    CALIBRE_EBOOK_CONVERT_PATH,
    CONVERTER_TIMEOUT_SECONDS,
)
from src.converters.base import BaseConverter
from src.converters.formats import (
    EBOOK_INPUT_FORMATS,
    EBOOK_OUTPUT_FORMATS,
)


class EbookConverter(BaseConverter):
    """Конвертує електронні книги за допомогою Calibre."""

    CALIBRE_PATH = CALIBRE_EBOOK_CONVERT_PATH
    TIMEOUT_SECONDS = CONVERTER_TIMEOUT_SECONDS

    SUPPORTED_INPUT_FORMATS = EBOOK_INPUT_FORMATS
    SUPPORTED_OUTPUT_FORMATS = EBOOK_OUTPUT_FORMATS

    @property
    def name(self) -> str:
        return "Ebook Converter"

    @property
    def supported_input_formats(self) -> set[str]:
        return set(self.SUPPORTED_INPUT_FORMATS)

    @property
    def supported_output_formats(self) -> set[str]:
        return set(self.SUPPORTED_OUTPUT_FORMATS)

    def can_convert(
        self,
        source_format: str,
        destination_format: str,
    ) -> bool:
        """Перевіряє підтримку конкретної пари форматів."""

        source_format = source_format.strip().lower().lstrip(".")
        destination_format = (
            destination_format.strip().lower().lstrip(".")
        )

        if source_format == destination_format:
            return False

        return (
            source_format in self.SUPPORTED_INPUT_FORMATS
            and destination_format in self.SUPPORTED_OUTPUT_FORMATS
        )

    def is_available_for(
        self,
        source_format: str,
        destination_format: str,
    ) -> bool:
        """Перевіряє доступність Calibre для конвертації."""

        return (
            self.can_convert(source_format, destination_format)
            and self.CALIBRE_PATH.is_file()
        )

    def convert(self, source: Path, destination: Path) -> Path:
        """Конвертує електронну книгу, зберігаючи оригінал."""

        source = Path(source).expanduser()
        destination = Path(destination).expanduser()

        if not source.is_file():
            raise FileNotFoundError(
                f"Вхідний файл не знайдено: {source}"
            )

        source_format = source.suffix.lower().lstrip(".")
        destination_format = destination.suffix.lower().lstrip(".")

        if not self.can_convert(source_format, destination_format):
            raise ValueError(
                "Непідтримувана конвертація: "
                f"{source_format or '(без розширення)'} → "
                f"{destination_format or '(без розширення)'}"
            )

        if source.resolve() == destination.resolve():
            raise ValueError(
                "Вихідний файл не може збігатися з оригіналом."
            )

        if destination.exists():
            raise FileExistsError(
                f"Файл призначення вже існує: {destination}"
            )

        if not destination.parent.is_dir():
            raise FileNotFoundError(
                f"Папка призначення не існує: {destination.parent}"
            )

        if not self.CALIBRE_PATH.is_file():
            raise FileNotFoundError(
                f"Не знайдено Calibre: {self.CALIBRE_PATH}"
            )

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                prefix=".mactools_",
                suffix=f".{destination_format}",
                dir=destination.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name).resolve()

            command = [
                str(self.CALIBRE_PATH),
                str(source.resolve()),
                str(temporary_path),
            ]

            self._run_command(command)

            if (
                not temporary_path.is_file()
                or temporary_path.stat().st_size == 0
            ):
                raise ValueError(
                    "Calibre не створив коректний вихідний файл."
                )

            self._publish_output(temporary_path, destination)
            return destination

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _kill_process_group(process: subprocess.Popen) -> None:
        """Завершує Calibre разом із дочірніми процесами."""

        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                process.kill()
            except ProcessLookupError:
                pass

    @staticmethod
    def _run_command(command: list[str]) -> None:
        """Запускає Calibre з обмеженням часу."""

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=True,
        )

        try:
            stdout, stderr = process.communicate(
                timeout=CONVERTER_TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired as exc:
            EbookConverter._kill_process_group(process)
            process.communicate()

            raise TimeoutError(
                "Конвертація електронної книги перевищила ліміт у "
                f"{CONVERTER_TIMEOUT_SECONDS} секунд."
            ) from exc
        except BaseException:
            EbookConverter._kill_process_group(process)
            process.communicate()
            raise

        if process.returncode != 0:
            details = (
                stderr.strip()
                or stdout.strip()
                or "Причину не повідомлено."
            )

            raise ValueError(
                f"Calibre не зміг конвертувати книгу: {details}"
            )

    @staticmethod
    def _publish_output(
        temporary_path: Path,
        destination: Path,
    ) -> None:
        """Публікує результат без перезапису наявного файлу."""

        try:
            os.link(temporary_path, destination)
        except FileExistsError:
            raise FileExistsError(
                f"Файл призначення вже існує: {destination}"
            ) from None
