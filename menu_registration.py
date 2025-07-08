import json
from functools import partial

from PySide6.QtWidgets import (QDialog,
                               QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QMenu, QMessageBox, QPushButton,
                               QScrollArea, QTabWidget, QVBoxLayout, QWidget)

from db import (add_addition, add_category, add_menu_item, get_all_additions_with_id,
                get_categories, get_category_additions, get_menu_items,
                init_db, set_category_additions)
from dialogs import CategoryAdditionsDialog
from log_utils import get_logger

logger = get_logger(__name__)


class MenuItem:
    def __init__(self, name, price, category, description='', additions=None):
        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.additions = additions or []


class MenuRegistrationWindow(QDialog):
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
            self.tabs.addTab(self.tab_additions, "Adicionais")
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
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Formulário de cadastro de item (agora em coluna)
        form_layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do item")
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("R$ ")
        self.price_input.setMaximum(9999)
        self.price_input.setDecimals(2)
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
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descrição")
        add_item_btn = QPushButton("Adicionar Item")
        add_item_btn.clicked.connect(self.add_menu_item)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.price_input)
        form_layout.addWidget(self.category_btn)
        form_layout.addWidget(self.description_input)
        form_layout.addWidget(add_item_btn)
        layout.addLayout(form_layout)

        # Layout para exibir os adicionais da categoria selecionada, agora com scroll
        from PySide6.QtWidgets import QScrollArea, QWidget
        self.additions_widget = QWidget()
        self.additions_layout = QVBoxLayout()
        self.additions_widget.setLayout(self.additions_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.additions_widget)
        self.scroll_area.setMinimumHeight(80)
        self.scroll_area.setMaximumHeight(200)
        layout.addWidget(self.scroll_area)
        self.update_additions_checks()

        self.tab_items.setLayout(layout)

    def select_category(self, category):
        """Seleciona uma categoria e atualiza a interface."""
        self.selected_category = category
        self.category_btn.setText(category)
        self.update_additions_checks()

    def add_menu_item(self):
        name = self.name_input.text().strip()
        price = self.price_input.value()
        category_name = self.selected_category
        description = self.description_input.text().strip()
        if not name or not category_name:
            QMessageBox.warning(self, "Erro", "Preencha nome e categoria.")
            return
        # Verifica se já existe item com esse nome
        from db import get_menu_items
        if any(item[1] == name for item in get_menu_items()):
            QMessageBox.warning(self, "Erro", "Já existe um item com esse nome.")
            return
        # Buscar o ID da categoria
        from db import (add_menu_item, get_category_addition_ids, get_category_id)
        category_id = get_category_id(category_name)
        # Buscar os IDs dos adicionais vinculados à categoria
        addition_ids = get_category_addition_ids(category_id)
        # Salvar o item com os IDs
        add_menu_item(name, price, category_id, description, addition_ids)
        self.menu_items = get_menu_items()
        self.name_input.clear()
        self.price_input.setValue(0)
        self.description_input.clear()
        if self.categories:
            self.select_category(self.categories[0])
        # Atualiza a lista de itens exibidos
        # self.refresh_items_list()

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
        btn_addition = QPushButton("Adicionais")
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
        from db import (get_all_additions_with_id, get_category_id,
                        set_category_addition_ids)
        cat_id = get_category_id(cat)
        all_additions = get_all_additions_with_id()  # [(id, nome, preco), ...]
        # Buscar IDs já vinculados (se houver)
        from db import get_category_addition_ids
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
        self.addition_new_input.setPlaceholderText("Novo adicional")
        self.addition_price_input = QDoubleSpinBox()
        self.addition_price_input.setPrefix("R$ ")
        self.addition_price_input.setMaximum(9999)
        self.addition_price_input.setDecimals(2)
        add_button = QPushButton("Adicionar Adicional")
        add_button.clicked.connect(self.add_addition)
        form_layout.addWidget(self.addition_new_input)
        form_layout.addWidget(self.addition_price_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)
        self.additions_list = QListWidget()
        # Exibe nome e valor do adicional
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
            QMessageBox.warning(self, "Erro", "Digite o nome do adicional.")
            return
        if name in [a[1] for a in get_all_additions_with_id()]:
            QMessageBox.warning(self, "Erro", "Adicional já existe.")
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
        from db import (get_all_additions_with_id, get_category_addition_ids,
                        get_category_id, set_category_addition_ids)
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
        from db import (get_all_additions_with_id, get_category_addition_ids,
                        get_category_id)
        cat_id = None
        if self.selected_category:
            from db import get_category_id
            cat_id = get_category_id(self.selected_category)
        if not cat_id:
            label = QLabel("Nenhum adicional vinculado a esta categoria.")
            label.setStyleSheet("color: gray; font-style: italic;")
            self.additions_layout.addWidget(label)
            return
        # Busca os IDs dos adicionais vinculados
        addition_ids = get_category_addition_ids(cat_id)
        # Busca todos os adicionais (id, nome, preco)
        all_additions = {add_id: (name, price)
                         for add_id, name, price in get_all_additions_with_id()}
        if not addition_ids:
            label = QLabel("Nenhum adicional vinculado a esta categoria.")
            label.setStyleSheet("color: gray; font-style: italic;")
            self.additions_layout.addWidget(label)
        else:
            for add_id in addition_ids:
                name, price = all_additions.get(add_id, ("(Removido)", 0.0))
                label = QLabel(f"• {name}   R$ {price:.2f}")
                self.additions_layout.addWidget(label)

    # Removido: métodos relacionados à lista de itens na aba de itens
    # def refresh_items_list(self): ...
    # def delete_selected_item(self): ...
    # def edit_selected_item(self): ...

# Fim do arquivo
