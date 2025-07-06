from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDoubleSpinBox, QHBoxLayout,
                               QHeaderView, QInputDialog, QLabel, QLineEdit,
                               QListWidget, QMenu, QMessageBox, QPushButton,
                               QSizePolicy, QTableWidget, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

from db import (add_addition, add_category, add_menu_item, delete_addition,
                delete_category, delete_menu_item, get_additions,
                get_categories, get_category_additions, get_menu_items,
                set_category_additions)
from dialogs import CategoryAdditionsDialog, MenuEditDialogItem
from log_utils import get_logger

logger = get_logger(__name__)


class MenuEditWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('MenuEditWindow inicializada')
        self.setWindowTitle("Edição de Cardápio")
        self.setModal(True)
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
        self.additions = get_additions()
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
        old_name = item[0]
        dialog = MenuEditDialogItem(
            item, self.categories, self.additions, self)
        if dialog.exec():
            updated_item = dialog.get_item()
            delete_menu_item(old_name)
            add_menu_item(updated_item[0], updated_item[1], updated_item[2],
                          updated_item[3], updated_item[4])
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
            f'Tentando adicionar adicional (edit): {name} - R$ {price:.2f}')
        if name and name not in self.additions:
            add_addition(name)
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
        layout_item = self.additions_btn_layout.itemAt(idx)
        if layout_item:
            self.clear_layout(layout_item.layout())
            self.additions_btn_layout.removeItem(layout_item)
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
            self.categories_list.item(idx).setText(new_name)

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
