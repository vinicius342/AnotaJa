from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QMenu, QMessageBox, QPushButton, QScrollArea,
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
        self.resize(450, 450)
        self.item_id = item_id

        layout = QVBoxLayout()

        # Título
        title_label = QLabel(
            f"Selecione complementos específicos para '{item_name}':")
        title_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Seção para adicionar novo complemento
        new_addition_frame = QWidget()
        new_addition_layout = QVBoxLayout()
        new_addition_frame.setLayout(new_addition_layout)

        new_addition_label = QLabel("Adicionar novo complemento:")
        new_addition_label.setStyleSheet(
            "font-weight: bold; margin-top: 10px;")
        new_addition_layout.addWidget(new_addition_label)

        # Campos para novo complemento
        new_addition_fields = QHBoxLayout()

        self.new_name_input = QLineEdit()
        self.new_name_input.setPlaceholderText("Nome do complemento")
        new_addition_fields.addWidget(self.new_name_input)

        self.new_price_input = QDoubleSpinBox()
        self.new_price_input.setPrefix("R$ ")
        self.new_price_input.setMaximum(999.99)
        self.new_price_input.setDecimals(2)
        new_addition_fields.addWidget(self.new_price_input)

        self.add_new_btn = QPushButton("Adicionar")
        self.add_new_btn.clicked.connect(self.add_new_addition)
        new_addition_fields.addWidget(self.add_new_btn)

        new_addition_layout.addLayout(new_addition_fields)
        layout.addWidget(new_addition_frame)

        # Checkbox para selecionar todas
        self.select_all_checkbox = QCheckBox("Selecionar todas")
        self.select_all_checkbox.stateChanged.connect(
            self.toggle_all_additions)
        layout.addWidget(self.select_all_checkbox)

        # Área de rolagem para os complementos
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(150)
        self.scroll_area.setMaximumHeight(250)

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

        # Carrega os complementos existentes
        self.load_additions()

    def load_additions(self):
        """Carrega todos os complementos disponíveis"""
        # Limpa o layout atual
        while self.additions_layout.count():
            child = self.additions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Carrega todos os complementos disponíveis
        all_additions = get_all_additions_with_id()

        # Carrega complementos já vinculados ao item
        try:
            selected_addition_ids = [
                add[0] for add in get_item_specific_additions(self.item_id)]
        except:
            selected_addition_ids = []

        self.addition_checks = []
        self.addition_ids = []

        for addition in all_additions:
            add_id, name, price = addition
            checkbox = QCheckBox(f"{name} - R$ {price:.2f}")
            if add_id in selected_addition_ids:
                checkbox.setChecked(True)

            self.additions_layout.addWidget(checkbox)
            self.addition_checks.append(checkbox)
            self.addition_ids.append(add_id)

    def add_new_addition(self):
        """Adiciona um novo complemento"""
        name = self.new_name_input.text().strip()
        price = self.new_price_input.value()

        if not name:
            QMessageBox.warning(
                self, "Erro", "Nome do complemento é obrigatório!")
            return

        try:
            # Adiciona o complemento no banco
            add_addition(name, price)

            # Limpa os campos
            self.new_name_input.clear()
            self.new_price_input.setValue(0.0)

            # Recarrega a lista de complementos
            self.load_additions()

            QMessageBox.information(
                self, "Sucesso", f"Complemento '{name}' adicionado com sucesso!")

        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao adicionar complemento: {str(e)}")

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
        set_item_specific_additions(self.item_id, selected_ids)


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
        from database.db import get_category_additions, get_category_id
        while self.additions_layout.count():
            child = self.additions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # Converte nome da categoria para ID
        category_id = get_category_id(selected_category)
        if category_id is None:
            self.additions_layout.addWidget(
                QLabel("Categoria não encontrada."))
            return
        category_addition_ids = get_category_additions().get(category_id, [])
        filtered_additions = [
            a for a in self.additions if a[0] in category_addition_ids]
        if filtered_additions:
            for add in filtered_additions:
                label = QLabel(f"• {add[1]} (R$ {add[2]:.2f})")
                self.additions_layout.addWidget(label)
        else:
            self.additions_layout.addWidget(
                QLabel("Nenhum complemento para esta categoria."))

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
