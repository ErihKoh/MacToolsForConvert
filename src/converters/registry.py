"""Реєстр конвертерів MacTools."""

from src.converters.base import BaseConverter


class ConverterRegistry:
    """Зберігає конвертери та знаходить відповідний для операції."""

    def __init__(self) -> None:
        self._converters: dict[str, BaseConverter] = {}

    @property
    def converters(self) -> dict[str, BaseConverter]:
        """Повертає копію реєстру конвертерів."""

        return self._converters.copy()

    def register(self, converter: BaseConverter) -> None:
        """Реєструє конвертер за його назвою."""

        key = converter.name.strip().casefold()

        if not key:
            raise ValueError("Назва конвертера не може бути порожньою.")

        if key in self._converters:
            raise ValueError(
                f"Конвертер із назвою '{converter.name}' уже зареєстрований."
            )

        self._converters[key] = converter

    def unregister(self, name: str) -> bool:
        """Видаляє конвертер за назвою.

        Повертає True, якщо конвертер знайдено та видалено.
        """

        key = name.strip().casefold()

        if key not in self._converters:
            return False

        del self._converters[key]
        return True

    def get(self, name: str) -> BaseConverter | None:
        """Знаходить конвертер за назвою."""

        return self._converters.get(name.strip().casefold())

    def find(
        self,
        source_format: str,
        destination_format: str,
    ) -> BaseConverter | None:
        """Знаходить перший конвертер для заданої пари форматів."""

        for converter in self._converters.values():
            if converter.can_convert(
                source_format,
                destination_format,
            ):
                return converter

        return None

    def clear(self) -> None:
        """Видаляє всі зареєстровані конвертери."""

        self._converters.clear()

    def __len__(self) -> int:
        """Повертає кількість зареєстрованих конвертерів."""

        return len(self._converters)