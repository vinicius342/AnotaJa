from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from database.db import (get_additions_by_category, search_customers,
                         search_menu_items)
from utils.log_utils import get_logger

LOGGER = get_logger(__name__)


class SearchWorker(QObject):
    """Worker para busca assíncrona no banco de dados"""
    customers_found = Signal(list)
    items_found = Signal(list)
    search_finished = Signal()

    def __init__(self):
        super().__init__()
        self.current_search_id = 0

    def search_customers_async(self, search_text, search_id):
        """Busca clientes de forma assíncrona"""
        try:
            if search_id != self.current_search_id:
                return  # Busca cancelada, uma nova foi iniciada

            customers = search_customers(search_text)

            if search_id == self.current_search_id:
                self.customers_found.emit(customers)
        except Exception as e:
            LOGGER.error(f"Erro na busca assíncrona de clientes: {e}")
        finally:
            if search_id == self.current_search_id:
                self.search_finished.emit()

    def search_items_async(self, search_text, search_id):
        """Busca itens de forma assíncrona"""
        try:
            if search_id != self.current_search_id:
                return  # Busca cancelada, uma nova foi iniciada

            items = search_menu_items(search_text)

            if search_id == self.current_search_id:
                self.items_found.emit(items)
        except Exception as e:
            LOGGER.error(f"Erro na busca assíncrona de itens: {e}")
        finally:
            if search_id == self.current_search_id:
                self.search_finished.emit()

    def cancel_current_search(self):
        """Cancela a busca atual"""
        self.current_search_id += 1


class CustomerSearchWidget(QWidget):
    """Widget para busca de clientes com sugestões em tempo real"""
    # Sinal emitido quando um cliente é selecionado
    customer_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_customers = []
        self.selected_customer_data = None  # Dados do cliente selecionado
        self.current_search_id = 0
        self.is_searching = False
        self.setup_ui()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # Worker para busca assíncrona
        self.search_worker = SearchWorker()
        self.search_thread = QThread()
        self.search_worker.moveToThread(self.search_thread)
        self.search_worker.customers_found.connect(self.on_customers_found)
        self.search_worker.search_finished.connect(self.on_search_finished)
        self.search_thread.start()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Campo de busca
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText(
            "Digite o nome ou telefone do cliente..."
        )
        self.search_line.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.search_line)

        # Dropdown de sugestões (sobreposto)
        self.suggestions_dropdown = QListWidget(self)
        self.suggestions_dropdown.setWindowFlags(Qt.WindowType.Popup)
        self.suggestions_dropdown.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
        """)
        self.suggestions_dropdown.setMaximumHeight(200)
        self.suggestions_dropdown.hide()
        self.suggestions_dropdown.itemClicked.connect(
            self.on_suggestion_selected
        )

    def on_text_changed(self, text):
        """Inicia busca com delay para evitar muitas consultas"""
        if len(text) >= 2:
            self.search_timer.start(500)  # Delay aumentado para 500ms
        else:
            self.suggestions_dropdown.hide()
            self.search_worker.cancel_current_search()

    def perform_search(self):
        """Executa a busca no banco de dados de forma assíncrona"""
        search_text = self.search_line.text().strip()

        if len(search_text) < 2:
            return

        # Cancela busca anterior se ainda estiver executando
        if self.is_searching:
            self.search_worker.cancel_current_search()

        # Indica que uma busca está em andamento
        self.is_searching = True
        self.current_search_id += 1

        # Mostra indicador de carregamento
        self.search_line.setStyleSheet("background-color: #fffacd;")

        # Inicia busca assíncrona
        QTimer.singleShot(0, lambda: self.search_worker.search_customers_async(
            search_text, self.current_search_id
        ))

    def on_customers_found(self, customers):
        """Callback quando clientes são encontrados"""
        self.current_customers = customers
        self.suggestions_dropdown.clear()

        if customers:
            for customer in customers[:10]:  # Limita a 10 sugestões
                # Nome - Telefone
                item_text = f"{customer[1]} - {customer[2]}"
                if customer[3]:  # Se tem rua
                    item_text += f" - {customer[3]}"
                if customer[4]:  # Se tem número
                    item_text += f", {customer[4]}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, customer)
                self.suggestions_dropdown.addItem(item)

            self.show_dropdown()
        else:
            self.suggestions_dropdown.hide()

    def on_search_finished(self):
        """Callback quando a busca termina"""
        self.is_searching = False
        # Remove indicador de carregamento
        self.search_line.setStyleSheet("")

    def show_dropdown(self):
        """Mostra o dropdown posicionado abaixo do campo de busca"""
        if (self.suggestions_dropdown.count() > 0 and
                not self.search_line.text().strip() == ""):
            # Posiciona o dropdown
            rect = self.search_line.rect()
            pos = self.search_line.mapToGlobal(rect.bottomLeft())
            self.suggestions_dropdown.move(pos)
            self.suggestions_dropdown.resize(self.search_line.width(), 200)
            self.suggestions_dropdown.show()
        else:
            self.suggestions_dropdown.hide()

    def on_suggestion_selected(self, item):
        """Quando uma sugestão é selecionada"""
        customer_data = item.data(Qt.ItemDataRole.UserRole)
        if customer_data:
            # Preenche os campos com os dados do cliente
            search_text = f"{customer_data[1]} - {customer_data[2]}"
            self.search_line.setText(search_text)

            self.suggestions_dropdown.hide()
            self.selected_customer_data = {
                'id': customer_data[0],
                'name': customer_data[1],
                'phone': customer_data[2],
                'street': customer_data[3],
                'number': customer_data[4],
                'neighborhood_id': customer_data[5],
                'reference': customer_data[6],
                'neighborhood_name': customer_data[7]
            }
            # Emite sinal com dados do cliente
            self.customer_selected.emit(self.selected_customer_data)

    def clear_selection(self):
        """Limpa a seleção atual"""
        self.search_line.clear()
        self.suggestions_dropdown.hide()
        self.selected_customer_data = None
        # Cancela busca em andamento
        if self.is_searching:
            self.search_worker.cancel_current_search()
            self.on_search_finished()

    def closeEvent(self, event):
        """Cleanup quando o widget é fechado"""
        if hasattr(self, 'search_thread'):
            self.search_thread.quit()
            self.search_thread.wait()
        super().closeEvent(event)


class OrderScreen(QWidget):
    """Tela de pedidos com busca de clientes e área para itens do pedido"""

    def __init__(self, screen_title, parent=None):
        super().__init__(parent)
        self.screen_title = screen_title
        self.selected_customer = None
        self.order_items = []
        self.current_item_search_id = 0
        self.is_searching_items = False

        # Worker para busca assíncrona de itens
        self.item_search_worker = SearchWorker()
        self.item_search_thread = QThread()
        self.item_search_worker.moveToThread(self.item_search_thread)
        self.item_search_worker.items_found.connect(self.on_items_found)
        self.item_search_worker.search_finished.connect(
            self.on_item_search_finished
        )
        self.item_search_thread.start()

        # Timer para busca de itens
        self.item_search_timer = QTimer()
        self.item_search_timer.setSingleShot(True)
        self.item_search_timer.timeout.connect(self.perform_item_search)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Primeira coluna: campo de busca no topo
        left_col = QVBoxLayout()
        main_layout.addLayout(left_col, 1)
        self.customer_search = CustomerSearchWidget()
        self.customer_search.customer_selected.connect(
            self.on_customer_selected
        )
        left_col.addWidget(self.customer_search)

        # Campo de busca de itens
        item_label = QLabel("Item:")
        item_font = QFont()
        item_font.setBold(True)
        item_label.setFont(item_font)
        left_col.addWidget(item_label)

        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("Digite o nome do item...")
        self.item_search.textChanged.connect(self.on_item_search_changed)
        self.item_search.returnPressed.connect(self.on_item_search_enter)
        left_col.addWidget(self.item_search)

        # Lista de sugestões de itens (dropdown sobreposto)
        self.item_suggestions = QListWidget(self)
        self.item_suggestions.setWindowFlags(Qt.WindowType.Popup)
        self.item_suggestions.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
        """)
        self.item_suggestions.setMaximumHeight(200)
        self.item_suggestions.hide()
        self.item_suggestions.itemClicked.connect(self.on_item_selected)

        left_col.addStretch()

        # Segunda coluna: título/nome do cliente no topo, itens abaixo
        right_col = QVBoxLayout()
        main_layout.addLayout(right_col, 2)
        self.title_label = QLabel(self.screen_title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_col.addWidget(self.title_label)

        order_frame = QFrame()
        order_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        order_frame.setMaximumWidth(320)

        order_layout = QVBoxLayout()
        order_frame.setLayout(order_layout)

        order_label = QLabel("Itens do Pedido:")
        order_font = QFont()
        order_font.setBold(True)
        order_label.setFont(order_font)
        order_layout.addWidget(order_label)

        # Tabela de itens do pedido
        self.order_table = QTableWidget(0, 4)
        self.order_table.setHorizontalHeaderLabels([
            "Qtd", "Nome", "Categoria", "Ver"
        ])
        header = self.order_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_table.setMaximumHeight(200)

        # Habilita menu de contexto personalizado
        context_policy = Qt.ContextMenuPolicy.CustomContextMenu
        self.order_table.setContextMenuPolicy(context_policy)
        self.order_table.customContextMenuRequested.connect(
            self.show_context_menu
        )

        order_layout.addWidget(self.order_table)

        buttons_layout = QHBoxLayout()
        self.add_item_button = QPushButton("Adicionar Item")
        self.add_item_button.clicked.connect(self.add_item)
        buttons_layout.addWidget(self.add_item_button)
        self.clear_order_button = QPushButton("Limpar Pedido")
        self.clear_order_button.clicked.connect(self.clear_order)
        buttons_layout.addWidget(self.clear_order_button)
        self.finalize_button = QPushButton("Finalizar Pedido")
        self.finalize_button.clicked.connect(self.finalize_order)
        buttons_layout.addWidget(self.finalize_button)
        order_layout.addLayout(buttons_layout)

        right_col.addWidget(order_frame)
        right_col.addStretch()

    def on_customer_selected(self, customer_data):
        """Callback quando um cliente é selecionado"""
        self.selected_customer = customer_data
        customer_name = customer_data['name']
        self.title_label.setText(customer_name)
        customer_phone = customer_data['phone']
        LOGGER.info(f"Cliente selecionado: {customer_name} - {customer_phone}")

    def add_item(self):
        """Adiciona um item à tabela de pedido (exemplo)"""
        if not self.selected_customer:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente primeiro!"
            )
            return
        row = self.order_table.rowCount()
        self.order_table.insertRow(row)
        # Exemplo de dados
        qtd_item = QTableWidgetItem("2x")
        nome_item = QTableWidgetItem("X-Burguer")
        categoria_item = QTableWidgetItem("Lanche")

        # Botão de visualizar (olho) - mostra adicionais e observações
        view_btn = QPushButton()
        view_btn.setIcon(QIcon.fromTheme("view-visible"))
        view_btn.setToolTip("Ver detalhes")
        view_btn.clicked.connect(lambda: self.show_item_details(row))

        self.order_table.setItem(row, 0, qtd_item)
        self.order_table.setItem(row, 1, nome_item)
        self.order_table.setItem(row, 2, categoria_item)
        self.order_table.setCellWidget(row, 3, view_btn)

    def clear_order(self):
        """Limpa o pedido atual"""
        self.order_table.setRowCount(0)
        self.customer_search.clear_selection()
        self.selected_customer = None
        self.title_label.setText(self.screen_title)

    def finalize_order(self):
        """Finaliza o pedido"""
        if not self.selected_customer:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente primeiro!"
            )
            return

        if self.order_table.rowCount() == 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Aviso", "Adicione itens ao pedido!"
            )
            return

        # Aqui você pode implementar a lógica para salvar o pedido
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Sucesso",
            f"Pedido finalizado para {self.selected_customer['name']}!\n"
            f"Total de itens: {self.order_table.rowCount()}"
        )

        # Limpa o pedido após finalizar
        self.clear_order()

    def show_item_details(self, row):
        """Mostra diálogo com detalhes do item (adicionais e observações)"""
        from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel,
                                       QPushButton, QTextEdit, QVBoxLayout)

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

        # Adicionais (exemplo)
        layout.addWidget(QLabel("Adicionais:"))
        adicionais_text = QTextEdit()
        adicionais_text.setMaximumHeight(80)
        adicionais_text.setText("Bacon, Ovo, Queijo extra")
        adicionais_text.setReadOnly(True)
        layout.addWidget(adicionais_text)

        # Observações (exemplo)
        layout.addWidget(QLabel("Observações:"))
        obs_text = QTextEdit()
        obs_text.setMaximumHeight(80)
        obs_text.setText("Sem cebola, ponto da carne bem passado")
        obs_text.setReadOnly(True)
        layout.addWidget(obs_text)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        # Botão editar
        edit_btn = QPushButton("Editar Item")
        edit_btn.setIcon(QIcon.fromTheme("document-edit"))
        edit_btn.clicked.connect(lambda: self.edit_item(row, dialog))
        buttons_layout.addWidget(edit_btn)

        # Botão excluir
        delete_btn = QPushButton("Excluir Item")
        delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        delete_btn.setStyleSheet("QPushButton { color: red; }")
        delete_btn.clicked.connect(lambda: self.delete_item(row, dialog))
        buttons_layout.addWidget(delete_btn)

        layout.addLayout(buttons_layout)

        # Botão fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def delete_item(self, row, dialog=None):
        """Remove item da tabela"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self, "Confirmar",
            "Deseja realmente excluir este item?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.order_table.removeRow(row)
            if dialog:
                dialog.accept()  # Fecha o diálogo após excluir

    def edit_item(self, row, dialog=None):
        """Edita um item do pedido"""
        from PySide6.QtWidgets import QMessageBox

        # Por enquanto, apenas uma mensagem de placeholder
        QMessageBox.information(
            self, "Editar Item",
            "Funcionalidade de edição será implementada em breve!"
        )
        # Aqui você pode implementar o diálogo de edição

    def show_context_menu(self, position):
        """Mostra menu de contexto ao clicar com botão direito"""
        from PySide6.QtWidgets import QMenu

        item = self.order_table.itemAt(position)
        if item is None:
            return

        row = item.row()

        menu = QMenu(self)

        # Ação visualizar
        view_action = menu.addAction("Visualizar")
        view_action.setIcon(QIcon.fromTheme("view-visible"))
        view_action.triggered.connect(lambda: self.show_item_details(row))

        # Ação excluir
        delete_action = menu.addAction("Excluir")
        delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        delete_action.triggered.connect(lambda: self.delete_item(row))

        # Mostra o menu na posição do cursor
        menu.exec(self.order_table.mapToGlobal(position))

    def on_item_search_changed(self, text):
        """Busca itens quando o texto mudar"""
        if len(text) >= 2:
            self.item_search_timer.start(500)  # Delay de 500ms
        else:
            self.item_suggestions.hide()
            self.item_search_worker.cancel_current_search()

    def on_item_search_enter(self):
        """Atalho Enter para buscar item"""
        text = self.item_search.text().strip()
        if text:
            self.perform_item_search()

    def perform_item_search(self):
        """Executa busca de itens de forma assíncrona"""
        search_text = self.item_search.text().strip()
        if len(search_text) < 2:
            return

        # Cancela busca anterior se ainda estiver executando
        if self.is_searching_items:
            self.item_search_worker.cancel_current_search()

        # Indica que uma busca está em andamento
        self.is_searching_items = True
        self.current_item_search_id += 1

        # Mostra indicador de carregamento
        self.item_search.setStyleSheet("background-color: #fffacd;")

        # Inicia busca assíncrona
        QTimer.singleShot(
            0, lambda: self.item_search_worker.search_items_async(
                search_text, self.current_item_search_id
            )
        )

    def on_items_found(self, items):
        """Callback quando itens são encontrados"""
        self.item_suggestions.clear()

        if items:
            for item in items[:10]:  # Limita a 10 sugestões
                # item: (id, name, price, category_id, category_name, desc)
                item_text = f"{item[1]} - R$ {item[2]:.2f} ({item[4]})"
                suggestion = QListWidgetItem(item_text)
                suggestion.setData(Qt.ItemDataRole.UserRole, item)
                self.item_suggestions.addItem(suggestion)

            self.show_item_dropdown()
        else:
            self.item_suggestions.hide()

    def on_item_search_finished(self):
        """Callback quando a busca de itens termina"""
        self.is_searching_items = False
        # Remove indicador de carregamento
        self.item_search.setStyleSheet("")

    def search_menu_items(self, search_text):
        """Método legado - agora usa busca assíncrona"""
        # Redireciona para busca assíncrona
        self.perform_item_search()

    def show_item_dropdown(self):
        """Mostra o dropdown de itens posicionado abaixo do campo"""
        if (self.item_suggestions.count() > 0 and
                not self.item_search.text().strip() == ""):
            # Posiciona o dropdown
            rect = self.item_search.rect()
            pos = self.item_search.mapToGlobal(rect.bottomLeft())
            self.item_suggestions.move(pos)
            self.item_suggestions.resize(self.item_search.width(), 200)
            self.item_suggestions.show()
        else:
            self.item_suggestions.hide()

    def on_item_selected(self, item):
        """Quando um item é selecionado"""
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if item_data:
            self.item_suggestions.hide()
            self.item_search.clear()
            self.open_add_item_modal(item_data)

    def open_add_item_modal(self, item_data):
        """Abre modal para adicionar item com adicionais"""
        from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel,
                                       QListWidget, QPushButton, QSpinBox,
                                       QTextEdit, QVBoxLayout)

        # item_data: (id, name, price, category_id, category_name, description)
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Item")
        dialog.setModal(True)
        dialog.resize(500, 400)

        # Posiciona o modal acima da tela atual
        parent_geometry = self.geometry()
        dialog.move(parent_geometry.x() + 50, parent_geometry.y() + 50)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Nome do item e categoria
        header_layout = QHBoxLayout()
        item_name_label = QLabel(f"Item: {item_data[1]}")
        item_name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(item_name_label)

        category_label = QLabel(f"Categoria: {item_data[4]}")
        category_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(category_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Seção de adicionais
        additions_label = QLabel("Adicionais:")
        additions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(additions_label)

        # Combo de adicionais + quantidade
        additions_layout = QHBoxLayout()

        # Combo para selecionar adicional
        self.additions_combo = QComboBox()
        self.additions_combo.addItem("Selecione um adicional...")
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
        add_addition_btn.clicked.connect(
            lambda: self.add_addition_to_list(dialog)
        )
        additions_layout.addWidget(add_addition_btn)

        layout.addLayout(additions_layout)

        # Lista de adicionais selecionados
        self.selected_additions = QListWidget()
        self.selected_additions.setMaximumHeight(100)
        layout.addWidget(self.selected_additions)

        # Campo observações
        obs_label = QLabel("Observações:")
        obs_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(obs_label)

        self.observations = QTextEdit()
        self.observations.setMaximumHeight(60)
        self.observations.setPlaceholderText("Observações especiais...")
        layout.addWidget(self.observations)

        # Valor total
        self.total_label = QLabel(f"Total: R$ {item_data[2]:.2f}")
        self.total_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #2e7d32;"
        )
        layout.addWidget(self.total_label)

        # Botões finais
        buttons_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)

        add_btn = QPushButton("Adicionar ao Pedido")
        add_btn.setStyleSheet("background-color: #4caf50; color: white;")
        add_btn.clicked.connect(lambda: self.add_to_order(item_data, dialog))
        buttons_layout.addWidget(add_btn)

        layout.addLayout(buttons_layout)

        # Carrega adicionais da categoria
        self.load_additions(item_data[3])  # category_id

        # Salva dados do item no dialog
        setattr(dialog, 'item_data', item_data)
        setattr(dialog, 'selected_additions_data', [])

        dialog.exec()

    def load_additions(self, category_id):
        """Carrega adicionais da categoria"""
        try:
            additions = get_additions_by_category(category_id)
            self.additions_combo.clear()
            self.additions_combo.addItem("Selecione um adicional...")

            for addition in additions:
                # addition: (id, name, price)
                text = f"{addition[1]} - R$ {addition[2]:.2f}"
                self.additions_combo.addItem(text, addition)

        except Exception as e:
            LOGGER.error(f"Erro ao carregar adicionais: {e}")

    def add_addition_to_list(self, dialog):
        """Adiciona adicional à lista"""
        current_index = self.additions_combo.currentIndex()
        if current_index <= 0:  # Não selecionou adicional válido
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
        dialog.selected_additions_data.append({
            'id': addition_data[0],
            'name': addition_data[1],
            'price': addition_data[2],
            'qty': qty,
            'total': addition_data[2] * qty
        })

        # Atualiza total
        self.update_total_price(dialog)

        # Reset campos
        self.additions_combo.setCurrentIndex(0)
        self.addition_qty.setValue(1)

    def update_total_price(self, dialog):
        """Atualiza o preço total"""
        base_price = dialog.item_data[2]
        additions_total = sum(add['total']
                              for add in dialog.selected_additions_data)
        total = base_price + additions_total
        self.total_label.setText(f"Total: R$ {total:.2f}")

    def add_to_order(self, item_data, dialog):
        """Adiciona item ao pedido"""
        if not self.selected_customer:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente primeiro!"
            )
            return

        # Por enquanto, apenas adiciona à tabela como antes
        # Mais tarde implementaremos a lógica completa
        row = self.order_table.rowCount()
        self.order_table.insertRow(row)

        # Monta texto dos adicionais
        additions_text = ""
        if dialog.selected_additions_data:
            additions_list = [f"{a['qty']}x {a['name']}"
                              for a in dialog.selected_additions_data]
            additions_text = ", ".join(additions_list)

        # Dados na tabela
        qtd_item = QTableWidgetItem("1x")
        nome_item = QTableWidgetItem(item_data[1])
        categoria_item = QTableWidgetItem(item_data[4])

        # Botão de visualizar
        view_btn = QPushButton()
        view_btn.setIcon(QIcon.fromTheme("view-visible"))
        view_btn.setToolTip("Ver detalhes")
        view_btn.clicked.connect(lambda: self.show_item_details(row))

        self.order_table.setItem(row, 0, qtd_item)
        self.order_table.setItem(row, 1, nome_item)
        self.order_table.setItem(row, 2, categoria_item)
        self.order_table.setCellWidget(row, 3, view_btn)

        dialog.accept()

        # Mostra confirmação
        from PySide6.QtWidgets import QMessageBox
        base_price = item_data[2]
        additions_total = sum(add['total']
                              for add in dialog.selected_additions_data)
        total = base_price + additions_total

        msg = f"Item adicionado: {item_data[1]}\n"
        if additions_text:
            msg += f"Adicionais: {additions_text}\n"
        msg += f"Total: R$ {total:.2f}"

        QMessageBox.information(self, "Item Adicionado", msg)

    def closeEvent(self, event):
        """Cleanup quando o widget é fechado"""
        if hasattr(self, 'item_search_thread'):
            self.item_search_thread.quit()
            self.item_search_thread.wait()
        super().closeEvent(event)
