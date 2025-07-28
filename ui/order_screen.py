"""
Tela de pedidos - versão refatorada e simplificada.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QHeaderView,
                               QLabel, QMenu, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QTextEdit,
                               QVBoxLayout, QWidget)

# Importa as configurações de impressão
from database.db import get_system_setting
from ui.add_item_dialog import AddItemDialog
from ui.widgets.search_widgets import CustomerSearchWidget, ItemSearchWidget
from utils.log_utils import get_logger
from utils.printer import Printer

LOGGER = get_logger(__name__)


class OrderScreen(QWidget):
    def refresh_order_table(self):
        """Força a atualização completa da tabela de itens do pedido."""
        self.order_table.setRowCount(0)
        for idx, item in enumerate(self.order_items):
            qtd = item.get('qty', 1)
            qtd_item = QTableWidgetItem(f"{qtd}x")
            nome_item = QTableWidgetItem(item['item_data'][1])
            categoria_item = QTableWidgetItem(item['item_data'][4])
            action_item = QTableWidgetItem("🖊️ Editar")
            action_item.setToolTip("Clique duplo para editar este item")
            self.order_table.insertRow(idx)
            self.order_table.setItem(idx, 0, qtd_item)
            self.order_table.setItem(idx, 1, nome_item)
            self.order_table.setItem(idx, 2, categoria_item)
            self.order_table.setItem(idx, 3, action_item)
        self.order_table.viewport().update()

    """Tela de pedidos simplificada."""

    def __init__(self, screen_title, parent=None, customers=None):
        super().__init__(parent)
        self.screen_title = screen_title
        self.selected_customer = None
        self.order_items = []
        self.customers = customers if customers is not None else []
        self._editing_dialog = None  # Controla múltiplas aberturas de diálogos
        self._last_edit_time = {}  # Controla tempo de último clique por botão

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
            "Qtd", "Nome", "Categoria", "Ações"
        ])
        header = self.order_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.order_table.setMaximumHeight(200)
        # Define largura para a coluna 'Ações'
        self.order_table.setColumnWidth(3, 80)

        # Remove a numeração da linha (vertical header)
        self.order_table.verticalHeader().setVisible(False)

        # Remove any custom border style to restore default borders
        self.order_table.setStyleSheet(
            "QTableWidget { border: 1px solid #bbb; }")

        # Conecta clique duplo para editar item
        self.order_table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # Habilita menu de contexto personalizado
        self.order_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.order_table.customContextMenuRequested.connect(
            self.show_context_menu
        )

        layout.addWidget(self.order_table)

    def on_cell_double_clicked(self, row, column):
        """Trata clique duplo na célula da tabela."""
        LOGGER.info(
            f"[DOUBLE_CLICK] Clique duplo na row {row}, column {column}")
        if row < len(self.order_items):
            self.edit_item(row)

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
        # Se for registro manual, garanta que nome e telefone estejam preenchidos
        if customer_data.get('state') == 'register':
            raw = customer_data.get('name', '').strip()
            # Só números: telefone
            if raw.isdigit():
                name = ''
                phone = raw
            # Só letras (ou letras e espaços): nome
            elif raw.replace(' ', '').isalpha():
                name = raw
                phone = ''
            # Ambos: preenche os dois
            else:
                name = raw
                phone = raw
            customer_data['name'] = name
            customer_data['phone'] = phone
            title = name if name else phone
        else:
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
        self.selected_customer = customer_data

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
        # Cria dialog sem parent para aparecer na barra de tarefas
        dialog = AddItemDialog(item_data, None, self)
        dialog.item_added.connect(self.add_item_to_order)
        dialog.dialog_closed.connect(self.on_add_item_dialog_closed)

        # Centraliza o diálogo na tela
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.show()
        dialog.move(
            dialog.screen().geometry().center() - dialog.rect().center()
        )

        dialog.exec()

    def on_add_item_dialog_closed(self):
        LOGGER.info("[DIALOG_CLOSED] Iniciando callback de fechamento")

        try:
            if hasattr(self, 'item_search') and self.item_search:
                LOGGER.info("[DIALOG_CLOSED] item_search existe")

                # Testa chamar clear_selection de forma mais segura
                try:
                    LOGGER.info("[DIALOG_CLOSED] Chamando clear_selection()")
                    self.item_search.clear_selection()
                    LOGGER.info("[DIALOG_CLOSED] clear_selection() completado")
                except Exception as clear_error:
                    LOGGER.error(
                        f"[DIALOG_CLOSED] ERRO em clear_selection: {clear_error}")
                    # Continua sem quebrar se clear_selection falhar

                if hasattr(self.item_search, 'item_lineedit'):
                    LOGGER.info("[DIALOG_CLOSED] Definindo foco no lineedit")
                    self.item_search.item_lineedit.setFocus()
                    LOGGER.info("[DIALOG_CLOSED] Foco definido")
                else:
                    LOGGER.warning("[DIALOG_CLOSED] item_lineedit não existe")
            else:
                LOGGER.warning("[DIALOG_CLOSED] item_search não existe")

            LOGGER.info("[DIALOG_CLOSED] Callback concluído com sucesso")

        except Exception as e:
            LOGGER.error(f"[DIALOG_CLOSED] ERRO: {str(e)}")
            import traceback
            LOGGER.error(traceback.format_exc())
            # Não re-propagar a exceção para evitar crash

    def add_item_to_order(self, item_complete):
        """Adiciona item completo ao pedido."""
        LOGGER.info("[ADD_ITEM] Adicionando novo item à ordem")

        try:
            row = self.order_table.rowCount()
            self.order_table.insertRow(row)
            LOGGER.info(f"[ADD_ITEM] Nova row criada: {row}")

            # Dados na tabela
            qtd = item_complete.get('qty', 1)
            qtd_item = QTableWidgetItem(f"{qtd}x")
            nome_item = QTableWidgetItem(item_complete['item_data'][1])
            categoria_item = QTableWidgetItem(item_complete['item_data'][4])

            # Item de ação como texto simples (sem botão widget)
            action_item = QTableWidgetItem("🖊️ Editar")
            action_item.setToolTip("Clique duplo para editar este item")

            # Armazena dados completos do item
            self.order_items.append(item_complete)
            LOGGER.info(f"[ADD_ITEM] Item data armazenado para row {row}")

            # Insere os itens na tabela (SEM botões widgets)
            self.order_table.setItem(row, 0, qtd_item)
            self.order_table.setItem(row, 1, nome_item)
            self.order_table.setItem(row, 2, categoria_item)
            self.order_table.setItem(row, 3, action_item)
            LOGGER.info(f"[ADD_ITEM] Items inseridos na tabela row {row}")

            # Atualiza lista de sugestões de itens com proteção
            LOGGER.info("[ADD_ITEM] Iniciando atualização de sugestões")
            if hasattr(self, 'item_search') and self.item_search:
                try:
                    # Temporariamente desconecta sinais para evitar problemas
                    self.item_search.blockSignals(True)
                    self.item_search.load_items()
                    self.item_search.blockSignals(False)
                    LOGGER.info("[ADD_ITEM] Lista de sugestões atualizada")
                except Exception as e:
                    LOGGER.error(
                        f"[ADD_ITEM] Erro ao atualizar sugestões: {e}")
                    # Reconecta sinais mesmo em caso de erro
                    self.item_search.blockSignals(False)

            # Atualiza o valor total
            self.update_total_label()
            LOGGER.info(f"[ADD_ITEM] Item adicionado com sucesso na row {row}")

        except Exception as e:
            LOGGER.error(f"[ADD_ITEM] ERRO ao adicionar item: {str(e)}")
            import traceback
            LOGGER.error(traceback.format_exc())
            raise

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
        action_item = QTableWidgetItem("🖊️ Editar")

        self.order_table.setItem(row, 0, qtd_item)
        self.order_table.setItem(row, 1, nome_item)
        self.order_table.setItem(row, 2, categoria_item)
        self.order_table.setItem(row, 3, action_item)

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
        # Zera o total
        self.total_label.setText("Total: R$ 0,00")

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

        # Se for registro manual, registra o cliente no banco antes de finalizar
        if self.selected_customer.get('state') == 'register':
            from database.db import add_customer, get_customers
            name = self.selected_customer.get('name', '').strip()
            phone = self.selected_customer.get('phone', '').strip()
            address = self.selected_customer.get('address', '').strip(
            ) if 'address' in self.selected_customer else ''
            neighborhood = self.selected_customer.get('neighborhood', '').strip(
            ) if 'neighborhood' in self.selected_customer else ''
            reference = self.selected_customer.get('reference', '').strip(
            ) if 'reference' in self.selected_customer else ''
            # Adiciona o cliente
            add_customer(name, phone, address, neighborhood, reference)
            # Busca o cliente recém-criado (por nome e telefone)
            all_customers = get_customers()
            found = None
            for c in all_customers:
                # c: (id, name, phone, address, neighborhood, reference)
                c_name = c[1].strip() if c[1] else ""
                c_phone = c[2].strip() if c[2] else ""
                if c_name == name and c_phone == phone:
                    found = c
                    break
            if found:
                self.selected_customer['id'] = found[0]
                self.selected_customer['name'] = found[1]
                self.selected_customer['phone'] = found[2]
                self.selected_customer['address'] = found[3]
                self.selected_customer['neighborhood'] = found[4]
                self.selected_customer['reference'] = found[5]
                # Remove o estado register para não tentar registrar de novo
                self.selected_customer.pop('state', None)
                # Atualiza a lista de sugestões do CustomerSearchWidget
                if hasattr(self, 'customer_search') and hasattr(self.customer_search, 'load_customers'):
                    self.customer_search.load_customers()
            else:
                QMessageBox.critical(
                    self, "Erro", "Não foi possível registrar o cliente no banco.")
                return

        # Calcula o total atual (base + opcionais + obrigatórios)
        total = 0.0
        for item in self.order_items:
            qtd = item.get('qty', 1)
            preco = item['item_data'][2] if len(item['item_data']) > 2 else 0.0
            total += qtd * preco
            # Soma opcionais
            for add in item.get('additions', []):
                add_qtd = add.get('qty', 1)
                add_preco = add.get('price', 0.0)
                total += add_qtd * add_preco
            # Soma obrigatórios
            for mand in item.get('mandatory_additions', []):
                mand_preco = mand.get('price', 0.0)
                total += mand_preco * qtd

        # Abre o modal de finalização
        from ui.finalize_order_dialog import FinalizeOrderDialog
        dialog = FinalizeOrderDialog(
            self.selected_customer, self.order_items, total, None)

        # Conecta o sinal para atualizar sugestões de clientes
        if hasattr(self.customer_search, 'load_customers'):
            dialog.customer_registered.connect(
                lambda _: self.customer_search.load_customers())

        if dialog.exec():
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
            # Soma opcionais
            for add in item.get('additions', []):
                add_qtd = add.get('qty', 1)
                add_preco = add.get('price', 0.0)
                total += add_qtd * add_preco
            # Soma obrigatórios
            for mand in item.get('mandatory_additions', []):
                mand_preco = mand.get('price', 0.0)
                total += mand_preco * qtd
        self.total_label.setText(f"Total: R$ {total:,.2f}".replace(
            ",", "X").replace(".", ",").replace("X", "."))

    def edit_item(self, row, dialog=None):
        """Edita um item do pedido."""
        LOGGER.info(f"[EDIT_ITEM] Iniciando edit_item para row={row}")

        if row >= len(self.order_items):
            LOGGER.warning(f"[EDIT_ITEM] Row {row} inválido. "
                           f"Total items: {len(self.order_items)}")
            return

        # Previne múltiplas aberturas de diálogos de edição
        if hasattr(self, '_editing_dialog') and self._editing_dialog:
            LOGGER.warning(f"[EDIT_ITEM] Diálogo já está aberto: "
                           f"{self._editing_dialog}")
            return

        # Proteção contra cliques muito rápidos (debounce)
        import time
        current_time = time.time()
        if row in self._last_edit_time:
            time_diff = current_time - self._last_edit_time[row]
            if time_diff < 0.5:  # 500ms
                LOGGER.warning(f"[EDIT_ITEM] Clique muito rápido. "
                               f"Diferença: {time_diff:.3f}s")
                return
        self._last_edit_time[row] = current_time
        LOGGER.info("[EDIT_ITEM] Debounce ok. Continuando com edição.")
        LOGGER.info("[EDIT_ITEM] Debounce ok. Continuando com edição.")

        try:
            LOGGER.info("[EDIT_ITEM] Iniciando bloco try")
            # Obtém dados do item atual (dicionário completo)
            item_dict = self.order_items[row]
            item_data = item_dict['item_data']
            item_name = item_data[1] if len(item_data) > 1 else 'N/A'
            LOGGER.info(f"[EDIT_ITEM] item_data obtido: {item_name}")

            # Cria o AddItemDialog pré-preenchido
            from ui.add_item_dialog import AddItemDialog
            LOGGER.info("[EDIT_ITEM] Importando AddItemDialog")

            edit_dialog = AddItemDialog(item_data, None, self)
            LOGGER.info(f"[EDIT_ITEM] AddItemDialog criado: {edit_dialog}")

            self._editing_dialog = edit_dialog
            LOGGER.info("[EDIT_ITEM] _editing_dialog definido")

            # Preenche os campos do dialog com os dados atuais
            if hasattr(edit_dialog, 'set_initial_state'):
                edit_dialog.set_initial_state(item_dict)
                LOGGER.info(
                    "[EDIT_ITEM] Estado inicial preenchido via set_initial_state")
            else:
                # Fallback para versões antigas
                qty = item_dict.get('qty', 1)
                edit_dialog.item_qty.setValue(qty)
                if 'observations' in item_dict:
                    edit_dialog.observations.setText(item_dict['observations'])
                LOGGER.info("[EDIT_ITEM] Estado inicial preenchido (fallback)")

            def update_item_on_save(edited_item):
                try:
                    LOGGER.info(f"[UPDATE_ITEM] Iniciando para row {row}")

                    # Verifica se o OrderScreen ainda existe
                    if not hasattr(self, 'order_table'):
                        LOGGER.error("[UPDATE_ITEM] OrderScreen sem tabela")
                        return

                    # Verifica se a linha ainda existe antes de atualizar
                    if (row < self.order_table.rowCount() and
                            row < len(self.order_items)):
                        LOGGER.info("[UPDATE_ITEM] Atualizando tabela")

                        # Atualiza dados primeiro
                        self.order_items[row] = edited_item

                        # Depois atualiza a tabela
                        qty_text = f"{edited_item.get('qty', 1)}x"
                        self.order_table.setItem(
                            row, 0, QTableWidgetItem(qty_text))

                        item_name = edited_item['item_data'][1]
                        self.order_table.setItem(
                            row, 1, QTableWidgetItem(item_name))

                        item_category = edited_item['item_data'][4]
                        self.order_table.setItem(
                            row, 2, QTableWidgetItem(item_category))

                        # Força atualização total da tabela
                        LOGGER.info(
                            f"[UPDATE_ITEM] order_items atual: {self.order_items}")
                        self.refresh_order_table()
                        self.update_total_label()
                        LOGGER.info(
                            "[UPDATE_ITEM] Atualização concluída (refresh total)")
                    else:
                        LOGGER.warning(f"[UPDATE_ITEM] Row {row} inválido")

                except Exception as e:
                    LOGGER.error(f"[UPDATE_ITEM] ERRO: {str(e)}")
                    import traceback
                    LOGGER.error(traceback.format_exc())

            def on_dialog_finished():
                LOGGER.info("[DIALOG_FINISHED] Callback chamado")
                if hasattr(self, '_editing_dialog'):
                    self._editing_dialog = None
                    LOGGER.info("[DIALOG_FINISHED] _editing_dialog limpo")

            # Conecta sinais normalmente (sem UniqueConnection)
            LOGGER.info("[EDIT_ITEM] Conectando sinais")
            edit_dialog.item_added.connect(update_item_on_save)
            edit_dialog.finished.connect(on_dialog_finished)
            LOGGER.info("[EDIT_ITEM] Sinais conectados")

            LOGGER.info("[EDIT_ITEM] Executando diálogo")
            edit_dialog.exec()
            LOGGER.info("[EDIT_ITEM] Diálogo executado")

            # Limpa referência após execução
            self._editing_dialog = None
            LOGGER.info("[EDIT_ITEM] _editing_dialog limpo após exec")

            if dialog:
                LOGGER.info("[EDIT_ITEM] Aceitando dialog parent")
                dialog.accept()

        except Exception as e:
            # Em caso de erro, limpa a referência do diálogo
            LOGGER.error(f"[EDIT_ITEM] ERRO: {str(e)}")
            if hasattr(self, '_editing_dialog'):
                self._editing_dialog = None
                LOGGER.info("[EDIT_ITEM] _editing_dialog limpo após erro")
            LOGGER.error("[EDIT_ITEM] Stack trace completo:")
            import traceback
            LOGGER.error(traceback.format_exc())
            raise

    def show_context_menu(self, position):
        """Mostra menu de contexto ao clicar com botão direito."""
        LOGGER.info("[CONTEXT_MENU] Menu de contexto solicitado")

        item = self.order_table.itemAt(position)
        if item is None:
            LOGGER.info("[CONTEXT_MENU] Nenhum item na posição, cancelando")
            return

        row = item.row()
        LOGGER.info(f"[CONTEXT_MENU] Menu para row: {row}")

        menu = QMenu(self)

        # Ação editar
        edit_action = menu.addAction("Editar")
        edit_action.setIcon(QIcon.fromTheme("document-edit"))
        LOGGER.info(f"[CONTEXT_MENU] Conectando ação editar para row {row}")
        edit_action.triggered.connect(lambda: self.edit_item_from_context(row))

        # Ação excluir
        delete_action = menu.addAction("Excluir")
        delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        LOGGER.info(f"[CONTEXT_MENU] Conectando ação excluir para row {row}")
        delete_action.triggered.connect(lambda: self.delete_item(row))

        # Mostra o menu na posição do cursor
        LOGGER.info("[CONTEXT_MENU] Exibindo menu")
        menu.exec(self.order_table.mapToGlobal(position))
        LOGGER.info("[CONTEXT_MENU] Menu executado")

    def edit_item_from_context(self, row):
        """Método wrapper para chamar edit_item a partir do menu contexto."""
        LOGGER.info(f"[CONTEXT_EDIT] Editando item via menu, row: {row}")
        self.edit_item(row)

    def closeEvent(self, event):
        """Finaliza threads ao fechar o widget."""
        LOGGER.info("[CLOSE_EVENT] Iniciando fechamento do OrderScreen")

        # Finaliza threads dos widgets de busca, se existirem
        if hasattr(self, 'customer_search') and self.customer_search:
            LOGGER.info("[CLOSE_EVENT] Finalizando customer_search")
            if hasattr(self.customer_search, 'finalize_threads'):
                self.customer_search.finalize_threads()
            self.customer_search.closeEvent(event)

        if hasattr(self, 'item_search') and self.item_search:
            LOGGER.info("[CLOSE_EVENT] Finalizando item_search")
            if hasattr(self.item_search, 'finalize_threads'):
                self.item_search.finalize_threads()
            self.item_search.closeEvent(event)

        # Limpa diálogo de edição se ainda existir
        if hasattr(self, '_editing_dialog') and self._editing_dialog:
            LOGGER.info("[CLOSE_EVENT] Limpando _editing_dialog")
            self._editing_dialog = None

        LOGGER.info("[CLOSE_EVENT] Finalizando closeEvent")
        super().closeEvent(event)

    def __del__(self):
        """Remove event filter ao destruir o widget."""
        LOGGER.info("[DEL] Destruindo OrderScreen")
