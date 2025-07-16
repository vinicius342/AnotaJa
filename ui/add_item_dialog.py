"""
Diálogo para adicionar itens ao pedido com complementos.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QHBoxLayout,
                               QLabel, QListWidget, QListWidgetItem,
                               QMessageBox, QPushButton, QSpinBox, QTextEdit,
                               QVBoxLayout, QWidget)

from database.db import get_all_additions_for_item_with_mandatory_info
from utils.log_utils import get_logger

LOGGER = get_logger(__name__)


class AddItemDialog(QDialog):
    """Diálogo para adicionar item ao pedido com complementos."""

    item_added = Signal(dict)  # Sinal emitido quando item é adicionado

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.selected_additions_data = []
        self.setup_ui()
        self.load_additions()

    def setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle("Adicionar Item")
        self.setModal(True)
        self.resize(500, 400)

        # Posiciona o modal
        if self.parent():
            parent_geometry = self.parent().geometry()
            self.move(parent_geometry.x() + 50, parent_geometry.y() + 50)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header com nome do item e categoria
        self.setup_header(layout)

        # Seção de complementos
        self.setup_additions_section(layout)

        # Campo de observações
        self.setup_observations_section(layout)

        # Valor total
        self.setup_total_section(layout)

        # Botões finais
        self.setup_buttons(layout)

    def setup_header(self, layout):
        """Configura o header com nome e categoria do item."""
        header_layout = QHBoxLayout()

        item_name_label = QLabel(f"Item: {self.item_data[1]}")
        item_name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(item_name_label)

        category_label = QLabel(f"Categoria: {self.item_data[4]}")
        category_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(category_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

    def setup_additions_section(self, layout):
        """Configura a seção de complementos."""
        # Label dos complementos
        additions_label = QLabel("Complementos:")
        additions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(additions_label)

        # Layout para seleção de complementos
        additions_layout = QHBoxLayout()

        # Combo para selecionar complemento
        self.additions_combo = QComboBox()
        self.additions_combo.addItem("Selecione um complemento...")
        additions_layout.addWidget(self.additions_combo)

        # Quantidade
        qty_label = QLabel("Qtd:")
        additions_layout.addWidget(qty_label)

        self.addition_qty = QSpinBox()
        self.addition_qty.setMinimum(1)
        self.addition_qty.setMaximum(10)
        self.addition_qty.setValue(1)
        additions_layout.addWidget(self.addition_qty)

        # Botão adicionar
        add_addition_btn = QPushButton("Adicionar")
        add_addition_btn.clicked.connect(self.add_addition_to_list)
        additions_layout.addWidget(add_addition_btn)

        layout.addLayout(additions_layout)

        # Lista de complementos selecionados
        self.selected_additions = QListWidget()
        self.selected_additions.setMaximumHeight(100)
        layout.addWidget(self.selected_additions)

    def setup_observations_section(self, layout):
        """Configura a seção de observações."""
        obs_label = QLabel("Observações:")
        obs_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(obs_label)

        self.observations = QTextEdit()
        self.observations.setMaximumHeight(60)
        self.observations.setPlaceholderText("Observações especiais...")
        layout.addWidget(self.observations)

    def setup_total_section(self, layout):
        """Configura a seção do valor total."""
        self.total_label = QLabel(f"Total: R$ {self.item_data[2]:.2f}")
        self.total_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #2e7d32;"
        )
        layout.addWidget(self.total_label)

    def setup_buttons(self, layout):
        """Configura os botões do diálogo."""
        buttons_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        add_btn = QPushButton("Adicionar ao Pedido")
        add_btn.setStyleSheet("background-color: #4caf50; color: white;")
        add_btn.clicked.connect(self.add_to_order)
        buttons_layout.addWidget(add_btn)

        layout.addLayout(buttons_layout)

    def load_additions(self):
        """Carrega complementos da categoria e específicos do item."""
        try:
            # category_id = self.item_data[3], item_id = self.item_data[0]
            additions = get_all_additions_for_item_with_mandatory_info(
                self.item_data[0], self.item_data[3]
            )

            self.additions_combo.clear()
            self.additions_combo.addItem("Selecione um complemento...")

            for addition in additions:
                # addition: (id, name, price, is_mandatory)
                mandatory_text = " (OBRIGATÓRIO)" if addition[3] else ""
                text = f"{addition[1]} - R$ {addition[2]:.2f}{mandatory_text}"
                self.additions_combo.addItem(text, addition)

        except Exception as e:
            LOGGER.error(f"Erro ao carregar complementos: {e}")

    def add_addition_to_list(self):
        """Adiciona complemento à lista."""
        current_index = self.additions_combo.currentIndex()
        if current_index <= 0:  # Não selecionou complemento válido
            return

        addition_data = self.additions_combo.itemData(current_index)
        qty = self.addition_qty.value()

        # Adiciona à lista visual
        text = f"{qty}x {addition_data[1]} - R$ {addition_data[2]*qty:.2f}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, {
            'id': addition_data[0],
            'name': addition_data[1],
            'price': addition_data[2],
            'qty': qty,
            'total': addition_data[2] * qty
        })
        self.selected_additions.addItem(item)

        # Adiciona aos dados do diálogo
        self.selected_additions_data.append({
            'id': addition_data[0],
            'name': addition_data[1],
            'price': addition_data[2],
            'qty': qty,
            'total': addition_data[2] * qty
        })

        # Atualiza total
        self.update_total_price()

        # Reset campos
        self.additions_combo.setCurrentIndex(0)
        self.addition_qty.setValue(1)

    def update_total_price(self):
        """Atualiza o preço total."""
        base_price = self.item_data[2]
        additions_total = sum(add['total']
                              for add in self.selected_additions_data)
        total = base_price + additions_total
        self.total_label.setText(f"Total: R$ {total:.2f}")

    def add_to_order(self):
        """Adiciona item ao pedido."""
        # Monta dados do item completo
        item_complete = {
            'item_data': self.item_data,
            'additions': self.selected_additions_data.copy(),
            'observations': self.observations.toPlainText().strip(),
            'total': self.calculate_total()
        }

        # Emite sinal com os dados
        self.item_added.emit(item_complete)

        # Mostra confirmação
        self.show_confirmation()

        # Fecha o diálogo
        self.accept()

    def calculate_total(self):
        """Calcula o total do item com complementos."""
        base_price = self.item_data[2]
        additions_total = sum(add['total']
                              for add in self.selected_additions_data)
        return base_price + additions_total

    def show_confirmation(self):
        """Mostra mensagem de confirmação."""
        additions_text = ""
        if self.selected_additions_data:
            additions_list = [f"{a['qty']}x {a['name']}"
                              for a in self.selected_additions_data]
            additions_text = ", ".join(additions_list)

        msg = f"Item adicionado: {self.item_data[1]}\n"
        if additions_text:
            msg += f"Complementos: {additions_text}\n"
        msg += f"Total: R$ {self.calculate_total():.2f}"

        QMessageBox.information(self, "Item Adicionado", msg)
