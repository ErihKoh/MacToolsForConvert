"""Тести аудіоконвертера MacTools."""

import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from src.converters.audio_converter import AudioConverter


class TestAudioConverter(unittest.TestCase):
    """Перевіряє роботу AudioConverter."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.converter = AudioConverter()

        # Для unit-тестів не потрібен реальний FFmpeg.
        self.converter._ffmpeg_path = "/usr/bin/ffmpeg"
        self.converter._ffprobe_path = "/usr/bin/ffprobe"

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_audio_file(self, path: Path) -> Path:
        """Створює умовний тестовий аудіофайл."""

        path.write_bytes(b"test audio content")

        return path

    def test_converter_name(self):
        """Перевіряє назву конвертера."""

        self.assertEqual(
            self.converter.name,
            "Audio Converter",
        )

    def test_supported_formats(self):
        """Перевіряє підтримувані аудіоформати."""

        expected_formats = {
            "mp3",
            "wav",
            "flac",
            "m4a",
            "aac",
            "ogg",
            "opus",
        }

        self.assertEqual(
            self.converter.supported_input_formats,
            expected_formats,
        )

        self.assertEqual(
            self.converter.supported_output_formats,
            expected_formats,
        )

    def test_supported_conversion_pairs(self):
        """Перевіряє підтримувані пари форматів."""

        self.assertTrue(self.converter.can_convert("mp3", "wav"))
        self.assertTrue(self.converter.can_convert("flac", "mp3"))
        self.assertTrue(self.converter.can_convert("m4a", "aac"))
        self.assertTrue(self.converter.can_convert("ogg", "opus"))

    def test_unsupported_conversion_pairs(self):
        """Перевіряє відхилення непідтримуваних пар."""

        self.assertFalse(self.converter.can_convert("mp3", "pdf"))
        self.assertFalse(self.converter.can_convert("wav", "jpg"))
        self.assertFalse(self.converter.can_convert("docx", "mp3"))

    def test_conversion_check_ignores_case_and_dots(self):
        """Перевіряє нормалізацію розширень."""

        self.assertTrue(self.converter.can_convert(".MP3", ".WAV"))
        self.assertTrue(self.converter.can_convert(".FLAC", ".MP3"))

    def test_is_available_for_requires_ffmpeg_and_ffprobe(self):
        """Перевіряє доступність конвертації."""

        self.assertTrue(
            self.converter.is_available_for("mp3", "wav")
        )

        self.converter._ffmpeg_path = None

        self.assertFalse(
            self.converter.is_available_for("mp3", "wav")
        )

        self.converter._ffmpeg_path = "/usr/bin/ffmpeg"
        self.converter._ffprobe_path = None

        self.assertFalse(
            self.converter.is_available_for("mp3", "wav")
        )

    def test_missing_source_raises_error(self):
        """Перевіряє обробку відсутнього вхідного файла."""

        source = self.root / "missing.mp3"
        destination = self.root / "result.wav"

        with self.assertRaises(FileNotFoundError):
            self.converter.convert(source, destination)

    def test_unsupported_source_format_raises_error(self):
        """Перевіряє відхилення непідтримуваного вхідного формату."""

        source = self.create_audio_file(
            self.root / "source.pdf"
        )
        destination = self.root / "result.mp3"

        with self.assertRaises(ValueError):
            self.converter.convert(source, destination)

    def test_unsupported_destination_format_raises_error(self):
        """Перевіряє відхилення непідтримуваного вихідного формату."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )
        destination = self.root / "result.pdf"

        with self.assertRaises(ValueError):
            self.converter.convert(source, destination)

    def test_source_cannot_equal_destination(self):
        """Перевіряє заборону конвертації файла в самого себе."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )

        with self.assertRaises(ValueError):
            self.converter.convert(source, source)

    def test_existing_destination_is_not_overwritten(self):
        """Перевіряє захист наявного вихідного файла."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )

        destination = self.root / "result.wav"
        destination.write_bytes(b"original content")

        with self.assertRaises(FileExistsError):
            self.converter.convert(source, destination)

        self.assertEqual(
            destination.read_bytes(),
            b"original content",
        )

    def test_missing_destination_directory_raises_error(self):
        """Перевіряє обробку відсутньої папки призначення."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )

        destination = (
            self.root
            / "missing"
            / "result.wav"
        )

        with self.assertRaises(FileNotFoundError):
            self.converter.convert(source, destination)

    def test_missing_ffmpeg_raises_error(self):
        """Перевіряє помилку за відсутності FFmpeg."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )
        destination = self.root / "result.wav"

        self.converter._ffmpeg_path = None

        with self.assertRaises(RuntimeError):
            self.converter.convert(source, destination)

    @patch("src.converters.audio_converter.subprocess.run")
    def test_missing_audio_stream_raises_error(self, mock_run):
        """Перевіряє файл без аудіопотоку."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )
        destination = self.root / "result.wav"

        mock_run.return_value = CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        with self.assertRaises(ValueError):
            self.converter.convert(source, destination)

    @patch("src.converters.audio_converter.subprocess.run")
    def test_ffmpeg_failure_raises_error(self, mock_run):
        """Перевіряє обробку помилки FFmpeg."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )
        destination = self.root / "result.wav"

        # Перший виклик — успішна перевірка вхідного аудіо.
        mock_run.side_effect = [
            CompletedProcess(
                args=[],
                returncode=0,
                stdout="audio",
                stderr="",
            ),
            # Другий виклик — помилка FFmpeg.
            CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="Conversion failed",
            ),
        ]

        with self.assertRaises(RuntimeError):
            self.converter.convert(source, destination)

        self.assertFalse(destination.exists())

    @patch("src.converters.audio_converter.subprocess.run")
    def test_successful_conversion(self, mock_run):
        """Перевіряє успішну конвертацію."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )
        destination = self.root / "result.wav"

        def mock_subprocess_run(command, **kwargs):
            """Імітує роботу ffprobe та FFmpeg."""

            executable = Path(command[0]).name

            if executable == "ffprobe":
                return CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="audio",
                    stderr="",
                )

            if executable == "ffmpeg":
                # Останній аргумент команди — тимчасовий файл.
                temporary_path = Path(command[-1])

                temporary_path.write_bytes(
                    b"converted audio content"
                )

                return CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="",
                    stderr="",
                )

            raise AssertionError(
                f"Неочікувана команда: {command}"
            )

        mock_run.side_effect = mock_subprocess_run

        result = self.converter.convert(
            source,
            destination,
        )

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())

        self.assertEqual(
            destination.read_bytes(),
            b"converted audio content",
        )

        # Оригінальний файл має залишитися незмінним.
        self.assertEqual(
            source.read_bytes(),
            b"test audio content",
        )

        # Тимчасовий файл має бути видалений.
        temporary_files = list(
            self.root.glob("*.partial*")
        )

        self.assertEqual(
            temporary_files,
            [],
        )

    @patch("src.converters.audio_converter.subprocess.run")
    def test_temporary_file_is_removed_after_failure(
        self,
        mock_run,
    ):
        """Перевіряє видалення тимчасового файла після помилки."""

        source = self.create_audio_file(
            self.root / "source.mp3"
        )
        destination = self.root / "result.wav"

        def mock_subprocess_run(command, **kwargs):
            executable = Path(command[0]).name

            if executable == "ffprobe":
                return CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="audio",
                    stderr="",
                )

            if executable == "ffmpeg":
                temporary_path = Path(command[-1])

                # Імітуємо частково створений файл.
                temporary_path.write_bytes(
                    b"partial audio"
                )

                return CompletedProcess(
                    args=command,
                    returncode=1,
                    stdout="",
                    stderr="Conversion failed",
                )

            raise AssertionError(
                f"Неочікувана команда: {command}"
            )

        mock_run.side_effect = mock_subprocess_run

        with self.assertRaises(RuntimeError):
            self.converter.convert(
                source,
                destination,
            )

        temporary_files = list(
            self.root.glob("*.partial*")
        )

        self.assertEqual(
            temporary_files,
            [],
        )

        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()