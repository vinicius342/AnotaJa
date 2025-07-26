"""
Diálogo de configurações do sistema.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFrame, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPushButton, QSpinBox,
                               QTabWidget, QVBoxLayout, QWidget)

from database.db import get_system_setting, set_system_setting
from utils.log_utils import get_logger
from utils.printer import Printer

LOGGER = get_logger(__name__)


class SettingsDialog(QDialog):
    """Diálogo de configurações do sistema."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle("Configurações do Sistema")
        self.setWindowFlags(Qt.WindowType.Dialog |
                            Qt.WindowType.WindowSystemMenuHint |
                            Qt.WindowType.WindowTitleHint |
                            Qt.WindowType.WindowCloseButtonHint)
        self.resize(600, 500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Título
        title_label = QLabel("Configurações do Sistema")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Tabs para organizar as configurações
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Aba Empresa
        self.setup_company_tab()

        # Aba Impressão
        self.setup_printer_tab()

        # Aba Sistema
        self.setup_system_tab()

        # Botões
        self.setup_buttons(layout)

    def setup_company_tab(self):
        """Configura a aba de informações da empresa."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Grupo: Informações da Empresa
        company_group = QGroupBox("Informações da Empresa")
        company_layout = QVBoxLayout()
        company_group.setLayout(company_layout)

        # Nome da empresa
        company_layout.addWidget(QLabel("Nome da Empresa:"))
        self.company_name_edit = QLineEdit()
        self.company_name_edit.setPlaceholderText(
            "Digite o nome da sua empresa")
        company_layout.addWidget(self.company_name_edit)

        # CNPJ/CPF (opcional)
        company_layout.addWidget(QLabel("CNPJ/CPF (opcional):"))
        self.company_document_edit = QLineEdit()
        self.company_document_edit.setPlaceholderText(
            "Ex: 00.000.000/0000-00")
        company_layout.addWidget(self.company_document_edit)

        # Endereço (opcional)
        company_layout.addWidget(QLabel("Endereço (opcional):"))
        self.company_address_edit = QLineEdit()
        self.company_address_edit.setPlaceholderText(
            "Rua, número, bairro, cidade")
        company_layout.addWidget(self.company_address_edit)

        # Telefone (opcional)
        company_layout.addWidget(QLabel("Telefone (opcional):"))
        self.company_phone_edit = QLineEdit()
        self.company_phone_edit.setPlaceholderText("(xx) xxxxx-xxxx")
        company_layout.addWidget(self.company_phone_edit)

        layout.addWidget(company_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Empresa")

    def setup_printer_tab(self):
        """Configura a aba de configurações de impressão."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Grupo: Seleção de Impressora
        printer_group = QGroupBox("Impressora")
        printer_layout = QVBoxLayout()
        printer_group.setLayout(printer_layout)

        printer_layout.addWidget(QLabel("Impressora Padrão:"))
        self.printer_combo = QComboBox()
        self.load_printers()
        printer_layout.addWidget(self.printer_combo)

        # Botão para atualizar lista de impressoras
        refresh_btn = QPushButton("Atualizar Lista")
        refresh_btn.clicked.connect(self.load_printers)
        printer_layout.addWidget(refresh_btn)

        # Botão para detectar impressoras térmicas
        detect_btn = QPushButton("Detectar Impressoras Térmicas")
        detect_btn.clicked.connect(self.detect_thermal_printers)
        detect_btn.setToolTip("Procura por impressoras térmicas conectadas")
        printer_layout.addWidget(detect_btn)

        layout.addWidget(printer_group)

        # Grupo: Configurações de Impressão
        print_settings_group = QGroupBox("Configurações de Impressão")
        print_settings_layout = QVBoxLayout()
        print_settings_group.setLayout(print_settings_layout)

        # Margem da impressão
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Margem (mm):"))
        self.margin_spinbox = QSpinBox()
        self.margin_spinbox.setMinimum(0)
        self.margin_spinbox.setMaximum(50)
        self.margin_spinbox.setValue(5)
        self.margin_spinbox.setSuffix(" mm")
        margin_layout.addWidget(self.margin_spinbox)
        margin_layout.addStretch()
        print_settings_layout.addLayout(margin_layout)

        # Configurações de fonte
        font_layout = QHBoxLayout()
        # Tipo de fonte (A/B)
        font_type_label = QLabel("Tipo de Fonte:")
        self.font_type_combo = QComboBox()
        self.font_type_combo.addItems(["A (12x24)", "B (9x17)"])
        font_layout.addWidget(font_type_label)
        font_layout.addWidget(self.font_type_combo)

        # Tamanho ESC/POS (normal, duplo, triplo)
        escpos_size_label = QLabel("Tamanho ESC/POS:")
        self.escpos_size_combo = QComboBox()
        self.escpos_size_combo.addItems(["normal", "duplo", "triplo"])
        font_layout.addWidget(escpos_size_label)
        font_layout.addWidget(self.escpos_size_combo)

        # Negrito
        self.bold_checkbox = QCheckBox("Negrito (ESC/POS)")
        font_layout.addWidget(self.bold_checkbox)

        # Adiciona o layout de fonte ao layout principal da aba
        print_settings_layout.addLayout(font_layout)

        # Configuração de tamanho de impressão
        size_layout = QHBoxLayout()
        size_label = QLabel("Tamanho de Impressão:")
        self.print_size_combo = QComboBox()
        self.print_size_combo.addItems([
            "Normal",
            "Duplo Altura",
            "Duplo Largura",
            "Duplo",
            "Intermediário Altura",
            "Intermediário Largura",
            "Intermediário",
            "Triplo"
        ])
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.print_size_combo)
        print_settings_layout.addLayout(size_layout)

        # Imprimir cabeçalho da empresa
        self.print_header_checkbox = QCheckBox(
            "Incluir cabeçalho da empresa nos pedidos")
        self.print_header_checkbox.setChecked(True)
        print_settings_layout.addWidget(self.print_header_checkbox)

        layout.addWidget(print_settings_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Impressão")

    def setup_system_tab(self):
        """Configura a aba de configurações do sistema."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Grupo: Interface
        interface_group = QGroupBox("Interface")
        interface_layout = QVBoxLayout()
        interface_group.setLayout(interface_layout)

        # Confirmar exclusões
        self.confirm_delete_checkbox = QCheckBox(
            "Confirmar antes de excluir itens")
        self.confirm_delete_checkbox.setChecked(True)
        interface_layout.addWidget(self.confirm_delete_checkbox)

        # Auto salvar
        self.auto_save_checkbox = QCheckBox(
            "Salvar automaticamente as alterações")
        self.auto_save_checkbox.setChecked(True)
        interface_layout.addWidget(self.auto_save_checkbox)

        # Som de notificação
        self.notification_sound_checkbox = QCheckBox(
            "Tocar som ao finalizar pedido")
        self.notification_sound_checkbox.setChecked(False)
        interface_layout.addWidget(self.notification_sound_checkbox)

        layout.addWidget(interface_group)

        # Grupo: Dados
        data_group = QGroupBox("Dados")
        data_layout = QVBoxLayout()
        data_group.setLayout(data_layout)

        # Backup automático
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(QLabel("Backup automático:"))
        self.backup_combo = QComboBox()
        self.backup_combo.addItems([
            "Desabilitado", "Diário", "Semanal", "Mensal"
        ])
        backup_layout.addWidget(self.backup_combo)
        backup_layout.addStretch()
        data_layout.addLayout(backup_layout)

        # Manter histórico por
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Manter histórico por:"))
        self.history_spinbox = QSpinBox()
        self.history_spinbox.setMinimum(1)
        self.history_spinbox.setMaximum(120)
        self.history_spinbox.setValue(12)
        self.history_spinbox.setSuffix(" meses")
        history_layout.addWidget(self.history_spinbox)
        history_layout.addStretch()
        data_layout.addLayout(history_layout)

        layout.addWidget(data_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Sistema")

    def setup_buttons(self, layout):
        """Configura os botões do diálogo."""
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.apply_settings)

        layout.addWidget(buttons)

    def load_printers(self):
        """Carrega a lista de impressoras disponíveis."""
        try:
            self.printer_combo.clear()
            printers = Printer.list_printers()
            current_printer = get_system_setting('default_printer', '')

            for printer in printers:
                self.printer_combo.addItem(printer.name)

            # Seleciona a impressora atual
            if current_printer:
                index = self.printer_combo.findText(current_printer)
                if index >= 0:
                    self.printer_combo.setCurrentIndex(index)

        except Exception as e:
            LOGGER.error(f"Erro ao carregar impressoras: {e}")
            QMessageBox.warning(
                self, "Erro", f"Erro ao carregar impressoras: {str(e)}")

    def detect_thermal_printers(self):
        """Detecta impressoras térmicas conectadas via USB."""
        try:
            QMessageBox.information(
                self, "Detectando Impressoras",
                "Procurando por impressoras térmicas conectadas...")

            # Recarrega a lista de impressoras
            self.load_printers()

            # Verifica se há impressoras térmicas na lista
            thermal_found = False
            thermal_keywords = [
                'elgin', 'i9', 'i7', 'i8', 'thermal', 'termica',
                'pos', 'bematech', 'epson', 'tm-'
            ]

            for i in range(self.printer_combo.count()):
                printer_name = self.printer_combo.itemText(i).lower()
                if any(
                    keyword in printer_name for keyword in thermal_keywords
                ):
                    thermal_found = True
                    self.printer_combo.setCurrentIndex(i)
                    QMessageBox.information(
                        self,
                        "Impressora Térmica Encontrada",
                        (
                            f"Impressora térmica detectada: "
                            f"{self.printer_combo.itemText(i)}\n"
                            "Esta impressora foi selecionada automaticamente."
                        )
                    )
                    return

            if not thermal_found:
                reply = QMessageBox.question(
                    self,
                    "Nenhuma Impressora Térmica Detectada",
                    (
                        "Não foi possível detectar impressoras térmicas "
                        "automaticamente.\n\n"
                        "Você gostaria de configurar manualmente uma "
                        "impressora térmica?\nIsso adicionará opções comuns "
                        "de impressoras térmicas à lista."
                    ),
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.add_thermal_printer_options()

        except Exception as e:
            LOGGER.error(f"Erro ao detectar impressoras térmicas: {e}")
            QMessageBox.warning(
                self, "Erro", f"Erro ao detectar impressoras: {str(e)}")

    def add_thermal_printer_options(self):
        """Adiciona opções de impressoras térmicas comuns."""
        thermal_printers = [
            "Elgin i9 (USB)",
            "Elgin i7 (USB)",
            "Elgin i8 (USB)",
            "Bematech MP-4200 TH",
            "Epson TM-T20",
            "Impressora Térmica (USB)",
            "Salvar em Arquivo TXT"
        ]

        current_items = [self.printer_combo.itemText(i)
                         for i in range(self.printer_combo.count())]

        added_count = 0
        for thermal in thermal_printers:
            if thermal not in current_items:
                self.printer_combo.addItem(thermal)
                added_count += 1

        if added_count > 0:
            QMessageBox.information(
                self,
                "Impressoras Adicionadas",
                (
                    f"{added_count} opções de impressoras térmicas foram "
                    f"adicionadas à lista.\nSelecione a que corresponde ao "
                    f"seu equipamento."
                )
            )
        else:
            QMessageBox.information(
                self,
                "Impressoras Térmicas",
                "As opções de impressoras térmicas já estão disponíveis "
                "na lista."
            )

    def load_settings(self):
        """Carrega as configurações salvas."""
        try:
            # Configurações da empresa
            self.company_name_edit.setText(
                get_system_setting('company_name', ''))
            self.company_document_edit.setText(
                get_system_setting('company_document', ''))
            self.company_address_edit.setText(
                get_system_setting('company_address', ''))
            self.company_phone_edit.setText(
                get_system_setting('company_phone', ''))

            # Configurações de impressão
            margin = int(get_system_setting('print_margin', '5'))
            self.margin_spinbox.setValue(margin)

            print_header = get_system_setting('print_header', 'true') == 'true'
            self.print_header_checkbox.setChecked(print_header)

            print_bold = get_system_setting('print_bold', 'false') == 'true'
            self.bold_checkbox.setChecked(print_bold)

            # Configurações do sistema
            confirm_delete = get_system_setting(
                'confirm_delete', 'true') == 'true'
            self.confirm_delete_checkbox.setChecked(confirm_delete)

            auto_save = get_system_setting('auto_save', 'true') == 'true'
            self.auto_save_checkbox.setChecked(auto_save)

            notification_sound = get_system_setting(
                'notification_sound', 'false') == 'true'
            self.notification_sound_checkbox.setChecked(notification_sound)

            backup_frequency = get_system_setting('backup_frequency', 'Mensal')
            index = self.backup_combo.findText(backup_frequency)
            if index >= 0:
                self.backup_combo.setCurrentIndex(index)

            history_months = int(get_system_setting('history_months', '12'))
            self.history_spinbox.setValue(history_months)

            # Tamanho de impressão
            self.print_size_commands = {
                "Normal": b'\x1d!\x00',
                "Duplo Altura": b'\x1d!\x01',
                "Duplo Largura": b'\x1d!\x10',
                "Duplo": b'\x1d!\x11',
                "Intermediário Altura": b'\x1d!\x02',
                "Intermediário Largura": b'\x1d!\x20',
                "Intermediário": b'\x1d!\x21',
                "Triplo": b'\x1d!\x12'
            }

            selected_size = get_system_setting('print_size', 'Normal')
            index = self.print_size_combo.findText(selected_size)
            if index >= 0:
                self.print_size_combo.setCurrentIndex(index)

        except Exception as e:
            LOGGER.error(f"Erro ao carregar configurações: {e}")

    def apply_settings(self):
        """Aplica as configurações sem fechar o diálogo."""
        self.save_settings()

    def save_and_close(self):
        """(Desativado) Salva as configurações e fecha o diálogo."""
        # Função desativada: OK não salva mais configurações
        self.accept()

    def save_settings(self):
        """Salva todas as configurações."""
        try:
            # Configurações da empresa
            set_system_setting('company_name',
                               self.company_name_edit.text().strip())
            set_system_setting('company_document',
                               self.company_document_edit.text().strip())
            set_system_setting('company_address',
                               self.company_address_edit.text().strip())
            set_system_setting('company_phone',
                               self.company_phone_edit.text().strip())

            # Configurações de impressão
            if self.printer_combo.currentText():
                set_system_setting('default_printer',
                                   self.printer_combo.currentText())

            set_system_setting('print_margin',
                               str(self.margin_spinbox.value()))

            print_header_value = ('true'
                                  if self.print_header_checkbox.isChecked()
                                  else 'false')
            set_system_setting('print_header', print_header_value)

            # Configuração de negrito
            print_bold_value = (
                'true' if self.bold_checkbox.isChecked() else 'false')
            set_system_setting('print_bold', print_bold_value)

            # Configurações do sistema
            confirm_delete_value = ('true'
                                    if self.confirm_delete_checkbox.isChecked()
                                    else 'false')
            set_system_setting('confirm_delete', confirm_delete_value)

            auto_save_value = ('true'
                               if self.auto_save_checkbox.isChecked()
                               else 'false')
            set_system_setting('auto_save', auto_save_value)

            notification_sound_checked = (
                self.notification_sound_checkbox.isChecked())
            notification_sound_value = (
                'true' if notification_sound_checked else 'false')
            set_system_setting('notification_sound', notification_sound_value)
            set_system_setting('backup_frequency',
                               self.backup_combo.currentText())
            set_system_setting('history_months',
                               str(self.history_spinbox.value()))

            # Tamanho de impressão
            set_system_setting(
                'print_size', self.print_size_combo.currentText()
            )

            QMessageBox.information(
                self, "Sucesso", "Configurações salvas com sucesso!")
            LOGGER.info("Configurações do sistema salvas")
            return True

        except Exception as e:
            LOGGER.error(f"Erro ao salvar configurações: {e}")
            QMessageBox.critical(
                self, "Erro", f"Erro ao salvar configurações: {str(e)}")
            return False
