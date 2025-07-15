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
    "border-color: #4CAF50;"
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
    "border-color: #4CAF50;"
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
    background-color: #f5f5f5;
}

QDialog {
    background-color: #ffffff;
}

QPushButton {
    background-color: #4CAF50;
    border: none;
    color: #222;
    padding: 8px 16px;
    text-align: center;
    font-size: 14px;
    margin: 4px 2px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #45a049;
}

QPushButton:pressed {
    background-color: #3d8b40;
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
    background-color: white;
}
QLineEdit:focus {
    border-color: #4CAF50;
}

QTableWidget {
    gridline-color: #ddd;
    selection-background-color: #e8f5e8;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #4CAF50;
    color: #222;
}

QComboBox {
    border: 2px solid #ddd;
    border-radius: 4px;
    padding: 5px;
    min-width: 6em;
}

QComboBox:hover {
    border-color: #4CAF50;
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

QComboBox, QComboBox QAbstractItemView {
    color: #222;
    background-color: white;
}

QListWidget, QListWidget::item {
    color: #222;
    background-color: white;
}

QListWidget::item:selected {
    background-color: #4CAF50;
    color: #fff;
}

QMenu, QMenu::item {
    color: #222;
    background-color: white;
}

QMenu::item:selected {
    background-color: #4CAF50;
    color: #fff;
}

QLabel {
    color: #333333;
    padding: 4px 4px;
    margin: 0px 0px;
}

QTabWidget::pane {
    border: 1px solid #ddd;
    background-color: white;
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
    background-color: #4CAF50;
    color: #222;
    border-top: 2px solid #388e3c;
}

QTabBar::tab:hover {
    background-color: #c8e6c9;
}

QMenuBar {
    background-color: #f0f0f0;
    border-bottom: 1px solid #ddd;
}

QMenuBar, QMenuBar::item {
    color: #222;
}

QMenuBar::item {
    padding: 8px 12px;
}

QMenuBar::item:selected {
    background-color: #4CAF50;
    color: black;
}
"""
