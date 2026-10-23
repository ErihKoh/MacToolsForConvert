"""Базовий інтерфейс конвертерів MacTools."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseConverter(ABC):
    """Базовий клас для всіх конвертерів."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Повертає назву конвертера."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_input_formats(self) -> set[str]:
        """Повертає підтримувані формати вхідних файлів."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_output_formats(self) -> set[str]:
        """Повертає підтримувані формати вихідних файлів."""
        raise NotImplementedError

    @abstractmethod
    def convert(
        self,
        source: Path,
        destination: Path,
    ) -> Path:
        """Конвертує файл і повертає шлях до результату."""
        raise NotImplementedError

    def can_convert(
        self,
        source_format: str,
        destination_format: str,
    ) -> bool:
        """Перевіряє, чи підтримує конвертер потрібну пару форматів."""

        source_format = source_format.lower().lstrip(".")
        destination_format = destination_format.lower().lstrip(".")

        input_formats = {
            fmt.lower().lstrip(".")
            for fmt in self.supported_input_formats
        }
        output_formats = {
            fmt.lower().lstrip(".")
            for fmt in self.supported_output_formats
        }

        return (
            source_format in input_formats
            and destination_format in output_formats
        )