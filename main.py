import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MacToolsForConvert")
        self.resize(800, 600)

        label = QLabel("MacTools — файловий інструментарій")
        label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                padding: 20px;
            }
        """)

        self.setCentralWidget(label)


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("MacTools")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())