"""Тести PDF-конвертера MacTools."""

import tempfile
import unittest
from pathlib import Path

import pymupdf
from PIL import Image

from src.converters.pdf_converter import PDFConverter


class TestPDFConverter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.converter = PDFConverter()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_image(self, path: Path) -> Path:
        """Створює тестове PNG-зображення."""
        image = Image.new("RGB", (100, 80), (120, 180, 220))
        image.save(path, format="PNG")
        return path

    def create_pdf(self, path: Path, pages: int = 1) -> Path:
        """Створює тестовий PDF із заданою кількістю сторінок."""
        document = pymupdf.open()

        try:
            for index in range(pages):
                page = document.new_page(width=300, height=200)
                page.insert_text(
                    (50, 80),
                    f"Test page {index + 1}",
                )

            document.save(str(path))
        finally:
            document.close()

        return path

    def test_converter_name(self):
        self.assertEqual(self.converter.name, "PDF Converter")

    def test_supported_conversion_pairs(self):
        self.assertTrue(self.converter.can_convert("png", "pdf"))
        self.assertTrue(self.converter.can_convert("jpg", "pdf"))
        self.assertTrue(self.converter.can_convert("pdf", "png"))
        self.assertTrue(self.converter.can_convert("pdf", "jpeg"))

    def test_unsupported_conversion_pairs(self):
        self.assertFalse(self.converter.can_convert("pdf", "pdf"))
        self.assertFalse(self.converter.can_convert("png", "jpg"))
        self.assertFalse(self.converter.can_convert("jpg", "webp"))
        self.assertFalse(self.converter.can_convert("docx", "pdf"))

    def test_conversion_check_ignores_case_and_dots(self):
        self.assertTrue(self.converter.can_convert(".PNG", ".PDF"))
        self.assertTrue(self.converter.can_convert(".PDF", ".JPG"))

    def test_png_to_pdf(self):
        source = self.create_image(self.root / "source.png")
        destination = self.root / "result.pdf"

        result = self.converter.convert(source, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())

        with pymupdf.open(str(destination)) as document:
            self.assertEqual(document.page_count, 1)

    def test_pdf_to_png(self):
        source = self.create_pdf(self.root / "source.pdf")
        destination = self.root / "result.png"

        result = self.converter.convert(source, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())

        with Image.open(destination) as image:
            self.assertEqual(image.format, "PNG")
            self.assertGreater(image.width, 0)
            self.assertGreater(image.height, 0)

    def test_pdf_to_jpeg(self):
        source = self.create_pdf(self.root / "source.pdf")
        destination = self.root / "result.jpg"

        result = self.converter.convert(source, destination)

        self.assertEqual(result, destination)

        with Image.open(destination) as image:
            self.assertEqual(image.format, "JPEG")

    def test_multipage_pdf_creates_directory(self):
        source = self.create_pdf(
            self.root / "source.pdf",
            pages=3,
        )
        destination = self.root / "result.png"

        result = self.converter.convert(source, destination)

        self.assertTrue(result.is_dir())

        images = sorted(result.glob("*.png"))
        self.assertEqual(len(images), 3)

    def test_missing_source_raises_error(self):
        source = self.root / "missing.pdf"
        destination = self.root / "result.png"

        with self.assertRaises((FileNotFoundError, ValueError)):
            self.converter.convert(source, destination)

    def test_existing_destination_is_not_overwritten(self):
        source = self.create_image(self.root / "source.png")
        destination = self.root / "result.pdf"
        destination.write_bytes(b"original content")

        with self.assertRaises(FileExistsError):
            self.converter.convert(source, destination)

        self.assertEqual(
            destination.read_bytes(),
            b"original content",
        )

    def test_source_cannot_equal_destination(self):
        source = self.create_image(self.root / "source.png")

        with self.assertRaises(ValueError):
            self.converter.convert(source, source)

    def test_missing_destination_directory_raises_error(self):
        source = self.create_image(self.root / "source.png")
        destination = self.root / "missing" / "result.pdf"

        with self.assertRaises((FileNotFoundError, ValueError)):
            self.converter.convert(source, destination)

    def test_invalid_image_raises_error(self):
        source = self.root / "broken.png"
        source.write_bytes(b"this is not a valid image")
        destination = self.root / "result.pdf"

        with self.assertRaises((ValueError, OSError)):
            self.converter.convert(source, destination)


if __name__ == "__main__":
    unittest.main()