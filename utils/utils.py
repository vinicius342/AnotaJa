# Estilos para CustomerSearchWidget
CUSTOMER_LINEEDIT_BASE_STYLE = (
    "QLineEdit {"
    "padding: 8px;"
    "border: 2px solid #ccc;"
    "border-radius: 4px 4px 0 0;"
    "font-size: 14px;"
    "background-color: white;"
    "}"
    "QLineEdit:focus {"
    "border-color: #2a7;"
    "}"
)

CUSTOMER_LINEEDIT_NO_BORDER_STYLE = (
    "QLineEdit {"
    "padding: 8px;"
    "border: 2px solid #ccc;"
    "border-radius: 4px 4px 0 0;"
    "font-size: 14px;"
    "background-color: white;"
    "border-bottom: none;"
    "}"
    "QLineEdit:focus {"
    "border-color: #2a7;"
    "border-bottom: none;"
    "}"
)

SUGGESTIONS_LIST_BASE_STYLE = (
    "QListWidget {"
    "border: none;"
    "border-radius: 0 0 4px 4px;"
    "background-color: white;"
    "selection-background-color: #e0e0e0;"
    "selection-color: #222;"
    "outline: none;"
    "}"
    "QListWidget::item {"
    "padding: 8px;"
    "border-bottom: 1px solid #eee;"
    "}"
    "QListWidget::item:hover {"
    "background-color: #f0f8ff;"
    "}"
    "QListWidget::item:selected {"
    "background-color: #e0e0e0;"
    "color: #222;"
    "}"
)
"""
Utilitários gerais para a aplicação AnotaJa.
"""

# Estilo CSS para a aplicação
STYLE = """
QMainWindow {
    background-color: #ffffff;
}

QDialog {
    background-color: #ffffff;
}

QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #222;
    background-color: #ffffff;
}

QPushButton {
    background-color: #2a7;
    border: none;
    color: #fff;
    padding: 8px;
    text-align: center;
    font-size: 14px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #1ec989;
    color: #fff;
}

QPushButton:pressed {
    background-color: #288f68;
    color: #fff;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QLineEdit {
    padding: 8px;
    border: 2px solid #ccc;
    border-radius: 4px 4px 0 0;
    font-size: 14px;
    background-color: #ffffff;
    color: #222;
}

QLineEdit:focus {
    border-color: #2a7;
}

QTableWidget {
    background-color: #ffffff;
    gridline-color: #ddd;
    selection-background-color: #e8f5e8;
    color: #222;
}

QTableWidget::item {
    padding: 5px;
    background-color: #ffffff;
    color: #222;
}

QTableWidget::item:selected {
    background-color: #2a7;
    color: #fff;
}

QComboBox {
    border: 2px solid #ddd;
    border-radius: 4px;
    padding: 5px;
    min-width: 6em;
    background-color: #ffffff;
    color: #222;
}

QComboBox:hover {
    border-color: #2a7;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: darkgray;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #222;
}

QListWidget {
    background-color: #ffffff;
    color: #222;
}

QListWidget::item {
    background-color: #ffffff;
    color: #222;
}

QListWidget::item:selected {
    background-color: #2a7;
    color: #fff;
}

QMenu {
    background-color: #ffffff;
    color: #222;
}

QMenu::item {
    background-color: #ffffff;
    color: #222;
}

QMenu::item:selected {
    background-color: #2a7;
    color: #fff;
}

QLabel {
    color: #333333;
    background-color: #ffffff;
    padding: 4px 4px;
    margin: 0px 0px;
}

QTabWidget::pane {
    border: 1px solid #ddd;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f0f0f0;
    padding: 8px 12px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #222;
}

QTabBar::tab:selected {
    background-color: #2a7;
    color: #fff;
    border-top: 2px solid #2a7;
}

QTabBar::tab:hover {
    background-color: #3bb75e;
    color: #fff;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #ddd;
}

QMenuBar, QMenuBar::item {
    background-color: #ffffff;
    color: #222;
}

QMenuBar::item {
    padding: 8px 12px;
}

QMenuBar::item:selected {
    background-color: #2a7;
    color: #fff;
}

/* Componentes adicionais */

QFrame {
    background-color: #ffffff;
    border: none;
    color: #222;
}

QGroupBox {
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-top: 10px;
    padding: 6px;
    background-color: #ffffff;
    color: #222;
}

QGroupBox:title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    color: #333;
    background-color: transparent;
}

QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #ccc;
    color: #333;
}

QScrollBar:vertical, QScrollBar:horizontal {
    background: #ffffff;
    border: none;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #ccc;
    border-radius: 6px;
}

QScrollBar::handle:hover {
    background: #aaa;
}

QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
    height: 0px;
}

QCheckBox {
    spacing: 6px;
    color: #222;
    background-color: #ffffff;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #888;
    border-radius: 3px;
    background: #fff;
}
QCheckBox::indicator:checked {
    background: #2a7;
    border: 1px solid #2a7;
}

QRadioButton {
    spacing: 6px;
    color: #222;
    background-color: #ffffff;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #222;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #2a7;
}
"""
