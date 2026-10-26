"""Централізовані визначення форматів файлів MacTools."""

# Відповідність розширень форматам Pillow.
FORMAT_MAP: dict[str, str] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "tif": "TIFF",
    "tiff": "TIFF",
    "bmp": "BMP",
}

# Групи форматів.
IMAGE_FORMATS: frozenset[str] = frozenset(FORMAT_MAP)

PDF_FORMATS: frozenset[str] = frozenset({"pdf"})

DOCUMENT_FORMATS: frozenset[str] = frozenset({
    "docx",
    "rtf",
    "txt",
})

# Вхідні відеоформати.
VIDEO_INPUT_FORMATS: frozenset[str] = frozenset({
    "mp4",
    "mts",
    "m2ts",
    "mov",
    "mkv",
    "avi",
    "webm",
    "mpeg",
    "mpg",
    "ts",
    "3gp",
})

# Вихідні відеоформати першої версії.
# Спочатку реалізуємо конвертацію в MP4.
VIDEO_OUTPUT_FORMATS: frozenset[str] = frozenset({
    "mp4",
})

# Усі відеоформати, які потрібно враховувати в інтерфейсі.
VIDEO_FORMATS: frozenset[str] = (
    VIDEO_INPUT_FORMATS | VIDEO_OUTPUT_FORMATS
)

# Формати, які PDFConverter може створювати з PDF.
PDF_OUTPUT_IMAGE_FORMATS: frozenset[str] = frozenset({
    "png",
    "jpg",
    "jpeg",
})

# Назви форматів для відображення в інтерфейсі.
FORMAT_DISPLAY_NAMES: dict[str, str] = {
    "jpg": "JPEG Image",
    "jpeg": "JPEG Image",
    "png": "PNG Image",
    "webp": "WebP Image",
    "tif": "TIFF Image",
    "tiff": "TIFF Image",
    "bmp": "BMP Image",
    "pdf": "PDF Document",
    "docx": "Word Document",
    "rtf": "Rich Text Format",
    "txt": "Plain Text",
    "mp4": "MP4 Video",
    "mts": "AVCHD Video (MTS)",
    "m2ts": "AVCHD Video (M2TS)",
    "mov": "QuickTime Video",
    "mkv": "Matroska Video",
    "avi": "AVI Video",
    "webm": "WebM Video",
    "mpeg": "MPEG Video",
    "mpg": "MPEG Video",
    "ts": "MPEG Transport Stream",
    "3gp": "3GPP Video",
    "heic": "HEIC Image (iPhone)",
    "heif": "HEIF Image",
}


def normalize_format(file_format: str) -> str:
    """Нормалізує розширення формату файлу."""

    return file_format.strip().lower().lstrip(".")


def get_format_display_name(file_format: str) -> str:
    """Повертає назву формату для інтерфейсу."""

    normalized = normalize_format(file_format)

    return FORMAT_DISPLAY_NAMES.get(
        normalized,
        normalized.upper() or "Невідомий формат",
    )