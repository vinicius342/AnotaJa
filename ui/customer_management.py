from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox,
                               QSizePolicy, QWidget, QMenu)

from database.db import (add_customer, get_customers, update_customer, delete_customer,
                init_db, search_customers, get_customer_orders, get_neighborhoods)
from utils.log_utils import get_logger

logger = get_logger(__name__)


class CustomerRegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('CustomerRegistrationDialog inicializado')
        self.setWindowTitle("Cadastro de Cliente")
        self.setWindowFlags(Qt.Window)
        self.resize(400, 350)
        
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        
        layout = QVBoxLayout()
        
        # Nome
        layout.addWidget(QLabel("Nome:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome completo")
        layout.addWidget(self.name_input)
        
        # Telefone
        layout.addWidget(QLabel("Telefone:"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(xx) xxxxx-xxxx")
        layout.addWidget(self.phone_input)
        
        # Endereço - Rua
        layout.addWidget(QLabel("Rua:"))
        self.street_input = QLineEdit()
        self.street_input.setPlaceholderText("Nome da rua")
        layout.addWidget(self.street_input)
        
        # Número da casa
        layout.addWidget(QLabel("Número:"))
        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Número da casa/apt")
        layout.addWidget(self.number_input)
        
        # Bairro
        layout.addWidget(QLabel("Bairro:"))
        self.neighborhood_button = QPushButton("Selecionar Bairro")
        self.neighborhood_menu = QMenu()
        self.neighborhood_button.setMenu(self.neighborhood_menu)
        self.selected_neighborhood_id = None
        self.load_neighborhoods()
        layout.addWidget(self.neighborhood_button)
        
        # Ponto de referência
        layout.addWidget(QLabel("Ponto de Referência:"))
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Próximo a...")
        layout.addWidget(self.reference_input)
        
        # Botões
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        
        save_btn.clicked.connect(self.save_customer)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_neighborhoods(self):
        """Carrega os bairros no menu"""
        self.neighborhood_menu.clear()
        neighborhoods = get_neighborhoods()
        
        if not neighborhoods:
            no_action = self.neighborhood_menu.addAction("Nenhum bairro cadastrado")
            no_action.setEnabled(False)
            return
        
        for neighborhood in neighborhoods:
            action = self.neighborhood_menu.addAction(
                f"{neighborhood[1]} - R$ {neighborhood[2]:.2f}"
            )
            action.triggered.connect(
                lambda checked, nid=neighborhood[0], name=neighborhood[1]: 
                self.select_neighborhood(nid, name)
            )
    
    def select_neighborhood(self, neighborhood_id, neighborhood_name):
        """Seleciona um bairro"""
        self.selected_neighborhood_id = neighborhood_id
        self.neighborhood_button.setText(f"Bairro: {neighborhood_name}")
    
    def save_customer(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        street = self.street_input.text().strip()
        number = self.number_input.text().strip()
        reference = self.reference_input.text().strip()
        
        if not name or not phone:
            QMessageBox.warning(self, "Erro",
                                "Nome e telefone são obrigatórios.")
            return
        
        try:
            add_customer(name, phone, street, number, 
                        self.selected_neighborhood_id, reference)
            QMessageBox.information(self, "Sucesso",
                                    "Cliente cadastrado com sucesso!")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))


class CustomerEditDialog(QDialog):
    def __init__(self, customer_data, parent=None):
        super().__init__(parent)
        logger.info('CustomerEditDialog inicializado')
        self.customer_id = customer_data[0]
        self.setWindowTitle("Editar Cliente")
        self.setWindowFlags(Qt.Window)
        self.resize(400, 350)
        
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        
        layout = QVBoxLayout()
        
        # Nome
        layout.addWidget(QLabel("Nome:"))
        self.name_input = QLineEdit(customer_data[1])
        layout.addWidget(self.name_input)
        
        # Telefone
        layout.addWidget(QLabel("Telefone:"))
        self.phone_input = QLineEdit(customer_data[2])
        layout.addWidget(self.phone_input)
        
        # Endereço - Rua
        layout.addWidget(QLabel("Rua:"))
        self.street_input = QLineEdit(customer_data[3] or "")
        layout.addWidget(self.street_input)
        
        # Número da casa
        layout.addWidget(QLabel("Número:"))
        self.number_input = QLineEdit(customer_data[4] or "")
        layout.addWidget(self.number_input)
        
        # Bairro
        layout.addWidget(QLabel("Bairro:"))
        self.neighborhood_button = QPushButton("Selecionar Bairro")
        self.neighborhood_menu = QMenu()
        self.neighborhood_button.setMenu(self.neighborhood_menu)
        self.selected_neighborhood_id = customer_data[5]  # neighborhood_id
        self.load_neighborhoods()
        layout.addWidget(self.neighborhood_button)
        
        # Ponto de referência
        layout.addWidget(QLabel("Ponto de Referência:"))
        self.reference_input = QLineEdit(customer_data[6] or "")
        layout.addWidget(self.reference_input)
        
        # Botões
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        
        save_btn.clicked.connect(self.save_customer)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_neighborhoods(self):
        """Carrega os bairros no menu"""
        self.neighborhood_menu.clear()
        neighborhoods = get_neighborhoods()
        
        if not neighborhoods:
            no_action = self.neighborhood_menu.addAction("Nenhum bairro cadastrado")
            no_action.setEnabled(False)
            return
        
        for neighborhood in neighborhoods:
            action = self.neighborhood_menu.addAction(
                f"{neighborhood[1]} - R$ {neighborhood[2]:.2f}"
            )
            action.triggered.connect(
                lambda checked, nid=neighborhood[0], name=neighborhood[1]: 
                self.select_neighborhood(nid, name)
            )
            
            # Se este é o bairro selecionado, marca o botão
            if self.selected_neighborhood_id == neighborhood[0]:
                self.neighborhood_button.setText(f"Bairro: {neighborhood[1]}")
    
    def select_neighborhood(self, neighborhood_id, neighborhood_name):
        """Seleciona um bairro"""
        self.selected_neighborhood_id = neighborhood_id
        self.neighborhood_button.setText(f"Bairro: {neighborhood_name}")
    
    def save_customer(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        street = self.street_input.text().strip()
        number = self.number_input.text().strip()
        reference = self.reference_input.text().strip()
        
        if not name or not phone:
            QMessageBox.warning(self, "Erro", "Nome e telefone são obrigatórios.")
            return
        
        try:
            update_customer(self.customer_id, name, phone, street, number, 
                           self.selected_neighborhood_id, reference)
            QMessageBox.information(self, "Sucesso", "Cliente atualizado com sucesso!")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))


class CustomerManagementWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('CustomerManagementWindow inicializada')
        
        # Inicializa o banco de dados para garantir que a tabela customers existe
        try:
            init_db()
            logger.info('Banco de dados inicializado para clientes')
        except Exception as e:
            logger.error(f'Erro ao inicializar banco de dados: {e}')
            QMessageBox.critical(self, "Erro", f"Erro ao inicializar banco de dados: {e}")
            return
        
        self.setWindowTitle("Gerenciar Clientes")
        self.setWindowFlags(Qt.Window)
        self.resize(800, 600)
        
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        
        layout = QVBoxLayout()
        
        # Campo de busca
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Digite nome, telefone ou endereço..."
        )
        self.search_input.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Botão para adicionar novo cliente
        add_btn = QPushButton("Novo Cliente")
        add_btn.clicked.connect(self.add_customer)
        layout.addWidget(add_btn)
        # Tabela de clientes
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Nome", "Telefone", "Rua", "Número", "Bairro", "Referência",
            "Histórico", "Editar", "Excluir"
        ])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Configurar redimensionamento das colunas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nome
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Telefone
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Rua
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Número
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Bairro
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Referência
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Histórico
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # Editar
        header.setSectionResizeMode(8, QHeaderView.Fixed)  # Excluir
        
        # Definir larguras fixas para os botões
        self.table.setColumnWidth(6, 100)  # Histórico
        self.table.setColumnWidth(7, 80)   # Editar
        self.table.setColumnWidth(8, 80)   # Excluir
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # Armazena todos os clientes para filtro
        self.all_customers = []
        self.refresh_table()
        
        self.table.cellDoubleClicked.connect(self.on_table_double_click)

    def on_table_double_click(self, row, column):
        """Evita crash ao clicar duas vezes em linhas inválidas ou vazias."""
        current_customers = self.get_current_displayed_customers()
        if not current_customers or row >= len(current_customers):
            return  # Ignora duplo clique em linha vazia ou mensagem
        # Por padrão, abre o histórico do cliente
        self.show_customer_history(row)
    
    def filter_customers(self):
        """Filtra clientes baseado no texto de busca"""
        search_text = self.search_input.text().strip()
        if not search_text:
            # Se não há texto de busca, mostra todos
            self.display_customers(self.all_customers)
        else:
            # Busca no banco de dados
            filtered_customers = search_customers(search_text)
            self.display_customers(filtered_customers)
    
    def refresh_table(self):
        """Recarrega todos os clientes do banco"""
        self.all_customers = get_customers()
        self.display_customers(self.all_customers)
        # Limpa o campo de busca ao atualizar a tabela (dica 2)
        self.search_input.clear()

    def display_customers(self, customers):
        """Exibe uma lista de clientes na tabela"""
        self.table.clearContents()
        if not customers:
            self.table.setRowCount(1)
            no_customers_item = QTableWidgetItem("Nenhum cliente encontrado")
            no_customers_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.table.setItem(0, 0, no_customers_item)
            self.table.setSpan(0, 0, 1, self.table.columnCount())
            # Limpa widgets dos botões
            for col in range(1, self.table.columnCount()):
                self.table.setItem(0, col, QTableWidgetItem(""))
                self.table.setCellWidget(0, col, None)
            return
        self.table.setRowCount(len(customers))
        for row, customer in enumerate(customers):
            # customer: (id, name, phone, street, number, neighborhood_id, reference, neighborhood_name)
            
            # Nome
            name_item = QTableWidgetItem(customer[1])
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 0, name_item)
            
            # Telefone
            phone_item = QTableWidgetItem(customer[2])
            phone_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 1, phone_item)
            
            # Rua
            street_item = QTableWidgetItem(customer[3] or "")
            street_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 2, street_item)
            
            # Número
            number_item = QTableWidgetItem(customer[4] or "")
            number_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 3, number_item)
            
            # Bairro
            neighborhood_item = QTableWidgetItem(customer[7] or "")
            neighborhood_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 4, neighborhood_item)
            
            # Referência
            reference_item = QTableWidgetItem(customer[6] or "")
            reference_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 5, reference_item)
            
            # Botão Histórico
            history_btn = QPushButton("Histórico")
            history_btn.clicked.connect(
                lambda checked, r=row: self.show_customer_history(r))
            history_cell = QWidget()
            history_layout = QHBoxLayout(history_cell)
            history_layout.addWidget(history_btn)
            history_layout.setAlignment(Qt.AlignCenter)
            history_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 6, history_cell)
            
            # Botão Editar
            edit_btn = QPushButton("Editar")
            edit_btn.clicked.connect(
                lambda checked, r=row: self.edit_customer(r))
            edit_cell = QWidget()
            edit_layout = QHBoxLayout(edit_cell)
            edit_layout.addWidget(edit_btn)
            edit_layout.setAlignment(Qt.AlignCenter)
            edit_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 7, edit_cell)
            
            # Botão Excluir
            delete_btn = QPushButton("Excluir")
            delete_btn.clicked.connect(
                lambda checked, r=row: self.delete_customer(r))
            delete_cell = QWidget()
            delete_layout = QHBoxLayout(delete_cell)
            delete_layout.addWidget(delete_btn)
            delete_layout.setAlignment(Qt.AlignCenter)
            delete_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 8, delete_cell)
            
            self.table.setRowHeight(row, 40)
    
    def show_customer_history(self, row):
        """Mostra o histórico de pedidos do cliente"""
        # Precisa buscar o cliente correto baseado na linha atual
        current_customers = self.get_current_displayed_customers()
        if row < len(current_customers):
            customer = current_customers[row]
            dialog = CustomerHistoryDialog(customer, self)
            dialog.exec()
    
    def get_current_displayed_customers(self):
        """Retorna os clientes atualmente exibidos na tabela"""
        search_text = self.search_input.text().strip()
        if not search_text:
            return self.all_customers
        else:
            return search_customers(search_text)
    
    def add_customer(self):
        dialog = CustomerRegistrationDialog(self)
        if dialog.exec():
            self.refresh_table()  # Isso já limpa o campo de busca
    
    def edit_customer(self, row):
        current_customers = self.get_current_displayed_customers()
        if row < len(current_customers):
            customer = current_customers[row]
            dialog = CustomerEditDialog(customer, self)
            if dialog.exec():
                self.refresh_table()  # Isso já limpa o campo de busca

    def delete_customer(self, row):
        current_customers = self.get_current_displayed_customers()
        if row < len(current_customers):
            customer = current_customers[row]
            reply = QMessageBox.question(
                self, "Confirmar Exclusão",
                f"Deseja realmente excluir o cliente {customer[1]}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                delete_customer(customer[0])
                self.refresh_table()  # Isso já limpa o campo de busca


class CustomerHistoryDialog(QDialog):
    def __init__(self, customer_data, parent=None):
        super().__init__(parent)
        self.customer_id = customer_data[0]
        self.customer_name = customer_data[1]
        
        logger.info(f'CustomerHistoryDialog inicializado para {self.customer_name}')
        self.setWindowTitle(f"Histórico de Pedidos - {self.customer_name}")
        self.setWindowFlags(Qt.Window)
        self.resize(700, 500)
        
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        
        layout = QVBoxLayout()
        
        # Informações do cliente
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"Cliente: {self.customer_name}"))
        info_layout.addWidget(QLabel(f"Telefone: {customer_data[2]}"))
        layout.addLayout(info_layout)
        
        # Tabela de pedidos
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels([
            "ID Pedido", "Data", "Total", "Status", "Observações"
        ])
        self.orders_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.orders_table)
        
        # Botão fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        self.refresh_orders()
    
    def refresh_orders(self):
        """Carrega e exibe os pedidos do cliente"""
        orders = get_customer_orders(self.customer_id)
        self.orders_table.setRowCount(len(orders))
        self.orders_table.clearContents()
        
        for row, order in enumerate(orders):
            # order: (id, order_date, total_amount, status, notes)
            
            # ID do Pedido
            id_item = QTableWidgetItem(str(order[0]))
            id_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.orders_table.setItem(row, 0, id_item)
            
            # Data (formatada)
            order_date = order[1]
            if order_date:
                # Formatar data se necessário
                date_str = order_date.split(' ')[0] if ' ' in order_date else order_date
            else:
                date_str = "N/A"
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.orders_table.setItem(row, 1, date_item)
            
            # Total
            total_item = QTableWidgetItem(f"R$ {order[2]:.2f}")
            total_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.orders_table.setItem(row, 2, total_item)
            
            # Status
            status_item = QTableWidgetItem(order[3] or "Pendente")
            status_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.orders_table.setItem(row, 3, status_item)
            
            # Observações
            notes_item = QTableWidgetItem(order[4] or "")
            notes_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.orders_table.setItem(row, 4, notes_item)
            
            self.orders_table.setRowHeight(row, 30)
        
        if not orders:
            # Se não há pedidos, mostra uma mensagem
            self.orders_table.setRowCount(1)
            no_orders_item = QTableWidgetItem("Nenhum pedido encontrado")
            no_orders_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.orders_table.setItem(0, 0, no_orders_item)
            # Mescla as colunas para a mensagem
            self.orders_table.setSpan(0, 0, 1, 5)
