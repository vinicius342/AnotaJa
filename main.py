import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog,
                               QDialogButtonBox, QGridLayout, QLabel,
                               QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)

from log_utils import get_logger
from menu_edit import MenuEditWindow
from menu_registration import MenuRegistrationWindow
from printer import Printer
from utils import style

logger = get_logger(__name__)

DEFAULT_PRINTER = None


class AjustesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('AjustesDialog inicializado')
        self.setWindowTitle("Ajustes de Impressora")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Escolha a impressora padrão:")
        self.layout.addWidget(self.label)

        self.combo = QComboBox()
        self.printers = Printer.list_printers()
        for printer in self.printers:
            self.combo.addItem(printer.name)
        self.layout.addWidget(self.combo)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def get_selected_printer(self):
        idx = self.combo.currentIndex()
        logger.info(
            f'Impressora selecionada: {self.printers[idx].name if idx != -1 else None}')
        if idx != -1:
            return self.printers[idx]
        return None


class PrintThread(QThread):
    finished_signal = Signal(str)

    def __init__(self, printer, text):
        super().__init__()
        self.printer = printer
        self.text = text

    def run(self):
        logger.info(f'Iniciando impressão em {self.printer.name}')
        # Executa a impressão (pode ser bloqueante)
        self.printer.print(self.text)
        logger.info(f'Impressão finalizada em {self.printer.name}')
        self.finished_signal.emit(self.printer.name)


class PrintScreen(QWidget):
    def __init__(self, title):
        super().__init__()
        self.setProperty("class", "tela-impressao")
        self.setObjectName("TelaImpressao")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel(title)
        self.layout.addWidget(self.label)

        self.print_button = QPushButton("Imprimir Pedido")
        self.layout.addWidget(self.print_button)

        self.print_button.clicked.connect(self.handle_print)

    def handle_print(self):
        global DEFAULT_PRINTER
        if DEFAULT_PRINTER is not None:
            printer = DEFAULT_PRINTER
        else:
            QMessageBox.warning(
                self, "Erro",
                "Nenhuma impressora selecionada nas configurações.")
            return

        text = "Pedido #123\n1x X-Burguer\n1x Coca-Cola\nTotal: R$ 25,00"
        self.thread = PrintThread(printer, text)
        self.thread.finished_signal.connect(self.print_finished)
        self.thread.start()

    def print_finished(self, printer_name):
        QMessageBox.information(
            self, "Impressão",
            f"Pedido enviado para a impressora:\n{printer_name}")
        self.thread = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info('MainWindow inicializada')
        self.setWindowTitle("AnotaJá")

        # Menu bar com botão Ajustes
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        menu_menu = QMenu("Cardápio", self)
        cadastro_action = QAction("Cadastro", self)
        cadastro_action.triggered.connect(self.open_menu_registration)
        edicao_action = QAction("Edição", self)
        edicao_action.triggered.connect(self.open_menu_edit)
        ajustes_action = QAction("Ajustes", self)
        ajustes_action.triggered.connect(self.open_settings)
        menu_menu.addAction(cadastro_action)
        menu_menu.addAction(edicao_action)
        menubar.addMenu(menu_menu)
        menubar.addAction(ajustes_action)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        central_widget.setLayout(layout)

        # Criar 4 telas independentes
        self.screen1 = PrintScreen("Tela 1")
        self.screen2 = PrintScreen("Tela 2")
        self.screen3 = PrintScreen("Tela 3")
        self.screen4 = PrintScreen("Tela 4")

        layout.addWidget(self.screen1, 0, 0)
        layout.addWidget(self.screen2, 0, 1)
        layout.addWidget(self.screen3, 1, 0)
        layout.addWidget(self.screen4, 1, 1)

    def open_settings(self):
        global DEFAULT_PRINTER
        logger.info('Abrindo ajustes de impressora')
        dialog = AjustesDialog(self)
        # Seleciona a impressora padrão atual, se houver
        if DEFAULT_PRINTER is not None:
            for i, p in enumerate(dialog.printers):
                if p.name == DEFAULT_PRINTER.name:
                    dialog.combo.setCurrentIndex(i)
                    break
        if dialog.exec() == QDialog.Accepted:
            DEFAULT_PRINTER = dialog.get_selected_printer()
            if DEFAULT_PRINTER:
                QMessageBox.information(
                    self, "Ajustes",
                    f"Impressora padrão definida: {DEFAULT_PRINTER.name}"
                )

    def open_menu_registration(self):
        logger.info('Abrindo cadastro de cardápio')
        # Mantém referência à janela para evitar destruição prematura
        # Remove parent para janela independente
        self.menu_registration_window = MenuRegistrationWindow()
        self.menu_registration_window.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)  # Força aparecer na área de trabalho
        self.menu_registration_window.show()
        self.menu_registration_window.raise_()  # Traz para frente
        self.menu_registration_window.activateWindow()  # Ativa a janela

    def open_menu_edit(self):
        logger.info('Abrindo edição de cardápio')
        dialog = MenuEditWindow(self)
        dialog.show()


if __name__ == "__main__":
    logger.info('Aplicação iniciada')
    app = QApplication(sys.argv)

    app.setStyleSheet(style)
    window = MainWindow()
    window.showMaximized()
    logger.info('Janela principal exibida')
    sys.exit(app.exec())
