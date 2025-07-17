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
    """Diálogo para selecionar complementos específicos de um item"""

    def __init__(self, item_name, item_id, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle(f"Complementos específicos para {item_name}")
        self.setModal(True)
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
        for comp_id, name, price in self.specific_complements:
            item = QListWidgetItem(f"{name} - R$ {price:.2f}")
            item.setData(Qt.UserRole, (comp_id, name, price))
            self.specific_list_widget.addItem(item)

    def edit_selected_specific(self):
        item = self.specific_list_widget.currentItem()
        if item:
            comp_id, name, price = item.data(Qt.UserRole)
            self.edit_specific_complement(comp_id, name, price)

    def remove_selected_specific(self):
        item = self.specific_list_widget.currentItem()
        if item:
            comp_id, name, price = item.data(Qt.UserRole)
            self.remove_specific_complement(comp_id)

    def edit_specific_complement(self, comp_id, name, price):
        # Preenche campos para edição
        self.new_name_input.setText(name)
        self.new_price_input.setValue(price)
        self.add_new_btn.setText("Salvar")
        self.add_new_btn.clicked.disconnect()
        self.add_new_btn.clicked.connect(
            lambda: self.save_specific_complement(comp_id))

    def save_specific_complement(self, comp_id):
        from database.db import (get_item_specific_additions,
                                 set_item_specific_additions)
        name = self.new_name_input.text().strip()
        price = self.new_price_input.value()
        if not name:
            QMessageBox.warning(
                self, "Erro", "Nome do complemento é obrigatório!")
            return
        # Atualiza no banco
        comps = [(cid, n, p) for cid, n, p in self.specific_complements]
        for i, (cid, _, _) in enumerate(comps):
            if cid == comp_id:
                comps[i] = (cid, name, price)
        # Envia lista de tuplas (name, price) para o banco
        set_item_specific_additions(
            self.item_id, [(n, p) for _, n, p in comps])
        self.new_name_input.clear()
        self.new_price_input.setValue(0.0)
        self.add_new_btn.setText("Adicionar")
        self.add_new_btn.clicked.disconnect()
        self.add_new_btn.clicked.connect(self.add_new_addition)
        self.load_specific_complements()
        self.load_additions()

    def remove_specific_complement(self, comp_id):
        from database.db import set_item_specific_additions
        comps = [(cid, n, p)
                 for cid, n, p in self.specific_complements if cid != comp_id]
        set_item_specific_additions(
            self.item_id, [{'name': n, 'price': p} for _, n, p in comps])
        self.load_specific_complements()
        self.load_additions()

    def load_additions(self):
        """Carrega todos os complementos obrigatórios (categoria + específicos)"""
        from database.db import (get_category_additions, get_category_id,
                                 get_item_specific_additions)

        # Limpa o layout atual
        while self.additions_layout.count():
            child = self.additions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # Complementos da categoria do item
        from database.db import (get_category_addition_ids, get_category_id,
                                 get_menu_items)
        items = get_menu_items()
        item_category = None
        item_id = None
        for item in items:
            # item: (id, name, price, category_name, description, additions)
            if item[1] == self.item_name:
                item_category = item[3]
                item_id = item[0]
                break
        cat_id = get_category_id(item_category) if item_category else None
        category_addition_ids = get_category_addition_ids(
            cat_id) if cat_id else []
        # Complementos específicos do item
        specific_comps = get_item_specific_additions(self.item_id)
        # IDs obrigatórios já salvos - obtém da nova função
        try:
            from database.db import \
                get_all_additions_for_item_with_mandatory_info
            all_additions_info = (
                get_all_additions_for_item_with_mandatory_info(
                    self.item_id, self.category_id))
            mandatory_ids = [add_id for add_id, name, price, is_mandatory
                             in all_additions_info if is_mandatory]
        except Exception:
            mandatory_ids = []
        # Monta lista completa
        all_additions = []
        from database.db import get_all_additions_with_id
        additions_dict = {add_id: (name, price)
                          for add_id, name, price in get_all_additions_with_id()}
        # Adiciona complementos da categoria
        for add_id in category_addition_ids:
            if add_id in additions_dict:
                name, price = additions_dict[add_id]
                all_additions.append(
                    {'id': add_id, 'name': name, 'price': price, 'source': 'category'})
        # Adiciona complementos específicos do item
        for comp in specific_comps:
            cid, name, price = comp
            all_additions.append(
                {'id': cid, 'name': name, 'price': price, 'source': 'specific'})
        # Exibe na interface
        self.addition_checks = []
        self.addition_ids = []
        for comp in all_additions:
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)
            checkbox = QCheckBox(f"{comp['name']} - R$ {comp['price']:.2f}")
            # Marca se for obrigatório (is_mandatory=1) ou se for específico do item
            checked = False
            if 'is_mandatory' in comp:
                checked = comp.get('is_mandatory', 0) == 1
            # Para complementos específicos, sempre marca
            if comp.get('source') == 'specific':
                checked = True
            checkbox.setChecked(checked)
            checkbox.comp_data = {'id': comp['id'], 'source': comp['source']}
            row_layout.addWidget(checkbox)
            row_widget.setLayout(row_layout)
            self.additions_layout.addWidget(row_widget)
            self.addition_checks.append(checkbox)
            self.addition_ids.append(comp['id'])

    def add_new_addition(self):
        """Adiciona um novo complemento específico ao item"""
        name = self.new_name_input.text().strip()
        price = self.new_price_input.value()

        if not name:
            QMessageBox.warning(
                self, "Erro", "Nome do complemento é obrigatório!")
            return

        try:
            # Recupera lista atual de complementos específicos
            from database.db import (get_item_specific_additions,
                                     set_item_specific_additions)
            comps = get_item_specific_additions(self.item_id)
            # None para novo, o banco deve gerar o id
            comps.append((None, name, price))
            # Salva todos os complementos específicos do item (formato correto)
            set_item_specific_additions(self.item_id, [
                {'name': n, 'price': p} for _, n, p in comps
            ])

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
        selected_ids = self.get_selected_additions()
        # Filtra os complementos específicos selecionados
        selected_comps = [
            {'name': name, 'price': price}
            for cid, name, price in self.specific_complements
            if cid in selected_ids
        ]
        set_item_specific_additions(self.item_id, selected_comps)


class MenuEditDialogItem(QDialog):
    def __init__(self, item, categories, additions, parent=None, item_id=None):
        super().__init__(parent)
        # Configura para aparecer na barra de tarefas com controles normais
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Editar Item do Cardápio")
        self.setModal(True)
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
            dialog = ItemAdditionsDialog(self.name, self.item_id, self)
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
