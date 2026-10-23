"""Централізовані стилі інтерфейсу MacTools."""


DARK_THEME = """
QMainWindow {
    background-color: #18191c;
    color: #f1f3f4;
}

QLabel#headerLabel {
    color: #f1f3f4;
    font-size: 25px;
    font-weight: 700;
}

QLabel#subtitleLabel {
    color: #aeb4be;
    font-size: 13px;
}

QLabel#sectionLabel {
    color: #f1f3f4;
    font-size: 15px;
    font-weight: 600;
}

QFrame#dropArea {
    background-color: #202124;
    border: 2px dashed #50545c;
    border-radius: 16px;
}

QFrame#dropArea[dragActive="true"] {
    background-color: #263448;
    border: 2px dashed #78a9fa;
}

QLabel#dropIcon {
    color: #8ab4f8;
    font-size: 34px;
    border: none;
}

QLabel#dropTitle {
    color: #f1f3f4;
    font-size: 17px;
    font-weight: 600;
    border: none;
}

QLabel#dropDescription {
    color: #aeb4be;
    font-size: 12px;
    border: none;
}

QPushButton#browseButton {
    color: #ffffff;
    background-color: #3c78d8;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#browseButton:hover {
    background-color: #4c89e8;
}

QPushButton#browseButton:pressed {
    background-color: #2c5fb0;
}

QListWidget#filesList {
    background-color: #202124;
    color: #f1f3f4;
    border: 1px solid #383b40;
    border-radius: 10px;
    padding: 6px;
    outline: none;
    alternate-background-color: #25272b;
}

QListWidget#filesList::item {
    padding: 8px;
    border-radius: 5px;
}

QListWidget#filesList::item:selected {
    background-color: #304b70;
}

QStatusBar {
    color: #aeb4be;
    background-color: #18191c;
}
QPushButton#clearButton {
    color: #f1f3f4;
    background-color: #303238;
    border: 1px solid #454850;
    border-radius: 8px;
    padding: 9px 14px;
    font-size: 12px;
}

QPushButton#clearButton:hover {
    background-color: #41444b;
}

QPushButton#clearButton:pressed {
    background-color: #25272b;
}

QTabBar#categoryTabs::tab {
    color: #aeb4be;
    background-color: transparent;
    border: none;
    padding: 10px 16px;
    margin-right: 4px;
}

QTabBar#categoryTabs::tab:selected {
    color: #8ab4f8;
    background-color: #263448;
    border-bottom: 2px solid #8ab4f8;
}

QTabBar#categoryTabs::tab:hover:!selected {
    color: #f1f3f4;
    background-color: #25272b;
}

QFrame#filesPanel,
QFrame#infoPanel {
    background-color: #202124;
    border: 1px solid #383b40;
    border-radius: 10px;
}

QLabel#countLabel {
    color: #aeb4be;
    background-color: #303238;
    border-radius: 9px;
    padding: 3px 8px;
}

QLabel#infoName {
    color: #f1f3f4;
    font-size: 14px;
    font-weight: 600;
}

QLabel#infoValue {
    color: #b9bec7;
    font-size: 12px;
}

QLabel#infoPath {
    color: #8ab4f8;
    font-size: 11px;
}
"""


LIGHT_THEME = """
QMainWindow {
    background-color: #f5f6f8;
    color: #202124;
}

QLabel#headerLabel {
    color: #202124;
    font-size: 25px;
    font-weight: 700;
}

QLabel#subtitleLabel {
    color: #60656f;
    font-size: 13px;
}

QLabel#sectionLabel {
    color: #202124;
    font-size: 15px;
    font-weight: 600;
}

QFrame#dropArea {
    background-color: #ffffff;
    border: 2px dashed #c4c9d1;
    border-radius: 16px;
}

QFrame#dropArea[dragActive="true"] {
    background-color: #e8f0fe;
    border: 2px dashed #3c78d8;
}

QLabel#dropIcon {
    color: #3c78d8;
    font-size: 34px;
    border: none;
}

QLabel#dropTitle {
    color: #202124;
    font-size: 17px;
    font-weight: 600;
    border: none;
}

QLabel#dropDescription {
    color: #60656f;
    font-size: 12px;
    border: none;
}

QPushButton#browseButton {
    color: #ffffff;
    background-color: #3c78d8;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#browseButton:hover {
    background-color: #4c89e8;
}

QPushButton#browseButton:pressed {
    background-color: #2c5fb0;
}

QListWidget#filesList {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #d5d8de;
    border-radius: 10px;
    padding: 6px;
    outline: none;
    alternate-background-color: #f0f1f4;
}

QListWidget#filesList::item {
    padding: 8px;
    border-radius: 5px;
}

QListWidget#filesList::item:selected {
    background-color: #d8e6fb;
    color: #202124;
}

QStatusBar {
    color: #60656f;
    background-color: #f5f6f8;
}
QPushButton#clearButton {
    color: #202124;
    background-color: #e9ebef;
    border: 1px solid #d5d8de;
    border-radius: 8px;
    padding: 9px 14px;
    font-size: 12px;
}

QPushButton#clearButton:hover {
    background-color: #dfe3e9;
}

QPushButton#clearButton:pressed {
    background-color: #d2d7df;
}

QTabBar#categoryTabs::tab {
    color: #60656f;
    background-color: transparent;
    border: none;
    padding: 10px 16px;
    margin-right: 4px;
}

QTabBar#categoryTabs::tab:selected {
    color: #245db5;
    background-color: #e8f0fe;
    border-bottom: 2px solid #3c78d8;
}

QTabBar#categoryTabs::tab:hover:!selected {
    color: #202124;
    background-color: #eef0f3;
}

QFrame#filesPanel,
QFrame#infoPanel {
    background-color: #ffffff;
    border: 1px solid #d5d8de;
    border-radius: 10px;
}

QLabel#countLabel {
    color: #60656f;
    background-color: #eef0f3;
    border-radius: 9px;
    padding: 3px 8px;
}

QLabel#infoName {
    color: #202124;
    font-size: 14px;
    font-weight: 600;
}

QLabel#infoValue {
    color: #60656f;
    font-size: 12px;
}

QLabel#infoPath {
    color: #245db5;
    font-size: 11px;
}
"""


THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}