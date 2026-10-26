"""Конвертер документів DOCX, TXT, RTF і PDF для macOS."""

import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

from src.config import (
    CONVERTER_TIMEOUT_SECONDS,
    LIBREOFFICE_PATH,
    TEXTUTIL_PATH,
)
from src.converters.base import BaseConverter
from src.converters.formats import DOCUMENT_FORMATS


class DocumentConverter(BaseConverter):
    """Конвертує документи через textutil і LibreOffice."""

    TEXTUTIL_PATH = TEXTUTIL_PATH
    LIBREOFFICE_PATH = LIBREOFFICE_PATH
    TIMEOUT_SECONDS = CONVERTER_TIMEOUT_SECONDS

    SUPPORTED_INPUT_FORMATS = DOCUMENT_FORMATS
    SUPPORTED_OUTPUT_FORMATS = DOCUMENT_FORMATS | frozenset({"pdf"})

    @property
    def name(self) -> str:
        return "Document Converter"

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

        # DOCX, TXT і RTF можна конвертувати між собою.
        if (
            source_format in DOCUMENT_FORMATS
            and destination_format in DOCUMENT_FORMATS
        ):
            return True

        # LibreOffice використовується для DOCX → PDF.
        return (
            source_format == "docx"
            and destination_format == "pdf"
        )

    def convert(self, source: Path, destination: Path) -> Path:
        """Конвертує документ, зберігаючи оригінал."""

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

        if destination_format == "pdf":
            return self._convert_docx_to_pdf(source, destination)

        return self._convert_with_textutil(
            source,
            destination,
            destination_format,
        )

    def _convert_with_textutil(
        self,
        source: Path,
        destination: Path,
        destination_format: str,
    ) -> Path:
        """Конвертує документи через системний textutil."""

        if not TEXTUTIL_PATH.is_file():
            raise FileNotFoundError(
                f"Не знайдено системну утиліту: {TEXTUTIL_PATH}"
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

            # Абсолютні шляхи починаються з «/», тому ім'я файла
            # на кшталт «-x.txt» не буде сприйняте як опція.
            command = [
                str(TEXTUTIL_PATH),
                "-convert",
                destination_format,
                "-output",
                str(temporary_path),
                str(source.resolve()),
            ]

            self._run_command(command, "textutil")

            if (
                not temporary_path.is_file()
                or temporary_path.stat().st_size == 0
            ):
                raise ValueError(
                    "textutil не створив коректний вихідний файл."
                )

            self._publish_output(temporary_path, destination)
            return destination

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def _convert_docx_to_pdf(
        self,
        source: Path,
        destination: Path,
    ) -> Path:
        """Конвертує DOCX у PDF через LibreOffice."""

        if not LIBREOFFICE_PATH.is_file():
            raise FileNotFoundError(
                f"Не знайдено LibreOffice: {LIBREOFFICE_PATH}"
            )

        temporary_directory: Path | None = None
        profile_directory: Path | None = None

        try:
            temporary_directory = Path(
                tempfile.mkdtemp(
                    prefix="mactools_",
                    dir=destination.parent,
                )
            ).resolve()

            # Окремий профіль: LibreOffice не конфліктує з уже
            # запущеним екземпляром і не чіпає профіль користувача.
            profile_directory = Path(
                tempfile.mkdtemp(prefix="mactools_lo_profile_")
            ).resolve()

            command = [
                str(LIBREOFFICE_PATH),
                f"-env:UserInstallation={profile_directory.as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temporary_directory),
                str(source.resolve()),
            ]

            self._run_command(command, "LibreOffice")

            # Не покладаємося на ім'я результату: у папці лише
            # файли, створені цією конвертацією.
            generated_files = sorted(
                temporary_directory.glob("*.pdf")
            )

            if len(generated_files) != 1:
                raise ValueError(
                    "LibreOffice не створив коректний PDF-файл."
                )

            generated_pdf = generated_files[0]

            if (
                not generated_pdf.is_file()
                or generated_pdf.stat().st_size == 0
            ):
                raise ValueError(
                    "LibreOffice не створив коректний PDF-файл."
                )

            self._publish_output(generated_pdf, destination)
            return destination

        finally:
            for directory in (temporary_directory, profile_directory):
                if directory is not None:
                    shutil.rmtree(directory, ignore_errors=True)

    @staticmethod
    def _kill_process_group(process: subprocess.Popen) -> None:
        """Завершує процес разом із усіма його дочірніми процесами."""

        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            # Група вже завершилась або недоступна: гасимо сам процес.
            try:
                process.kill()
            except ProcessLookupError:
                pass

    @staticmethod
    def _run_command(command: list[str], program_name: str) -> None:
        """Запускає зовнішню програму з обмеженням часу.

        Процес запускається в окремій сесії, тому при таймауті
        завершується вся група (наприклад, soffice і soffice.bin).
        """

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
            DocumentConverter._kill_process_group(process)
            process.communicate()
            raise TimeoutError(
                "Конвертація перевищила ліміт у "
                f"{CONVERTER_TIMEOUT_SECONDS} секунд."
            ) from exc
        except BaseException:
            DocumentConverter._kill_process_group(process)
            process.communicate()
            raise

        if process.returncode != 0:
            details = (
                stderr.strip()
                or stdout.strip()
                or "Причину не повідомлено."
            )
            raise ValueError(
                f"{program_name} не зміг конвертувати документ: "
                f"{details}"
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