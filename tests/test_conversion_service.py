"""Тести сервісу конвертації MacTools."""

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from PIL import Image

from src.converters.setup import create_default_registry
from src.services.conversion_service import ConversionService


class TestConversionService(unittest.TestCase):
    """Перевіряє роботу сервісу конвертації."""

    def setUp(self) -> None:
        """Готує тимчасові файли для кожного тесту."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.output_directory = self.root / "output"
        self.output_directory.mkdir()

        self.service = ConversionService(
            create_default_registry()
        )

    def tearDown(self) -> None:
        """Видаляє тимчасові файли після тесту."""

        self.temp_dir.cleanup()

    def create_png(self, name: str = "test_image.png") -> Path:
        """Створює тестове PNG-зображення."""

        path = self.root / name

        image = Image.new("RGB", (100, 100), color="red")
        image.save(path, format="PNG")

        return path

    def test_convert_png_to_jpeg(self) -> None:
        """Перевіряє конвертацію PNG у JPEG."""

        source = self.create_png()

        result = self.service.convert_file(
            source=source,
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertTrue(result.success, result.error)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.destination)
        self.assertTrue(result.destination.exists())
        self.assertEqual(result.destination.suffix, ".jpg")
        self.assertTrue(source.exists())

        with Image.open(result.destination) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (100, 100))

    def test_batch_conversion(self) -> None:
        """Перевіряє пакетну конвертацію трьох зображень."""

        sources = [
            self.create_png(f"image_{index}.png")
            for index in range(3)
        ]

        results = self.service.convert_files(
            sources=sources,
            output_directory=self.output_directory,
            output_format="webp",
        )

        self.assertEqual(len(results), 3)
        self.assertTrue(
            all(result.success for result in results),
            [result.error for result in results],
        )
        self.assertEqual(
            len(list(self.output_directory.glob("*.webp"))),
            3,
        )

    def test_missing_source_file(self) -> None:
        """Перевіряє обробку відсутнього вхідного файла."""

        missing_file = self.root / "missing.png"

        result = self.service.convert_file(
            source=missing_file,
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertFalse(result.success)
        self.assertIsNone(result.destination)
        self.assertIsNotNone(result.error)
        self.assertIn("не знайдено", result.error)

    def test_existing_output_is_not_overwritten(self) -> None:
        """Перевіряє створення нового імені для повторного результату."""

        source = self.create_png()

        first = self.service.convert_file(
            source=source,
            output_directory=self.output_directory,
            output_format="jpg",
        )

        second = self.service.convert_file(
            source=source,
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertTrue(first.success, first.error)
        self.assertTrue(second.success, second.error)
        self.assertNotEqual(first.destination, second.destination)
        self.assertTrue(first.destination.exists())
        self.assertTrue(second.destination.exists())

    def test_get_available_formats_for_png(self) -> None:
        """Повертає формати, доступні для PNG."""

        source = self.create_png()

        formats = self.service.get_available_formats(
            sources=[source],
            output_formats=["jpg", "webp", "pdf"],
        )

        self.assertEqual(formats, {"jpg", "webp", "pdf"})

    def test_get_available_formats_for_multiple_files(self) -> None:
        """Повертає формати, сумісні з усіма файлами."""

        png_file = self.create_png("image.png")

        jpeg_file = self.root / "image.jpg"
        Image.new("RGB", (100, 100), color="blue").save(
            jpeg_file,
            format="JPEG",
        )

        formats = self.service.get_available_formats(
            sources=[png_file, jpeg_file],
            output_formats=["jpg", "webp", "png", "pdf"],
        )

        self.assertEqual(formats, {"jpg", "webp", "png", "pdf"})

    def test_get_available_formats_for_empty_sources(self) -> None:
        """Повертає порожню множину без вхідних файлів."""

        formats = self.service.get_available_formats(
            sources=[],
            output_formats=["jpg", "webp"],
        )

        self.assertEqual(formats, set())

    def test_docx_to_pdf_available_when_libreoffice_exists(self) -> None:
        """DOCX → PDF доступний, якщо LibreOffice існує."""

        source = self.root / "document.docx"
        source.touch()

        libreoffice = self.root / "soffice"
        libreoffice.touch()

        with patch(
            "src.converters.document_converter.LIBREOFFICE_PATH",
            libreoffice,
        ):
            formats = self.service.get_available_formats(
                sources=[source],
                output_formats=["pdf"],
            )

        self.assertEqual(formats, {"pdf"})

    def test_docx_to_pdf_unavailable_without_libreoffice(self) -> None:
        """DOCX → PDF недоступний, якщо LibreOffice відсутній."""

        source = self.root / "document.docx"
        source.touch()

        missing_libreoffice = self.root / "missing" / "soffice"

        with patch(
            "src.converters.document_converter.LIBREOFFICE_PATH",
            missing_libreoffice,
        ):
            formats = self.service.get_available_formats(
                sources=[source],
                output_formats=["pdf"],
            )

        self.assertEqual(formats, set())

    def test_png_to_pdf_available_without_libreoffice(self) -> None:
        """PNG → PDF доступний без LibreOffice."""

        source = self.create_png()

        missing_libreoffice = self.root / "missing" / "soffice"

        with patch(
            "src.converters.document_converter.LIBREOFFICE_PATH",
            missing_libreoffice,
        ):
            formats = self.service.get_available_formats(
                sources=[source],
                output_formats=["pdf"],
            )

        self.assertEqual(formats, {"pdf"})

    def test_unsupported_format(self) -> None:
        """Перевіряє відмову від непідтримуваної пари форматів."""

        source = self.root / "document.txt"
        source.write_text("Тестовий документ", encoding="utf-8")

        result = self.service.convert_file(
            source=source,
            output_directory=self.output_directory,
            output_format="jpg",
        )

        self.assertFalse(result.success)
        self.assertIsNone(result.destination)
        self.assertIsNotNone(result.error)
        self.assertIn("Немає конвертера", result.error)


if __name__ == "__main__":
    unittest.main()
