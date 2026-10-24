"""Створення стандартного реєстру конвертерів."""

from src.converters.image_converter import ImageConverter
from src.converters.pdf_converter import PDFConverter
from src.converters.registry import ConverterRegistry


def create_default_registry() -> ConverterRegistry:
    """Створює реєстр зі стандартним набором конвертерів."""

    registry = ConverterRegistry()

    registry.register(ImageConverter())
    registry.register(PDFConverter())

    return registry
