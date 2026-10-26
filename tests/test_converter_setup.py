"""Тести створення стандартного реєстру конвертерів."""

import unittest

from src.converters.document_converter import DocumentConverter
from src.converters.image_converter import ImageConverter
from src.converters.pdf_converter import PDFConverter
from src.converters.video_converter import VideoConverter
from src.converters.registry import ConverterRegistry
from src.converters.setup import create_default_registry


class TestConverterSetup(unittest.TestCase):
    """Перевіряє стандартну конфігурацію реєстру."""

    def test_create_default_registry_returns_registry(self):
        registry = create_default_registry()

        self.assertIsInstance(registry, ConverterRegistry)

    def test_image_converter_is_registered(self):
        registry = create_default_registry()

        converter = registry.get("Image Converter")

        self.assertIsInstance(converter, ImageConverter)

    def test_pdf_converter_is_registered(self):
        registry = create_default_registry()

        converter = registry.get("PDF Converter")

        self.assertIsInstance(converter, PDFConverter)

    def test_document_converter_is_registered(self):
        registry = create_default_registry()

        converter = registry.get("Document Converter")

        self.assertIsInstance(converter, DocumentConverter)

    def test_video_converter_is_registered(self):
        registry = create_default_registry()

        converter = registry.find("mts", "mp4")

        self.assertIsInstance(converter, VideoConverter)

    def test_find_converter_for_png_to_jpeg(self):
        registry = create_default_registry()

        converter = registry.find("png", "jpeg")

        self.assertIsInstance(converter, ImageConverter)

    def test_find_converter_for_png_to_pdf(self):
        registry = create_default_registry()

        converter = registry.find("png", "pdf")

        self.assertIsInstance(converter, PDFConverter)

    def test_find_converter_for_pdf_to_png(self):
        registry = create_default_registry()

        converter = registry.find("pdf", "png")

        self.assertIsInstance(converter, PDFConverter)

    def test_find_converter_for_docx_to_txt(self):
        registry = create_default_registry()

        converter = registry.find("docx", "txt")

        self.assertIsInstance(converter, DocumentConverter)

    def test_find_converter_for_rtf_to_docx(self):
        registry = create_default_registry()

        converter = registry.find("rtf", "docx")

        self.assertIsInstance(converter, DocumentConverter)

    def test_find_converter_ignores_format_case(self):
        registry = create_default_registry()

        converter = registry.find("PNG", "JPEG")

        self.assertIsInstance(converter, ImageConverter)

    def test_default_registry_contains_four_converters(self):
        registry = create_default_registry()

        self.assertEqual(len(registry), 4)


if __name__ == '__main__':
    unittest.main()
