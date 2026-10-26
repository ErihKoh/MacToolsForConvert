"""Тести конвертера зображень MacTools."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pillow_heif import from_pillow

from src.converters.image_converter import ImageConverter


class TestImageConverter(unittest.TestCase):
    """Перевірки конвертації зображень."""

    def setUp(self) -> None:
        """Створює тимчасову папку та тестове PNG-зображення."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)
        self.converter = ImageConverter()

        self.source = self.directory / "source.png"

        image = Image.new("RGB", (20, 10), (255, 0, 0))
        image.save(self.source)

        self.original_bytes = self.source.read_bytes()

    def tearDown(self) -> None:
        """Видаляє тимчасові файли після тесту."""
        self.temp_dir.cleanup()

    def test_converter_name(self) -> None:
        """Перевіряє назву конвертера."""
        self.assertEqual(self.converter.name, "Image Converter")

    def test_supported_formats(self):
        expected_input = {
            "jpg",
            "jpeg",
            "png",
            "webp",
            "tif",
            "tiff",
            "bmp",
            "heic",
            "heif",
        }

        expected_output = {
            "jpg",
            "jpeg",
            "png",
            "webp",
            "tif",
            "tiff",
            "bmp",
        }

        self.assertEqual(
            self.converter.supported_input_formats,
            expected_input,
        )
        self.assertEqual(
            self.converter.supported_output_formats,
            expected_output,
        )

    def test_can_convert_png_to_jpeg(self) -> None:
        """Перевіряє визначення підтримуваної пари форматів."""
        self.assertTrue(self.converter.can_convert("PNG", "jpg"))
        self.assertTrue(self.converter.can_convert("png", ".JPEG"))

    def test_convert_png_to_jpeg(self) -> None:
        """Перевіряє конвертацію PNG у JPEG."""
        destination = self.directory / "result.jpg"

        result = self.converter.convert(self.source, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())

        with Image.open(destination) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (20, 10))
            self.assertEqual(image.mode, "RGB")

    def _create_heif_source(self, filename: str) -> Path:
        """Створює тестове HEIF/HEIC-зображення."""
        source = self.directory / filename

        image = Image.new("RGB", (20, 10), (255, 0, 0))
        heif_image = from_pillow(image)
        heif_image.save(source)

        return source

    def test_convert_heic_to_jpeg(self) -> None:
        """Перевіряє конвертацію HEIC у JPEG."""
        source = self._create_heif_source("source.heic")
        destination = self.directory / "result.jpg"

        self.converter.convert(source, destination)

        with Image.open(destination) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (20, 10))
            self.assertEqual(image.mode, "RGB")

    def test_convert_heif_to_png(self) -> None:
        """Перевіряє конвертацію HEIF у PNG."""
        source = self._create_heif_source("source.heif")
        destination = self.directory / "result.png"

        self.converter.convert(source, destination)

        with Image.open(destination) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (20, 10))

    def test_heic_source_is_preserved(self) -> None:
        """Перевіряє, що конвертація не змінює оригінал HEIC."""
        source = self._create_heif_source("source.heic")
        original_bytes = source.read_bytes()
        destination = self.directory / "result.png"

        self.converter.convert(source, destination)

        self.assertEqual(source.read_bytes(), original_bytes)

    def test_convert_png_to_webp(self) -> None:
        """Перевіряє конвертацію PNG у WebP."""
        destination = self.directory / "result.webp"

        self.converter.convert(self.source, destination)

        with Image.open(destination) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (20, 10))

    def test_convert_png_to_tiff(self) -> None:
        """Перевіряє конвертацію PNG у TIFF."""
        destination = self.directory / "result.tiff"

        self.converter.convert(self.source, destination)

        with Image.open(destination) as image:
            self.assertEqual(image.format, "TIFF")
            self.assertEqual(image.size, (20, 10))

    def test_convert_png_to_bmp(self) -> None:
        """Перевіряє конвертацію PNG у BMP."""
        destination = self.directory / "result.bmp"

        self.converter.convert(self.source, destination)

        with Image.open(destination) as image:
            self.assertEqual(image.format, "BMP")
            self.assertEqual(image.size, (20, 10))

    def test_original_is_preserved(self) -> None:
        """Перевіряє, що оригінал не змінюється."""
        destination = self.directory / "result.jpg"

        self.converter.convert(self.source, destination)

        self.assertEqual(
            self.source.read_bytes(),
            self.original_bytes,
        )

    def test_transparency_becomes_white_in_jpeg(self) -> None:
        """Перевіряє заміну прозорого фону білим під час конвертації в JPEG."""
        source = self.directory / "transparent.png"
        destination = self.directory / "transparent.jpg"
        image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        image.paste((255, 0, 0, 255), (0, 0, 50, 100))
        image.save(source)

        self.converter.convert(source, destination)

        with Image.open(destination) as result:
            result.load()

            self.assertEqual(result.mode, "RGB")

            # Перевіряємо піксель далеко від межі червоної ділянки.
            pixel = result.getpixel((90, 50))

            for channel in pixel:
                self.assertGreaterEqual(channel, 245)

    def test_missing_source_raises_error(self) -> None:
        """Перевіряє помилку для відсутнього вхідного файла."""
        destination = self.directory / "result.jpg"

        with self.assertRaises(FileNotFoundError):
            self.converter.convert(
                self.directory / "missing.png",
                destination,
            )

    def test_unsupported_source_format_raises_error(self) -> None:
        """Перевіряє відхилення непідтримуваного вхідного формату."""
        source = self.directory / "source.gif"
        source.write_bytes(b"not an image")

        with self.assertRaises(ValueError):
            self.converter.convert(
                source,
                self.directory / "result.jpg",
            )

    def test_unsupported_destination_format_raises_error(self) -> None:
        """Перевіряє відхилення непідтримуваного вихідного формату."""
        with self.assertRaises(ValueError):
            self.converter.convert(
                self.source,
                self.directory / "result.gif",
            )

    def test_cannot_overwrite_source(self) -> None:
        """Перевіряє заборону перезапису оригіналу."""
        with self.assertRaises(ValueError):
            self.converter.convert(self.source, self.source)

        self.assertEqual(
            self.source.read_bytes(),
            self.original_bytes,
        )

    def test_missing_destination_directory_raises_error(self) -> None:
        """Перевіряє помилку, якщо папка призначення не існує."""
        destination = self.directory / "missing" / "result.jpg"

        with self.assertRaises(FileNotFoundError):
            self.converter.convert(self.source, destination)

    def test_existing_destination_is_not_overwritten(self) -> None:
        """Перевіряє, що наявний файл призначення не перезаписується."""
        destination = self.directory / "result.jpg"
        existing_content = b"existing destination content"
        destination.write_bytes(existing_content)
        with self.assertRaises(FileExistsError):
            self.converter.convert(self.source, destination)

        self.assertEqual(destination.read_bytes(), existing_content)
        self.assertEqual(self.source.read_bytes(), self.original_bytes)

    def test_corrupted_image_raises_error(self) -> None:
        """Перевіряє обробку пошкодженого зображення."""
        source = self.directory / "corrupted.png"
        destination = self.directory / "result.jpg"
        source.write_bytes(b"this is not a valid image")

        with self.assertRaises(ValueError):
            self.converter.convert(source, destination)

        self.assertFalse(destination.exists())

    def test_existing_destination_is_preserved_after_failed_conversion(self) -> None:
        """Перевіряє збереження файла призначення після помилки."""
        source = self.directory / "corrupted.png"
        destination = self.directory / "result.jpg"
        existing_content = b"keep this file unchanged"

        source.write_bytes(b"this is not a valid image")
        destination.write_bytes(existing_content)

        with self.assertRaises(FileExistsError):
            self.converter.convert(source, destination)

        self.assertEqual(destination.read_bytes(), existing_content)
        self.assertEqual(self.source.read_bytes(), self.original_bytes)


if __name__ == '__main__':
    unittest.main()
