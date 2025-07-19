"""
Tela de pedidos - versão refatorada e simplificada.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
                               QHeaderView, QLabel, QMenu, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QTextEdit, QVBoxLayout, QWidget)

from ui.add_item_dialog import AddItemDialog
from ui.widgets.search_widgets import CustomerSearchWidget, ItemSearchWidget
from utils.log_utils import get_logger

LOGGER = get_logger(__name__)


class OrderScreen(QWidget):
    """Tela de pedidos simplificada."""

    def __init__(self, screen_title, parent=None, customers=None):
        super().__init__(parent)
        self.screen_title = screen_title
        self.selected_customer = None
        self.order_items = []
        self.customers = customers if customers is not None else []
        LOGGER.info(
            f"Carregando {len(self.customers)} clientes na tela de pedidos"
        )
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface da tela de pedidos."""
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Primeira coluna: campos de busca
        self.setup_left_column(main_layout)

        # Segunda coluna: título e tabela de pedidos
        self.setup_right_column(main_layout)

    def setup_left_column(self, main_layout):
        """Configura a coluna esquerda com campos de busca."""
        left_col = QVBoxLayout()
        main_layout.addLayout(left_col, 1)

        # Campo de busca de clientes
        self.customer_search = CustomerSearchWidget(customers=self.customers)
        self.customer_search.customer_selected.connect(
            self.on_customer_selected)
        self.customer_search.suggestions_list_shown.connect(
            self.hide_left_column_widgets
        )
        self.customer_search.suggestions_list_hidden.connect(
            self.show_left_column_widgets
        )
        left_col.addWidget(self.customer_search)

        # Campo de busca de itens
        self.item_search = ItemSearchWidget()
        self.item_search.item_selected.connect(self.on_item_selected)
        self.item_search.suggestions_list_shown.connect(
            self.hide_left_column_widgets_for_items
        )
        self.item_search.suggestions_list_hidden.connect(
            self.show_left_column_widgets
        )
        left_col.addWidget(self.item_search)

        # Armazena referências aos widgets que devem ser escondidos
        self.left_column_widgets = []  # Para busca de clientes
        self.left_column_widgets_for_items = [
            self.customer_search]  # Para busca de itens

        # Botão Limpar Pedido (será escondido quando sugestões aparecerem)
        self.clear_order_button = QPushButton("Limpar Pedido")
        self.clear_order_button.clicked.connect(self.clear_order)
        clear_layout = QHBoxLayout()
        clear_layout.addWidget(self.clear_order_button,
                               alignment=Qt.AlignmentFlag.AlignLeft)
        self.clear_button_layout = clear_layout
        left_col.addLayout(clear_layout)

        # Adiciona o botão à lista de widgets que serão escondidos
        self.left_column_widgets.append(self.item_search)
        self.left_column_widgets.append(self.clear_order_button)
        self.left_column_widgets_for_items.append(self.clear_order_button)

        # Desabilita o campo de item até que um cliente seja selecionado
        self.item_search.item_lineedit.setEnabled(False)

        left_col.addStretch()

    def setup_right_column(self, main_layout):
        """Configura a coluna direita com título e tabela de pedidos."""
        right_col = QVBoxLayout()
        main_layout.addLayout(right_col, 2)

        # Título da tela
        self.setup_title_label(right_col)

        # Frame do pedido
        self.setup_order_frame(right_col)

        right_col.addStretch()

    def setup_title_label(self, layout):
        """Configura o label do título."""
        self.title_label = QLabel(self.screen_title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("QLabel { padding: 2px 4px; }")
        self.title_label.setWordWrap(False)
        self.title_label.setMinimumHeight(24)
        self.title_label.setMaximumHeight(28)
        self.title_label.setSizePolicy(
            self.title_label.sizePolicy().horizontalPolicy(),
            QWidget().sizePolicy().verticalPolicy()
        )
        self.title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.title_label)

    def setup_order_frame(self, layout):
        """Configura o frame do pedido."""
        order_frame = QFrame()
        order_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        order_frame.setMaximumWidth(320)
        # Remove border from order_frame
        order_frame.setStyleSheet("QFrame { border: none; }")

        order_layout = QVBoxLayout()
        order_frame.setLayout(order_layout)

        # Label do pedido
        order_label = QLabel("Itens do Pedido:")
        order_font = QFont()
        order_font.setBold(True)
        order_label.setFont(order_font)
        order_layout.addWidget(order_label)

        # Tabela de itens do pedido
        self.setup_order_table(order_layout)

        # Botões de ação
        self.setup_action_buttons(order_layout)

        layout.addWidget(order_frame)

    def setup_order_table(self, layout):
        """Configura a tabela de itens do pedido."""
        self.order_table = QTableWidget(0, 4)
        self.order_table.setHorizontalHeaderLabels([
            "Qtd", "Nome", "Categoria", "Editar"
        ])
        header = self.order_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        self.order_table.setMaximumHeight(200)
        # Define largura menor para a coluna 'Ver'
        self.order_table.setColumnWidth(3, 60)

        # Remove a numeração da linha (vertical header)
        self.order_table.verticalHeader().setVisible(False)

        # Remove any custom border style to restore default borders
        self.order_table.setStyleSheet(
            "QTableWidget { border: 1px solid #bbb; }")

        # Habilita menu de contexto personalizado
        self.order_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.order_table.customContextMenuRequested.connect(
            self.show_context_menu
        )

        layout.addWidget(self.order_table)

    def setup_action_buttons(self, layout):
        """Substitui o botão de adicionar item por um campo de valor total."""
        total_layout = QHBoxLayout()
        self.total_label = QLabel("Total: R$ 0,00")
        total_font = QFont()
        total_font.setBold(True)
        self.total_label.setFont(total_font)
        self.total_label.setStyleSheet(
            "QLabel { color: #2a7; font-size: 15px; padding: 0px 1px; }")
        from PySide6.QtWidgets import QSizePolicy
        self.total_label.setMinimumWidth(120)
        self.total_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)
        total_layout.addWidget(self.total_label)

        self.finalize_button = QPushButton("Finalizar Pedido")
        self.finalize_button.clicked.connect(self.finalize_order)
        self.finalize_button.setMinimumWidth(120)
        total_layout.addWidget(self.finalize_button)

        total_layout.setSpacing(12)
        layout.addLayout(total_layout)

    def hide_left_column_widgets(self):
        """Esconde todos os widgets da primeira coluna exceto o campo de busca."""
        for widget in self.left_column_widgets:
            widget.hide()

    def hide_left_column_widgets_for_items(self):
        """Esconde widgets quando busca de itens está ativa."""
        for widget in self.left_column_widgets_for_items:
            widget.hide()

    def show_left_column_widgets(self):
        """Mostra todos os widgets da primeira coluna."""
        for widget in self.left_column_widgets:
            widget.show()
        for widget in self.left_column_widgets_for_items:
            widget.show()

    def on_customer_selected(self, customer_data):
        """Callback quando um cliente é selecionado."""
        self.selected_customer = customer_data
        customer_name = customer_data.get('name', '').strip()
        customer_phone = customer_data.get('phone', '').strip()

        if customer_name and customer_phone:
            title = f"{customer_phone} - {customer_name}"
        elif customer_phone:
            title = customer_phone
        elif customer_name:
            title = customer_name
        else:
            title = self.screen_title

        # Aplica elipse manualmente se necessário
        metrics = self.title_label.fontMetrics()
        max_width = (self.title_label.width()
                     if self.title_label.width() > 0 else 250)
        elided_title = metrics.elidedText(
            title, Qt.TextElideMode.ElideRight, max_width
        )
        self.title_label.setText(elided_title)
        LOGGER.info(f"Cliente selecionado: {title}")

        # Habilita o campo de item após seleção de cliente
        self.item_search.item_lineedit.setEnabled(True)
        # Foca no campo de busca de item
        self.item_search.item_lineedit.setFocus()

    def on_item_selected(self, item_data):
        """Callback quando um item é selecionado."""
        LOGGER.info(
            f"Item selecionado: {item_data[1]} - R$ {item_data[2]:.2f}")
        # Abre o modal para adicionar o item com adicionais
        self.open_add_item_modal(item_data)

    def open_add_item_modal(self, item_data):
        """Abre modal para adicionar item com complementos e limpa campo ao fechar/cancelar/adicionar."""
        dialog = AddItemDialog(item_data, self)
        dialog.item_added.connect(self.add_item_to_order)
        dialog.exec()
        # Limpa o campo de busca de item e o estado do widget sempre após fechar o diálogo
        if hasattr(self, 'item_search') and self.item_search:
            self.item_search.clear_selection()
            if hasattr(self.item_search, 'item_lineedit'):
                self.item_search.item_lineedit.setFocus()

    def add_item_to_order(self, item_complete):
        """Adiciona item completo ao pedido."""
        row = self.order_table.rowCount()
        self.order_table.insertRow(row)

        # Dados na tabela
        qtd = item_complete.get('qty', 1)
        qtd_item = QTableWidgetItem(f"{qtd}x")
        nome_item = QTableWidgetItem(item_complete['item_data'][1])
        categoria_item = QTableWidgetItem(item_complete['item_data'][4])

        # Botão de editar (ícone lápis local ou padrão) com tamanho maior
        edit_btn = QPushButton()
        edit_btn.setToolTip("Ver detalhes do item")
        import os
        icon_path = os.path.join(
            os.path.dirname(__file__), "icons", "dots.svg")
        if os.path.exists(icon_path):
            edit_btn.setIcon(QIcon(icon_path))
        else:
            from PySide6.QtWidgets import QStyle
            edit_btn.setIcon(self.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView))
        edit_btn.setToolTip("Editar")
        edit_btn.setIconSize(QSize(24, 24))
        edit_btn.setStyleSheet(
            'margin: 0; padding: 0; width: 40px;')
        edit_btn.clicked.connect(lambda: self.edit_item(row))

        self.order_table.setItem(row, 0, qtd_item)
        self.order_table.setItem(row, 1, nome_item)
        self.order_table.setItem(row, 2, categoria_item)
        self.order_table.setCellWidget(row, 3, edit_btn)

        # Armazena dados completos do item
        self.order_items.append(item_complete)

        # Atualiza lista de sugestões de itens
        if hasattr(self, 'item_search') and self.item_search:
            self.item_search.load_items()

        # Atualiza o valor total
        self.update_total_label()

    def add_item(self):
        """Adiciona um item à tabela de pedido (exemplo)."""
        if not self.selected_customer:
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente primeiro!"
            )
            return

        # Exemplo de dados para teste
        row = self.order_table.rowCount()
        self.order_table.insertRow(row)

        qtd_item = QTableWidgetItem("2x")
        nome_item = QTableWidgetItem("X-Burguer")
        categoria_item = QTableWidgetItem("Lanche")

        # Botão de editar padronizado
        edit_btn = QPushButton()
        icon_path = os.path.join(os.path.dirname(
            __file__), "icons", "pencil.svg")
        if os.path.exists(icon_path):
            edit_btn.setIcon(QIcon(icon_path))
        else:
            from PySide6.QtWidgets import QStyle
            edit_btn.setIcon(self.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView))
        edit_btn.setToolTip("Editar")
        edit_btn.setIconSize(QSize(18, 18))
        edit_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: white; background-color: #2a7; }")
        edit_btn.clicked.connect(lambda: self.edit_item(row))

        self.order_table.setItem(row, 0, qtd_item)
        self.order_table.setItem(row, 1, nome_item)
        self.order_table.setItem(row, 2, categoria_item)
        self.order_table.setCellWidget(row, 3, edit_btn)

        # Atualiza lista de sugestões de itens
        if hasattr(self, 'item_search') and self.item_search:
            self.item_search.load_items()

    def clear_order(self):
        """Limpa o pedido atual."""
        self.order_table.setRowCount(0)
        self.order_items.clear()
        self.customer_search.clear_selection()
        self.selected_customer = None
        self.title_label.setText(self.screen_title)

        # Desabilita o campo de item ao limpar o pedido
        self.item_search.item_lineedit.setEnabled(False)

    def finalize_order(self):
        """Finaliza o pedido."""
        if not self.selected_customer:
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente primeiro!"
            )
            return

        if self.order_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Aviso", "Adicione itens ao pedido!"
            )
            return

        # Implementar lógica para salvar o pedido
        QMessageBox.information(
            self, "Sucesso",
            f"Pedido finalizado para {self.selected_customer['name']}!\n"
            f"Total de itens: {self.order_table.rowCount()}"
        )

        # Limpa o pedido após finalizar
        self.clear_order()

    def show_item_details(self, row):
        """Mostra diálogo com detalhes do item."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Detalhes do Item")
        dialog.setModal(True)
        dialog.resize(400, 350)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Nome do item
        item_widget = self.order_table.item(row, 1)
        item_name = item_widget.text() if item_widget else "Item"
        name_label = QLabel(f"Item: {item_name}")
        font = QFont()
        font.setBold(True)
        name_label.setFont(font)
        layout.addWidget(name_label)

        # Complementos (exemplo ou dados reais se disponíveis)
        layout.addWidget(QLabel("Complementos:"))
        adicionais_text = QTextEdit()
        adicionais_text.setMaximumHeight(80)

        if row < len(self.order_items):
            additions = self.order_items[row].get('additions', [])
            additions_str = ", ".join([f"{a['qty']}x {a['name']}"
                                       for a in additions])
            adicionais_text.setText(additions_str)
        else:
            adicionais_text.setText("Bacon, Ovo, Queijo extra")

        adicionais_text.setReadOnly(True)
        layout.addWidget(adicionais_text)

        # Observações
        layout.addWidget(QLabel("Observações:"))
        obs_text = QTextEdit()
        obs_text.setMaximumHeight(80)

        if row < len(self.order_items):
            observations = self.order_items[row].get('observations', '')
            obs_text.setText(observations)
        else:
            obs_text.setText("Sem cebola, ponto da carne bem passado")

        obs_text.setReadOnly(True)
        layout.addWidget(obs_text)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        edit_btn = QPushButton("Editar Item")
        edit_btn.setIcon(QIcon.fromTheme("document-edit"))
        edit_btn.setStyleSheet(
            "QPushButton { color: white; background-color: #2a7; }")
        edit_btn.clicked.connect(lambda: self.edit_item(row, dialog))
        buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Excluir Item")
        delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        delete_btn.setStyleSheet(
            "QPushButton { color: white; background-color: #d33; }")
        delete_btn.clicked.connect(lambda: self.delete_item(row, dialog))
        buttons_layout.addWidget(delete_btn)

        layout.addLayout(buttons_layout)

        # Botão fechar
        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet(
            "QPushButton { color: white; background-color: #555; }")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def delete_item(self, row, dialog=None):
        """Remove item da tabela."""
        reply = QMessageBox.question(
            self, "Confirmar",
            "Deseja realmente excluir este item?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.order_table.removeRow(row)
            # Remove também dos dados
            if row < len(self.order_items):
                del self.order_items[row]
            if dialog:
                dialog.accept()
            # Atualiza o valor total
            self.update_total_label()

    def update_total_label(self):
        """Atualiza o campo de valor total com base nos itens do pedido."""
        total = 0.0
        for item in self.order_items:
            qtd = item.get('qty', 1)
            preco = item['item_data'][2] if len(item['item_data']) > 2 else 0.0
            total += qtd * preco
            # Soma complementos se existirem
            for add in item.get('additions', []):
                add_qtd = add.get('qty', 1)
                add_preco = add.get('price', 0.0)
                total += add_qtd * add_preco
        self.total_label.setText(f"Total: R$ {total:,.2f}".replace(
            ",", "X").replace(".", ",").replace("X", "."))

    def edit_item(self, row, dialog=None):
        """Edita um item do pedido."""
        if row >= len(self.order_items):
            return

        self.show_item_details(row)

        if dialog:
            dialog.accept()

    def show_context_menu(self, position):
        """Mostra menu de contexto ao clicar com botão direito."""
        item = self.order_table.itemAt(position)
        if item is None:
            return

        row = item.row()
        menu = QMenu(self)

        # Ação editar
        edit_action = menu.addAction("Editar")
        edit_action.setIcon(QIcon.fromTheme("document-edit"))
        edit_action.triggered.connect(lambda: self.edit_item(row))

        # Ação excluir
        delete_action = menu.addAction("Excluir")
        delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        delete_action.triggered.connect(lambda: self.delete_item(row))

        # Mostra o menu na posição do cursor
        menu.exec(self.order_table.mapToGlobal(position))

    def closeEvent(self, event):
        """Finaliza threads ao fechar o widget."""
        # Finaliza threads dos widgets de busca, se existirem
        if hasattr(self, 'customer_search') and self.customer_search:
            if hasattr(self.customer_search, 'finalize_threads'):
                self.customer_search.finalize_threads()
            self.customer_search.closeEvent(event)

        if hasattr(self, 'item_search') and self.item_search:
            if hasattr(self.item_search, 'finalize_threads'):
                self.item_search.finalize_threads()
            self.item_search.closeEvent(event)

        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        super().closeEvent(event)

    def __del__(self):
        """Remove event filter ao destruir o widget."""
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
