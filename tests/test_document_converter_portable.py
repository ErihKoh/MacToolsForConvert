"""Платформонезалежні тести DocumentConverter.

Замість textutil і LibreOffice використовуються фальшиві скрипти,
тому тести працюють на будь-якій POSIX-системі (macOS, Linux).
"""

import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from src.converters.document_converter import DocumentConverter

MODULE = "src.converters.document_converter"

FAKE_SOFFICE_OK = """#!/bin/sh
prev=""
outdir=""
for arg in "$@"; do
  printf '%s\\n' "$arg" >> "$(dirname "$0")/args.txt"
  if [ "$prev" = "--outdir" ]; then outdir="$arg"; fi
  prev="$arg"
done
printf '%%PDF-1.4 fake' > "$outdir/unexpected_name.pdf"
"""

FAKE_SOFFICE_NO_OUTPUT = "#!/bin/sh\nexit 0\n"

FAKE_SOFFICE_FAIL = "#!/bin/sh\necho 'boom' >&2\nexit 3\n"

FAKE_SOFFICE_HANG = """#!/bin/sh
sleep 60 &
echo $! > "$(dirname "$0")/child.pid"
wait
"""


def _process_alive(pid: int) -> bool:
    """Повертає True, якщо процес існує і не є зомбі."""

    result = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    state = result.stdout.strip()
    return bool(state) and not state.startswith("Z")


@unittest.skipIf(
    sys.platform == "win32",
    "Потрібна POSIX-система.",
)
class TestDocumentConverterPortable(unittest.TestCase):
    """Перевіряє логіку запуску зовнішніх програм."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

        self.output = self.root / "out"
        self.output.mkdir()

        self.source = self.root / "sample.docx"
        self.source.write_bytes(b"not a real docx")

        self.converter = DocumentConverter()

    def _fake_soffice(self, script: str) -> Path:
        path = self.root / "fake_soffice"
        path.write_text(script, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def _args(self) -> list[str]:
        return (
            (self.root / "args.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        )

    def test_pdf_found_even_if_name_differs(self):
        fake = self._fake_soffice(FAKE_SOFFICE_OK)
        destination = self.output / "result.pdf"

        with patch(f"{MODULE}.LIBREOFFICE_PATH", fake):
            result = self.converter.convert(self.source, destination)

        self.assertEqual(result, destination)
        self.assertTrue(destination.is_file())
        self.assertGreater(destination.stat().st_size, 0)

    def test_libreoffice_uses_separate_profile_and_cleans_up(self):
        fake = self._fake_soffice(FAKE_SOFFICE_OK)
        destination = self.output / "result.pdf"

        with patch(f"{MODULE}.LIBREOFFICE_PATH", fake):
            self.converter.convert(self.source, destination)

        profile_args = [
            arg for arg in self._args()
            if arg.startswith("-env:UserInstallation=file://")
        ]
        self.assertEqual(len(profile_args), 1)

        profile_path = Path(
            profile_args[0].removeprefix("-env:UserInstallation=file://")
        )
        self.assertFalse(profile_path.exists())

        # У папці результатів не лишилось тимчасових папок.
        self.assertEqual(
            [p.name for p in self.output.iterdir()],
            ["result.pdf"],
        )

    def test_dash_prefixed_source_is_passed_as_absolute_path(self):
        fake = self._fake_soffice(FAKE_SOFFICE_OK)
        dashed = self.root / "-weird.docx"
        dashed.write_bytes(b"x")

        previous_cwd = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous_cwd)

        with patch(f"{MODULE}.LIBREOFFICE_PATH", fake):
            self.converter.convert(
                Path("-weird.docx"),
                self.output / "result.pdf",
            )

        # Останній аргумент — вхідний файл.
        source_arg = self._args()[-1]
        self.assertTrue(source_arg.startswith("/"))
        self.assertTrue(source_arg.endswith("/-weird.docx"))

    def test_missing_pdf_raises_value_error(self):
        fake = self._fake_soffice(FAKE_SOFFICE_NO_OUTPUT)

        with patch(f"{MODULE}.LIBREOFFICE_PATH", fake):
            with self.assertRaises(ValueError):
                self.converter.convert(
                    self.source,
                    self.output / "result.pdf",
                )

        self.assertEqual(list(self.output.iterdir()), [])

    def test_nonzero_exit_reports_stderr(self):
        fake = self._fake_soffice(FAKE_SOFFICE_FAIL)

        with patch(f"{MODULE}.LIBREOFFICE_PATH", fake):
            with self.assertRaisesRegex(ValueError, "boom"):
                self.converter.convert(
                    self.source,
                    self.output / "result.pdf",
                )

    def test_timeout_kills_child_processes(self):
        fake = self._fake_soffice(FAKE_SOFFICE_HANG)

        with patch(f"{MODULE}.LIBREOFFICE_PATH", fake), patch(
            f"{MODULE}.CONVERTER_TIMEOUT_SECONDS", 1
        ):
            with self.assertRaises(TimeoutError):
                self.converter.convert(
                    self.source,
                    self.output / "result.pdf",
                )

        child_pid = int(
            (self.root / "child.pid").read_text().strip()
        )

        deadline = time.monotonic() + 3
        while _process_alive(child_pid) and time.monotonic() < deadline:
            time.sleep(0.1)

        self.assertFalse(_process_alive(child_pid))
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
