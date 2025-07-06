style = """
/* Python Dark Theme QSS */

/* Janela Principal */
QMainWindow {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: none;
}

/* Widget Base */
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
}

/* Borda fina branca nas telas de impressão */
QWidget#TelaImpressao {
    border: 2px solid #fff;
    border-radius: 8px;
    margin: 8px;
    background-color: #232323;
}

/* Menu Bar */
QMenuBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-bottom: 1px solid #3d3d3d;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #3776ab;
    color: #ffffff;
}

QMenuBar::item:pressed {
    background-color: #2c5f87;
}

/* Menu */
QMenu {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 16px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #3776ab;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #3d3d3d;
    margin: 4px 8px;
}

/* Tool Bar */
QToolBar {
    background-color: #2d2d2d;
    border: none;
    spacing: 2px;
    padding: 4px;
}

QToolButton {
    background-color: transparent;
    color: #e0e0e0;
    border: none;
    padding: 6px;
    border-radius: 4px;
    min-width: 20px;
    min-height: 20px;
}

QToolButton:hover {
    background-color: #3776ab;
    color: #ffffff;
}

QToolButton:pressed {
    background-color: #2c5f87;
}

/* Status Bar */
QStatusBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-top: 1px solid #3d3d3d;
    padding: 4px;
}

/* Botões */
QPushButton {
    background-color: #3776ab;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #4a8bc2, stop: 1 #3776ab);
}

QPushButton:pressed {
    background-color: #2c5f87;
}

QPushButton:disabled {
    background-color: #404040;
    color: #808080;
}

/* Campos de Texto */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #252525;
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #3776ab;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #3776ab;
    border-width: 3px; /* Borda mais grossa para destacar */
}

/* ComboBox */
QComboBox {
    background-color: #252525;
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #3776ab;
}

QComboBox:focus {
    border-color: #3776ab;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}

QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIg\
        dmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczL\
            m9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDEuNUw2IDYuNUwxMSAxLjUiIHN0cm\
                9rZT0iI2UwZTBlMCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0
                icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    selection-background-color: #3776ab;
    outline: none;
}

/* Checkbox */
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3d3d3d;
    border-radius: 4px;
    background-color: #252525;
}

QCheckBox::indicator:hover {
    border-color: #3776ab;
}

QCheckBox::indicator:checked {
    background-color: #3776ab;
    border-color: #3776ab;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSI\
        gdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3Lnc\
            zLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxLjUiIHN\
                0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWN\
                    hcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}

/* Radio Button */
QRadioButton {
    color: #e0e0e0;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3d3d3d;
    border-radius: 9px;
    background-color: #252525;
}

QRadioButton::indicator:hover {
    border-color: #3776ab;
}

QRadioButton::indicator:checked {
    background-color: #3776ab;
    border-color: #3776ab;
}

QRadioButton::indicator:checked::after {
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 3px;
    background-color: #ffffff;
    position: absolute;
    top: 6px;
    left: 6px;
}

/* Slider */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background-color: #3d3d3d;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #3776ab;
    border: none;
    width: 20px;
    height: 20px;
    border-radius: 10px;
    margin: -7px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #4a8bc2;
}

QSlider::handle:horizontal:pressed {
    background-color: #2c5f87;
}

QSlider::sub-page:horizontal {
    background-color: #3776ab;
    border-radius: 3px;
}

/* Progress Bar */
QProgressBar {
    background-color: #3d3d3d;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #e0e0e0;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #3776ab;
    border-radius: 6px;
}

/* Scroll Bar */
QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 14px;
    border-radius: 7px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3776ab;
    border-radius: 7px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a8bc2;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #2d2d2d;
    height: 14px;
    border-radius: 7px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #3776ab;
    border-radius: 7px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4a8bc2;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* Tab Widget */
QTabWidget::pane {
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    background-color: #252525;
    top: -1px;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #3776ab;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #404040;
}

/* List Widget */
QListWidget {
    background-color: #252525;
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    outline: none;
    selection-background-color: #3776ab;
}

QListWidget::item {
    padding: 6px;
    border-bottom: 1px solid #3d3d3d;
}

QListWidget::item:selected {
    background-color: #3776ab;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #404040;
}

/* Tree Widget */
QTreeWidget {
    background-color: #252525;
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    outline: none;
    selection-background-color: #3776ab;
}

QTreeWidget::item {
    padding: 4px;
    border-bottom: 1px solid #333333;
}

QTreeWidget::item:selected {
    background-color: #3776ab;
    color: #ffffff;
}

QTreeWidget::item:hover {
    background-color: #404040;
}

/* Table Widget */
QTableWidget {
    background-color: #252525;
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    gridline-color: #3d3d3d;
    selection-background-color: #3776ab;
}

QHeaderView::section {
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 8px;
    border: 1px solid #3d3d3d;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #404040;
}

/* Splitter */
QSplitter::handle {
    background-color: #3d3d3d;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

/* Tooltip */
QToolTip {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3776ab;
    border-radius: 4px;
    padding: 6px;
    font-size: 11px;
}

/* Group Box */
QGroupBox {
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: #3776ab;
}

/* Spin Box */
QSpinBox, QDoubleSpinBox {
    background-color: #252525;
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #3776ab;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3776ab;
    border-width: 3px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border: none;
    background-color: #3d3d3d;
    border-top-right-radius: 4px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #3776ab;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border: none;
    background-color: #3d3d3d;
    border-bottom-right-radius: 4px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #3776ab;
}

/* Dial */
QDial {
    background-color: #252525;
    color: #3776ab;
}
"""
