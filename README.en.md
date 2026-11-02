# MacToolsForConvert

**MacTools** is a desktop application for macOS designed to convert images, PDF files, text documents, video, audio, and ebooks.

The application is built with Python and PySide6. It processes files locally and uses external tools for selected conversion operations.

## Features

- PySide6 graphical user interface.
- Add files using drag and drop or a file selection dialog.
- Batch file conversion.
- Automatic detection of available output formats.
- File information display.
- Multiple file categories.
- Original file preservation.
- Protection against overwriting existing files.
- Temporary output files before publishing conversion results.
- Error handling and external process timeouts.

## Supported formats

### Images

Input formats:
- JPG / JPEG
- PNG
- WebP
- TIFF / TIF
- BMP
- HEIC / HEIF

Output formats:
- JPG / JPEG
- PNG
- WebP
- TIFF / TIF
- BMP

Image processing is handled by Pillow. HEIC/HEIF support is provided by pillow-heif.

### PDF

Supported operations:
- Images → PDF.
- PDF → PNG.
- PDF → JPG / JPEG.
- Multi-page PDF files can be exported as separate images.

PDF processing is handled by PyMuPDF.

### Text documents

Supported formats:
- DOCX
- TXT
- RTF

Supported conversions:
- DOCX ↔ TXT
- DOCX ↔ RTF
- TXT ↔ RTF
- DOCX → PDF

Text document conversions use the macOS system utility `textutil`.

DOCX-to-PDF conversion uses LibreOffice.

### Video

Input formats:
- MP4
- MTS
- M2TS
- MOV
- MKV
- AVI
- WebM
- MPEG
- MPG
- TS
- 3GP

Output format:
- MP4

Video conversion uses FFmpeg and ffprobe.

Video is encoded using H.264 and audio using AAC when the original streams cannot be copied without re-encoding.

### Audio

Supported formats:
- MP3
- WAV
- FLAC
- M4A
- AAC
- OGG
- OPUS

Conversion between the listed formats is supported.

Audio processing uses FFmpeg and ffprobe.

### Ebooks

Input formats:
- FB2
- EPUB
- PDF

Output formats:
- FB2
- EPUB

Supported conversions:
- FB2 → EPUB
- EPUB → FB2
- PDF → EPUB
- PDF → FB2

Ebook conversion is handled by Calibre.

**Note:** Scanned PDF files may require OCR. Built-in optical character recognition is not provided.

## Technologies and dependencies

Main technologies:
- Python 3.12
- PySide6 — graphical user interface.
- Pillow — image processing.
- pillow-heif — HEIC/HEIF support.
- PyMuPDF — PDF processing.

External tools:
- FFmpeg — video and audio conversion.
- ffprobe — media file analysis.
- Calibre — ebook conversion.
- LibreOffice — DOCX-to-PDF conversion.
- macOS textutil — text document conversion.

## Development environment setup

### Requirements

- macOS.
- Python 3.12.
- Homebrew for installing external tools.

Check the Python version:

```bash
python3.12 --version
```

### Clone the repository

```bash
git clone <repository-url>
cd MacToolsForConvert
```

### Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Install external tools

FFmpeg:

```bash
brew install ffmpeg
```

LibreOffice:

```bash
brew install --cask libreoffice
```

Calibre must be installed separately from its official website:

https://calibre-ebook.com/download

`textutil` is included with macOS.

The application uses external tool paths defined in the project configuration.

## Run the application

From the project root directory:

```bash
source .venv/bin/activate
python main.py
```

## Usage

1. Launch MacTools.
2. Add files by dragging them into the application or using the file selection button.
3. Select the files you want to convert.
4. Choose an output format.
5. Start the conversion.
6. Find the converted files in the destination folder.

Available output formats depend on the selected files and the availability of required external tools.

## File storage

By default, converted files are saved to:

```text
~/Documents/MacTools
```

Application cache:

```text
~/Library/Caches/MacTools
```

Original files are preserved. If a file with the same name already exists in the destination directory, the application does not overwrite it.

## Testing

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
MacToolsForConvert/
├── main.py
├── requirements.txt
├── README.md
├── README.en.md
├── src/
│   ├── config.py
│   ├── converters/
│   │   ├── base.py
│   │   ├── formats.py
│   │   ├── registry.py
│   │   ├── setup.py
│   │   ├── image_converter.py
│   │   ├── pdf_converter.py
│   │   ├── document_converter.py
│   │   ├── video_converter.py
│   │   ├── audio_converter.py
│   │   └── ebook_converter.py
│   ├── services/
│   │   ├── conversion_controller.py
│   │   ├── conversion_service.py
│   │   └── conversion_worker.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── conversion_panel.py
│   │   ├── drop_area.py
│   │   ├── file_info_panel.py
│   │   ├── file_list_controller.py
│   │   ├── file_list_panel.py
│   │   └── styles.py
│   └── utils/
│       ├── file_info.py
│       └── file_manager.py
└── tests/
```

## Troubleshooting

**Video or audio conversion is unavailable**

Check that FFmpeg and ffprobe are installed:

```bash
ffmpeg -version
ffprobe -version
```

**Ebook conversion is unavailable**

Make sure Calibre is installed and available at the path specified in the project configuration.

**DOCX-to-PDF conversion is unavailable**

Check the LibreOffice installation and the configured path to the `soffice` executable.

**Text document conversion is unavailable**

Check the macOS system utility:

```bash
/usr/bin/textutil -help
```

**HEIC/HEIF files cannot be opened**

Check that the Python dependency `pillow-heif` is installed.

## Development principles

- Local file processing.
- Original file preservation.
- No automatic file overwriting.
- Separation of the user interface and conversion logic.
- Modular project structure.
- Error handling.
- External process management.
- Automated testing.

## Version

**MacToolsForConvert 0.1.0**

Developed for macOS.
