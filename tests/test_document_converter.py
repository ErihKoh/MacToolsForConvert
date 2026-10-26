"""Тести конвертера документів DOCX, TXT і RTF."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.converters.document_converter import DocumentConverter


@unittest.skipUnless(
    sys.platform == "darwin"
    and DocumentConverter.TEXTUTIL_PATH.is_file(),
    "Потрібна macOS із системною утилітою textutil.",
)
class TestDocumentConverter(unittest.TestCase):
    """Перевіряє конвертацію документів через textutil."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.directory = Path(self.temp_dir.name)
        self.converter = DocumentConverter()

        self.text_file = self.directory / "sample.txt"
        self.text_file.write_text(
            "MacTools document conversion test.\nSecond line.",
            encoding="utf-8",
        )

        self.docx_file = self.directory / "sample.docx"
        self.rtf_file = self.directory / "sample.rtf"

        self._create_document(
            self.text_file,
            self.docx_file,
            "docx",
        )
        self._create_document(
            self.text_file,
            self.rtf_file,
            "rtf",
        )

    def _create_document(
            self,
            source: Path,
            destination: Path,
            output_format: str,
    ) -> None:
        """Створює тестовий документ за допомогою textutil."""

        result = subprocess.run(
            [
                str(self.converter.TEXTUTIL_PATH),
                "-convert",
                output_format,
                "-output",
                str(destination),
                str(source),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            self.fail(
                "Не вдалося підготувати тестовий документ: "
                f"{result.stderr.strip()}"
            )

        self.assertTrue(destination.is_file())
        self.assertGreater(destination.stat().st_size, 0)

    def test_txt_to_docx(self):
        destination = self.directory / "converted.docx"

        result = self.converter.convert(self.text_file, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())
        self.assertGreater(destination.stat().st_size, 0)

    def test_docx_to_txt(self):
        destination = self.directory / "converted.txt"

        result = self.converter.convert(self.docx_file, destination)

        self.assertEqual(result, destination)
        self.assertIn(
            "MacTools document conversion test.",
            destination.read_text(encoding="utf-8"),
        )

    def test_txt_to_rtf(self):
        destination = self.directory / "converted.rtf"

        result = self.converter.convert(self.text_file, destination)

        self.assertEqual(result, destination)
        self.assertIn(
            r"{\rtf",
            destination.read_text(encoding="utf-8", errors="replace")[:100],
        )

    def test_rtf_to_txt(self):
        destination = self.directory / "converted.txt"

        self.converter.convert(self.rtf_file, destination)

        content = destination.read_text(encoding="utf-8")
        self.assertIn("MacTools document conversion test.", content)

    def test_docx_to_rtf(self):
        destination = self.directory / "converted.rtf"

        result = self.converter.convert(self.docx_file, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())
        self.assertGreater(destination.stat().st_size, 0)

    def test_rtf_to_docx(self):
        destination = self.directory / "converted.docx"

        result = self.converter.convert(self.rtf_file, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())
        self.assertGreater(destination.stat().st_size, 0)

    def test_original_file_is_preserved(self):
        original_content = self.text_file.read_bytes()

        self.converter.convert(
            self.text_file,
            self.directory / "converted.docx",
        )

        self.assertEqual(self.text_file.read_bytes(), original_content)

    def test_existing_destination_is_not_overwritten(self):
        destination = self.directory / "existing.docx"
        original_content = b"keep this content"
        destination.write_bytes(original_content)

        with self.assertRaises(FileExistsError):
            self.converter.convert(self.text_file, destination)

        self.assertEqual(destination.read_bytes(), original_content)

    def test_missing_source_raises_error(self):
        source = self.directory / "missing.txt"
        destination = self.directory / "converted.docx"

        with self.assertRaises(FileNotFoundError):
            self.converter.convert(source, destination)

    def test_same_format_conversion_is_rejected(self):
        with self.assertRaises(ValueError):
            self.converter.convert(
                self.text_file,
                self.directory / "converted.txt",
            )

    def test_missing_destination_directory_raises_error(self):
        destination = self.directory / "missing" / "converted.docx"

        with self.assertRaises(FileNotFoundError):
            self.converter.convert(self.text_file, destination)

    def test_docx_to_pdf(self):
        """Перевіряє конвертацію DOCX у PDF через LibreOffice."""

        source = self.directory / "sample.docx"
        destination = self.directory / "sample.pdf"

        converter = DocumentConverter()
        result = converter.convert(source, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())
        self.assertGreater(destination.stat().st_size, 0)
        self.assertTrue(source.is_file())

    def test_temporary_files_are_removed_after_conversion(self):
        destination = self.directory / "converted.docx"

        self.converter.convert(self.text_file, destination)

        leftovers = list(self.directory.glob(".mactools_*"))
        self.assertEqual(leftovers, [])


if __name__ == '__main__':
    unittest.main()
