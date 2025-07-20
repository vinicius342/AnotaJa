from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMenu,
                               QMessageBox, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from database.db import (add_addition, get_all_additions_with_id,
                         get_item_specific_additions,
                         set_item_specific_additions)


class CategoryAdditionsDialog(QDialog):
    def __init__(self, category, all_additions, selected_addition_ids, parent=None):
        super().__init__(parent)
        # Configura para aparecer na barra de tarefas com controles normais
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle(f"Complementos para {category}")
        self.setModal(True)
        self.resize(400, 350)

        layout = QVBoxLayout()
        title_row = QHBoxLayout()
        title_label = QLabel(
            f"Selecione os complementos para a categoria '{category}':")
        title_row.addWidget(title_label)
        # Checkbox Selecionar todas alinhado à direita
        self.select_all_checkbox = QCheckBox("Selecionar todas")
        self.select_all_checkbox.stateChanged.connect(
            self.toggle_all_additions)
        title_row.addStretch()
        title_row.addWidget(self.select_all_checkbox)
        layout.addLayout(title_row)

        # Área de rolagem para os complementos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(100)
        scroll_area.setMaximumHeight(220)
        additions_widget = QWidget()
        additions_layout = QVBoxLayout()
        additions_widget.setLayout(additions_layout)
        self.addition_checks = []
        self.addition_ids = []
        for addition in all_additions:
            # all_additions: lista de tuplas (id, nome, preco)
            add_id, name, price = addition
            row = QHBoxLayout()
            checkbox = QCheckBox(f"{name}   R$ {price:.2f}")
            if add_id in selected_addition_ids:
                checkbox.setChecked(True)
            row.addWidget(checkbox)
            additions_layout.addLayout(row)
            self.addition_checks.append(checkbox)
            self.addition_ids.append(add_id)
        scroll_area.setWidget(additions_widget)
        layout.addWidget(scroll_area)

        # Botões OK/Cancelar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def toggle_all_additions(self, state):
        checked = state == 2
        for checkbox in self.addition_checks:
            checkbox.setChecked(checked)

    def update_select_all_checkbox(self):
        all_checked = all(cb.isChecked() for cb in self.addition_checks)
        self.select_all_checkbox.setChecked(all_checked)

    def get_selected_additions(self):
        selected = []
        for idx, checkbox in enumerate(self.addition_checks):
            if checkbox.isChecked():
                selected.append(self.addition_ids[idx])
        return selected


class ItemAdditionsDialog(QDialog):
    def closeEvent(self, event):
        # Ao fechar o diálogo, foca no campo de busca de item se o parent tiver esse atributo
        parent = self.parent()
        if parent and hasattr(parent, 'item_search') and hasattr(parent.item_search, 'item_lineedit'):
            parent.item_search.item_lineedit.setFocus()
        super().closeEvent(event)

    """Diálogo para selecionar complementos específicos de um item"""

    def __init__(self, item_name, item_id, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setModal(False)  # NÃO modal para permitir interação simultânea
        self.setWindowTitle(f"Complementos específicos para {item_name}")
        self.resize(500, 600)
        self.item_id = item_id
        self.item_name = item_name

        layout = QVBoxLayout()

        # Título
        title_label = QLabel(f"Complementos específicos de '{item_name}':")
        title_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Seção para adicionar novo complemento específico (agora no topo)
        new_addition_frame = QWidget()
        new_addition_layout = QHBoxLayout()
        new_addition_frame.setLayout(new_addition_layout)
        self.new_name_input = QLineEdit()
        self.new_name_input.setPlaceholderText("Nome do complemento")
        new_addition_layout.addWidget(self.new_name_input)
        self.new_price_input = QDoubleSpinBox()
        self.new_price_input.setPrefix("R$ ")
        self.new_price_input.setMaximum(999.99)
        self.new_price_input.setDecimals(2)
        new_addition_layout.addWidget(self.new_price_input)
        self.add_new_btn = QPushButton("Adicionar")
        self.add_new_btn.clicked.connect(self.add_new_addition)
        new_addition_layout.addWidget(self.add_new_btn)
        layout.addWidget(new_addition_frame)

        # Lista de complementos específicos do item (QListWidget)
        self.specific_list_widget = QListWidget()
        layout.addWidget(self.specific_list_widget)
        btns_row = QHBoxLayout()
        self.edit_specific_btn = QPushButton("Editar selecionado")
        self.edit_specific_btn.clicked.connect(self.edit_selected_specific)
        btns_row.addWidget(self.edit_specific_btn)
        self.remove_specific_btn = QPushButton("Remover selecionado")
        self.remove_specific_btn.clicked.connect(self.remove_selected_specific)
        btns_row.addWidget(self.remove_specific_btn)
        layout.addLayout(btns_row)

        # Separador
        layout.addWidget(
            QLabel("Complementos obrigatórios (categoria + específicos):"))

        # Checkbox para selecionar todas
        self.select_all_checkbox = QCheckBox("Selecionar todos")
        self.select_all_checkbox.stateChanged.connect(
            self.toggle_all_additions)
        layout.addWidget(self.select_all_checkbox)

        # Área de rolagem para os complementos obrigatórios
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(200)
        self.scroll_area.setMaximumHeight(350)
        self.additions_widget = QWidget()
        self.additions_layout = QVBoxLayout()
        self.additions_widget.setLayout(self.additions_layout)
        self.scroll_area.setWidget(self.additions_widget)
        layout.addWidget(self.scroll_area)

        # Botões OK/Cancelar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Carrega os complementos específicos e obrigatórios
        self.load_specific_complements()
        self.load_additions()

    def load_specific_complements(self):
        """Carrega e exibe complementos específicos do item no QListWidget"""
        from database.db import get_item_specific_additions
        self.specific_complements = get_item_specific_additions(self.item_id)
        self.specific_list_widget.clear()
        for comp_id, name, price, is_mandatory in self.specific_complements:
            mandatory_text = " (OBRIGATÓRIO)" if is_mandatory else ""
            item = QListWidgetItem(f"{name} - R$ {price:.2f}{mandatory_text}")
            item.setData(Qt.UserRole, (comp_id, name, price, is_mandatory))
            self.specific_list_widget.addItem(item)

    def edit_selected_specific(self):
        item = self.specific_list_widget.currentItem()
        if item:
            comp_id, name, price, is_mandatory = item.data(Qt.UserRole)
            self.edit_specific_complement(comp_id, name, price, is_mandatory)

    def remove_selected_specific(self):
        item = self.specific_list_widget.currentItem()
        if item:
            comp_id, name, price, is_mandatory = item.data(Qt.UserRole)
            self.remove_specific_complement(comp_id)

    def edit_specific_complement(self, comp_id, name, price, is_mandatory=False):
        # Preenche campos para edição
        self.new_name_input.setText(name)
        self.new_price_input.setValue(price)

        # Adiciona checkbox de obrigatoriedade se não existir
        if not hasattr(self, 'mandatory_checkbox'):
            self.mandatory_checkbox = QCheckBox("Obrigatório")
            self.new_name_input.parentWidget().layout().addWidget(self.mandatory_checkbox)

        self.mandatory_checkbox.setChecked(is_mandatory)
        self.mandatory_checkbox.show()

        self.add_new_btn.setText("Salvar")
        self.add_new_btn.clicked.disconnect()
        self.add_new_btn.clicked.connect(
            lambda: self.save_specific_complement(comp_id))

        # Adiciona botão de cancelar edição se não existir
        if not hasattr(self, 'cancel_edit_btn') or self.cancel_edit_btn is None:
            self.cancel_edit_btn = QPushButton("Cancelar")
            self.cancel_edit_btn.setStyleSheet(
                "QPushButton { background-color: #d9534f; color: white; font-weight: bold; }")
            self.cancel_edit_btn.clicked.connect(self.cancel_edit_specific)
            self.new_name_input.parentWidget().layout().addWidget(self.cancel_edit_btn)
        self.cancel_edit_btn.show()

    def cancel_edit_specific(self):
        # Restaura campo de adicionar
        self.new_name_input.clear()
        self.new_price_input.setValue(0.0)
        self.add_new_btn.setText("Adicionar")
        self.add_new_btn.clicked.disconnect()
        self.add_new_btn.clicked.connect(self.add_new_addition)
        if hasattr(self, 'cancel_edit_btn') and self.cancel_edit_btn:
            self.cancel_edit_btn.hide()
        if hasattr(self, 'mandatory_checkbox') and self.mandatory_checkbox:
            self.mandatory_checkbox.hide()

    def save_specific_complement(self, comp_id):
        from database.db import update_item_specific_addition
        name = self.new_name_input.text().strip()
        price = self.new_price_input.value()
        is_mandatory = hasattr(
            self, 'mandatory_checkbox') and self.mandatory_checkbox.isChecked()

        if not name:
            QMessageBox.warning(
                self, "Erro", "Nome do complemento é obrigatório!")
            return

        try:
            # Atualiza diretamente no banco usando o ID
            update_item_specific_addition(comp_id, name, price, is_mandatory)

            # Restaura estado do formulário
            self.new_name_input.clear()
            self.new_price_input.setValue(0.0)
            self.add_new_btn.setText("Adicionar")
            self.add_new_btn.clicked.disconnect()
            self.add_new_btn.clicked.connect(self.add_new_addition)
            if hasattr(self, 'cancel_edit_btn') and self.cancel_edit_btn:
                self.cancel_edit_btn.hide()
            if hasattr(self, 'mandatory_checkbox') and self.mandatory_checkbox:
                self.mandatory_checkbox.hide()

            # Atualiza as listas
            self.load_specific_complements()
            self.load_additions()

            QMessageBox.information(
                self, "Sucesso", "Complemento atualizado com sucesso!")
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao atualizar complemento: {str(e)}")

    def remove_specific_complement(self, comp_id):
        from database.db import delete_item_specific_addition
        try:
            # Remove diretamente do banco usando o ID
            delete_item_specific_addition(comp_id)

            # Atualiza as listas
            self.load_specific_complements()
            self.load_additions()

            QMessageBox.information(
                self, "Sucesso", "Complemento removido com sucesso!")
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao remover complemento: {str(e)}")

    def load_additions(self):
        """Carrega todos os complementos obrigatórios (categoria + específicos)"""
        from database.db import (
            get_all_additions_for_item_with_mandatory_and_specific_info,
            get_category_id, get_menu_items)

        # Limpa o layout atual
        while self.additions_layout.count():
            child = self.additions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Busca informações do item
        items = get_menu_items()
        item_category = None
        cat_id = None
        for item in items:
            # item: (id, name, price, category_name, description, additions)
            if item[1] == self.item_name:
                item_category = item[3]
                cat_id = get_category_id(item_category)
                break

        if not cat_id:
            return

        # Busca todos os complementos com informações de obrigatoriedade
        try:
            all_additions_info = get_all_additions_for_item_with_mandatory_and_specific_info(
                self.item_id, cat_id)
        except Exception:
            all_additions_info = []

        # Exibe na interface
        self.addition_checks = []
        self.addition_ids = []
        for comp_id, name, price, is_mandatory, source in all_additions_info:
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)

            checkbox_text = f"{name} - R$ {price:.2f}"
            if source == 'item_specific':
                checkbox_text += " (Específico)"

            checkbox = QCheckBox(checkbox_text)
            checkbox.setChecked(bool(is_mandatory))
            checkbox.comp_data = {'id': comp_id, 'source': source}

            row_layout.addWidget(checkbox)
            row_widget.setLayout(row_layout)
            self.additions_layout.addWidget(row_widget)
            self.addition_checks.append(checkbox)
            self.addition_ids.append(comp_id)

    def add_new_addition(self):
        """Adiciona um novo complemento específico ao item"""
        name = self.new_name_input.text().strip()
        price = self.new_price_input.value()

        if not name:
            QMessageBox.warning(
                self, "Erro", "Nome do complemento é obrigatório!")
            return

        try:
            # Adiciona diretamente no banco
            from database.db import add_item_specific_addition_single
            add_item_specific_addition_single(self.item_id, name, price)

            # Limpa os campos
            self.new_name_input.clear()
            self.new_price_input.setValue(0.0)

            # Atualiza a lista em tempo real
            self.load_specific_complements()
            self.load_additions()

            QMessageBox.information(
                self, "Sucesso", f"Complemento específico '{name}' adicionado!")
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao adicionar complemento específico: {str(e)}")

    def get_selected_additions(self):
        """Retorna lista de IDs dos complementos selecionados"""
        return [self.addition_ids[i] for i, checkbox in enumerate(self.addition_checks) if checkbox.isChecked()]

    def toggle_all_additions(self, checked):
        """Marca/desmarca todas as checkboxes"""
        for checkbox in self.addition_checks:
            checkbox.setChecked(checked)

    def save_selections(self):
        """Salva as seleções no banco de dados"""
        from database.db import (set_item_mandatory_additions,
                                 set_item_specific_mandatory_additions)

        selected_ids = self.get_selected_additions()

        # Separa IDs por tipo de complemento
        category_addition_ids = []
        specific_addition_ids = []

        for i, checkbox in enumerate(self.addition_checks):
            if checkbox.isChecked() and hasattr(checkbox, 'comp_data'):
                comp_id = self.addition_ids[i]
                source = checkbox.comp_data.get('source', '')

                if source == 'category':
                    category_addition_ids.append(comp_id)
                elif source == 'item_specific':
                    specific_addition_ids.append(comp_id)

        # Salva obrigatoriedade dos complementos da categoria
        if category_addition_ids:
            set_item_mandatory_additions(self.item_id, category_addition_ids)

        # Salva obrigatoriedade dos complementos específicos
        if specific_addition_ids:
            set_item_specific_mandatory_additions(
                self.item_id, specific_addition_ids)


class MenuEditDialogItem(QWidget):
    def exec(self):
        """Simula comportamento modal usando QEventLoop"""
        from PySide6.QtCore import QEventLoop
        self._accepted = False
        self._event_loop = QEventLoop()
        self.show()
        self._event_loop.exec()
        return self._accepted

    def accept(self):
        self._accepted = True
        self.close()

    def reject(self):
        self._accepted = False
        self.close()

    def __init__(self, item, categories, additions, parent=None, item_id=None):
        super().__init__(parent)
        # Configura para aparecer na barra de tarefas com controles normais
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Editar Item do Cardápio")
        self.resize(400, 300)

        # Timer para o efeito de piscar
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.flash_window)
        self.flash_count = 0
        self.original_title = self.windowTitle()

        self.name, self.price, self.category, self.description, _ = item  # ignora item_additions
        self.categories = categories
        self.additions = additions
        self.item_id = item_id  # Armazena o ID do item
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nome:"))
        self.name_input = QLineEdit(self.name)
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Preço:"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("R$ ")
        self.price_input.setMaximum(9999)
        self.price_input.setDecimals(2)
        self.price_input.setValue(self.price)
        layout.addWidget(self.price_input)
        layout.addWidget(QLabel("Categoria:"))
        self.category_btn = QPushButton(self.category)
        self.category_menu = QMenu(self.category_btn)
        for cat in self.categories:
            action = self.category_menu.addAction(cat)
            action.triggered.connect(
                lambda checked, c=cat: self.select_category(c))
        self.category_btn.setMenu(self.category_menu)
        layout.addWidget(self.category_btn)
        layout.addWidget(QLabel("Descrição:"))
        self.description_input = QLineEdit(self.description)
        layout.addWidget(self.description_input)

        # Seção de complementos
        layout.addWidget(QLabel("Complementos:"))

        # Botão para gerenciar complementos específicos do item
        self.manage_additions_btn = QPushButton(
            "Gerenciar Complementos Específicos")
        self.manage_additions_btn.clicked.connect(
            self.open_item_additions_dialog)
        layout.addWidget(self.manage_additions_btn)

        # Widget e layout para exibir os complementos
        self.additions_widget = QWidget()
        self.additions_layout = QVBoxLayout()
        self.additions_widget.setLayout(self.additions_layout)
        layout.addWidget(self.additions_widget)
        self.setLayout(layout)
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        # Sempre exibe os complementos da categoria selecionada
        self.update_additions_view(self.category_btn.text())

    def changeEvent(self, event):
        # Detecta quando a janela perde o foco
        if event.type() == event.Type.WindowDeactivate:
            self.start_flashing()
        elif event.type() == event.Type.WindowActivate:
            self.stop_flashing()
        super().changeEvent(event)

    def closeEvent(self, event):
        if hasattr(self, '_event_loop') and self._event_loop.isRunning():
            self._event_loop.exit()
        super().closeEvent(event)

    def start_flashing(self):
        """Inicia o efeito de piscar da janela"""
        self.flash_count = 0
        self.flash_timer.start(300)  # Pisca a cada 300ms
        self.raise_()  # Traz a janela para frente
        self.activateWindow()  # Ativa a janela

    def stop_flashing(self):
        """Para o efeito de piscar"""
        self.flash_timer.stop()
        self.setWindowTitle(self.original_title)

    def flash_window(self):
        """Alterna o título da janela para criar efeito de piscar"""
        if self.flash_count >= 6:  # Pisca 3 vezes (6 mudanças)
            self.stop_flashing()
            return

        if self.flash_count % 2 == 0:
            self.setWindowTitle("🔔 " + self.original_title + " 🔔")
        else:
            self.setWindowTitle(self.original_title)

        self.flash_count += 1
        self.raise_()  # Mantém a janela no topo
        self.activateWindow()

    def update_additions_view(self, selected_category):
        # Remove a exibição dos complementos da categoria na edição de item
        while self.additions_layout.count():
            child = self.additions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_item(self):
        return (
            self.name_input.text().strip(),
            self.price_input.value(),
            self.category,  # agora pega do botão
            self.description_input.text().strip(),
            []  # itens não têm complementos próprios
        )

    def select_category(self, category):
        self.category = category
        self.category_btn.setText(category)
        self.update_additions_view(category)

    def open_item_additions_dialog(self):
        """Abre diálogo para gerenciar complementos específicos do item"""
        if self.item_id is not None:
            dialog = ItemAdditionsDialog(self.name, self.item_id, None)
            if dialog.exec():
                dialog.save_selections()
                # Atualiza a visualização após salvar
                self.update_additions_view(self.category)
        else:
            QMessageBox.warning(
                self, "Erro",
                "Item deve ser salvo antes de gerenciar complementos."
            )


class EditCategoryDialog(QDialog):
    def __init__(self, old_name, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Editar Categoria")
        self.resize(350, 120)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Novo nome da categoria:"))
        self.input = QLineEdit(old_name)
        layout.addWidget(self.input)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_new_name(self):
        return self.input.text().strip()
