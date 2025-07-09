from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox,
                               QSizePolicy, QWidget, QDoubleSpinBox)

from db import (add_neighborhood, get_neighborhoods, update_neighborhood, 
                delete_neighborhood, init_db)
from log_utils import get_logger

logger = get_logger(__name__)


class NeighborhoodRegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('NeighborhoodRegistrationDialog inicializado')
        self.setWindowTitle("Cadastro de Bairro")
        self.setWindowFlags(Qt.Window)
        self.resize(400, 200)
        
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        
        layout = QVBoxLayout()
        
        # Nome
        layout.addWidget(QLabel("Nome do Bairro:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome do bairro")
        layout.addWidget(self.name_input)
        
        # Taxa de entrega
        layout.addWidget(QLabel("Taxa de Entrega (R$):"))
        self.delivery_fee_input = QDoubleSpinBox()
        self.delivery_fee_input.setRange(0.0, 999.99)
        self.delivery_fee_input.setDecimals(2)
        self.delivery_fee_input.setSingleStep(0.50)
        self.delivery_fee_input.setValue(0.0)
        layout.addWidget(self.delivery_fee_input)
        
        # Botões
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        
        save_btn.clicked.connect(self.save_neighborhood)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def save_neighborhood(self):
        name = self.name_input.text().strip()
        delivery_fee = self.delivery_fee_input.value()
        
        if not name:
            QMessageBox.warning(self, "Erro", "Nome do bairro é obrigatório.")
            return
        
        try:
            add_neighborhood(name, delivery_fee)
            QMessageBox.information(self, "Sucesso",
                                    "Bairro cadastrado com sucesso!")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))


class NeighborhoodEditDialog(QDialog):
    def __init__(self, neighborhood_data, parent=None):
        super().__init__(parent)
        logger.info('NeighborhoodEditDialog inicializado')
        self.neighborhood_id = neighborhood_data[0]
        self.setWindowTitle("Editar Bairro")
        self.setWindowFlags(Qt.Window)
        self.resize(400, 200)
        
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        
        layout = QVBoxLayout()
        
        # Nome
        layout.addWidget(QLabel("Nome do Bairro:"))
        self.name_input = QLineEdit(neighborhood_data[1])
        layout.addWidget(self.name_input)
        
        # Taxa de entrega
        layout.addWidget(QLabel("Taxa de Entrega (R$):"))
        self.delivery_fee_input = QDoubleSpinBox()
        self.delivery_fee_input.setRange(0.0, 999.99)
        self.delivery_fee_input.setDecimals(2)
        self.delivery_fee_input.setSingleStep(0.50)
        self.delivery_fee_input.setValue(neighborhood_data[2])
        layout.addWidget(self.delivery_fee_input)
        
        # Botões
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        
        save_btn.clicked.connect(self.save_neighborhood)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def save_neighborhood(self):
        name = self.name_input.text().strip()
        delivery_fee = self.delivery_fee_input.value()
        
        if not name:
            QMessageBox.warning(self, "Erro", "Nome do bairro é obrigatório.")
            return
        
        try:
            update_neighborhood(self.neighborhood_id, name, delivery_fee)
            QMessageBox.information(self, "Sucesso", 
                                    "Bairro atualizado com sucesso!")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))


class NeighborhoodManagementWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('NeighborhoodManagementWindow inicializada')
        
        # Inicializa o banco de dados para garantir que a tabela neighborhoods existe
        try:
            init_db()
            logger.info('Banco de dados inicializado para bairros')
        except Exception as e:
            logger.error(f'Erro ao inicializar banco de dados: {e}')
            QMessageBox.critical(self, "Erro", 
                                f"Erro ao inicializar banco de dados: {e}")
            return
        
        self.setWindowTitle("Gerenciar Bairros")
        self.setWindowFlags(Qt.Window)
        self.resize(600, 400)
        
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        
        layout = QVBoxLayout()
        
        # Botão para adicionar novo bairro
        add_btn = QPushButton("Novo Bairro")
        add_btn.clicked.connect(self.add_neighborhood)
        layout.addWidget(add_btn)
        
        # Tabela de bairros
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Nome", "Taxa de Entrega (R$)", "Editar", "Excluir"
        ])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Configurar redimensionamento das colunas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nome
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Taxa
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Editar
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Excluir
        
        # Definir larguras fixas para os botões
        self.table.setColumnWidth(2, 80)   # Editar
        self.table.setColumnWidth(3, 80)   # Excluir
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.refresh_table()
    
    def refresh_table(self):
        """Recarrega todos os bairros do banco"""
        neighborhoods = get_neighborhoods()
        self.display_neighborhoods(neighborhoods)
    
    def display_neighborhoods(self, neighborhoods):
        """Exibe uma lista de bairros na tabela"""
        self.table.setRowCount(len(neighborhoods))
        self.table.clearContents()
        
        for row, neighborhood in enumerate(neighborhoods):
            # neighborhood: (id, name, delivery_fee)
            
            # Nome
            name_item = QTableWidgetItem(neighborhood[1])
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 0, name_item)
            
            # Taxa de entrega
            fee_item = QTableWidgetItem(f"R$ {neighborhood[2]:.2f}")
            fee_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.table.setItem(row, 1, fee_item)
            
            # Botão Editar
            edit_btn = QPushButton("Editar")
            edit_btn.clicked.connect(
                lambda checked, r=row: self.edit_neighborhood(r))
            edit_cell = QWidget()
            edit_layout = QHBoxLayout(edit_cell)
            edit_layout.addWidget(edit_btn)
            edit_layout.setAlignment(Qt.AlignCenter)
            edit_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 2, edit_cell)
            
            # Botão Excluir
            delete_btn = QPushButton("Excluir")
            delete_btn.clicked.connect(
                lambda checked, r=row: self.delete_neighborhood(r))
            delete_cell = QWidget()
            delete_layout = QHBoxLayout(delete_cell)
            delete_layout.addWidget(delete_btn)
            delete_layout.setAlignment(Qt.AlignCenter)
            delete_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 3, delete_cell)
            
            self.table.setRowHeight(row, 40)
    
    def add_neighborhood(self):
        dialog = NeighborhoodRegistrationDialog(self)
        if dialog.exec():
            self.refresh_table()
    
    def edit_neighborhood(self, row):
        neighborhoods = get_neighborhoods()
        if row < len(neighborhoods):
            neighborhood = neighborhoods[row]
            dialog = NeighborhoodEditDialog(neighborhood, self)
            if dialog.exec():
                self.refresh_table()
    
    def delete_neighborhood(self, row):
        neighborhoods = get_neighborhoods()
        if row < len(neighborhoods):
            neighborhood = neighborhoods[row]
            reply = QMessageBox.question(
                self, "Confirmar Exclusão",
                f"Deseja realmente excluir o bairro {neighborhood[1]}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    delete_neighborhood(neighborhood[0])
                    self.refresh_table()
                except ValueError as e:
                    QMessageBox.warning(self, "Erro", str(e))
