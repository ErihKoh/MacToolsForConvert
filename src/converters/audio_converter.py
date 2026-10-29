"""Конвертер аудіофайлів на основі FFmpeg."""

import os
import shutil
import subprocess
import uuid
from pathlib import Path

from src.converters.base import BaseConverter
from src.converters.formats import (
    AUDIO_INPUT_FORMATS,
    AUDIO_OUTPUT_FORMATS,
)


class AudioConverter(BaseConverter):
    """Конвертує аудіофайли між підтримуваними форматами."""

    @staticmethod
    def _find_executable(name: str) -> str | None:
        """Знаходить виконуваний файл у PATH або стандартних каталогах."""

        executable = shutil.which(name)

        if executable:
            return executable

        for candidate in (
                Path("/opt/homebrew/bin") / name,
                Path("/usr/local/bin") / name,
        ):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)

        return None

    def __init__(self) -> None:
        self._ffmpeg_path = self._find_executable("ffmpeg")
        self._ffprobe_path = self._find_executable("ffprobe")

    @property
    def name(self) -> str:
        """Назва конвертера."""

        return "Audio Converter"

    @property
    def supported_input_formats(self) -> set[str]:
        """Підтримувані вхідні аудіоформати."""

        return set(AUDIO_INPUT_FORMATS)

    @property
    def supported_output_formats(self) -> set[str]:
        """Підтримувані вихідні аудіоформати."""

        return set(AUDIO_OUTPUT_FORMATS)

    def is_available_for(
            self,
            source_format: str,
            destination_format: str,
    ) -> bool:
        """Перевіряє підтримку форматів і наявність FFmpeg."""

        return (
                super().is_available_for(
                    source_format,
                    destination_format,
                )
                and self._ffmpeg_path is not None
                and self._ffprobe_path is not None
        )

    def convert(
            self,
            source: Path,
            destination: Path,
    ) -> Path:
        """Конвертує аудіофайл, не перезаписуючи наявні файли."""

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

        if not self._ffmpeg_path or not self._ffprobe_path:
            raise RuntimeError(
                "Для конвертації аудіо потрібні FFmpeg і ffprobe. "
                "Перевірте їх установлення."
            )

        temporary_path = destination.with_name(
            f".{destination.stem}.{uuid.uuid4().hex}.partial"
            f"{destination.suffix.lower()}"
        )

        try:
            self._validate_audio_streams(source)

            command = [
                self._ffmpeg_path,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-vn",
            ]

            # Форматозалежні параметри кодування.
            if destination_format == "mp3":
                command.extend([
                    "-c:a", "libmp3lame",
                    "-q:a", "2",
                ])
            elif destination_format == "wav":
                command.extend([
                    "-c:a", "pcm_s16le",
                ])
            elif destination_format == "flac":
                command.extend([
                    "-c:a", "flac",
                    "-compression_level", "5",
                ])
            elif destination_format == "m4a":
                command.extend([
                    "-c:a", "aac",
                    "-b:a", "192k",
                ])
            elif destination_format == "aac":
                command.extend([
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-f", "adts",
                ])
            elif destination_format == "ogg":
                command.extend([
                    "-c:a", "libvorbis",
                    "-q:a", "5",
                ])
            elif destination_format == "opus":
                command.extend([
                    "-c:a", "libopus",
                    "-b:a", "128k",
                ])

            command.extend([
                "-y",
                str(temporary_path),
            ])

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                details = result.stderr.strip()

                if len(details) > 1500:
                    details = details[-1500:]

                raise RuntimeError(
                    "FFmpeg не зміг конвертувати аудіо."
                    + (f"\nДеталі: {details}" if details else "")
                )

            if (
                    not temporary_path.is_file()
                    or temporary_path.stat().st_size == 0
            ):
                raise RuntimeError(
                    "FFmpeg не створив коректний вихідний файл."
                )

            self._validate_audio_streams(temporary_path)

            # os.link не перезаписує файл, який міг з'явитися
            # паралельно після початкової перевірки.
            os.link(temporary_path, destination)

            return destination

        finally:
            temporary_path.unlink(missing_ok=True)

    def _validate_audio_streams(self, source: Path) -> None:
        """Перевіряє, чи містить файл аудіопотік."""

        if not self._ffprobe_path:
            raise RuntimeError("Не знайдено ffprobe.")

        command = [
            self._ffprobe_path,
            "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            str(source),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            details = result.stderr.strip()

            raise ValueError(
                f"Не вдалося прочитати аудіофайл: {source.name}"
                + (f"\nДеталі: {details}" if details else "")
            )

        if not result.stdout.strip():
            raise ValueError(
                f"У файлі не знайдено аудіопотоку: {source.name}"
            )
