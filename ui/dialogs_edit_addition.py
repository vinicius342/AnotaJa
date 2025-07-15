from PySide6.QtWidgets import (QDialog, QDoubleSpinBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout)


class EditAdditionDialog(QDialog):
    def __init__(self, name, price, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Complemento")
        self.setModal(True)
        layout = QVBoxLayout()
        # Nome
        name_layout = QHBoxLayout()
        name_label = QLabel("Nome:")
        self.name_input = QLineEdit(name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        # Preço
        price_layout = QHBoxLayout()
        price_label = QLabel("Preço:")
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("R$ ")
        self.price_input.setMaximum(9999)
        self.price_input.setDecimals(2)
        self.price_input.setValue(float(price))
        price_layout.addWidget(price_label)
        price_layout.addWidget(self.price_input)
        layout.addLayout(price_layout)
        # Botões
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Salvar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_data(self):
        return self.name_input.text().strip(), self.price_input.value()
