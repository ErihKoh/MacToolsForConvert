"""Конвертер відео на основі FFmpeg."""

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from src.converters.base import BaseConverter
from src.converters.formats import (
    VIDEO_INPUT_FORMATS,
    VIDEO_OUTPUT_FORMATS,
)


class VideoConverter(BaseConverter):
    """Конвертує відеофайли у MP4 за допомогою FFmpeg."""

    @staticmethod
    def _find_executable(name: str) -> str | None:
        """Знаходить виконуваний файл у PATH або стандартних каталогах."""

        executable = shutil.which(name)

        if executable:
            return executable

        # Запасні шляхи для macOS.
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

        return "Video Converter"

    @property
    def supported_input_formats(self) -> set[str]:
        """Підтримувані вхідні відеоформати."""

        return set(VIDEO_INPUT_FORMATS)

    @property
    def supported_output_formats(self) -> set[str]:
        """Підтримувані вихідні відеоформати."""

        return set(VIDEO_OUTPUT_FORMATS)

    def is_available_for(
        self,
        source_format: str,
        destination_format: str,
    ) -> bool:
        """Перевіряє формати та доступність FFmpeg і ffprobe."""

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
        """Конвертує відео в MP4.

        Якщо відео використовує H.264, а всі аудіопотоки
        використовують AAC, виконується копіювання потоків.
        В інших випадках застосовується перекодування
        відео в H.264, а аудіо — в AAC.

        Оригінал не змінюється. Готовий результат не
        перезаписує наявний файл.
        """

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
                "Для конвертації відео потрібні FFmpeg і ffprobe. "
                "Перевірте їх установлення."
            )

        # Тимчасовий файл створюється поруч із результатом.
        # Це дає змогу не показувати неповний файл під
        # остаточним ім'ям.
        temporary_path = destination.with_name(
            f".{destination.stem}.{uuid.uuid4().hex}.partial.mp4"
        )

        try:
            streams = self._probe_streams(source)

            video_streams = [
                stream
                for stream in streams
                if stream.get("codec_type") == "video"
            ]

            if not video_streams:
                raise ValueError(
                    "У файлі не знайдено відеопотоку."
                )

            audio_streams = [
                stream
                for stream in streams
                if stream.get("codec_type") == "audio"
            ]

            can_copy_streams = (
                video_streams[0].get("codec_name") == "h264"
                and all(
                    stream.get("codec_name") == "aac"
                    for stream in audio_streams
                )
            )

            command = [
                self._ffmpeg_path,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-map",
                "0:a?",
            ]

            if can_copy_streams:
                command.extend([
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                ])
            else:
                command.extend([
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "20",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                ])

            command.extend([
                "-movflags",
                "+faststart",
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
                    "FFmpeg не зміг конвертувати відео."
                    + (f"\nДеталі: {details}" if details else "")
                )

            if (
                not temporary_path.is_file()
                or temporary_path.stat().st_size == 0
            ):
                raise RuntimeError(
                    "FFmpeg не створив коректний вихідний файл."
                )

            # Перевіряємо створений MP4 через ffprobe.
            output_streams = self._probe_streams(temporary_path)

            if not any(
                stream.get("codec_type") == "video"
                for stream in output_streams
            ):
                raise RuntimeError(
                    "Створений файл не містить відеопотоку."
                )

            # Створюємо остаточне ім'я без перезапису
            # файла, який міг з'явитися паралельно.
            os.link(temporary_path, destination)

            return destination

        finally:
            # Видаляємо тимчасовий файл і після помилки,
            # і після успішного створення результату.
            temporary_path.unlink(missing_ok=True)

    def _probe_streams(self, source: Path) -> list[dict]:
        """Повертає інформацію про потоки за допомогою ffprobe."""

        if not self._ffprobe_path:
            raise RuntimeError(
                "Не знайдено ffprobe."
            )

        command = [
            self._ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name",
            "-of",
            "json",
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
                f"Не вдалося прочитати відео: {source.name}"
                + (f"\nДеталі: {details}" if details else "")
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "ffprobe повернув некоректні дані про відео."
            ) from exc

        streams = data.get("streams", [])

        if not isinstance(streams, list):
            raise ValueError(
                "Не вдалося визначити відеопотоки."
            )

        return streams
