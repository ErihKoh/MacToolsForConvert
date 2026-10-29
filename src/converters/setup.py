"""Створення стандартного реєстру конвертерів."""
from src.converters.document_converter import DocumentConverter
from src.converters.image_converter import ImageConverter
from src.converters.pdf_converter import PDFConverter
from src.converters.registry import ConverterRegistry
from src.converters.video_converter import VideoConverter
from src.converters.audio_converter import AudioConverter


def create_default_registry() -> ConverterRegistry:
    """Створює реєстр зі стандартним набором конвертерів."""

    registry = ConverterRegistry()

    registry.register(ImageConverter())
    registry.register(PDFConverter())
    registry.register(DocumentConverter())
    registry.register(VideoConverter())
    registry.register(AudioConverter())

    return registry
