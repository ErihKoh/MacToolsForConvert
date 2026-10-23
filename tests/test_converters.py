"""Тести базового інтерфейсу та реєстру конвертерів."""

import tempfile
import unittest
from pathlib import Path

from src.converters.base import BaseConverter
from src.converters.registry import ConverterRegistry


class FakeConverter(BaseConverter):
    """Тестовий конвертер для перевірки реєстру."""

    def __init__(
        self,
        converter_name: str = "Image Converter",
        input_formats: set[str] | None = None,
        output_formats: set[str] | None = None,
    ) -> None:
        self._name = converter_name
        self._input_formats = (
            input_formats if input_formats is not None else {"png", "jpg"}
        )
        self._output_formats = (
            output_formats if output_formats is not None else {"webp", "jpg"}
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_input_formats(self) -> set[str]:
        return self._input_formats

    @property
    def supported_output_formats(self) -> set[str]:
        return self._output_formats

    def convert(self, source: Path, destination: Path) -> Path:
        """Імітує конвертацію для тестів."""

        if not source.is_file():
            raise FileNotFoundError(source)

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())

        return destination


class TestBaseConverter(unittest.TestCase):
    """Перевіряє базовий інтерфейс конвертера."""

    def setUp(self) -> None:
        self.converter = FakeConverter()

    def test_converter_name(self) -> None:
        self.assertEqual(self.converter.name, "Image Converter")

    def test_supported_formats(self) -> None:
        self.assertEqual(
            self.converter.supported_input_formats,
            {"png", "jpg"},
        )
        self.assertEqual(
            self.converter.supported_output_formats,
            {"webp", "jpg"},
        )

    def test_can_convert_supported_formats(self) -> None:
        self.assertTrue(self.converter.can_convert("png", "webp"))

    def test_can_convert_is_case_insensitive(self) -> None:
        self.assertTrue(self.converter.can_convert(".PNG", ".WEBP"))

    def test_can_convert_rejects_unsupported_input(self) -> None:
        self.assertFalse(self.converter.can_convert("pdf", "webp"))

    def test_can_convert_rejects_unsupported_output(self) -> None:
        self.assertFalse(self.converter.can_convert("png", "pdf"))

    def test_convert_copies_test_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.png"
            destination = root / "output" / "result.webp"
            source.write_bytes(b"test image data")

            result = self.converter.convert(source, destination)

            self.assertEqual(result, destination)
            self.assertTrue(destination.is_file())
            self.assertEqual(
                destination.read_bytes(),
                b"test image data",
            )

    def test_convert_missing_source_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "missing.png"
            destination = root / "result.webp"

            with self.assertRaises(FileNotFoundError):
                self.converter.convert(source, destination)


class TestConverterRegistry(unittest.TestCase):
    """Перевіряє реєстрацію та пошук конвертерів."""

    def setUp(self) -> None:
        self.registry = ConverterRegistry()
        self.converter = FakeConverter()
        self.registry.register(self.converter)

    def test_empty_registry(self) -> None:
        registry = ConverterRegistry()

        self.assertEqual(len(registry), 0)
        self.assertEqual(registry.converters, {})

    def test_register_converter(self) -> None:
        self.assertEqual(len(self.registry), 1)

    def test_get_converter(self) -> None:
        result = self.registry.get("Image Converter")

        self.assertIs(result, self.converter)

    def test_get_converter_is_case_insensitive(self) -> None:
        result = self.registry.get("IMAGE CONVERTER")

        self.assertIs(result, self.converter)

    def test_get_unknown_converter(self) -> None:
        self.assertIsNone(self.registry.get("Unknown Converter"))

    def test_register_duplicate_raises_error(self) -> None:
        duplicate = FakeConverter("IMAGE CONVERTER")

        with self.assertRaises(ValueError):
            self.registry.register(duplicate)

        self.assertEqual(len(self.registry), 1)

    def test_register_empty_name_raises_error(self) -> None:
        converter = FakeConverter("   ")

        with self.assertRaises(ValueError):
            self.registry.register(converter)

        self.assertEqual(len(self.registry), 1)

    def test_find_converter_for_supported_formats(self) -> None:
        result = self.registry.find("png", "webp")

        self.assertIs(result, self.converter)

    def test_find_converter_is_case_insensitive(self) -> None:
        result = self.registry.find(".PNG", ".WEBP")

        self.assertIs(result, self.converter)

    def test_find_unsupported_formats(self) -> None:
        self.assertIsNone(self.registry.find("pdf", "docx"))

    def test_unregister_converter(self) -> None:
        result = self.registry.unregister("Image Converter")

        self.assertTrue(result)
        self.assertEqual(len(self.registry), 0)
        self.assertIsNone(self.registry.get("Image Converter"))

    def test_unregister_unknown_converter(self) -> None:
        result = self.registry.unregister("Unknown Converter")

        self.assertFalse(result)
        self.assertEqual(len(self.registry), 1)

    def test_clear_registry(self) -> None:
        self.registry.clear()

        self.assertEqual(len(self.registry), 0)
        self.assertEqual(self.registry.converters, {})

    def test_converters_returns_copy(self) -> None:
        converters = self.registry.converters
        converters.clear()

        self.assertEqual(len(self.registry), 1)


if __name__ == "__main__":
    unittest.main()