"""Конвертер PDF та зображень для MacTools."""

from pathlib import Path

import pymupdf
from PIL import Image, UnidentifiedImageError

from src.converters.base import BaseConverter
from src.converters.formats import (
    IMAGE_FORMATS,
    PDF_FORMATS,
    PDF_OUTPUT_IMAGE_FORMATS,
)


class PDFConverter(BaseConverter):
    """Конвертує PDF у зображення та зображення у PDF."""

    INPUT_IMAGE_FORMATS = IMAGE_FORMATS
    OUTPUT_IMAGE_FORMATS = PDF_OUTPUT_IMAGE_FORMATS

    @property
    def name(self) -> str:
        return "PDF Converter"

    @property
    def supported_input_formats(self) -> set[str]:
        return set(IMAGE_FORMATS | PDF_FORMATS)

    @property
    def supported_output_formats(self) -> set[str]:
        return set(PDF_FORMATS | PDF_OUTPUT_IMAGE_FORMATS)

    def can_convert(
        self,
        source_format: str,
        destination_format: str,
    ) -> bool:
        """Перевіряє підтримувані пари форматів."""

        source_format = source_format.lower().strip().lstrip(".")
        destination_format = (
            destination_format.lower().strip().lstrip(".")
        )

        if source_format in PDF_FORMATS:
            return destination_format in PDF_OUTPUT_IMAGE_FORMATS

        if source_format in IMAGE_FORMATS:
            return destination_format in PDF_FORMATS

        return False

    def convert(self, source: Path, destination: Path) -> Path:
        """Конвертує PDF або зображення."""

        source = Path(source).expanduser()
        destination = Path(destination).expanduser()

        if not source.is_file():
            raise FileNotFoundError(
                f"Вхідний файл не знайдено: {source}"
            )

        source_format = source.suffix.lower().lstrip(".")
        destination_format = destination.suffix.lower().lstrip(".")

        if not self.can_convert(source_format, destination_format):
            raise ValueError(
                f"Непідтримувана конвертація: "
                f"{source_format or '(без розширення)'} → "
                f"{destination_format or '(без розширення)'}"
            )

        if source.resolve() == destination.resolve():
            raise ValueError(
                "Вихідний файл не може збігатися з оригіналом."
            )

        if destination.exists():
            raise FileExistsError(
                f"Файл призначення вже існує: {destination}"
            )

        if not destination.parent.is_dir():
            raise FileNotFoundError(
                f"Папка призначення не існує: {destination.parent}"
            )

        if source_format == "pdf":
            return self._pdf_to_images(source, destination)

        return self._image_to_pdf(source, destination)

    def _pdf_to_images(
        self,
        source: Path,
        destination: Path,
    ) -> Path:
        """Зберігає сторінки PDF як окремі зображення."""

        output_format = destination.suffix.lower().lstrip(".")

        try:
            with pymupdf.open(source) as document:
                if document.is_encrypted:
                    raise ValueError(
                        "PDF захищений паролем або зашифрований."
                    )

                if len(document) == 0:
                    raise ValueError("PDF не містить сторінок.")

                if len(document) == 1:
                    pixmap = document[0].get_pixmap(
                        matrix=pymupdf.Matrix(2, 2),
                        alpha=False,
                    )

                    self._save_pixmap(
                        pixmap,
                        destination,
                        output_format,
                    )

                    return destination

                output_directory = (
                    destination.parent / f"{destination.stem}_pages"
                )

                if output_directory.exists():
                    raise FileExistsError(
                        f"Папка результатів уже існує: "
                        f"{output_directory}"
                    )

                output_directory.mkdir()

                try:
                    for page_number, page in enumerate(
                        document,
                        start=1,
                    ):
                        pixmap = page.get_pixmap(
                            matrix=pymupdf.Matrix(2, 2),
                            alpha=False,
                        )

                        output_path = output_directory / (
                            f"{destination.stem}_{page_number:03d}."
                            f"{output_format}"
                        )

                        self._save_pixmap(
                            pixmap,
                            output_path,
                            output_format,
                        )

                except Exception:
                    for file_path in output_directory.iterdir():
                        file_path.unlink(missing_ok=True)

                    output_directory.rmdir()
                    raise

                return output_directory

        except pymupdf.FileDataError as exc:
            raise ValueError(
                f"Не вдалося прочитати PDF: {exc}"
            ) from exc

    @staticmethod
    def _save_pixmap(
        pixmap: pymupdf.Pixmap,
        destination: Path,
        output_format: str,
    ) -> None:
        """Зберігає сторінку PDF у потрібному форматі."""

        if output_format in {"jpg", "jpeg"}:
            pixmap.save(str(destination), jpg_quality=95)
        else:
            pixmap.save(str(destination))

    def _image_to_pdf(
        self,
        source: Path,
        destination: Path,
    ) -> Path:
        """Створює односторінковий PDF із зображення."""

        try:
            with Image.open(source) as opened_image:
                opened_image.load()
                image = opened_image.copy()

        except (OSError, ValueError, UnidentifiedImageError) as exc:
            raise ValueError(
                f"Не вдалося прочитати зображення: {exc}"
            ) from exc

        has_transparency = (
            image.mode in {"RGBA", "LA"}
            or (
                image.mode == "P"
                and "transparency" in image.info
            )
        )

        if has_transparency:
            rgba_image = image.convert("RGBA")

            background = Image.new(
                "RGB",
                rgba_image.size,
                (255, 255, 255),
            )

            background.paste(
                rgba_image,
                mask=rgba_image.getchannel("A"),
            )

            image = background

        elif image.mode != "RGB":
            image = image.convert("RGB")

        try:
            image.save(
                destination,
                format="PDF",
                resolution=150.0,
            )

        except OSError as exc:
            raise ValueError(
                f"Не вдалося створити PDF: {exc}"
            ) from exc

        return destination
