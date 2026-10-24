"""Сервіс конвертації файлів MacTools."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.converters.registry import ConverterRegistry


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Результат конвертації одного файла."""

    source: Path
    destination: Path | None
    success: bool
    error: str | None = None


class ConversionService:
    """Координує конвертацію файлів через реєстр конвертерів."""

    def __init__(self, registry: ConverterRegistry) -> None:
        self._registry = registry

    def convert_file(
        self,
        source: str | Path,
        output_directory: str | Path,
        output_format: str,
        *,
        suffix: str = "_converted",
    ) -> ConversionResult:
        """Конвертує один файл у вибраний формат.

        Результат зберігається в output_directory.
        Оригінальний файл не змінюється.

        Якщо вихідний файл уже існує, підбирається інше ім'я.
        """

        source_path = Path(source).expanduser()
        output_path = Path(output_directory).expanduser()
        target_format = output_format.lower().lstrip(".")

        try:
            if not source_path.is_file():
                raise FileNotFoundError(
                    f"Вхідний файл не знайдено: {source_path}"
                )

            if not output_path.is_dir():
                raise FileNotFoundError(
                    f"Папка результатів не існує: {output_path}"
                )

            if not target_format:
                raise ValueError("Не вказано вихідний формат.")

            source_format = source_path.suffix.lower().lstrip(".")

            converter = self._registry.find(
                source_format,
                target_format,
            )

            if converter is None:
                raise ValueError(
                    "Немає конвертера для формату "
                    f"{source_format or '(без розширення)'} "
                    f"→ {target_format}."
                )

            destination = self._build_destination(
                source_path=source_path,
                output_directory=output_path,
                output_format=target_format,
                suffix=suffix,
            )

            converted_path = converter.convert(
                source_path,
                destination,
            )

            return ConversionResult(
                source=source_path,
                destination=converted_path,
                success=True,
            )

        except Exception as exc:
            return ConversionResult(
                source=source_path,
                destination=None,
                success=False,
                error=str(exc),
            )

    def convert_files(
        self,
        sources: Iterable[str | Path],
        output_directory: str | Path,
        output_format: str,
        *,
        suffix: str = "_converted",
    ) -> list[ConversionResult]:
        """Послідовно конвертує список файлів.

        Помилка окремого файла не зупиняє обробку решти.
        """

        results: list[ConversionResult] = []

        for source in sources:
            result = self.convert_file(
                source=source,
                output_directory=output_directory,
                output_format=output_format,
                suffix=suffix,
            )
            results.append(result)

        return results

    @staticmethod
    def _build_destination(
        source_path: Path,
        output_directory: Path,
        output_format: str,
        suffix: str,
    ) -> Path:
        """Створює вільне ім'я вихідного файла."""

        base_name = source_path.stem
        candidate = output_directory / (
            f"{base_name}{suffix}.{output_format}"
        )

        counter = 1

        while candidate.exists():
            candidate = output_directory / (
                f"{base_name}{suffix}_{counter}.{output_format}"
            )
            counter += 1

        return candidate