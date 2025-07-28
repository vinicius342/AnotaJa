"""
Diálogo para adicionar itens ao pedido com complementos.
"""

from PySide6.QtCore import QEventLoop, Qt, Signal
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
                               QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QMenu, QMessageBox,
                               QPushButton, QScrollArea, QSpinBox, QTextEdit,
                               QVBoxLayout, QWidget)

from database.db import get_all_additions_for_item_with_mandatory_info
from utils.log_utils import get_logger

LOGGER = get_logger(__name__)


class AddItemDialog(QDialog):
    def set_initial_state(self, item_dict):
        """Preenche o diálogo com os dados de um item já existente (edição)."""
        # Quantidade
        qty = item_dict.get('qty', 1)
        self.item_qty.setValue(qty)

        # Observações
        obs = item_dict.get('observations', '')
        self.observations.setText(obs)

        # Complementos opcionais: só adiciona os que não são obrigatórios
        self.selected_additions_data = []
        self.selected_additions.clear()
        # Pega ids dos obrigatórios para filtrar
        mandatory_ids = set(a['id']
                            for a in item_dict.get('mandatory_additions', []))
        for add in item_dict.get('additions', []):
            if add.get('id') not in mandatory_ids:
                text = f"{add.get('qty', 1)}x {add.get('name', '')} - R$ {add.get('price', 0.0)*add.get('qty', 1):.2f}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, add)
                self.selected_additions.addItem(item)
                self.selected_additions_data.append(add.copy())

        # Complementos obrigatórios (checkboxes)
        # Só é possível marcar após load_additions, então usamos singleShot para garantir
        from PySide6.QtCore import QTimer

        def marcar_obrigatorios():
            obrigatorios = item_dict.get('mandatory_additions', [])
            for i in range(self.mandatory_additions_layout.count()):
                item = self.mandatory_additions_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        add_data = checkbox.property('addition_data')
                        if add_data and any(a['id'] == add_data['id'] for a in obrigatorios):
                            checkbox.setChecked(True)
                        else:
                            checkbox.setChecked(False)
        QTimer.singleShot(0, marcar_obrigatorios)

        # Recalcula o valor total ao abrir para edição
        self.update_total_price()
    """Diálogo para adicionar item ao pedido com complementos."""

    item_added = Signal(dict)  # Sinal emitido quando item é adicionado
    dialog_closed = Signal()  # Sinal emitido ao fechar o diálogo

    def __init__(self, item_data, parent=None, order_screen=None):
        super().__init__(parent)
        try:
            self.item_data = item_data
            self.order_screen = order_screen  # Referência para order_screen
            self.selected_additions_data = []
            self.setup_ui()
            self.load_additions()

            # Define foco inicial no campo de quantidade após carregar tudo
            self.item_qty.setFocus()

        except Exception as e:
            LOGGER.error(f"Erro na inicialização do AddItemDialog: {e}")
            QMessageBox.critical(None, "Erro",
                                 f"Erro ao inicializar diálogo: {str(e)}")
            self.close()  # Fecha o widget em caso de erro

    def setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle("Adicionar Item")

        # Configura flags para aparecer na barra de tarefas
        flags = (Qt.WindowType.Dialog |
                 Qt.WindowType.WindowSystemMenuHint |
                 Qt.WindowType.WindowTitleHint |
                 Qt.WindowType.WindowCloseButtonHint |
                 Qt.WindowType.WindowMinMaxButtonsHint)
        self.setWindowFlags(flags)

        # Força o diálogo a aparecer na barra de tarefas
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        self.resize(500, 400)

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

        # Configurar atalhos de teclado
        self.setup_keyboard_shortcuts()

        # Configura eventos de teclado para navegação
        self.item_qty.keyPressEvent = lambda event: self.qty_key_handler(event)

    def setup_keyboard_shortcuts(self):
        """Configura os atalhos de teclado."""
        # Escape para cancelar
        escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        escape_shortcut.activated.connect(self.reject)

        # Ctrl+Enter para adicionar o item ao pedido
        add_item_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        add_item_shortcut.activated.connect(self.add_to_order)

        # Ctrl+M para focar nos complementos obrigatórios (Mandatory)
        mandatory_shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        mandatory_shortcut.activated.connect(self.focus_first_checkbox)

        # Removido shortcut global de Enter para evitar conflito com campo de quantidade

    def setup_header(self, layout):
        """Configura o header com nome, categoria (abaixo) e quantidade."""
        header_layout = QHBoxLayout()

        # Label do nome do item
        item_name_label = QLabel(f"Item: {self.item_data[1]}")
        item_name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(item_name_label)

        # Campo de quantidade do item
        qty_item_label = QLabel("Qtd:")
        qty_item_label.setStyleSheet(
            "margin-left: 12px; margin-right: 2px; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(qty_item_label)

        self.item_qty = QSpinBox()
        self.item_qty.setMinimum(1)
        self.item_qty.setMaximum(99)
        self.item_qty.setValue(1)
        self.item_qty.setFixedWidth(50)
        self.item_qty.valueChanged.connect(self.update_total_price)
        header_layout.addWidget(self.item_qty)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Label da categoria embaixo do nome do item
        category_label = QLabel(f"Categoria: {self.item_data[4]}")
        category_label.setStyleSheet(
            "color: #666; font-size: 12px; margin-top: 2px;")
        layout.addWidget(category_label)

    def setup_additions_section(self, layout):
        """Configura a seção de complementos."""
        # Label dos complementos
        additions_label = QLabel("Complementos Obrigatórios:")
        additions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(additions_label)

        # NOVO: Seção de complementos obrigatórios com altura fixa e overscroll
        self.mandatory_additions_layout = QVBoxLayout()
        self.mandatory_additions_layout.setContentsMargins(5, 0, 5, 0)
        self.mandatory_additions_layout.setSpacing(2)
        mandatory_group = QGroupBox("Complementos obrigatórios")
        mandatory_group.setStyleSheet("margin-bottom: 0px;")
        # Widget para scroll
        mandatory_widget = QWidget()
        mandatory_widget.setLayout(self.mandatory_additions_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(mandatory_widget)
        # altura fixa, ajuste conforme necessário
        scroll_area.setFixedHeight(130)
        scroll_area.setStyleSheet(
            "QScrollArea {background: transparent; border: none;} "
            "QScrollBar:vertical {width: 8px;}")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.addWidget(scroll_area)
        mandatory_group.setLayout(group_layout)
        layout.addWidget(mandatory_group)

        # Label "Complementos" acima do combo
        complementos_label = QLabel("Complementos:")
        complementos_label.setStyleSheet(
            "font-weight: bold; margin-top: 10px;")
        layout.addWidget(complementos_label)

        # Layout para seleção de complementos
        additions_layout = QHBoxLayout()

        # QPushButton + QMenu para selecionar complemento
        self.additions_button = QPushButton("Selecione um complemento...")
        self.additions_menu = QMenu()
        self.additions_button.setMenu(self.additions_menu)

        # Configura navegação por teclado no QPushButton
        self.additions_button.keyPressEvent = lambda event: \
            self.button_key_handler(event)

        additions_layout.addWidget(self.additions_button)

        # Quantidade
        qty_label = QLabel("Qtd:")
        additions_layout.addWidget(qty_label)

        self.addition_qty = QSpinBox()
        self.addition_qty.setMinimum(1)
        self.addition_qty.setMaximum(10)
        self.addition_qty.setValue(1)
        # Configura navegação por teclado na quantidade
        self.addition_qty.keyPressEvent = lambda event: \
            self.addition_qty_key_handler(event)
        additions_layout.addWidget(self.addition_qty)
        # Botão adicionar
        self.add_addition_btn = QPushButton("Adicionar")
        self.add_addition_btn.clicked.connect(self.add_addition_to_list)
        additions_layout.addWidget(self.add_addition_btn)

        layout.addLayout(additions_layout)

        # Lista de complementos selecionados
        self.selected_additions = QListWidget()
        self.selected_additions.setMaximumHeight(100)
        layout.addWidget(self.selected_additions)

        # Estilização de foco para checkboxes obrigatórios
        self.setStyleSheet(self.styleSheet() + """
            QCheckBox:focus {
                outline: 2px solid #1976d2;
                background-color: #e3f2fd;
                border-radius: 3px;
                padding: 2px;
            }
        """)

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
        layout.addWidget(self.total_label)

    def setup_buttons(self, layout):
        """Configura os botões do diálogo."""
        buttons_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        add_btn = QPushButton("Adicionar ao Pedido [Ctrl+Enter]")
        add_btn.clicked.connect(self.add_to_order)
        buttons_layout.addWidget(add_btn)

        layout.addLayout(buttons_layout)

    def load_additions(self):
        """Carrega todos os complementos do item (categoria e específicos)."""
        try:
            LOGGER.debug(f"Loading additions for item_data: {self.item_data}")

            # Valida dados do item
            if not self.item_data or len(self.item_data) < 6:
                LOGGER.error(f"item_data inválido: {self.item_data}")
                raise ValueError("Dados do item inválidos")

            item_id = self.item_data[0]
            # item: (id, name, price, category_id, category_name, description)
            category_name = self.item_data[4]  # category_name está no índice 4

            if not item_id or not category_name:
                LOGGER.error(
                    f"ID ou categoria inválidos: {item_id}, {category_name}")
                raise ValueError("ID do item ou categoria inválidos")

            from database.db import get_category_id
            category_id = get_category_id(category_name)

            if not category_id:
                LOGGER.warning(f"Categoria não encontrada: {category_name}")
                category_id = 0  # Valor padrão

            # Busca todos os complementos com status de obrigatoriedade
            all_additions_info = \
                get_all_additions_for_item_with_mandatory_info(
                    item_id, category_id)
            LOGGER.debug(f"all_additions_info: {all_additions_info}")

            # Monta lista de complementos para o menu e obrigatórios
            self.additions_menu.clear()

            mandatory_count = 0
            # Limpa widgets obrigatórios existentes
            while self.mandatory_additions_layout.count():
                child = self.mandatory_additions_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            for add_id, name, price, is_mandatory in all_additions_info:
                LOGGER.debug(
                    f"Complemento: id={add_id}, nome={name}, preco={price}, "
                    f"obrigatorio={is_mandatory}")

                # Determina se é específico ou da categoria
                source = "specific" if is_mandatory else "category"

                comp = {
                    'id': add_id,
                    'name': name,
                    'price': price,
                    'source': source,
                    'is_mandatory': is_mandatory
                }

                if not is_mandatory:
                    # Adiciona apenas complementos não obrigatórios ao menu
                    text = f"{name} - R$ {price:.2f}"
                    action = QAction(text, self)
                    action.setData(comp)
                    action.triggered.connect(
                        lambda checked, c=comp: self.select_addition(c))
                    self.additions_menu.addAction(action)

                if is_mandatory:
                    mandatory_count += 1
                    # Cria checkbox e label para complemento obrigatório
                    row_widget = QWidget()
                    row_layout = QHBoxLayout()
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    row_layout.setSpacing(4)

                    checkbox = QCheckBox()
                    checkbox.setObjectName(f"mandatory_{add_id}")
                    checkbox.setProperty("addition_data", comp)
                    checkbox.setChecked(False)
                    # Permite foco para navegação por teclado
                    checkbox.setFocusPolicy(Qt.FocusPolicy.TabFocus)

                    # Conecta eventos de teclado
                    checkbox.keyPressEvent = lambda event, cb=checkbox: \
                        self.checkbox_key_handler(event, cb)
                    # NOVO: Atualiza o total ao marcar/desmarcar
                    checkbox.stateChanged.connect(self.update_total_price)

                    label = QLabel(f"{name} - R$ {price:.2f}")
                    label.setStyleSheet("font-size: 11px;")
                    # Permite clicar no label para marcar/desmarcar checkbox
                    label.mousePressEvent = lambda event, cb=checkbox: \
                        cb.setChecked(not cb.isChecked())

                    row_layout.addWidget(checkbox)
                    row_layout.addWidget(label)
                    row_layout.addStretch()
                    row_widget.setLayout(row_layout)
                    self.mandatory_additions_layout.addWidget(row_widget)

            LOGGER.debug(f"Total mandatory additions added: {mandatory_count}")
            if mandatory_count == 0:
                no_mandatory_label = QLabel("Nenhum complemento obrigatório")
                no_mandatory_label.setStyleSheet(
                    "font-size: 10px; color: #666;")
                self.mandatory_additions_layout.addWidget(no_mandatory_label)

        except Exception as e:
            LOGGER.error(f"Erro ao carregar complementos: {e}")
            QMessageBox.critical(self, "Erro",
                                 f"Erro ao carregar complementos: {str(e)}")
            # Adiciona fallback para evitar crash
            if self.mandatory_additions_layout.count() == 0:
                no_items_label = QLabel("Erro ao carregar complementos")
                no_items_label.setStyleSheet("color: red; font-size: 10px;")
                self.mandatory_additions_layout.addWidget(no_items_label)

    def select_addition(self, addition_data):
        """Seleciona complemento do menu e atualiza botão."""
        self.selected_addition_data = addition_data
        self.additions_button.setText(
            f"{addition_data['name']} - R$ {addition_data['price']:.2f}")
        # Foca na quantidade do complemento ao selecionar
        self.addition_qty.setFocus()

    def addition_qty_key_handler(self, event):
        """Manipula eventos de teclado na quantidade de complemento."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Enter adiciona o complemento diretamente
            self.add_addition_to_list()
            event.accept()
        else:
            QSpinBox.keyPressEvent(self.addition_qty, event)

    def checkbox_key_handler(self, event, checkbox):
        """Manipula eventos de teclado nos checkboxes."""
        if event.key() == Qt.Key.Key_Space:
            # Espaço marca/desmarca o checkbox
            checkbox.setChecked(not checkbox.isChecked())
            event.accept()
        elif (event.key() == Qt.Key.Key_Return or
              event.key() == Qt.Key.Key_Enter):
            # Enter também marca/desmarca o checkbox
            checkbox.setChecked(not checkbox.isChecked())
            event.accept()
        elif event.key() == Qt.Key.Key_Tab:
            # Tab navega para o próximo checkbox
            self.focus_next_checkbox(checkbox)
            event.accept()
        elif event.key() == Qt.Key.Key_Backtab:
            # Shift+Tab navega para o checkbox anterior
            self.focus_previous_checkbox(checkbox)
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            # Seta para baixo: próximo checkbox ou QPushButton/QMenu se último
            checkboxes = self.get_all_checkboxes()
            if len(checkboxes) == 1 or self.is_last_checkbox(checkbox):
                self.additions_button.setFocus()
                # Abre o QMenu na posição do botão
                pos = self.additions_button.mapToGlobal(
                    self.additions_button.rect().bottomLeft())
                self.additions_menu.popup(pos)
            else:
                self.focus_next_checkbox(checkbox)
            event.accept()
        elif event.key() == Qt.Key.Key_Up:
            # Seta para cima: checkbox anterior ou campo quantidade se primeiro
            if self.is_first_checkbox(checkbox):
                self.item_qty.setFocus()
            else:
                self.focus_previous_checkbox(checkbox)
            event.accept()
        else:
            # Para outras teclas, usa o comportamento padrão
            QCheckBox.keyPressEvent(checkbox, event)

    def focus_next_checkbox(self, current_checkbox):
        """Foca no próximo checkbox da lista."""
        checkboxes = self.get_all_checkboxes()
        if not checkboxes:
            return

        try:
            current_index = checkboxes.index(current_checkbox)
            next_index = (current_index + 1) % len(checkboxes)
            checkboxes[next_index].setFocus()
        except ValueError:
            # Se não encontrar o checkbox atual, foca no primeiro
            if checkboxes:
                checkboxes[0].setFocus()

    def focus_previous_checkbox(self, current_checkbox):
        """Foca no checkbox anterior da lista."""
        checkboxes = self.get_all_checkboxes()
        if not checkboxes:
            return

        try:
            current_index = checkboxes.index(current_checkbox)
            previous_index = (current_index - 1) % len(checkboxes)
            checkboxes[previous_index].setFocus()
        except ValueError:
            # Se não encontrar o checkbox atual, foca no último
            if checkboxes:
                checkboxes[-1].setFocus()

    def get_all_checkboxes(self):
        """Retorna lista de todos os checkboxes obrigatórios."""
        checkboxes = []
        for i in range(self.mandatory_additions_layout.count()):
            item = self.mandatory_additions_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkboxes.append(checkbox)
        return checkboxes

    def is_first_checkbox(self, checkbox):
        """Verifica se é o primeiro checkbox."""
        checkboxes = self.get_all_checkboxes()
        return checkboxes and checkboxes[0] == checkbox

    def is_last_checkbox(self, checkbox):
        """Verifica se é o último checkbox."""
        checkboxes = self.get_all_checkboxes()
        return checkboxes and checkboxes[-1] == checkbox

    def button_key_handler(self, event):
        """Manipula eventos de teclado no QPushButton de complementos."""
        if event.key() == Qt.Key.Key_Up:
            # Seta para cima: vai para o último checkbox se existir
            checkboxes = self.get_all_checkboxes()
            if checkboxes:
                checkboxes[-1].setFocus()
            else:
                # Se não há checkboxes, vai para quantidade
                self.item_qty.setFocus()
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            # Seta para baixo: vai para o campo de quantidade de complemento
            self.addition_qty.setFocus()
            event.accept()
        else:
            # Para outras teclas, usa o comportamento padrão
            QPushButton.keyPressEvent(self.additions_button, event)

    def focus_first_checkbox(self):
        """Foca no primeiro checkbox disponível."""
        checkboxes = self.get_all_checkboxes()
        if checkboxes:
            checkboxes[0].setFocus()

    def handle_enter_key(self):
        """Manipula a tecla Enter conforme o controle focado."""
        focused_widget = QApplication.focusWidget()

        # Se o foco está no campo de quantidade do item, vai para os checkboxes
        if focused_widget == self.item_qty:
            self.focus_first_checkbox()
        # Se o foco está em um checkbox, marca/desmarca ele
        elif focused_widget in self.get_all_checkboxes():
            focused_widget.setChecked(not focused_widget.isChecked())
        # Se não há foco específico ou está em outro lugar, adiciona ao pedido
        elif not self.is_in_navigation_area(focused_widget):
            self.add_to_order()

    def qty_key_handler(self, event):
        """Manipula eventos de teclado no campo de quantidade do item."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Enter vai para os checkboxes obrigatórios
            self.focus_first_checkbox()
            event.accept()
            return  # Retorna para evitar processamento adicional
        else:
            # Para outras teclas, usa o comportamento padrão
            QSpinBox.keyPressEvent(self.item_qty, event)

    def is_in_navigation_area(self, widget):
        """Verifica se o widget está na área de navegação especial."""
        if not widget:
            return False

        # Verifica se é o campo de quantidade do item
        if widget == self.item_qty:
            return True

        # Verifica se é um checkbox obrigatório
        checkboxes = self.get_all_checkboxes()
        if widget in checkboxes:
            return True

        # Verifica se é o QPushButton de complementos
        if widget == self.additions_button:
            return True

        return False

    def add_addition_to_list(self):
        """Adiciona complemento à lista."""
        # Verifica se algum complemento foi selecionado
        if not hasattr(self, 'selected_addition_data') or \
           not self.selected_addition_data:
            return

        addition_data = self.selected_addition_data
        qty = self.addition_qty.value()

        # Adiciona à lista visual
        text = f"{qty}x {addition_data['name']} - " \
               f"R$ {addition_data['price']*qty:.2f}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, {
            'id': addition_data['id'],
            'name': addition_data['name'],
            'price': addition_data['price'],
            'qty': qty,
            'total': addition_data['price'] * qty
        })
        self.selected_additions.addItem(item)

        # Adiciona aos dados do diálogo
        self.selected_additions_data.append({
            'id': addition_data['id'],
            'name': addition_data['name'],
            'price': addition_data['price'],
            'qty': qty,
            'total': addition_data['price'] * qty
        })

        # Atualiza total
        self.update_total_price()

        # Reset campos
        self.additions_button.setText("Selecione um complemento...")
        self.selected_addition_data = None
        self.addition_qty.setValue(1)

        # Volta o foco para o QMenu (abre novamente)
        pos = self.additions_button.mapToGlobal(
            self.additions_button.rect().bottomLeft())
        self.additions_menu.popup(pos)

    def update_total_price(self):
        """Atualiza o preço total considerando a quantidade do item e obrigatórios."""
        total = self.calculate_total()
        self.total_label.setText(f"Total: R$ {total:.2f}")

    def get_selected_mandatory_additions(self):
        """Retorna lista dos complementos obrigatórios selecionados."""
        selected = []
        try:
            for i in range(self.mandatory_additions_layout.count()):
                item = self.mandatory_additions_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        addition_data = checkbox.property("addition_data")
                        if addition_data:
                            selected.append(addition_data)
        except Exception as e:
            LOGGER.error(f"Erro ao obter complementos obrigatórios: {e}")
        return selected

    def add_to_order(self):
        """Adiciona item ao pedido."""
        try:
            # Pega complementos obrigatórios selecionados
            mandatory_additions = self.get_selected_mandatory_additions()

            # Monta dados do item completo
            item_complete = {
                'item_data': self.item_data,
                'additions': self.selected_additions_data.copy(),  # apenas opcionais
                'mandatory_additions': mandatory_additions,         # apenas obrigatórios
                'observations': self.observations.toPlainText().strip(),
                'total': self.calculate_total(),
                'qty': self.item_qty.value()
            }

            # Emite sinal com os dados
            self.item_added.emit(item_complete)

            # Fecha o diálogo
            self.accept()
        except Exception as e:
            LOGGER.error(f"Erro ao adicionar item ao pedido: {e}")
            QMessageBox.critical(self, "Erro",
                                 f"Erro ao adicionar item: {str(e)}")

    def calculate_total(self):
        """Calcula o total do item com complementos opcionais e obrigatórios."""
        base_price = self.item_data[2]
        item_qty = self.item_qty.value() if hasattr(self, 'item_qty') else 1
        # Total dos opcionais (já multiplicados pela quantidade deles)
        additions_total = sum(add['total']
                              for add in self.selected_additions_data)
        # Total dos obrigatórios marcados (cada obrigatório é 1x por item)
        mandatory_additions = self.get_selected_mandatory_additions()
        mandatory_total = sum(add.get('price', 0.0)
                              for add in mandatory_additions) * item_qty
        return (base_price * item_qty) + additions_total + mandatory_total

    def accept(self):
        """Sobrescreve accept para garantir que o sinal seja emitido."""
        self.clear_item_search_and_focus()
        self.dialog_closed.emit()
        super().accept()

    def reject(self):
        """Sobrescreve reject para garantir que o sinal seja emitido."""
        self.clear_item_search_and_focus()
        self.dialog_closed.emit()
        super().reject()

    def clear_item_search_and_focus(self):
        """Limpa o campo de busca e define o foco."""
        LOGGER.info("[AddItemDialog] clear_item_search_and_focus chamado")
        target_screen = (self.order_screen if self.order_screen
                         else self.parent())

        if (target_screen and hasattr(target_screen, 'item_search')
                and hasattr(target_screen.item_search, 'item_lineedit')):
            LOGGER.info("[AddItemDialog] Limpando search e definindo foco")
            target_screen.item_search.clear_selection()
            target_screen.item_search.item_lineedit.setFocus()
        else:
            LOGGER.warning("[AddItemDialog] target_screen ou item_search "
                           "não encontrado")

    def show_confirmation(self, qty=1):
        """Mostra mensagem de confirmação."""
        additions_text = ""
        if self.selected_additions_data:
            additions_list = [f"{a['qty']}x {a['name']}"
                              for a in self.selected_additions_data]
            additions_text = ", ".join(additions_list)

        msg = f"Item adicionado: {qty}x {self.item_data[1]}\n"
        if additions_text:
            msg += f"Complementos: {additions_text}\n"
        msg += f"Total: R$ {self.calculate_total():.2f}"

        QMessageBox.information(self, "Item Adicionado", msg)

    def closeEvent(self, event):
        """Ao fechar o diálogo, foca no campo de busca de item."""
        # Os métodos accept/reject já cuidam da limpeza,
        # mas garantimos aqui para outros casos de fechamento
        self.clear_item_search_and_focus()
        self.dialog_closed.emit()
        super().closeEvent(event)
