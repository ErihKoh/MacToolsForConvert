"""Конвертер зображень для MacTools."""

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from src.converters.base import BaseConverter
from src.converters.formats import FORMAT_MAP


class ImageConverter(BaseConverter):
    """Конвертує зображення між JPEG, PNG, WebP, TIFF і BMP."""

    JPEG_QUALITY = 95
    WEBP_QUALITY = 90

    @property
    def name(self) -> str:
        """Назва конвертера."""
        return "Image Converter"

    @property
    def supported_input_formats(self) -> set[str]:
        """Підтримувані формати вхідних зображень."""
        return set(FORMAT_MAP)

    @property
    def supported_output_formats(self) -> set[str]:
        """Підтримувані формати вихідних зображень."""
        return set(FORMAT_MAP)

    def convert(
            self,
            source: Path,
            destination: Path,
    ) -> Path:
        """Конвертує зображення та повертає шлях до результату.

        Формат результату визначається розширенням destination.
        Оригінальний файл і наявні файли призначення не змінюються.
        """

        source = Path(source).expanduser()
        destination = Path(destination).expanduser()

        # Перевіряємо наявність вхідного файла.
        if not source.is_file():
            raise FileNotFoundError(
                f"Вхідний файл не знайдено: {source}"
            )

        # Визначаємо формати за розширеннями.
        source_format = source.suffix.lower().lstrip(".")
        destination_format = destination.suffix.lower().lstrip(".")

        if source_format not in self.supported_input_formats:
            raise ValueError(
                "Непідтримуваний вхідний формат: "
                f"{source.suffix or '(без розширення)'}"
            )

        if destination_format not in self.supported_output_formats:
            raise ValueError(
                "Непідтримуваний вихідний формат: "
                f"{destination.suffix or '(без розширення)'}"
            )

        # Забороняємо перезапис оригіналу.
        if source.resolve() == destination.resolve():
            raise ValueError(
                "Вихідний файл не може збігатися з оригіналом."
            )

        # Забороняємо перезапис будь-якого наявного файла.
        if destination.exists():
            raise FileExistsError(
                f"Файл призначення вже існує: {destination}"
            )

        # Папка призначення має існувати.
        if not destination.parent.is_dir():
            raise FileNotFoundError(
                f"Папка призначення не існує: {destination.parent}"
            )

        # Відкриваємо зображення та застосовуємо EXIF-орієнтацію.
        try:
            with Image.open(source) as opened_image:
                opened_image.load()
                image = ImageOps.exif_transpose(opened_image)
                image = image.copy()

        except UnidentifiedImageError as exc:
            raise ValueError(
                f"Файл не є розпізнаваним зображенням: {source.name}"
            ) from exc

        except OSError as exc:
            raise ValueError(
                f"Не вдалося прочитати зображення: {exc}"
            ) from exc

        # Перетворюємо розширення на формат Pillow.
        output_format = FORMAT_MAP[destination_format]

        # Зберігаємо зображення у вибраному форматі.
        if output_format == "JPEG":
            image = self._prepare_for_jpeg(image)

            image.save(
                destination,
                format="JPEG",
                quality=self.JPEG_QUALITY,
                optimize=True,
            )

        elif output_format == "WEBP":
            image.save(
                destination,
                format="WEBP",
                quality=self.WEBP_QUALITY,
                method=4,
            )

        else:
            image.save(
                destination,
                format=output_format,
            )

        return destination

    @staticmethod
    def _prepare_for_jpeg(image: Image.Image) -> Image.Image:
        """Готує зображення до збереження у JPEG.

        JPEG не підтримує прозорість. Прозорі ділянки
        накладаються на білий фон.
        """

        has_transparency = (
                image.mode in ("RGBA", "LA")
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

            return background

        if image.mode != "RGB":
            return image.convert("RGB")

        return image
