import os
import sys

from genericpath import exists
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QMainWindow,
                               QMenu, QMenuBar, QPushButton, QWidget)

from database.db import (get_customers, get_system_setting, init_db,
                         set_system_setting)
from ui.customer_management import CustomerManagementWindow
from ui.menu_edit import MenuEditWindow
from ui.menu_registration import MenuRegistrationWindow
from ui.neighborhood_management import NeighborhoodManagementWindow
from ui.order_screen import OrderScreen
from ui.settings_dialog import SettingsDialog
from utils.log_utils import get_logger
from utils.printer import Printer
from utils.utils import STYLE

# Adiciona o diretório do projeto ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

LOGGER = get_logger(__name__)

# Inicializa o banco de dados e cria as tabelas se necessário
init_db()
# Lista global de todos os clientes (nome, telefone)
ALL_CUSTOMERS = []
# Busca todos os clientes e salva apenas nome e telefone
ALL_CUSTOMERS = [(c[1], c[2]) for c in get_customers()]
LOGGER.info(f'{len(ALL_CUSTOMERS)} clientes carregados em ALL_CUSTOMERS')


class PrintThread(QThread):
    finished_signal = Signal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        printer = Printer.get_default_printer()
        if printer:
            LOGGER.info(f'Iniciando impressão em {printer.name}')
            # Executa a impressão (pode ser bloqueante)
            printer.print(self.text)
            LOGGER.info(f'Impressão finalizada em {printer.name}')
            self.finished_signal.emit(printer.name)
        else:
            LOGGER.warning('Nenhuma impressora configurada')
            self.finished_signal.emit('Impressora não configurada')


class MainWindow(QMainWindow):
    def update_all_customer_suggestions(self):
        """Atualiza sugestões de clientes em todas as telas OrderScreen."""
        # Primeiro atualiza a lista global
        global ALL_CUSTOMERS
        old_count = len(ALL_CUSTOMERS)
        ALL_CUSTOMERS = [(c[1], c[2]) for c in get_customers()]
        new_count = len(ALL_CUSTOMERS)
        LOGGER.info(
            f'Lista global atualizada: {old_count} -> {new_count} clientes')

        # Mostra alguns clientes para debug
        for i, customer in enumerate(ALL_CUSTOMERS[-3:]):
            LOGGER.info(f'Cliente {i}: {customer}')

        # Depois atualiza todas as telas
        for screen in self.screens:
            if hasattr(screen, 'customer_search') and \
               hasattr(screen.customer_search, 'load_customers'):
                LOGGER.info(f'Atualizando {screen.screen_title}')
                screen.customer_search.load_customers()

    def __init__(self):
        super().__init__()
        LOGGER.info('MainWindow inicializada')
        self.setWindowTitle("AnotaJá")

        # Define o ícone do app
        import os
        import sys

        from PySide6.QtGui import QIcon

        # Detecta se está rodando como executável PyInstaller
        if getattr(sys, 'frozen', False):
            # Executável PyInstaller
            base_path = sys._MEIPASS
        else:
            # Desenvolvimento
            base_path = os.path.dirname(__file__)

        icon_path = os.path.join(base_path, "ui", "icons", "main_icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        # Lê o número de telas configurado (padrão 4)
        self.num_screens = int(get_system_setting('num_order_screens', '4'))
        LOGGER.info(f'Configurado para {self.num_screens} telas de pedido')

        # Menu bar com botão Ajustes
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        menu_menu = QMenu("Cardápio", self)
        cadastro_action = QAction("Cadastro", self)
        cadastro_action.triggered.connect(self.open_menu_registration)
        edicao_action = QAction("Edição", self)
        edicao_action.triggered.connect(self.open_menu_edit)
        menu_menu.addAction(cadastro_action)
        menu_menu.addAction(edicao_action)
        menubar.addMenu(menu_menu)

        # Menu de Clientes
        cliente_menu = QMenu("Cliente", self)
        gerenciar_cliente_action = QAction("Gerenciar Clientes", self)
        gerenciar_cliente_action.triggered.connect(
            self.open_customer_management)
        cliente_menu.addAction(gerenciar_cliente_action)

        bairros_action = QAction("Gerenciar Bairros", self)
        bairros_action.triggered.connect(self.open_neighborhood_management)
        cliente_menu.addAction(bairros_action)
        menubar.addMenu(cliente_menu)

        # Menu de Ajustes
        ajustes_action = QAction("Ajustes", self)
        ajustes_action.triggered.connect(self.open_settings)
        menubar.addAction(ajustes_action)

        self.setup_ui()

    def setup_ui(self):
        """Configura a interface baseada no número de telas"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        central_widget.setLayout(layout)

        # Cria as telas de pedido baseado na configuração
        self.screens = []
        for i in range(self.num_screens):
            # Se são 3 telas, usar layout de uma coluna para OrderScreen
            use_single_column = (self.num_screens == 3)
            screen = OrderScreen(f"Pedido {i+1}", customers=ALL_CUSTOMERS,
                                 single_column_layout=use_single_column)
            self.screens.append(screen)

        # Configura o layout baseado no número de telas
        if self.num_screens == 1:
            layout.addWidget(self.screens[0], 0, 0)
        elif self.num_screens == 2:
            layout.addWidget(self.screens[0], 0, 0)
            layout.addWidget(self.screens[1], 0, 1)
            # Linha vertical entre as telas
            vline = QFrame()
            vline.setFrameShape(QFrame.VLine)
            vline.setFrameShadow(QFrame.Sunken)
            vline.setLineWidth(2)
            vline.setStyleSheet(
                "QFrame { border-left: 1px solid #282e39; margin: 0; }")
            layout.addWidget(vline, 0, 1)
        elif self.num_screens == 3:
            # Layout horizontal (uma linha com 3 colunas)
            layout.addWidget(self.screens[0], 0, 0)
            layout.addWidget(self.screens[1], 0, 2)
            layout.addWidget(self.screens[2], 0, 4)
            # Linhas verticais entre as telas
            vline1 = QFrame()
            vline1.setFrameShape(QFrame.VLine)
            vline1.setFrameShadow(QFrame.Sunken)
            vline1.setLineWidth(2)
            vline1.setStyleSheet(
                "QFrame { border-left: 1px solid #bbb; margin: 0; }")
            layout.addWidget(vline1, 0, 1)

            vline2 = QFrame()
            vline2.setFrameShape(QFrame.VLine)
            vline2.setFrameShadow(QFrame.Sunken)
            vline2.setLineWidth(2)
            vline2.setStyleSheet(
                "QFrame { border-left: 1px solid #bbb; margin: 0; }")
            layout.addWidget(vline2, 0, 3)
        elif self.num_screens == 4:
            # Layout em grade 2x2
            layout.addWidget(self.screens[0], 0, 0)
            layout.addWidget(self.screens[1], 0, 2)
            layout.addWidget(self.screens[2], 2, 0)
            layout.addWidget(self.screens[3], 2, 2)

            # Linha vertical
            vline = QFrame()
            vline.setFrameShape(QFrame.VLine)
            vline.setFrameShadow(QFrame.Sunken)
            vline.setLineWidth(2)
            vline.setStyleSheet(
                "QFrame { border-left: 1px solid #282e39; margin: 0; }")
            layout.addWidget(vline, 0, 1, 3, 1)

            # Linha horizontal
            hline = QFrame()
            hline.setFrameShape(QFrame.HLine)
            hline.setFrameShadow(QFrame.Sunken)
            hline.setLineWidth(2)
            hline.setStyleSheet(
                "QFrame { border-top: 1px solid #bbb; margin: 0; }")
            layout.addWidget(hline, 1, 0, 1, 3)

        # Conecta sinais de todas as telas ativas
        for screen in self.screens:
            if hasattr(screen, 'customer_registered'):
                screen.customer_registered.connect(
                    self.update_all_customer_suggestions)

            if hasattr(screen, 'customer_search') and hasattr(screen.customer_search, 'load_customers'):
                def make_connect(s=screen):
                    if hasattr(s, 'finalize_order'):
                        orig_finalize = s.finalize_order

                        def wrapped_finalize_order(*args, **kwargs):
                            result = orig_finalize(*args, **kwargs)
                            self.update_all_customer_suggestions()
                            return result
                        s.finalize_order = wrapped_finalize_order
                make_connect(screen)

    def open_settings(self):
        """Abre a janela de configurações do sistema."""
        LOGGER.info('Abrindo configurações do sistema')
        dialog = SettingsDialog(self)
        dialog.exec()

    def open_menu_registration(self):
        LOGGER.info('Abrindo cadastro de cardápio')
        self.menu_registration_window = MenuRegistrationWindow()
        self.menu_registration_window.setWindowFlags(Qt.WindowType.Window)
        # Conecta o sinal de item adicionado para atualizar as listas
        self.menu_registration_window.item_added.connect(self.refresh_items)
        self.menu_registration_window.show()

    def refresh_items(self):
        """Atualiza as listas de itens em todas as telas de pedidos
        após cadastro."""
        LOGGER.info('Atualizando listas de itens após cadastro')
        # Atualiza todos os widgets de busca de itens
        for screen in self.screens:
            if hasattr(screen, 'item_search'):
                screen.item_search.load_items()

    def open_menu_edit(self):
        LOGGER.info('Abrindo edição de cardápio')
        self.menu_edit_window = MenuEditWindow()
        self.menu_edit_window.setWindowFlags(Qt.WindowType.Window)
        self.menu_edit_window.show()

    def open_customer_management(self):
        LOGGER.info('Abrindo gerenciamento de clientes')
        self.customer_management_window = CustomerManagementWindow(self)
        self.customer_management_window.finished.connect(
            self.refresh_customers)
        self.customer_management_window.show()

    def refresh_customers(self):
        """Atualiza a lista global de clientes e widgets de busca
        após cadastro/edição."""
        global ALL_CUSTOMERS
        ALL_CUSTOMERS = [(c[1], c[2]) for c in get_customers()]
        LOGGER.info(
            f'{len(ALL_CUSTOMERS)} clientes recarregados em ALL_CUSTOMERS')
        # Atualiza todos os widgets de busca de clientes
        for screen in self.screens:
            if hasattr(screen, 'customer_search'):
                screen.customer_search.set_customers(ALL_CUSTOMERS)

    def open_neighborhood_management(self):
        LOGGER.info('Abrindo gerenciamento de bairros')
        self.neighborhood_management_window = NeighborhoodManagementWindow(
            self)
        self.neighborhood_management_window.show()

    def closeEvent(self, event):
        """Finaliza todas as threads antes de fechar a aplicação"""
        LOGGER.info('Finalizando aplicação e threads...')

        # Finaliza threads das telas de pedido chamando seus closeEvent
        for screen in self.screens:
            if hasattr(screen, 'closeEvent'):
                screen.closeEvent(event)

        LOGGER.info('Todas as threads finalizadas')
        super().closeEvent(event)


if __name__ == "__main__":
    LOGGER.info('Aplicação iniciada')

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    # Força foco na aplicação
    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    window.showMaximized()

    # Força ativação da janela e foco
    window.raise_()
    window.activateWindow()
    app.processEvents()  # Processa eventos pendentes

    LOGGER.info('Janela principal exibida')
    sys.exit(app.exec())
