"""Тести створення стандартного реєстру конвертерів."""
import unittest
from src.converters.image_converter import ImageConverter
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

    def test_find_converter_for_png_to_jpeg(self):
        registry = create_default_registry()
        converter = registry.find("png", "jpeg")
        self.assertIsInstance(converter, ImageConverter)

    def test_find_converter_ignores_format_case(self):
        registry = create_default_registry()
        converter = registry.find("PNG", "JPEG")
        self.assertIsInstance(converter, ImageConverter)

    def test_default_registry_contains_one_converter(self):
        registry = create_default_registry()
        self.assertEqual(len(registry), 1)


if __name__ == "__main__":
    unittest.main()
