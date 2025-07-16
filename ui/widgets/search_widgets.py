"""
Widgets de busca para clientes e itens.
"""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QVBoxLayout, QWidget)

from database.db import search_menu_items
from utils.log_utils import get_logger
from utils.utils import (CUSTOMER_LINEEDIT_BASE_STYLE,
                         CUSTOMER_LINEEDIT_NO_BORDER_STYLE,
                         SUGGESTIONS_LIST_BASE_STYLE)

from .workers import CustomerFilterWorker, ItemFilterWorker

LOGGER = get_logger(__name__)


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
