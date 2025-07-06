from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox,  # Adiciona QMainWindow
                               QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QHBoxLayout, QHeaderView, QInputDialog, QLabel,
                               QLineEdit, QListWidget, QMainWindow, QMenu,
                               QMessageBox, QPushButton, QSizePolicy,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from db import (add_addition, add_category, add_menu_item, delete_addition,
                delete_category, delete_menu_item, get_additions,
                get_categories, get_category_additions, get_menu_items,
                init_db, set_category_additions)
from log_utils import get_logger

logger = get_logger(__name__)


class MenuItem:
    def __init__(self, name, price, category, description='', additions=None):
        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.additions = additions or []


class MenuRegistrationWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('MenuRegistrationWindow inicializada')
        self.setWindowTitle("Cadastro de Cardápio")
        try:
            init_db()
            logger.info('Banco de dados inicializado')
            self.categories = get_categories()
            logger.info(f'Categorias carregadas: {self.categories}')
            self.additions = get_additions()
            logger.info(f'Adicionais carregados: {self.additions}')
            self.menu_items = get_menu_items()
            logger.info(f'Itens do cardápio carregados: {self.menu_items}')
            # Carrega vínculos do banco
            self.category_additions = get_category_additions()

            # Adiciona categorias padrão se não existir nenhuma
            if not self.categories:
                default_categories = [
                    "Bebidas", "Pratos Principais", "Sobremesas", "Aperitivos"]
                for cat in default_categories:
                    add_category(cat)
                self.categories = get_categories()

            # Adiciona adicionais padrão se não existir nenhum
            if not self.additions:
                default_additions = ["Sem Açúcar",
                                     "Gelado", "Quente", "Porção Extra"]
                for add in default_additions:
                    add_addition(add)
                self.additions = get_additions()

            # Vincula alguns adicionais às categorias padrão para demonstração
            if not self.category_additions:
                self.category_additions = {
                    "Bebidas": ["Sem Açúcar", "Gelado", "Quente"],
                    "Pratos Principais": ["Porção Extra"],
                    "Sobremesas": ["Sem Açúcar"],
                    "Aperitivos": ["Porção Extra"]
                }
                # Salva vínculos padrão no banco
                for cat, adds in self.category_additions.items():
                    set_category_additions(cat, adds)

            # Cria o widget central e aplica o layout nele
            central_widget = QWidget()
            layout = QVBoxLayout()
            self.tabs = QTabWidget()
            self.tab_items = QWidget()
            self.tab_categories = QWidget()
            self.tab_additions = QWidget()
            self.tabs.addTab(self.tab_items, "Itens")
            self.tabs.addTab(self.tab_categories, "Categorias")
            self.tabs.addTab(self.tab_additions, "Adicionais")
            layout.addWidget(self.tabs)
            self.setCentralWidget(central_widget)
            self.setup_categories_tab()
            self.setup_additions_tab()
            self.setup_items_tab()
            central_widget.setLayout(layout)
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
        # Substitui QComboBox por QPushButton com menu
        self.category_btn = QPushButton()
        self.category_menu = QMenu(self.category_btn)
        self.selected_category = self.categories[0] if self.categories else ''
        self.category_btn.setText(self.selected_category or "Selecione a categoria")
        for cat in self.categories:
            action = self.category_menu.addAction(cat)
            action.triggered.connect(lambda checked, c=cat: self.select_category(c))
        self.category_btn.setMenu(self.category_menu)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descrição")
        self.additions_input = QLineEdit()
        self.additions_input.setPlaceholderText(
            "Adicionais (separados por vírgula)")
        add_item_btn = QPushButton("Adicionar Item")
        add_item_btn.clicked.connect(self.add_menu_item)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.price_input)
        form_layout.addWidget(self.category_btn)
        form_layout.addWidget(self.description_input)
        form_layout.addWidget(self.additions_input)
        form_layout.addWidget(add_item_btn)
        layout.addLayout(form_layout)
        self.tab_items.setLayout(layout)

    def select_category(self, category):
        self.selected_category = category
        self.category_btn.setText(category)

    def add_menu_item(self):
        name = self.name_input.text().strip()
        price = self.price_input.value()
        category = self.selected_category
        description = self.description_input.text().strip()
        additions = self.additions_input.text().strip()
        if not name or not category:
            QMessageBox.warning(self, "Erro", "Preencha nome e categoria.")
            return
        add_menu_item(name, price, category, description, additions)
        self.menu_items = get_menu_items()
        self.refresh_table()
        self.name_input.clear()
        self.price_input.setValue(0)
        self.description_input.clear()
        self.additions_input.clear()
        # Restaura categoria selecionada
        if self.categories:
            self.select_category(self.categories[0])

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
        form_layout.addWidget(self.category_new_input)
        form_layout.addWidget(add_category_btn)
        layout.addLayout(form_layout)
        self.tab_categories.setLayout(layout)

    def add_category_with_dialog(self):
        name = self.category_new_input.text().strip()
        if name and name not in self.categories:
            add_category(name)
            self.categories.append(name)
            self.categories_list.addItem(name)
            self.category_new_input.clear()
            # Após adicionar, já abre o diálogo para vincular adicionais
            self.open_link_additions_dialog(new_category=name)

    def open_link_additions_dialog(self, new_category=None):
        if new_category:
            cat = new_category
        else:
            idx = self.categories_list.currentRow()
            if idx < 0 or idx >= len(self.categories):
                QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
                return
            cat = self.categories[idx]
        dialog = CategoryAdditionsDialog(
            cat, self.additions, self.category_additions.get(cat, []), self)
        if dialog.exec():
            selected = dialog.get_selected_additions()
            self.category_additions[cat] = selected
            set_category_additions(cat, selected)

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
        self.tab_additions.setLayout(layout)

    def add_addition(self):
        name = self.addition_new_input.text().strip()
        price = self.addition_price_input.value()
        logger.info(
            f'Tentando adicionar adicional (edit): {name} - R$ {price:.2f}')
        if name and name not in self.additions:
            # Aqui você pode adaptar para salvar o valor do adicional no banco, se necessário
            add_addition(name)  # Adapte para aceitar preço se necessário
            self.additions.append(name)
            self.addition_new_input.clear()
            self.addition_price_input.setValue(0)

    def open_category_additions(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
            return
        cat = self.categories[idx]
        dialog = CategoryAdditionsDialog(
            cat, self.additions, self.category_additions.get(cat, []), self)
        if dialog.exec():
            selected = dialog.get_selected_additions()
            self.category_additions[cat] = selected
            set_category_additions(cat, selected)  # Salva vínculo no banco
        self.update_additions_checks()

    def setup_category_menu(self):
        """Configura o menu de categorias do QPushButton."""
        self.category_menu.clear()
        for category in self.categories:
            action = self.category_menu.addAction(category)
            action.triggered.connect(
                lambda checked, cat=category: self.select_category(cat))

        # Seleciona a primeira categoria por padrão
        if self.categories:
            self.select_category(self.categories[0])

    def select_category(self, category):
        """Seleciona uma categoria e atualiza a interface."""
        self.selected_category = category
        self.category_input.setText(category)
        self.update_additions_checks()

    def get_selected_category(self):
        """Retorna a categoria selecionada."""
        return self.selected_category

    def update_additions_checks(self):
        print(
            f"update_additions_checks chamado! Categoria selecionada: {self.selected_category}")
        # Limpa widgets antigos
        for i in reversed(range(self.additions_layout.count())):
            widget = self.additions_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.additions_checks = []
        cat = self.selected_category
        adds = self.category_additions.get(cat, [])

        # Se não há adicionais vinculados à categoria, mostra mensagem
        if not adds:
            label = QLabel("Nenhum adicional vinculado a esta categoria.")
            label.setStyleSheet("color: gray; font-style: italic;")
            self.additions_layout.addWidget(label)
        else:
            # Apenas mostra os nomes dos adicionais, sem checkbox
            for add in adds:
                label = QLabel(f"• {add}")
                self.additions_layout.addWidget(label)

    def on_category_selected(self, index):
        """Método chamado quando uma categoria é selecionada via clique no popup."""
        # Força o fechamento do popup do QComboBox
        self.category_input.hidePopup()
        # Garante que o foco saia do combo para outro widget
        self.name_input.setFocus()

    def setup_categories_tab(self):
        # Limpa layout antigo, se existir
        if hasattr(self, 'tab_categories') and self.tab_categories.layout() is not None:
            self.clear_layout(self.tab_categories.layout())
        layout = QVBoxLayout()
        row_layout = QHBoxLayout()
        btn_addition = QPushButton("Adicionais")
        btn_addition.clicked.connect(self.open_category_additions)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self.edit_selected_category)
        btn_delete = QPushButton("Excluir")
        btn_delete.clicked.connect(self.delete_selected_category)
        row_layout.addWidget(btn_addition)
        row_layout.addWidget(btn_edit)
        row_layout.addWidget(btn_delete)
        layout.addLayout(row_layout)

        # Lista de categorias com menu de contexto
        self.categories_list = QListWidget()
        self.categories_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.categories_list.customContextMenuRequested.connect(
            self.show_category_context_menu)
        for cat in self.categories:
            self.categories_list.addItem(cat)
        layout.addWidget(self.categories_list)
        self.tab_categories.setLayout(layout)

    def edit_selected_category(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(
                self, "Erro", "Selecione uma categoria para editar.")
            return
        self.edit_category(idx)

    def delete_selected_category(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(
                self, "Erro", "Selecione uma categoria para excluir.")
            return
        self.delete_category(idx)

    def setup_additions_tab(self):
        # Limpa layout antigo, se existir
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
        # Lista de adicionais
        self.additions_list = QListWidget()
        for add in self.additions:
            self.additions_list.addItem(add)
        layout.addWidget(self.additions_list)
        self.tab_additions.setLayout(layout)

    def edit_item(self, row):
        logger.info(f'Editando item na linha: {row}')
        item = self.menu_items[row]
        old_name = item[0]  # Store the old name to delete the old record
        dialog = MenuEditDialogItem(
            item, self.categories, self.additions, self)
        if dialog.exec():
            # Get the updated item data
            updated_item = dialog.get_item()
            # Delete the old item and add the new one
            delete_menu_item(old_name)
            add_menu_item(updated_item[0], updated_item[1], updated_item[2],
                          updated_item[3], updated_item[4])
            # Refresh the menu items from database
            self.menu_items = get_menu_items()
            self.refresh_table()

    def delete_item(self, row):
        logger.info(f'Excluindo item na linha: {row}')
        name = self.menu_items[row][0]
        delete_menu_item(name)
        del self.menu_items[row]
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.menu_items))
        self.table.clearContents()  # Limpa widgets antigos das células
        self.table.verticalHeader().setMinimumSectionSize(40)
        for row, item in enumerate(self.menu_items):
            name, price, category, description, additions = item
            item_nome = QTableWidgetItem(name)
            item_nome.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 0, item_nome)
            item_cat = QTableWidgetItem(category)
            item_cat.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 1, item_cat)
            item_preco = QTableWidgetItem(f"R$ {price:.2f}")
            item_preco.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 2, item_preco)

            # Centraliza os botões nas células
            btn_edit = QPushButton("Editar")
            btn_edit.setMinimumWidth(70)
            btn_edit.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
            btn_edit.clicked.connect(lambda checked, r=row: self.edit_item(r))
            cell_edit = QWidget()
            layout_edit = QHBoxLayout(cell_edit)
            layout_edit.addWidget(btn_edit)
            layout_edit.setAlignment(Qt.AlignCenter)
            layout_edit.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 3, cell_edit)

            btn_delete = QPushButton("Excluir")
            btn_delete.setMinimumWidth(70)
            btn_delete.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn_delete.clicked.connect(
                lambda checked, r=row: self.delete_item(r))
            cell_delete = QWidget()
            layout_delete = QHBoxLayout(cell_delete)
            layout_delete.addWidget(btn_delete)
            layout_delete.setAlignment(Qt.AlignCenter)
            layout_delete.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 4, cell_delete)

            # Ajusta a altura da linha para melhor encaixe dos botões
            self.table.setRowHeight(row, 40)
        # Removido self.table.resizeColumnsToContents() para não sobrescrever altura

    def add_category(self):
        name = self.category_new_input.text().strip()
        logger.info(f'Tentando adicionar categoria (edit): {name}')
        if name and name not in self.categories:
            add_category(name)
            self.categories.append(name)
            self.categories_list.addItem(name)
            self.category_new_input.clear()

    def add_addition(self):
        name = self.addition_new_input.text().strip()
        price = self.addition_price_input.value()
        logger.info(
            f'Tentando adicionar adicional (edit): {name} - R$ {price:.2f}')
        if name and name not in self.additions:
            # Aqui você pode adaptar para salvar o valor do adicional no banco, se necessário
            add_addition(name)  # Adapte para aceitar preço se necessário
            self.additions.append(name)
            self.addition_new_input.clear()
            self.addition_price_input.setValue(0)

    def open_category_additions(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
            return
        cat = self.categories[idx]
        dialog = CategoryAdditionsDialog(
            cat, self.additions, self.category_additions.get(cat, []), self)
        if dialog.exec():
            selected = dialog.get_selected_additions()
            self.category_additions[cat] = selected
            set_category_additions(cat, selected)

    def edit_category(self, idx):
        old_name = self.categories[idx]
        new_name, ok = QInputDialog.getText(
            self, "Editar Categoria", "Novo nome:", text=old_name)
        if ok and new_name and new_name != old_name:
            self.categories[idx] = new_name
            delete_category(old_name)
            add_category(new_name)
            # Atualiza o item na lista
            self.categories_list.item(idx).setText(new_name)

    def delete_category(self, idx):
        name = self.categories[idx]
        delete_category(name)
        del self.categories[idx]
        # Remove o item da lista
        self.categories_list.takeItem(idx)

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

    def update_addition_buttons(self):
        """Atualiza os índices dos botões de adicionais após exclusão."""
        for i in range(self.additions_btn_layout.count()):
            h_layout = self.additions_btn_layout.itemAt(i).layout()
            if h_layout and h_layout.count() >= 3:
                edit_btn = h_layout.itemAt(i).widget()
                del_btn = h_layout.itemAt(2).widget()
                if edit_btn and del_btn:
                    edit_btn.clicked.disconnect()
                    del_btn.clicked.disconnect()
                    edit_btn.clicked.connect(partial(self.edit_addition, i))
                    del_btn.clicked.connect(partial(self.delete_addition, i))

    def show_category_context_menu(self, position):
        """Mostra menu de contexto para a lista de categorias."""
        item = self.categories_list.itemAt(position)
        if item is None:
            return

        idx = self.categories_list.row(item)
        context_menu = QMenu(self)

        edit_action = context_menu.addAction("Editar")
        edit_action.triggered.connect(lambda: self.edit_category(idx))

        delete_action = context_menu.addAction("Excluir")
        delete_action.triggered.connect(lambda: self.delete_category(idx))

        context_menu.exec(self.categories_list.mapToGlobal(position))


class MenuEditWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('MenuEditWindow inicializada')
        self.setWindowTitle("Edição de Cardápio")
        self.menu_items = get_menu_items()
        self.categories = get_categories()
        self.additions = get_additions()
        self.category_additions = get_category_additions()

        central_widget = QWidget()
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tab_items = QWidget()
        self.tab_categories = QWidget()
        self.tab_additions = QWidget()
        self.tabs.addTab(self.tab_items, "Itens")
        self.tabs.addTab(self.tab_categories, "Categorias")
        self.tabs.addTab(self.tab_additions, "Adicionais")
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.resize(800, 500)
        self.setup_items_tab()
        self.setup_categories_tab()
        self.setup_additions_tab()

    def setup_items_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Nome", "Categoria", "Preço", "Editar", "Excluir"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.refresh_table()
        layout.addWidget(self.table)
        # Removido layout.addStretch() para a tabela ocupar toda a altura
        self.tab_items.setLayout(layout)

    def setup_categories_tab(self):
        # Limpa layout antigo, se existir
        if hasattr(self, 'tab_categories') and self.tab_categories.layout() is not None:
            self.clear_layout(self.tab_categories.layout())
        layout = QVBoxLayout()
        row_layout = QHBoxLayout()
        btn_addition = QPushButton("Adicionais")
        btn_addition.clicked.connect(self.open_category_additions)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self.edit_selected_category)
        btn_delete = QPushButton("Excluir")
        btn_delete.clicked.connect(self.delete_selected_category)
        row_layout.addWidget(btn_addition)
        row_layout.addWidget(btn_edit)
        row_layout.addWidget(btn_delete)
        layout.addLayout(row_layout)

        # Lista de categorias com menu de contexto
        self.categories_list = QListWidget()
        self.categories_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.categories_list.customContextMenuRequested.connect(
            self.show_category_context_menu)
        for cat in self.categories:
            self.categories_list.addItem(cat)
        layout.addWidget(self.categories_list)
        self.tab_categories.setLayout(layout)

    def edit_selected_category(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(
                self, "Erro", "Selecione uma categoria para editar.")
            return
        self.edit_category(idx)

    def delete_selected_category(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(
                self, "Erro", "Selecione uma categoria para excluir.")
            return
        self.delete_category(idx)

    def setup_additions_tab(self):
        # Limpa layout antigo, se existir
        if hasattr(self, 'tab_additions') and self.tab_additions.layout() is not None:
            self.clear_layout(self.tab_additions.layout())
        layout = QVBoxLayout()
        row_layout = QHBoxLayout()
        self.addition_new_input = QLineEdit()
        self.addition_new_input.setPlaceholderText("Novo adicional")
        self.addition_price_input = QDoubleSpinBox()
        self.addition_price_input.setPrefix("R$ ")
        self.addition_price_input.setMaximum(9999)
        self.addition_price_input.setDecimals(2)
        add_button = QPushButton("Adicionar Adicional")
        add_button.clicked.connect(self.add_addition)
        row_layout.addWidget(self.addition_new_input)
        row_layout.addWidget(add_button)
        layout.addLayout(row_layout)
        # Adiciona botões de editar e excluir para cada adicional
        self.additions_btn_layout = QVBoxLayout()
        for i, add in enumerate(self.additions):
            h = QHBoxLayout()
            edit_btn = QPushButton("Editar")
            edit_btn.clicked.connect(partial(self.edit_addition, i))
            del_btn = QPushButton("Excluir")
            del_btn.clicked.connect(partial(self.delete_addition, i))
            h.addWidget(QLabel(add))
            h.addWidget(edit_btn)
            h.addWidget(del_btn)
            self.additions_btn_layout.addLayout(h)
        layout.addLayout(self.additions_btn_layout)
        self.tab_additions.setLayout(layout)

    def edit_item(self, row):
        logger.info(f'Editando item na linha: {row}')
        item = self.menu_items[row]
        old_name = item[0]  # Store the old name to delete the old record
        dialog = MenuEditDialogItem(
            item, self.categories, self.additions, self)
        if dialog.exec():
            # Get the updated item data
            updated_item = dialog.get_item()
            # Delete the old item and add the new one
            delete_menu_item(old_name)
            add_menu_item(updated_item[0], updated_item[1], updated_item[2],
                          updated_item[3], updated_item[4])
            # Refresh the menu items from database
            self.menu_items = get_menu_items()
            self.refresh_table()

    def delete_item(self, row):
        logger.info(f'Excluindo item na linha: {row}')
        name = self.menu_items[row][0]
        delete_menu_item(name)
        del self.menu_items[row]
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.menu_items))
        self.table.clearContents()  # Limpa widgets antigos das células
        self.table.verticalHeader().setMinimumSectionSize(40)
        for row, item in enumerate(self.menu_items):
            name, price, category, description, additions = item
            item_nome = QTableWidgetItem(name)
            item_nome.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 0, item_nome)
            item_cat = QTableWidgetItem(category)
            item_cat.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 1, item_cat)
            item_preco = QTableWidgetItem(f"R$ {price:.2f}")
            item_preco.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 2, item_preco)

            # Centraliza os botões nas células
            btn_edit = QPushButton("Editar")
            btn_edit.setMinimumWidth(70)
            btn_edit.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
            btn_edit.clicked.connect(lambda checked, r=row: self.edit_item(r))
            cell_edit = QWidget()
            layout_edit = QHBoxLayout(cell_edit)
            layout_edit.addWidget(btn_edit)
            layout_edit.setAlignment(Qt.AlignCenter)
            layout_edit.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 3, cell_edit)

            btn_delete = QPushButton("Excluir")
            btn_delete.setMinimumWidth(70)
            btn_delete.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn_delete.clicked.connect(
                lambda checked, r=row: self.delete_item(r))
            cell_delete = QWidget()
            layout_delete = QHBoxLayout(cell_delete)
            layout_delete.addWidget(btn_delete)
            layout_delete.setAlignment(Qt.AlignCenter)
            layout_delete.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 4, cell_delete)

            # Ajusta a altura da linha para melhor encaixe dos botões
            self.table.setRowHeight(row, 40)
        # Removido self.table.resizeColumnsToContents() para não sobrescrever altura

    def add_category(self):
        name = self.category_new_input.text().strip()
        logger.info(f'Tentando adicionar categoria (edit): {name}')
        if name and name not in self.categories:
            add_category(name)
            self.categories.append(name)
            self.categories_list.addItem(name)
            self.category_new_input.clear()

    def add_addition(self):
        name = self.addition_new_input.text().strip()
        price = self.addition_price_input.value()
        logger.info(
            f'Tentando adicionar adicional (edit): {name} - R$ {price:.2f}')
        if name and name not in self.additions:
            # Aqui você pode adaptar para salvar o valor do adicional no banco, se necessário
            add_addition(name)  # Adapte para aceitar preço se necessário
            self.additions.append(name)
            self.addition_new_input.clear()
            self.addition_price_input.setValue(0)

    def edit_addition(self, idx):
        old_name = self.additions[idx]
        new_name, ok = QInputDialog.getText(
            self, "Editar Adicional", "Novo nome:", text=old_name)
        if ok and new_name and new_name != old_name:
            self.additions[idx] = new_name
            delete_addition(old_name)
            add_addition(new_name)
            # Atualiza a interface instantaneamente
            layout_item = self.additions_btn_layout.itemAt(idx)
            if layout_item:
                label = layout_item.layout().itemAt(0).widget()
                if label:
                    label.setText(new_name)
            self.update_addition_buttons()

    def delete_addition(self, idx):
        name = self.additions[idx]
        delete_addition(name)
        del self.additions[idx]
        # Remove a linha correspondente da interface imediatamente
        layout_item = self.additions_btn_layout.itemAt(idx)
        if layout_item:
            self.clear_layout(layout_item.layout())
            self.additions_btn_layout.removeItem(layout_item)
        # Atualiza índices dos botões restantes
        self.update_addition_buttons()

    def open_category_additions(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
            return
        cat = self.categories[idx]
        dialog = CategoryAdditionsDialog(
            cat, self.additions, self.category_additions.get(cat, []), self)
        if dialog.exec():
            selected = dialog.get_selected_additions()
            self.category_additions[cat] = selected
            set_category_additions(cat, selected)

    def edit_category(self, idx):
        old_name = self.categories[idx]
        new_name, ok = QInputDialog.getText(
            self, "Editar Categoria", "Novo nome:", text=old_name)
        if ok and new_name and new_name != old_name:
            self.categories[idx] = new_name
            delete_category(old_name)
            add_category(new_name)
            # Atualiza o item na lista
            self.categories_list.item(idx).setText(new_name)

    def delete_category(self, idx):
        name = self.categories[idx]
        delete_category(name)
        del self.categories[idx]
        # Remove o item da lista
        self.categories_list.takeItem(idx)

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

    def update_addition_buttons(self):
        """Atualiza os índices dos botões de adicionais após exclusão."""
        for i in range(self.additions_btn_layout.count()):
            h_layout = self.additions_btn_layout.itemAt(i).layout()
            if h_layout and h_layout.count() >= 3:
                edit_btn = h_layout.itemAt(i).widget()
                del_btn = h_layout.itemAt(2).widget()
                if edit_btn and del_btn:
                    edit_btn.clicked.disconnect()
                    del_btn.clicked.disconnect()
                    edit_btn.clicked.connect(partial(self.edit_addition, i))
                    del_btn.clicked.connect(partial(self.delete_addition, i))

    def show_category_context_menu(self, position):
        """Mostra menu de contexto para a lista de categorias."""
        item = self.categories_list.itemAt(position)
        if item is None:
            return

        idx = self.categories_list.row(item)
        context_menu = QMenu(self)

        edit_action = context_menu.addAction("Editar")
        edit_action.triggered.connect(lambda: self.edit_category(idx))

        delete_action = context_menu.addAction("Excluir")
        delete_action.triggered.connect(lambda: self.delete_category(idx))

        context_menu.exec(self.categories_list.mapToGlobal(position))


class CategoryAdditionsDialog(QDialog):
    def __init__(self, category, all_additions, selected_additions, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Adicionais para {category}")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Título
        title_label = QLabel(
            f"Selecione os adicionais para a categoria '{category}':")
        layout.addWidget(title_label)

        # Lista de checkboxes para adicionais
        self.addition_checks = []
        for addition in all_additions:
            checkbox = QCheckBox(addition)
            if addition in selected_additions:
                checkbox.setChecked(True)
            self.addition_checks.append(checkbox)
            layout.addWidget(checkbox)

        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_additions(self):
        """Retorna lista dos adicionais selecionados."""
        selected = []
        for checkbox in self.addition_checks:
            if checkbox.isChecked():
                selected.append(checkbox.text())
        return selected


class MenuEditDialogItem(QDialog):
    def __init__(self, item, categories, additions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Item do Cardápio")
        self.setModal(True)
        self.resize(400, 300)

        # Dados do item
        self.name, self.price, self.category, self.description, self.item_additions = item

        layout = QVBoxLayout()

        # Campo Nome
        layout.addWidget(QLabel("Nome:"))
        self.name_input = QLineEdit(self.name)
        layout.addWidget(self.name_input)

        # Campo Preço
        layout.addWidget(QLabel("Preço:"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("R$ ")
        self.price_input.setMaximum(9999)
        self.price_input.setDecimals(2)
        self.price_input.setValue(self.price)
        layout.addWidget(self.price_input)

        # Campo Categoria
        layout.addWidget(QLabel("Categoria:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)
        if self.category in categories:
            self.category_combo.setCurrentText(self.category)
        layout.addWidget(self.category_combo)

        # Campo Descrição
        layout.addWidget(QLabel("Descrição:"))
        self.description_input = QLineEdit(self.description)
        layout.addWidget(self.description_input)

        # Adicionais
        layout.addWidget(QLabel("Adicionais:"))
        self.additions_input = QLineEdit(self.item_additions)
        layout.addWidget(self.additions_input)

        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_item(self):
        """Retorna os dados do item editado."""
        return (
            self.name_input.text().strip(),
            self.price_input.value(),
            self.category_combo.currentText(),
            self.description_input.text().strip(),
            self.additions_input.text().strip()
        )
