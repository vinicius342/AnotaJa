from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDoubleSpinBox, QHBoxLayout,
                               QHeaderView, QInputDialog, QLabel, QLineEdit,
                               QListWidget, QMenu, QMessageBox, QPushButton,
                               QSizePolicy, QTableWidget, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

from database.db import (add_addition, add_category, add_menu_item,
                         delete_addition, delete_category, delete_menu_item,
                         get_all_additions_with_id, get_categories,
                         get_category_additions, get_category_id,
                         get_menu_items, set_category_additions,
                         update_addition, update_category)
from utils.log_utils import get_logger

from .dialogs import (CategoryAdditionsDialog, EditCategoryDialog,
                      MenuEditDialogItem)
from .dialogs_edit_addition import EditAdditionDialog

logger = get_logger(__name__)


class MenuEditWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('MenuEditWindow inicializada')
        self.setWindowTitle("Edição de Cardápio")
        self.resize(800, 500)
        # Centraliza a janela em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        # --- FIX: Initialize data before setting up tabs ---
        self.menu_items = get_menu_items()
        self.categories = get_categories()
        self.additions = get_all_additions_with_id()
        self.category_additions = get_category_additions()
        # ---
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
        self.tab_items.setLayout(layout)

    def setup_categories_tab(self):
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
        if hasattr(self, 'tab_additions') and self.tab_additions.layout() is not None:
            self.clear_layout(self.tab_additions.layout())
        layout = QVBoxLayout()
        # Campo de pesquisa
        search_layout = QHBoxLayout()
        self.addition_search_input = QLineEdit()
        self.addition_search_input.setPlaceholderText(
            "Pesquisar complemento pelo nome...")
        self.addition_search_input.textChanged.connect(
            self.refresh_additions_list)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.addition_search_input)
        layout.addLayout(search_layout)
        # Layout apenas para a lista de adicionais
        self.additions_btn_layout = QVBoxLayout()
        layout.addLayout(self.additions_btn_layout)
        self.tab_additions.setLayout(layout)
        self.refresh_additions_list()

    def refresh_additions_list(self):
        # Limpa a lista de botões e labels
        while self.additions_btn_layout.count():
            item = self.additions_btn_layout.takeAt(0)
            if item.layout():
                self.clear_layout(item.layout())
        # Filtra adicionais pelo campo de busca
        search = self.addition_search_input.text().strip().lower() if hasattr(self,
                                                                              'addition_search_input') else ''
        filtered = [a for a in self.additions if search in a[1].lower()]
        for i, add in enumerate(filtered):
            item_text = f"{add[1]}   R$ {add[2]:.2f}"
            h = QHBoxLayout()
            edit_btn = QPushButton("Editar")
            edit_btn.clicked.connect(
                partial(self.edit_addition, self.additions.index(add)))
            del_btn = QPushButton("Excluir")
            del_btn.clicked.connect(
                partial(self.delete_addition, self.additions.index(add)))
            label = QLabel(item_text)
            h.addWidget(label)
            h.addWidget(edit_btn)
            h.addWidget(del_btn)
            self.additions_btn_layout.addLayout(h)

    def edit_item(self, row):
        logger.info(f'🔧 MENU_EDIT: Editando item na linha: {row}')
        item = self.menu_items[row]
        item_id = item[0]

        # Log estado ANTES de abrir o diálogo
        from database.db import (
            get_all_additions_for_item_with_mandatory_info, get_category_id)
        # categoria é o 4º campo (índice 3)
        category_id = get_category_id(item[3])
        before_edit = get_all_additions_for_item_with_mandatory_info(
            item_id, category_id)
        mandatory_before_edit = [aid for aid, name, price,
                                 is_mandatory, source in before_edit if is_mandatory]
        logger.info(
            f'🔧 MENU_EDIT: ANTES de abrir diálogo - Item {item_id} tem {len(mandatory_before_edit)} obrigatórios: {mandatory_before_edit}')

        dialog = MenuEditDialogItem(
            item[1:], self.categories, self.additions, None, item_id)
        dialog.setWindowFlags(Qt.Window)

        if dialog.exec():
            logger.info(
                f'🔧 MENU_EDIT: Usuário clicou OK no diálogo principal de edição')

            # Log estado DEPOIS do diálogo mas ANTES da atualização básica
            after_dialog = get_all_additions_for_item_with_mandatory_info(
                item_id, category_id)
            mandatory_after_dialog = [
                aid for aid, name, price, is_mandatory, source in after_dialog if is_mandatory]
            logger.info(
                f'🔧 MENU_EDIT: DEPOIS do diálogo - Item {item_id} tem {len(mandatory_after_dialog)} obrigatórios: {mandatory_after_dialog}')

            updated_item = dialog.get_item()
            from database.db import update_menu_item_basic
            category_id = get_category_id(updated_item[2])
            if category_id is None:
                logger.error(f"Categoria não encontrada: {updated_item[2]}")
                return

            # Atualiza apenas os campos básicos, preservando todos os vínculos
            try:
                logger.info(
                    f"🔧 MENU_EDIT: Atualizando apenas campos básicos do item {item_id}")
                logger.info(
                    f"🔧 MENU_EDIT: Novos valores - Nome: {updated_item[0]}, Preço: {updated_item[1]}, Categoria: {updated_item[2]}, Descrição: {updated_item[3]}")

                update_menu_item_basic(item_id, updated_item[0], updated_item[1],
                                       category_id, updated_item[3])

                # Log estado FINAL depois da atualização básica
                final_state = get_all_additions_for_item_with_mandatory_info(
                    item_id, category_id)
                mandatory_final = [
                    aid for aid, name, price, is_mandatory, source in final_state if is_mandatory]
                logger.info(
                    f'🔧 MENU_EDIT: ESTADO FINAL - Item {item_id} tem {len(mandatory_final)} obrigatórios: {mandatory_final}')

                logger.info(
                    "🔧 MENU_EDIT: Campos básicos atualizados com sucesso - vínculos preservados")
            except ValueError as e:
                QMessageBox.warning(self, "Erro ao editar item", str(e))
                return
        else:
            logger.info(
                f'🔧 MENU_EDIT: Usuário cancelou o diálogo principal de edição')

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
        self.table.clearContents()
        self.table.verticalHeader().setMinimumSectionSize(40)
        for row, item in enumerate(self.menu_items):
            # Solução robusta: validação do tamanho e log de erro
            if len(item) < 6:
                logger.error(f"Item do menu com campos insuficientes: {item}")
                continue
            _, name, price, category, description, additions = item[:6]
            item_nome = QTableWidgetItem(name)
            item_nome.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 0, item_nome)
            item_cat = QTableWidgetItem(category)
            item_cat.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 1, item_cat)
            # Conversão robusta do preço
            try:
                preco_float = float(price)
                preco_str = f"R$ {preco_float:.2f}"
            except (ValueError, TypeError):
                preco_str = str(price)
            item_preco = QTableWidgetItem(preco_str)
            item_preco.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 2, item_preco)
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
            self.table.setRowHeight(row, 40)

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
            f'Tentando adicionar complemento (edit): {name} - R$ {price:.2f}')
        if name and not any(a[1] == name for a in self.additions):
            add_addition(name, price)
            self.additions = get_all_additions_with_id()
            self.addition_new_input.clear()
            self.addition_price_input.setValue(0)
            self.refresh_additions_list()  # Só atualiza a lista

    def edit_addition(self, idx):
        addition = self.additions[idx]
        addition_id, old_name, old_price = addition
        dialog = EditAdditionDialog(old_name, old_price, self)
        if dialog.exec():
            new_name, new_price = dialog.get_data()
            if not new_name or (new_name == old_name and new_price == old_price):
                return
            try:
                update_addition(addition_id, new_name, new_price)
                self.additions = get_all_additions_with_id()
                self.refresh_additions_list()
            except ValueError as e:
                QMessageBox.warning(self, "Erro", str(e))

    def delete_addition(self, idx):
        addition = self.additions[idx]
        addition_id, name, price = addition
        delete_addition(addition_id)
        self.additions = get_all_additions_with_id()
        self.refresh_additions_list()  # Só atualiza a lista

    def open_category_additions(self):
        idx = self.categories_list.currentRow()
        if idx < 0 or idx >= len(self.categories):
            QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
            return
        cat = self.categories[idx]
        category_id = get_category_id(cat)
        if category_id is None:
            QMessageBox.warning(
                self, "Erro", "Categoria não encontrada no banco.")
            return
        dialog = CategoryAdditionsDialog(
            cat, self.additions, self.category_additions.get(category_id, []), None)
        dialog.setWindowFlags(Qt.Window)
        if dialog.exec():
            selected = dialog.get_selected_additions()
            self.category_additions[category_id] = selected
            set_category_additions(category_id, selected)

    def edit_category(self, idx):
        old_name = self.categories[idx]
        dialog = EditCategoryDialog(old_name)
        dialog.setWindowFlags(Qt.Window)
        if dialog.exec():
            new_name = dialog.get_new_name()
            if new_name and new_name != old_name:
                # Busca o ID da categoria para atualizar sem perder vínculos
                category_id = get_category_id(old_name)
                if category_id is None:
                    QMessageBox.warning(
                        self, "Erro", "Categoria não encontrada no banco.")
                    return
                try:
                    update_category(category_id, new_name)
                    self.categories[idx] = new_name
                    self.categories_list.item(idx).setText(new_name)
                except ValueError as e:
                    QMessageBox.warning(self, "Erro", str(e))

    def delete_category(self, idx):
        name = self.categories[idx]
        delete_category(name)
        del self.categories[idx]
        self.categories_list.takeItem(idx)

    def refresh_categories_tab(self):
        self.setup_categories_tab()

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clear_layout(child.layout())

    def update_addition_buttons(self):
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
