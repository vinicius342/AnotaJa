"""
Utilitários gerais para a aplicação AnotaJa.
"""

# Estilo CSS para a aplicação
style = """
QMainWindow {
    background-color: #f5f5f5;
}

QDialog {
    background-color: #ffffff;
}

QPushButton {
    background-color: #4CAF50;
    border: none;
    color: white;
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
    border: 2px solid #ddd;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
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
    color: white;
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

QLabel {
    color: #333333;
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
}

QTabBar::tab:selected {
    background-color: #4CAF50;
    color: white;
}

QTabBar::tab:hover {
    background-color: #e0e0e0;
}

QMenuBar {
    background-color: #f0f0f0;
    border-bottom: 1px solid #ddd;
}

QMenuBar::item {
    padding: 8px 12px;
}

QMenuBar::item:selected {
    background-color: #4CAF50;
    color: white;
}

QMenu {
    background-color: white;
    border: 1px solid #ddd;
}

QMenu::item {
    padding: 8px 20px;
}

QMenu::item:selected {
    background-color: #4CAF50;
    color: white;
}
"""
