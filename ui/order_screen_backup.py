from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QListView, QListWidget, QListWidgetItem, QMenu,
                               QMessageBox, QPushButton, QSpinBox,
                               QTableWidget, QTableWidgetItem, QTextEdit,
                               QVBoxLayout, QWidget)

from database.db import (get_all_additions_for_item,
                         get_all_additions_for_item_with_mandatory_info,
                         search_customers, search_menu_items)
from utils.log_utils import get_logger
from utils.utils import (CUSTOMER_LINEEDIT_BASE_STYLE,
                         CUSTOMER_LINEEDIT_NO_BORDER_STYLE,
                         SUGGESTIONS_LIST_BASE_STYLE)

LOGGER = get_logger(__name__)


class ItemFilterWorker(QObject):
    """
    Worker que executa a filtragem de itens em uma thread separada.
    """
    finished = Signal(
        list, str)  # Sinal emitido com a lista filtrada e o texto original

    def __init__(self, items):
        super().__init__()
        self.items = items

    def filter_items(self, text):
        """Filtra a lista de itens com base no texto."""
        if not text:
            self.finished.emit([], text)
            return

        filtered_items = [
            item for item in self.items
            if text.lower() in item[1].lower()  # item[1] é o nome do item
        ]
        self.finished.emit(filtered_items, text)

    def set_items(self, items):
        """Atualiza a lista de itens no worker."""
        self.items = items


class CustomerFilterWorker(QObject):
    """
    Worker que executa a filtragem de clientes em uma thread separada.
    """
    finished = Signal(
        list, str)  # Sinal emitido com a lista filtrada e o texto original

    def __init__(self, customers):
        super().__init__()
        self.customers = customers

    def filter_customers(self, text):
        """Filtra a lista de clientes com base no texto."""
        if not text:
            self.finished.emit([], text)
            return

        filtered_customers = [
            c for c in self.customers
            if text in c[0].lower() or text in c[1]
        ]
        self.finished.emit(filtered_customers, text)

    def set_customers(self, customers):
        """Atualiza a lista de clientes no worker."""
        self.customers = customers


class CustomerSearchWidget(QWidget):
    """Widget de busca integrado com QLineEdit no topo e QListWidget abaixo."""
    customer_selected = Signal(dict)
    suggestions_list_shown = Signal()
    suggestions_list_hidden = Signal()

    def suggestions_list_key_press(self, event):
        # Se pressionar seta para cima no primeiro item, volta o foco para o QLineEdit
        if (event.key() == Qt.Key_Up and self.suggestions_list.currentRow() == 0):
            self.customer_lineedit.setFocus()
            return True
        return False

    def __init__(self, parent=None, customers=None):
        super().__init__(parent)
        self.customers = customers if customers is not None else []
        self.customer_data = {}
        self.setup_ui()
        self.setup_worker_thread()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Label acima do campo de busca
        self.customer_label = QLabel("Cliente:")
        label_font = QFont()
        label_font.setBold(True)
        self.customer_label.setFont(label_font)
        self.customer_label.setStyleSheet("margin-bottom: 6px;")
        # Aplica o estilo centralizado do QLabel)
        layout.addWidget(self.customer_label)

        # Campo de busca no topo
        self.customer_lineedit = QLineEdit()
        self.customer_lineedit.setPlaceholderText(
            "Digite para buscar cliente...")
        self.lineedit_base_style = CUSTOMER_LINEEDIT_BASE_STYLE
        self.lineedit_no_border_style = CUSTOMER_LINEEDIT_NO_BORDER_STYLE
        self.suggestions_list_base_style = SUGGESTIONS_LIST_BASE_STYLE
        self.customer_lineedit.setStyleSheet(self.lineedit_base_style)
        layout.addWidget(self.customer_lineedit)

        # Lista de sugestões abaixo
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(200)
        self.suggestions_list.setMinimumHeight(0)
        self.suggestions_list.hide()  # Inicialmente oculto
        self.suggestions_list.setStyleSheet(self.suggestions_list_base_style)
        layout.addWidget(self.suggestions_list)

        # Não cria o item especial aqui, será criado dinamicamente

        # Permite navegação reversa: seta para cima volta para o QLineEdit
        self.suggestions_list.installEventFilter(self)

        # Conecta eventos
        self.customer_lineedit.textChanged.connect(self.on_text_changed)
        self.suggestions_list.itemClicked.connect(self.on_item_selected)
        self.suggestions_list.itemActivated.connect(self.on_item_selected)

        # Permite navegação com teclado
        self.customer_lineedit.installEventFilter(self)

    def setup_worker_thread(self):
        """Configura e inicia a thread para a filtragem."""
        self.thread = QThread()
        self.worker = CustomerFilterWorker(self.customers)
        self.worker.moveToThread(self.thread)

        # Conecta os sinais e slots entre as threads
        self.worker.finished.connect(self.on_filtering_finished)

        # Limpeza da thread
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

    def on_text_changed(self, text):
        """Chamado quando o texto do campo de busca muda."""
        if text.strip():
            # Envia para o worker filtrar
            self.worker.filter_customers(text)
        else:
            # Se não há texto, esconde a lista
            self.hide_suggestions()

    def on_filtering_finished(self, filtered_customers, original_text):
        """Slot para receber os resultados da thread e atualizar a UI."""
        # Garante que estamos atualizando a UI com a busca mais recente
        if original_text != self.customer_lineedit.text():
            return

        self.customer_data.clear()
        self.suggestions_list.clear()

        if not filtered_customers:
            # Nenhum cliente encontrado, mostra apenas o item de adicionar
            add_customer_item = QListWidgetItem("+ Adicionar novo cliente")
            add_customer_item.setData(
                Qt.ItemDataRole.UserRole, {"is_add_new": True})
            self.suggestions_list.addItem(add_customer_item)
            self.show_suggestions()
            return

        # Adiciona os itens filtrados na lista
        for nome, tel in filtered_customers:
            suggestion_text = f"{nome} - {tel}"
            self.customer_data[suggestion_text] = {"name": nome, "phone": tel}
            self.suggestions_list.addItem(suggestion_text)

        self.show_suggestions()

    def show_suggestions(self):
        """Mostra a lista de sugestões com altura fixa."""
        if self.suggestions_list.count() > 0:
            self.suggestions_list.show()
            # Adiciona o item especial ao final (cria novo a cada vez)
            if self.suggestions_list.findItems("+ Adicionar novo cliente", Qt.MatchExactly) == []:
                add_customer_item = QListWidgetItem("+ Adicionar novo cliente")
                add_customer_item.setData(
                    Qt.ItemDataRole.UserRole, {"is_add_new": True})
                self.suggestions_list.addItem(add_customer_item)
            # Altura fixa para evitar movimento da barra
            fixed_height = 120  # Altura menor para evitar problemas de buffer
            self.suggestions_list.setMaximumHeight(fixed_height)
            self.suggestions_list.setMinimumHeight(fixed_height)
            # Remove o border-bottom colorido da QLineEdit
            self.customer_lineedit.setStyleSheet(self.lineedit_no_border_style)
            # Emite sinal de que as sugestões foram mostradas
            self.suggestions_list_shown.emit()
        else:
            self.hide_suggestions()

    def hide_suggestions(self):
        """Esconde a lista de sugestões e restaura a borda inferior do QLineEdit."""
        self.suggestions_list.hide()
        # Remove o item especial se presente
        items = self.suggestions_list.findItems(
            "+ Adicionar novo cliente", Qt.MatchExactly)
        for item in items:
            self.suggestions_list.takeItem(self.suggestions_list.row(item))
        self.suggestions_list.setMaximumHeight(0)
        self.suggestions_list.setMinimumHeight(0)
        # Restaura a borda inferior colorida da QLineEdit
        self.customer_lineedit.setStyleSheet(self.lineedit_base_style)
        self.suggestions_list.setStyleSheet(self.suggestions_list_base_style)
        # Emite sinal de que as sugestões foram escondidas
        self.suggestions_list_hidden.emit()

    def on_item_selected(self, item):
        """Chamado quando um item da lista é selecionado."""
        if item:
            suggestion_text = item.text()
            if suggestion_text in self.customer_data:
                selected_data = self.customer_data[suggestion_text]
                self.customer_selected.emit(selected_data)

                # Atualiza o campo de texto com o nome do cliente
                customer_name = selected_data["name"]
                self.customer_lineedit.setText(customer_name)

                # Esconde as sugestões
                self.hide_suggestions()

    def eventFilter(self, source, event):
        """Filtro de eventos para navegação com teclado."""
        if source == self.customer_lineedit and event.type() == event.Type.KeyPress:
            key_down = (event.key() ==
                        Qt.Key_Down and self.suggestions_list.isVisible())
            if key_down:
                # Move foco para a lista
                self.suggestions_list.setFocus()
                if self.suggestions_list.count() > 0:
                    self.suggestions_list.setCurrentRow(0)
                return True
            elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                # Se há item selecionado na lista, usa ele
                has_selected = (self.suggestions_list.isVisible()
                                and self.suggestions_list.currentItem())
                if has_selected:
                    self.on_item_selected(self.suggestions_list.currentItem())
                    return True
            elif event.key() == Qt.Key_Escape:
                # Esconde as sugestões
                self.hide_suggestions()
                return True
        elif source == self.suggestions_list and event.type() == event.Type.KeyPress:
            # ESC: volta para o QLineEdit e fecha sugestões
            if event.key() == Qt.Key_Escape:
                self.hide_suggestions()
                self.customer_lineedit.setFocus()
                return True
            if self.suggestions_list_key_press(event):
                return True
        return super().eventFilter(source, event)

    def set_customers(self, customers):
        """Atualiza a lista de clientes, inclusive no worker da thread."""
        self.customers = customers
        self.worker.set_customers(customers)
        self.clear_selection()

    def clear_selection(self):
        """Limpa o campo de busca e o estado do widget."""
        self.customer_lineedit.clear()
        self.hide_suggestions()
        self.customer_data.clear()

    def closeEvent(self, event):
        """Garante que a thread seja finalizada corretamente."""
        LOGGER.info("Fechando a thread do worker de busca de clientes.")
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


class ItemSearchWidget(QWidget):
    """Widget de busca integrado para itens com QLineEdit no topo e QListWidget abaixo."""
    item_selected = Signal(tuple)
    suggestions_list_shown = Signal()
    suggestions_list_hidden = Signal()
    items_updated = Signal()

    def suggestions_list_key_press(self, event):
        # Se pressionar seta para cima no primeiro item, volta o foco para o QLineEdit
        if (event.key() == Qt.Key_Up and self.suggestions_list.currentRow() == 0):
            self.item_lineedit.setFocus()
            return True
        return False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.item_data = {}
        self.setup_ui()
        self.setup_worker_thread()
        self.load_items()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Label acima do campo de busca
        self.item_label = QLabel("Item:")
        label_font = QFont()
        label_font.setBold(True)
        self.item_label.setFont(label_font)
        self.item_label.setStyleSheet("margin-bottom: 6px;")
        layout.addWidget(self.item_label)

        # Campo de busca no topo
        self.item_lineedit = QLineEdit()
        self.item_lineedit.setPlaceholderText("Digite para buscar item...")
        self.lineedit_base_style = CUSTOMER_LINEEDIT_BASE_STYLE
        self.lineedit_no_border_style = CUSTOMER_LINEEDIT_NO_BORDER_STYLE
        self.suggestions_list_base_style = SUGGESTIONS_LIST_BASE_STYLE
        self.item_lineedit.setStyleSheet(self.lineedit_base_style)
        layout.addWidget(self.item_lineedit)

        # Lista de sugestões abaixo
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(200)
        self.suggestions_list.setMinimumHeight(0)
        self.suggestions_list.hide()  # Inicialmente oculto
        self.suggestions_list.setStyleSheet(self.suggestions_list_base_style)
        layout.addWidget(self.suggestions_list)

        # Permite navegação reversa: seta para cima volta para o QLineEdit
        self.suggestions_list.installEventFilter(self)

        # Conecta eventos
        self.item_lineedit.textChanged.connect(self.on_text_changed)
        self.suggestions_list.itemClicked.connect(self.on_item_selected)
        self.suggestions_list.itemActivated.connect(self.on_item_selected)

        # Permite navegação com teclado
        self.item_lineedit.installEventFilter(self)

    def setup_worker_thread(self):
        """Configura e inicia a thread para a filtragem."""
        self.thread = QThread()
        self.worker = ItemFilterWorker(self.items)
        self.worker.moveToThread(self.thread)

        # Conecta os sinais e slots entre as threads
        self.worker.finished.connect(self.on_filtering_finished)

        # Limpeza da thread
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

    def load_items(self):
        """Carrega itens do menu do banco de dados"""
        try:
            self.items = search_menu_items("")  # Carrega todos os itens
            self.worker.set_items(self.items)
            self.items_updated.emit()
        except Exception as e:
            LOGGER.error(f"Erro ao carregar itens do menu: {e}")
            self.items = []

    def on_text_changed(self, text):
        """Chamado quando o texto do campo de busca muda."""
        if text.strip():
            # Envia para o worker filtrar
            self.worker.filter_items(text)
        else:
            # Se não há texto, esconde a lista
            self.hide_suggestions()

    def on_filtering_finished(self, filtered_items, original_text):
        """Slot para receber os resultados da thread e atualizar a UI."""
        # Garante que estamos atualizando a UI com a busca mais recente
        if original_text != self.item_lineedit.text():
            return

        self.item_data.clear()
        self.suggestions_list.clear()

        if not filtered_items:
            # Nenhum item encontrado, não mostra sugestões
            self.hide_suggestions()
            return

        # Adiciona os itens filtrados na lista
        for item in filtered_items:
            # item: (id, name, price, category_id, category_name, description)
            suggestion_text = f"{item[1]}"
            self.item_data[suggestion_text] = item
            self.suggestions_list.addItem(suggestion_text)

        self.show_suggestions()

    def show_suggestions(self):
        """Mostra a lista de sugestões com altura fixa."""
        if self.suggestions_list.count() > 0:
            self.suggestions_list.show()
            # Altura fixa para evitar movimento da barra
            fixed_height = 120  # Altura menor para evitar problemas de buffer
            self.suggestions_list.setMaximumHeight(fixed_height)
            self.suggestions_list.setMinimumHeight(fixed_height)
            # Remove o border-bottom colorido da QLineEdit
            self.item_lineedit.setStyleSheet(self.lineedit_no_border_style)
            # Emite sinal de que as sugestões foram mostradas
            self.suggestions_list_shown.emit()
        else:
            self.hide_suggestions()

    def hide_suggestions(self):
        """Esconde a lista de sugestões e restaura a borda inferior do QLineEdit."""
        self.suggestions_list.hide()
        self.suggestions_list.setMaximumHeight(0)
        self.suggestions_list.setMinimumHeight(0)
        # Restaura a borda inferior colorida da QLineEdit
        self.item_lineedit.setStyleSheet(self.lineedit_base_style)
        self.suggestions_list.setStyleSheet(self.suggestions_list_base_style)
        # Emite sinal de que as sugestões foram escondidas
        self.suggestions_list_hidden.emit()

    def on_item_selected(self, item):
        """Chamado quando um item da lista é selecionado."""
        if item:
            suggestion_text = item.text()
            if suggestion_text in self.item_data:
                selected_data = self.item_data[suggestion_text]
                self.item_selected.emit(selected_data)

                # Atualiza o campo de texto com o nome do item
                item_name = selected_data[1]
                self.item_lineedit.setText(item_name)

                # Esconde as sugestões
                self.hide_suggestions()

    def eventFilter(self, source, event):
        """Filtro de eventos para navegação com teclado."""
        if source == self.item_lineedit and event.type() == event.Type.KeyPress:
            key_down = (event.key() ==
                        Qt.Key_Down and self.suggestions_list.isVisible())
            if key_down:
                # Move foco para a lista
                self.suggestions_list.setFocus()
                if self.suggestions_list.count() > 0:
                    self.suggestions_list.setCurrentRow(0)
                return True
            elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                # Se há item selecionado na lista, usa ele
                has_selected = (self.suggestions_list.isVisible()
                                and self.suggestions_list.currentItem())
                if has_selected:
                    self.on_item_selected(self.suggestions_list.currentItem())
                    return True
            elif event.key() == Qt.Key_Escape:
                # Esconde as sugestões
                self.hide_suggestions()
                return True
        elif source == self.suggestions_list and event.type() == event.Type.KeyPress:
            # ESC: volta para o QLineEdit e fecha sugestões
            if event.key() == Qt.Key_Escape:
                self.hide_suggestions()
                self.item_lineedit.setFocus()
                return True
            if self.suggestions_list_key_press(event):
                return True
        return super().eventFilter(source, event)

    def clear_selection(self):
        """Limpa o campo de busca e o estado do widget."""
        self.item_lineedit.clear()
        self.hide_suggestions()
        self.item_data.clear()

    def closeEvent(self, event):
        """Garante que a thread seja finalizada corretamente."""
        LOGGER.info("Fechando a thread do worker de busca de itens.")
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


class OrderScreen(QWidget):
    def hide_left_column_widgets(self):
        """Esconde todos os widgets da primeira coluna exceto o campo de busca"""
        for widget in self.left_column_widgets:
            widget.hide()

    def show_left_column_widgets(self):
        """Mostra todos os widgets da primeira coluna"""
        for widget in self.left_column_widgets:
            widget.show()
    """Tela de pedidos simplificada"""

    def __init__(self, screen_title, parent=None, customers=None):
        super().__init__(parent)
        self.screen_title = screen_title
        self.selected_customer = None
        self.order_items = []
        self.customers = customers if customers is not None else []
        LOGGER.info(
            f"Carregando {len(self.customers)} clientes na tela de pedidos")

        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Primeira coluna: campo de busca no topo
        left_col = QVBoxLayout()
        main_layout.addLayout(left_col, 1)
        self.customer_search = CustomerSearchWidget(customers=self.customers)
        self.customer_search.customer_selected.connect(
            self.on_customer_selected
        )
        # Conecta os sinais para esconder/mostrar widgets da primeira coluna
        self.customer_search.suggestions_list_shown.connect(
            self.hide_left_column_widgets
        )
        self.customer_search.suggestions_list_hidden.connect(
            self.show_left_column_widgets
        )
        left_col.addWidget(self.customer_search)

        # Campo de busca de itens (igual ao de clientes)
        self.item_search = ItemSearchWidget()
        self.item_search.item_selected.connect(self.on_item_selected)
        # Conecta os sinais para esconder/mostrar widgets quando as sugestões de item aparecem
        self.item_search.suggestions_list_shown.connect(
            self.hide_left_column_widgets
        )
        self.item_search.suggestions_list_hidden.connect(
            self.show_left_column_widgets
        )
        left_col.addWidget(self.item_search)

        # Armazena referências aos widgets que devem ser escondidos
        self.left_column_widgets = []

        # Desabilita o campo de item até que um cliente seja selecionado
        self.item_search.item_lineedit.setEnabled(False)

        left_col.addStretch()

        # Segunda coluna: título/nome do cliente no topo, itens abaixo
        right_col = QVBoxLayout()
        main_layout.addLayout(right_col, 2)
        self.title_label = QLabel(self.screen_title)
        title_font = QFont()
        title_font.setPointSize(11)  # Fonte menor
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("QLabel { padding: 2px 4px; }")
        self.title_label.setWordWrap(False)
        self.title_label.setMinimumHeight(24)
        self.title_label.setMaximumHeight(28)
        self.title_label.setSizePolicy(self.title_label.sizePolicy(
        ).horizontalPolicy(), QWidget().sizePolicy().verticalPolicy())
        self.title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        # Removido: setElideMode (não existe em QLabel)
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
        max_width = self.title_label.width() if self.title_label.width() > 0 else 250
        elided_title = metrics.elidedText(
            title, Qt.TextElideMode.ElideRight, max_width)
        self.title_label.setText(elided_title)
        LOGGER.info(f"Cliente selecionado: {title}")

        # Habilita o campo de item após seleção de cliente
        self.item_search.item_lineedit.setEnabled(True)

    def on_item_selected(self, item_data):
        """Callback quando um item é selecionado"""
        LOGGER.info(
            f"Item selecionado: {item_data[1]} - R$ {item_data[2]:.2f}")
        # Abre o modal para adicionar o item com adicionais
        self.open_add_item_modal(item_data)

    def add_item(self):
        """Adiciona um item à tabela de pedido (exemplo)"""
        if not self.selected_customer:
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

        # Botão de visualizar (olho) - mostra complementos e observações
        view_btn = QPushButton()
        view_btn.setIcon(QIcon.fromTheme("view-visible"))
        view_btn.setToolTip("Ver detalhes")
        view_btn.clicked.connect(lambda: self.show_item_details(row))

        self.order_table.setItem(row, 0, qtd_item)
        self.order_table.setItem(row, 1, nome_item)
        self.order_table.setItem(row, 2, categoria_item)
        self.order_table.setCellWidget(row, 3, view_btn)

        # Atualiza lista de sugestões de itens após cadastro
        if hasattr(self, 'item_search') and self.item_search:
            self.item_search.load_items()

    def clear_order(self):
        """Limpa o pedido atual"""
        self.order_table.setRowCount(0)
        self.customer_search.clear_selection()
        self.selected_customer = None
        self.title_label.setText(self.screen_title)

        # Desabilita o campo de item ao limpar o pedido
        self.item_search.item_lineedit.setEnabled(False)

    def finalize_order(self):
        """Finaliza o pedido"""
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

        # Aqui você pode implementar a lógica para salvar o pedido
        QMessageBox.information(
            self, "Sucesso",
            f"Pedido finalizado para {self.selected_customer['name']}!\n"
            f"Total de itens: {self.order_table.rowCount()}"
        )

        # Limpa o pedido após finalizar
        self.clear_order()

    def show_item_details(self, row):
        """Mostra diálogo com detalhes do item (complementos e observações)"""
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

        # Complementos (exemplo)
        layout.addWidget(QLabel("Complementos:"))
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
        # Por enquanto, apenas uma mensagem de placeholder
        QMessageBox.information(
            self, "Editar Item",
            "Funcionalidade de edição será implementada em breve!"
        )
        # Aqui você pode implementar o diálogo de edição

    def show_context_menu(self, position):
        """Mostra menu de contexto ao clicar com botão direito"""
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

    def open_add_item_modal(self, item_data):
        """Abre modal para adicionar item com complementos"""
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

        # Seção de complementos
        additions_label = QLabel("Complementos:")
        additions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(additions_label)

        # Combo de complementos + quantidade
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
        add_addition_btn.clicked.connect(
            lambda: self.add_addition_to_list(dialog)
        )
        additions_layout.addWidget(add_addition_btn)

        layout.addLayout(additions_layout)

        # Lista de complementos selecionados
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

        # Carrega complementos da categoria e específicos do item
        self.load_additions(item_data[3], item_data[0])  # category_id, item_id

        # Salva dados do item no dialog
        setattr(dialog, 'item_data', item_data)
        setattr(dialog, 'selected_additions_data', [])

        dialog.exec()

    def load_additions(self, category_id, item_id):
        """Carrega complementos da categoria e específicos do item com info de obrigatoriedade"""
        try:
            additions = get_all_additions_for_item_with_mandatory_info(
                item_id, category_id)
            self.additions_combo.clear()
            self.additions_combo.addItem("Selecione um complemento...")

            for addition in additions:
                # addition: (id, name, price, is_mandatory)
                mandatory_text = " (OBRIGATÓRIO)" if addition[3] else ""
                text = f"{addition[1]} - R$ {addition[2]:.2f}{mandatory_text}"
                self.additions_combo.addItem(text, addition)

        except Exception as e:
            LOGGER.error(f"Erro ao carregar complementos: {e}")

    def add_addition_to_list(self, dialog):
        """Adiciona complemento à lista"""
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
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente primeiro!"
            )
            return

        # Por enquanto, apenas adiciona à tabela como antes
        # Mais tarde implementaremos a lógica completa
        row = self.order_table.rowCount()
        self.order_table.insertRow(row)

        # Monta texto dos complementos
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
        base_price = item_data[2]
        additions_total = sum(add['total']
                              for add in dialog.selected_additions_data)
        total = base_price + additions_total

        msg = f"Item adicionado: {item_data[1]}\n"
        if additions_text:
            msg += f"Complementos: {additions_text}\n"
        msg += f"Total: R$ {total:.2f}"

        QMessageBox.information(self, "Item Adicionado", msg)

        # Atualiza lista de sugestões de itens após cadastro via modal
        if hasattr(self, 'item_search') and self.item_search:
            self.item_search.load_items()

    def closeEvent(self, event):
        """Finaliza threads e remove event filter ao fechar o widget"""
        # Finaliza a thread do customer_search primeiro
        if hasattr(self, 'customer_search') and self.customer_search:
            self.customer_search.closeEvent(event)

        # Finaliza a thread do item_search
        if hasattr(self, 'item_search') and self.item_search:
            self.item_search.closeEvent(event)

        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        super().closeEvent(event)

    def __del__(self):
        """Remove event filter ao destruir o widget"""
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
