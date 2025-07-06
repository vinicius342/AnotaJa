from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QScrollArea, QVBoxLayout, QWidget)

from db import get_additions


class CategoryAdditionsDialog(QDialog):
    def __init__(self, category, all_additions, selected_addition_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Adicionais para {category}")
        self.setModal(True)
        self.resize(400, 350)

        layout = QVBoxLayout()
        title_row = QHBoxLayout()
        title_label = QLabel(
            f"Selecione os adicionais para a categoria '{category}':")
        title_row.addWidget(title_label)
        # Checkbox Selecionar todas alinhado à direita
        self.select_all_checkbox = QCheckBox("Selecionar todas")
        self.select_all_checkbox.stateChanged.connect(
            self.toggle_all_additions)
        title_row.addStretch()
        title_row.addWidget(self.select_all_checkbox)
        layout.addLayout(title_row)

        # Área de rolagem para os adicionais
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


class MenuEditDialogItem(QDialog):
    def __init__(self, item, categories, additions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Item do Cardápio")
        self.setModal(True)
        self.resize(400, 300)
        # Centraliza o diálogo em relação ao parent, se houver
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(parent_center)
            self.move(geo.topLeft())
        self.name, self.price, self.category, self.description, self.item_additions = item
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
        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)
        if self.category in categories:
            self.category_combo.setCurrentText(self.category)
        layout.addWidget(self.category_combo)
        layout.addWidget(QLabel("Descrição:"))
        self.description_input = QLineEdit(self.description)
        layout.addWidget(self.description_input)
        layout.addWidget(QLabel("Adicionais:"))
        self.additions_input = QLineEdit(self.item_additions)
        layout.addWidget(self.additions_input)
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_item(self):
        return (
            self.name_input.text().strip(),
            self.price_input.value(),
            self.category_combo.currentText(),
            self.description_input.text().strip(),
            self.additions_input.text().strip()
        )
