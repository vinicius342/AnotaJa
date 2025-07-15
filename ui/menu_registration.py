import json
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QDoubleSpinBox, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMenu,
                               QMessageBox, QPushButton, QScrollArea,
                               QTabWidget, QVBoxLayout, QWidget)

from database.db import (add_addition, add_category, add_menu_item,
                         get_all_additions_with_id, get_categories,
                         get_category_additions, get_menu_items, init_db,
                         set_category_additions)
from ui.dialogs import CategoryAdditionsDialog
from utils.log_utils import get_logger

logger = get_logger(__name__)


class MenuItem:
    def __init__(self, name, price, category, description='', additions=None):
        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.additions = additions or []


class MenuRegistrationWindow(QDialog):
    # Sinal emitido quando um item é adicionado ao cardápio
    item_added = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('MenuRegistrationWindow inicializada')
        self.setWindowTitle("Cadastro de Cardápio")
        self.resize(800, 500)
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        try:
            init_db()
            logger.info('Banco de dados inicializado')
            self.categories = get_categories()
            logger.info(f'Categorias carregadas: {self.categories}')
            self.additions = get_all_additions_with_id()
            logger.info(f'Adicionais carregados: {self.additions}')
            self.menu_items = get_menu_items()
            logger.info(f'Itens do cardápio carregados: {self.menu_items}')
            # Carrega vínculos do banco
            self.category_additions = get_category_additions()

            # Adiciona categorias padrão se não existir nenhuma
            if not self.categories:
                default_categories = []
                for cat in default_categories:
                    add_category(cat)
                self.categories = get_categories()

            # Adiciona adicionais padrão se não existir nenhum
            if not self.additions:
                default_additions = []
                for add in default_additions:
                    add_addition(add)
                self.additions = get_all_additions_with_id()

            # Vincula alguns adicionais às categorias padrão para demonstração
            if not self.category_additions:
                self.category_additions = {}
                # Salva vínculos padrão no banco
                for cat, adds in self.category_additions.items():
                    set_category_additions(cat, adds)

            # Cria o widget central e aplica o layout nele
            layout = QVBoxLayout()
            self.tabs = QTabWidget()
            self.tab_items = QWidget()
            self.tab_categories = QWidget()
            self.tab_additions = QWidget()
            self.tabs.addTab(self.tab_items, "Itens")
            self.tabs.addTab(self.tab_categories, "Categorias")
            self.tabs.addTab(self.tab_additions, "Complementos")
            layout.addWidget(self.tabs)
            self.setLayout(layout)
            self.setup_categories_tab()
            self.setup_additions_tab()
            self.setup_items_tab()
        except Exception as e:
            logger.error(f'Erro ao abrir cadastro: {e}')
            QMessageBox.critical(self, "Erro ao abrir cadastro", str(e))
            raise

    def setup_items_tab(self):
        # Adiciona scroll area para o formulário de cadastro de item
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Formulário de cadastro de item
        form_layout = QVBoxLayout()
        # ...existing code...
        # Campo nome do item
        name_label = QLabel("Nome do Item:")
        name_label.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do item")
        form_layout.addWidget(self.name_input)
        # ...existing code...
        # Campo preço
        price_label = QLabel("Preço:")
        price_label.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(price_label)
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("R$ ")
        self.price_input.setMaximum(9999)
        self.price_input.setDecimals(2)
        form_layout.addWidget(self.price_input)
        # ...existing code...
        # Campo categoria
        category_label = QLabel("Categoria:")
        category_label.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(category_label)
        self.category_btn = QPushButton()
        self.category_menu = QMenu(self.category_btn)
        self.selected_category = self.categories[0] if self.categories else ''
        self.category_btn.setText(
            self.selected_category or "Selecione a categoria")
        for cat in self.categories:
            action = self.category_menu.addAction(cat)
            action.triggered.connect(
                lambda checked, c=cat: self.select_category(c))
        self.category_btn.setMenu(self.category_menu)
        form_layout.addWidget(self.category_btn)
        # ...existing code...
        # Campo descrição
        description_label = QLabel("Descrição:")
        description_label.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(description_label)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descrição")
        form_layout.addWidget(self.description_input)
        layout.addLayout(form_layout)

        # ...existing code...
        # Seção de complementos específicos do item
        complement_section_label = QLabel("Complementos Específicos do Item:")
        complement_section_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; margin-top: 15px;")
        layout.addWidget(complement_section_label)

        # ...existing code...
        # Formulário para adicionar complemento específico
        complement_form_layout = QHBoxLayout()
        complement_name_label = QLabel("Nome:")
        complement_form_layout.addWidget(complement_name_label)
        self.complement_name_input = QLineEdit()
        self.complement_name_input.setPlaceholderText("Nome do complemento")
        complement_form_layout.addWidget(self.complement_name_input)
        complement_price_label = QLabel("Valor:")
        complement_form_layout.addWidget(complement_price_label)
        self.complement_price_input = QDoubleSpinBox()
        self.complement_price_input.setPrefix("R$ ")
        self.complement_price_input.setMaximum(999.99)
        self.complement_price_input.setDecimals(2)
        complement_form_layout.addWidget(self.complement_price_input)
        add_complement_btn = QPushButton("Adicionar Complemento")
        add_complement_btn.clicked.connect(self.add_item_specific_complement)
        complement_form_layout.addWidget(add_complement_btn)
        layout.addLayout(complement_form_layout)

        # ...existing code...
        # Lista de complementos específicos sendo criados
        item_complements_label = QLabel("Complementos do Item:")
        item_complements_label.setStyleSheet(
            "font-weight: bold; margin-top: 10px;")
        layout.addWidget(item_complements_label)
        self.item_complements_list = QListWidget()
        self.item_complements_list.setMinimumHeight(80)
        self.item_complements_list.setMaximumHeight(120)
        layout.addWidget(self.item_complements_list)

        # ...existing code...
        # Botão para remover complemento específico
        remove_complement_btn = QPushButton("Remover Complemento Selecionado")
        remove_complement_btn.clicked.connect(
            self.remove_item_specific_complement)
        layout.addWidget(remove_complement_btn)

        # ...existing code...
        # Seção para selecionar complementos obrigatórios
        mandatory_section_label = QLabel("Complementos Obrigatórios:")
        mandatory_section_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; margin-top: 15px;")
        layout.addWidget(mandatory_section_label)

        # ...existing code...
        # Explicação
        explanation_label = QLabel(
            "Selecione quais complementos serão obrigatórios na hora do pedido:")
        explanation_label.setStyleSheet(
            "color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(explanation_label)

        # ...existing code...
        # Layout para complementos obrigatórios (checkbox à esquerda, nome à direita)
        self.mandatory_complements_widget = QWidget()
        self.mandatory_complements_layout = QVBoxLayout()
        self.mandatory_complements_layout.setContentsMargins(0, 0, 0, 0)
        self.mandatory_complements_layout.setSpacing(5)
        self.mandatory_complements_widget.setLayout(
            self.mandatory_complements_layout)
        layout.addWidget(self.mandatory_complements_widget)

        # ...existing code...
        # Botão para adicionar item
        add_item_btn = QPushButton("Adicionar Item")
        add_item_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        add_item_btn.clicked.connect(self.add_menu_item)
        layout.addWidget(add_item_btn)

        # Inicializa listas vazias de complementos específicos
        self.item_specific_complements = []

        # Atualiza as listas
        self.update_complement_lists()

        # Carrega os itens iniciais

        # Adiciona o scroll area à tab
        scroll_area.setWidget(scroll_content)
        self.tab_items.setLayout(QVBoxLayout())
        self.tab_items.layout().addWidget(scroll_area)
        self.refresh_items_list()

        self.tab_items.setLayout(layout)

    def select_category(self, category):
        """Seleciona uma categoria e atualiza a interface."""
        self.selected_category = category
        self.category_btn.setText(category)
        self.update_complement_lists()

    def add_item_specific_complement(self):
        """Adiciona um complemento específico à lista temporária"""
        name = self.complement_name_input.text().strip()
        price = self.complement_price_input.value()

        if not name:
            QMessageBox.warning(self, "Erro", "Digite o nome do complemento.")
            return

        # Verifica se já existe um complemento com esse nome na lista temporária
        for comp in self.item_specific_complements:
            if comp['name'].lower() == name.lower():
                QMessageBox.warning(
                    self, "Erro", "Já existe um complemento com esse nome para este item.")
                return

        # Adiciona à lista temporária
        complement = {
            'name': name,
            'price': price
        }
        self.item_specific_complements.append(complement)

        # Limpa os campos
        self.complement_name_input.clear()
        self.complement_price_input.setValue(0.0)

        # Atualiza a lista visual
        self.update_complement_lists()

    def remove_item_specific_complement(self):
        """Remove um complemento específico da lista temporária"""
        current_row = self.item_complements_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, "Aviso", "Selecione um complemento para remover.")
            return

        # Remove da lista temporária
        self.item_specific_complements.pop(current_row)

        # Atualiza a lista visual
        self.update_complement_lists()

    def update_complement_lists(self):
        """Atualiza as listas de complementos específicos e opções para obrigatórios"""
        # Atualiza lista de complementos específicos do item
        self.item_complements_list.clear()
        for comp in self.item_specific_complements:
            item_text = f"{comp['name']} - R$ {comp['price']:.2f}"
            self.item_complements_list.addItem(item_text)

        # Atualiza lista de complementos disponíveis para seleção como obrigatórios
        self.update_mandatory_complements_selection()

    def update_mandatory_complements_selection(self):
        """Atualiza a lista de complementos disponíveis para seleção como obrigatórios (QCheckBox à esquerda, QLabel à direita)"""
        from PySide6.QtWidgets import QCheckBox

        # Limpa o layout anterior
        while self.mandatory_complements_layout.count():
            child = self.mandatory_complements_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        from database.db import (get_all_additions_with_id,
                                 get_category_addition_ids, get_category_id)
        try:
            category_id = get_category_id(
                self.selected_category) if self.selected_category else None
            all_additions = []
            if category_id:
                # Complementos da categoria
                addition_ids = get_category_addition_ids(category_id)
                additions_dict = {
                    add_id: (name, price) for add_id, name, price in get_all_additions_with_id()}
                for add_id in addition_ids:
                    if add_id in additions_dict:
                        name, price = additions_dict[add_id]
                        all_additions.append(
                            {'id': add_id, 'name': name, 'price': price, 'source': 'category'})
            # Complementos específicos do item (temporários)
            for comp in self.item_specific_complements:
                all_additions.append({'id': comp.get(
                    'id', comp['name']), 'name': comp['name'], 'price': comp['price'], 'source': 'specific'})

            if not all_additions:
                label = QLabel(
                    "Nenhum complemento disponível para esta categoria")
                label.setStyleSheet("color: gray; font-style: italic;")
                self.mandatory_complements_layout.addWidget(label)
                return

            # Armazena checkboxes para consulta posterior
            self.mandatory_complements_checkboxes = []
            for comp in all_additions:
                row_widget = QWidget()
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(10)
                checkbox = QCheckBox()
                checkbox.setChecked(False)
                checkbox.comp_data = {
                    'id': comp['id'], 'source': comp['source']}
                label = QLabel(f"{comp['name']} - R$ {comp['price']:.2f}")
                row_layout.addWidget(checkbox)
                row_layout.addWidget(label)
                row_layout.addStretch()
                row_widget.setLayout(row_layout)
                self.mandatory_complements_layout.addWidget(row_widget)
                self.mandatory_complements_checkboxes.append(checkbox)

        except Exception as e:
            logger.error(f"Erro ao carregar complementos obrigatórios: {e}")
            label = QLabel("Erro ao carregar complementos")
            label.setStyleSheet("color: red;")
            self.mandatory_complements_layout.addWidget(label)

    def get_selected_mandatory_complements(self):
        """Retorna os IDs dos complementos marcados como obrigatórios (checkboxes)"""
        selected_ids = []
        if hasattr(self, 'mandatory_complements_checkboxes'):
            for checkbox in self.mandatory_complements_checkboxes:
                if checkbox.isChecked():
                    comp_data = getattr(checkbox, 'comp_data', None)
                    if comp_data and 'id' in comp_data:
                        selected_ids.append(comp_data['id'])
        return selected_ids

    def add_menu_item(self):
        name = self.name_input.text().strip()
        price = self.price_input.value()
        category_name = self.selected_category
        description = self.description_input.text().strip()

        if not name or not category_name:
            QMessageBox.warning(self, "Erro", "Preencha nome e categoria.")
            return

        # Verifica se já existe item com esse nome
        from database.db import get_menu_items
        if any(item[1] == name for item in get_menu_items()):
            QMessageBox.warning(
                self, "Erro", "Já existe um item com esse nome.")
            return

        # Buscar o ID da categoria
        from database.db import (add_menu_item, get_category_addition_ids,
                                 get_category_id, set_item_mandatory_additions)
        category_id = get_category_id(category_name)

        # Buscar os IDs dos adicionais vinculados à categoria
        addition_ids = get_category_addition_ids(category_id)

        # Salvar o item com os IDs da categoria
        item_id = add_menu_item(name, price, category_id,
                                description, addition_ids)

        # Salvar complementos específicos do item no banco
        specific_complement_ids = []
        if self.item_specific_complements:
            specific_complement_ids = self.save_item_specific_complements(
                item_id)

        # Salvar complementos obrigatórios selecionados
        mandatory_complement_ids = self.get_selected_mandatory_complements()
        if mandatory_complement_ids:
            # Filtra apenas IDs válidos (numéricos) e mapeia nomes temporários para IDs reais
            valid_ids = []
            for comp_id in mandatory_complement_ids:
                if isinstance(comp_id, int):
                    valid_ids.append(comp_id)
                elif isinstance(comp_id, str):
                    # Busca o ID real do complemento específico que foi salvo
                    for saved_id, comp in zip(specific_complement_ids, self.item_specific_complements):
                        if comp['name'] == comp_id:
                            valid_ids.append(saved_id)
                            break

            if valid_ids:
                set_item_mandatory_additions(item_id, valid_ids)

        # Limpa os campos
        self.name_input.clear()
        self.price_input.setValue(0)
        self.description_input.clear()
        self.item_specific_complements.clear()

        # Atualiza categoria selecionada
        if self.categories:
            self.select_category(self.categories[0])

        # Atualiza a lista de itens
        self.menu_items = get_menu_items()
        self.refresh_items_list()

        # Atualiza as listas de complementos
        self.update_complement_lists()

        QMessageBox.information(
            self, "Sucesso", f"Item '{name}' adicionado com sucesso!")

        # Emite sinal para notificar que um item foi adicionado
        self.item_added.emit()

        QMessageBox.information(
            self, "Sucesso", f"Item '{name}' adicionado com sucesso!")

    def save_item_specific_complements(self, item_id):
        """Salva os complementos específicos do item no banco de dados"""
        from database.db import add_addition

        try:
            complement_ids = []
            for comp in self.item_specific_complements:
                # Adiciona cada complemento específico ao banco
                comp_id = add_addition(comp['name'], comp['price'])
                complement_ids.append(comp_id)

            # Vincula os complementos específicos ao item
            from database.db import set_item_specific_additions
            set_item_specific_additions(item_id, complement_ids)

            return complement_ids

        except Exception as e:
            logger.error(f"Erro ao salvar complementos específicos: {e}")
            QMessageBox.warning(
                self, "Erro", f"Erro ao salvar complementos específicos: {str(e)}")
            return []

    def refresh_items_list(self):
        """Atualiza a lista de itens cadastrados (se existir)"""
        # Este método pode ser implementado se houver uma lista de itens na interface
        pass

    def setup_categories_tab(self):
        if hasattr(self, 'tab_categories') and self.tab_categories.layout() is not None:
            self.clear_layout(self.tab_categories.layout())
        layout = QVBoxLayout()
        # Formulário de cadastro de categoria
        form_layout = QHBoxLayout()
        self.category_new_input = QLineEdit()
        self.category_new_input.setPlaceholderText("Nova categoria")
        add_category_btn = QPushButton("Adicionar Categoria")
        add_category_btn.clicked.connect(self.add_category_with_dialog)
        btn_addition = QPushButton("Complementos")
        btn_addition.clicked.connect(self.open_category_additions)
        form_layout.addWidget(self.category_new_input)
        form_layout.addWidget(add_category_btn)
        form_layout.addWidget(btn_addition)
        layout.addLayout(form_layout)
        # Lista de categorias
        self.categories_list = QListWidget()
        for cat in self.categories:
            self.categories_list.addItem(cat)
        layout.addWidget(self.categories_list)
        self.tab_categories.setLayout(layout)

    def add_category_with_dialog(self):
        name = self.category_new_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Erro", "Digite o nome da categoria.")
            return
        if name in self.categories:
            QMessageBox.warning(self, "Erro", "Categoria já existe.")
            return
        add_category(name)
        self.categories.append(name)
        self.categories_list.addItem(name)
        self.category_new_input.clear()
        # Após adicionar, já abre o diálogo para vincular adicionais
        self.open_link_additions_dialog(new_category=name)
        # Atualiza o menu de categorias na aba de itens
        self.update_category_menu_items_tab()

    def update_category_menu_items_tab(self):
        # Atualiza o menu de categorias na aba de itens
        self.category_menu.clear()
        for cat in self.categories:
            action = self.category_menu.addAction(cat)
            action.triggered.connect(
                lambda checked, c=cat: self.select_category(c))
        if self.categories:
            self.selected_category = self.categories[0]
            self.category_btn.setText(self.selected_category)
        else:
            self.selected_category = ''
            self.category_btn.setText("Selecione a categoria")
        self.update_additions_checks()

    def open_link_additions_dialog(self, new_category=None):
        if new_category:
            cat = new_category
        else:
            idx = self.categories_list.currentRow()
            if idx < 0 or idx >= len(self.categories):
                QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
                return
            cat = self.categories[idx]
        # Buscar o ID da categoria
        from database.db import (get_all_additions_with_id, get_category_id,
                                 set_category_addition_ids)
        cat_id = get_category_id(cat)
        all_additions = get_all_additions_with_id()  # [(id, nome, preco), ...]
        # Buscar IDs já vinculados (se houver)
        from database.db import get_category_addition_ids
        selected = get_category_addition_ids(cat_id)
        dialog = CategoryAdditionsDialog(
            cat, all_additions, selected, self)
        if dialog.exec():
            selected = dialog.get_selected_additions()  # lista de IDs
            set_category_addition_ids(cat_id, selected)
            self.update_additions_checks()

    def setup_additions_tab(self):
        if hasattr(self, 'tab_additions') and self.tab_additions.layout() is not None:
            self.clear_layout(self.tab_additions.layout())
        layout = QVBoxLayout()
        form_layout = QHBoxLayout()
        self.addition_new_input = QLineEdit()
        self.addition_new_input.setPlaceholderText("Novo complemento")
        self.addition_price_input = QDoubleSpinBox()
        self.addition_price_input.setPrefix("R$ ")
        self.addition_price_input.setMaximum(9999)
        self.addition_price_input.setDecimals(2)
        add_button = QPushButton("Adicionar Complemento")
        add_button.clicked.connect(self.add_addition)
        form_layout.addWidget(self.addition_new_input)
        form_layout.addWidget(self.addition_price_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)
        # Layout dinâmico para exibir complementos vinculados à categoria
        self.additions_layout = QVBoxLayout()
        self.additions_layout.setContentsMargins(0, 0, 0, 0)
        self.additions_layout.setSpacing(5)
        layout.addLayout(self.additions_layout)

        self.additions_list = QListWidget()
        # Exibe nome e valor do complemento
        for add_tuple in get_all_additions_with_id():
            _, add, price = add_tuple
            item_text = f"{add}   R$ {price:.2f}"
            self.additions_list.addItem(item_text)
        layout.addWidget(self.additions_list)
        self.tab_additions.setLayout(layout)

    def add_addition(self):
        name = self.addition_new_input.text().strip()
        price = self.addition_price_input.value()
        if not name:
            QMessageBox.warning(self, "Erro", "Digite o nome do complemento.")
            return
        if name in [a[1] for a in get_all_additions_with_id()]:
            QMessageBox.warning(self, "Erro", "Complemento já existe.")
            return
        add_addition(name, price)
        # Atualiza a lista de adicionais (id, nome, preço)
        self.additions = get_all_additions_with_id()
        self.additions_list.clear()
        for _, add, price in self.additions:
            item_text = f"{add}   R$ {price:.2f}"
            self.additions_list.addItem(item_text)
        self.addition_new_input.clear()
        self.addition_price_input.setValue(0)

    def open_category_additions(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
            return
        cat_name = self.categories[idx]
        # Buscar o ID da categoria
        from database.db import (get_all_additions_with_id,
                                 get_category_addition_ids, get_category_id,
                                 set_category_addition_ids)
        cat_id = get_category_id(cat_name)
        all_additions = get_all_additions_with_id()  # [(id, nome, preco), ...]
        selected_addition_ids = get_category_addition_ids(cat_id)  # [id, ...]
        dialog = CategoryAdditionsDialog(
            cat_name, all_additions, selected_addition_ids, self)
        if dialog.exec():
            selected = dialog.get_selected_additions()  # lista de IDs
            set_category_addition_ids(cat_id, selected)
        self.update_additions_checks()

    def refresh_categories_tab(self):
        self.setup_categories_tab()

    def clear_layout(self, layout):
        """Remove todos os widgets de um layout."""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clear_layout(child.layout())

    def update_additions_checks(self):
        # Atualiza a visualização dos adicionais vinculados à categoria selecionada
        for i in reversed(range(self.additions_layout.count())):
            widget = self.additions_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # Buscar o ID da categoria selecionada
        from database.db import (get_all_additions_with_id,
                                 get_category_addition_ids, get_category_id)
        cat_id = None
        if self.selected_category:
            from database.db import get_category_id
            cat_id = get_category_id(self.selected_category)
        if not cat_id:
            label = QLabel("Nenhum complemento vinculado a esta categoria.")
            label.setStyleSheet("color: gray; font-style: italic;")
            self.additions_layout.addWidget(label)
            return
        # Busca os IDs dos adicionais vinculados
        addition_ids = get_category_addition_ids(cat_id)
        # Busca todos os adicionais (id, nome, preco)
        all_additions = {add_id: (name, price)
                         for add_id, name, price in get_all_additions_with_id()}
        if not addition_ids:
            label = QLabel("Nenhum complemento vinculado a esta categoria.")
            label.setStyleSheet("color: gray; font-style: italic;")
            self.additions_layout.addWidget(label)
        else:
            for add_id in addition_ids:
                name, price = all_additions.get(add_id, ("(Removido)", 0.0))
                label = QLabel(f"• {name}   R$ {price:.2f}")
                self.additions_layout.addWidget(label)

    def refresh_items_list(self):
        """Atualiza a lista de itens cadastrados (se existir)"""
        # Este método pode ser implementado se houver uma lista de itens na interface
        pass

# Fim do arquivo
