"""
Modal para finalização de pedido com opções de entrega ou retirada.
"""

from PySide6.QtCore import QEventLoop, Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialog, QHBoxLayout, QLabel,
                               QLineEdit, QMenu, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

from database.db import (get_customer_by_phone, get_neighborhoods,
                         get_system_setting, save_order, update_customer)
from utils.log_utils import get_logger
from utils.print_settings import (format_order_for_print, get_default_printer,
                                  should_play_notification_sound)
from utils.printer import Printer

LOGGER = get_logger(__name__)


class PrintThread(QThread):
    """Thread para impressão em background usando HTML."""
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, customer_data, order_items, total_amount, parent=None):
        super().__init__(parent)
        self.customer_data = customer_data
        self.order_items = order_items
        self.total_amount = total_amount

    def run(self):
        """Executa a impressão HTML centralizada pelo Printer."""
        try:
            LOGGER.info(
                '[PRINT_THREAD] Iniciando thread de impressão (HTML via Printer)')
            printer = Printer("Sistema de Impressão")
            success = printer.print_html_order(
                self.customer_data,
                self.order_items,
                self.total_amount
            )
            if success:
                LOGGER.info(
                    '[PRINT_THREAD] Impressão HTML concluída com sucesso')
                self.finished_signal.emit("Sistema de Impressão")
            else:
                LOGGER.error('[PRINT_THREAD] Falha na impressão HTML')
                self.error_signal.emit('Erro na impressão HTML')
        except Exception as e:
            LOGGER.error(f'[PRINT_THREAD] Exceção durante impressão: {e}')
            self.error_signal.emit(f'Erro durante impressão: {str(e)}')


class FinalizeOrderDialog(QDialog):
    customer_registered = Signal(dict)

    def update_total_label(self):
        total = self.total_amount
        if self.delivery_checkbox.isChecked():
            fee = 0.0
            neighborhoods = get_neighborhoods()
            for n in neighborhoods:
                if n[0] == self.selected_neighborhood_id:
                    fee = n[2]
                    break
            total += fee
        self.total_label.setText(f"Total: R$ {total:,.2f}".replace(
            ",", "X").replace(".", ",").replace("X", "."))
    """Modal para finalização de pedido com opções de entrega/retirada."""

    def __init__(self, customer_data, order_items, total_amount, parent=None):
        super().__init__(parent)
        self.order_items = order_items
        self.total_amount = total_amount
        self.result: bool = False
        self.event_loop = None

        # Busca dados completos do cliente se necessário
        self.customer_data = self.get_full_customer_data(customer_data)

        # Dados originais do cliente para comparação
        self.original_street = self.customer_data.get('street', '') or ''
        self.original_number = self.customer_data.get('number', '') or ''
        self.original_reference = self.customer_data.get('reference', '') or ''

        self.setup_ui()
        self.setup_connections()

        # Foco inicial no checkbox Entrega após toda a UI
        self.delivery_checkbox.setFocus()

    def get_full_customer_data(self, customer_data):
        """Obtém dados completos do cliente. Adiciona log detalhado na busca por nome."""
        if customer_data.get('id'):
            return customer_data

        phone = customer_data.get('phone', '')
        if phone:
            full_data = get_customer_by_phone(phone)
            if full_data:
                return {
                    'id': full_data[0],
                    'name': full_data[1],
                    'phone': full_data[2],
                    'street': full_data[3] or '',
                    'number': full_data[4] or '',
                    'neighborhood_id': full_data[5],
                    'reference': full_data[6] or '',
                    'neighborhood_name': full_data[7] if len(full_data) > 7 else ''
                }

        # Busca por nome (debug detalhado)
        from database.db import get_customers
        name = customer_data.get('name', '').strip()
        if name:
            customers = get_customers()
            LOGGER.info(
                f"Buscando cliente por nome: '{name}' (total: {len(customers)})")
            for c in customers:
                nome_c = c.get('name', '') if isinstance(
                    c, dict) else str(c[1])
                LOGGER.info(
                    f"Comparando com: '{nome_c}' (id: {c.get('id') if isinstance(c, dict) else c[0]})")
                if nome_c.strip().lower() == name.lower():
                    LOGGER.info(
                        f"Cliente encontrado por nome: '{nome_c}' (id: {c.get('id') if isinstance(c, dict) else c[0]})")
                    if isinstance(c, dict):
                        return c
                    else:
                        return {
                            'id': c[0],
                            'name': c[1],
                            'phone': c[2],
                            'street': c[3] or '',
                            'number': c[4] or '',
                            'neighborhood_id': c[5],
                            'reference': c[6] or '',
                            'neighborhood_name': c[7] if len(c) > 7 else ''
                        }
            LOGGER.warning(f"Nenhum cliente encontrado por nome: '{name}'")

        return customer_data

    def setup_ui(self):
        """Configura a interface do modal."""
        # Estilização de foco para checkboxes
        self.setStyleSheet(self.styleSheet() + """
            QCheckBox:focus {
                outline: 2px solid #1976d2;
                background-color: #e3f2fd;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        self.setWindowTitle("Finalizar Pedido")
        flags = (Qt.WindowType.Dialog |
                 Qt.WindowType.WindowSystemMenuHint |
                 Qt.WindowType.WindowTitleHint |
                 Qt.WindowType.WindowCloseButtonHint |
                 Qt.WindowType.WindowMinMaxButtonsHint)
        self.setWindowFlags(flags)
        self.resize(450, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Título
        title_label = QLabel("Finalizar Pedido")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Cliente
        customer_name = self.customer_data.get('name', '')
        customer_phone = self.customer_data.get('phone', '')
        customer_label = QLabel(f"Cliente: {customer_name} - {customer_phone}")
        customer_label.setStyleSheet(
            "QLabel { font-weight: bold; margin: 10px 0; }")
        layout.addWidget(customer_label)

        # Checkbox Entrega
        self.delivery_checkbox = QCheckBox("Entrega")
        self.delivery_checkbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.delivery_checkbox.keyPressEvent = lambda event: self.checkbox_key_handler(
            event, self.delivery_checkbox)
        layout.addWidget(self.delivery_checkbox)

        # Campos de endereço (inicialmente desabilitados)
        self.setup_delivery_fields(layout)

        # Checkbox Retirada
        self.pickup_checkbox = QCheckBox("Retirada")
        self.pickup_checkbox.setFocusPolicy(Qt.StrongFocus)
        self.pickup_checkbox.keyPressEvent = lambda event: self.checkbox_key_handler(
            event, self.pickup_checkbox)
        layout.addWidget(self.pickup_checkbox)

        # Forma de pagamento
        payment_label = QLabel("Forma de Pagamento:")
        payment_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(payment_label)

        payment_layout = QHBoxLayout()
        self.payment_button = QPushButton("Selecione...")
        self.payment_menu = QMenu()
        self.payment_button.setMenu(self.payment_menu)
        self.payment_method = None
        self.change_label = QLabel("Troco para:")
        self.change_label.setVisible(False)
        self.change_input = QLineEdit()
        self.change_input.setPlaceholderText("R$ 0,00")
        self.change_input.setFixedWidth(90)
        self.change_input.setVisible(False)
        payment_layout.addWidget(self.payment_button)
        payment_layout.addWidget(self.change_label)
        payment_layout.addWidget(self.change_input)
        layout.addLayout(payment_layout)

        # Adiciona opções ao menu
        dinheiro_action = self.payment_menu.addAction("Dinheiro")
        cartao_action = self.payment_menu.addAction("Cartão")
        pix_action = self.payment_menu.addAction("Pix")

        def set_payment_method(method):
            self.payment_method = method
            self.payment_button.setText(method)
            if method == "Dinheiro":
                self.change_label.setVisible(True)
                self.change_input.setVisible(True)
                self.change_input.setFocus()
            else:
                self.change_label.setVisible(False)
                self.change_input.setVisible(False)

        dinheiro_action.triggered.connect(
            lambda: set_payment_method("Dinheiro"))
        cartao_action.triggered.connect(lambda: set_payment_method("Cartão"))
        pix_action.triggered.connect(lambda: set_payment_method("Pix"))

        # Label do total
        self.total_label = QLabel()
        total_font = QFont()
        total_font.setPointSize(16)
        total_font.setBold(True)
        self.total_label.setFont(total_font)
        self.total_label.setStyleSheet(
            "QLabel { color: #2a7; margin: 15px 0; }")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_total_label()
        layout.addWidget(self.total_label)

        # Botões
        self.setup_buttons(layout)

        layout.addStretch()

    def setup_delivery_fields(self, layout):
        """Configura os campos de entrega."""
        # Rua e número na mesma linha
        address_layout = QHBoxLayout()

        # Rua
        street_layout = QVBoxLayout()
        street_layout.addWidget(QLabel("Rua:"))
        self.street_input = QLineEdit(self.original_street)
        self.street_input.setPlaceholderText("Nome da rua")
        self.street_input.setEnabled(False)
        street_layout.addWidget(self.street_input)
        address_layout.addLayout(street_layout)

        # Número
        number_layout = QVBoxLayout()
        number_layout.addWidget(QLabel("Número:"))
        self.number_input = QLineEdit(self.original_number)
        self.number_input.setPlaceholderText("Nº")
        self.number_input.setEnabled(False)
        number_layout.addWidget(self.number_input)
        address_layout.addLayout(number_layout)

        layout.addLayout(address_layout)

        # Bairro e taxa
        neighborhood_layout = QHBoxLayout()
        neighborhood_col = QVBoxLayout()
        neighborhood_col.addWidget(QLabel("Bairro:"))
        self.neighborhood_button = QPushButton("Selecionar Bairro")
        self.neighborhood_menu = QMenu()
        self.neighborhood_button.setMenu(self.neighborhood_menu)
        self.selected_neighborhood_id = self.customer_data.get(
            'neighborhood_id')
        self.neighborhood_button.setEnabled(False)
        neighborhood_col.addWidget(self.neighborhood_button)
        neighborhood_layout.addLayout(neighborhood_col)

        # Taxa de entrega
        fee_col = QVBoxLayout()
        fee_col.addWidget(QLabel("Taxa:"))
        self.delivery_fee_label = QLabel("R$ 0,00")
        self.delivery_fee_label.setStyleSheet("QLabel { font-weight: bold; }")
        fee_col.addWidget(self.delivery_fee_label)
        neighborhood_layout.addLayout(fee_col)

        layout.addLayout(neighborhood_layout)

        # Ponto de referência
        layout.addWidget(QLabel("Ponto de Referência:"))
        self.reference_input = QLineEdit(self.original_reference)
        self.reference_input.setPlaceholderText("Próximo a...")
        self.reference_input.setEnabled(False)
        layout.addWidget(self.reference_input)

        # Carrega bairros e define o atual
        self.load_neighborhoods()

        # Navegação dinâmica com Enter entre campos de entrega
        self.street_input.keyPressEvent = lambda event: self.delivery_key_handler(
            event, self.street_input)
        self.number_input.keyPressEvent = lambda event: self.delivery_key_handler(
            event, self.number_input)
        self.reference_input.keyPressEvent = lambda event: self.delivery_key_handler(
            event, self.reference_input)

    def delivery_key_handler(self, event, widget):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if widget == self.street_input:
                self.number_input.setFocus()
                event.accept()
            elif widget == self.number_input:
                self.reference_input.setFocus()
                event.accept()
            elif widget == self.reference_input:
                self.neighborhood_button.setFocus()
                event.accept()
        else:
            QLineEdit.keyPressEvent(widget, event)

    def setup_buttons(self, layout):
        """Configura os botões do modal."""
        buttons_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setStyleSheet(
            "QPushButton { color: white; background-color: #555; border-radius: 6px; }"
            "QPushButton:hover { background-color: #777; }"
            "QPushButton:pressed { background-color: #333; }"
        )
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.finalize_button = QPushButton("Finalizar [Ctrl+Enter]")
        self.finalize_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.finalize_button)

        layout.addLayout(buttons_layout)

    def setup_connections(self):
        """Configura as conexões de sinais."""
        # Atalho Ctrl+Enter para finalizar pedido
        from PySide6.QtGui import QKeySequence, QShortcut
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.accept)

        self.delivery_checkbox.toggled.connect(self.on_delivery_toggled)
        self.pickup_checkbox.toggled.connect(self.on_pickup_toggled)

        # Conecta mudanças nos campos para detectar alterações
        self.street_input.textChanged.connect(self.on_address_changed)
        self.number_input.textChanged.connect(self.on_address_changed)
        self.reference_input.textChanged.connect(self.on_address_changed)

    def load_neighborhoods(self):
        """Carrega os bairros no menu."""
        self.neighborhood_menu.clear()
        neighborhoods = get_neighborhoods()

        if not neighborhoods:
            no_action = self.neighborhood_menu.addAction(
                "Nenhum bairro cadastrado")
            no_action.setEnabled(False)
            return

        for neighborhood in neighborhoods:
            action = self.neighborhood_menu.addAction(
                f"{neighborhood[1]} - R$ {neighborhood[2]:.2f}"
            )
            action.triggered.connect(
                lambda checked, nid=neighborhood[0], name=neighborhood[1],
                fee=neighborhood[2]: self.select_neighborhood(nid, name, fee)
            )

            # Se este é o bairro selecionado, marca o botão
            if self.selected_neighborhood_id == neighborhood[0]:
                self.neighborhood_button.setText(f"Bairro: {neighborhood[1]}")
                self.delivery_fee_label.setText(f"R$ {neighborhood[2]:,.2f}".replace(
                    ",", "X").replace(".", ",").replace("X", "."))

    def select_neighborhood(self, neighborhood_id, neighborhood_name, fee):
        """Seleciona um bairro."""
        self.selected_neighborhood_id = neighborhood_id
        self.neighborhood_button.setText(f"Bairro: {neighborhood_name}")
        self.delivery_fee_label.setText(f"R$ {fee:,.2f}".replace(
            ",", "X").replace(".", ",").replace("X", "."))
        self.update_total_label()

    def on_delivery_toggled(self, checked):
        """Ativa/desativa campos de entrega."""
        self.street_input.setEnabled(checked)
        self.number_input.setEnabled(checked)
        self.reference_input.setEnabled(checked)
        self.neighborhood_button.setEnabled(checked)

        if checked:
            self.pickup_checkbox.setChecked(False)
            # Foca no primeiro campo de entrega
            self.street_input.setFocus()
        self.update_total_label()

    def on_pickup_toggled(self, checked):
        """Gerencia checkbox de retirada."""
        if checked:
            self.delivery_checkbox.setChecked(False)

    def on_address_changed(self):
        """Chamado quando algum campo de endereço é alterado."""
        # Apenas para detectar mudanças - lógica será na finalização
        pass

    def has_address_changes(self):
        """Verifica se houve mudanças no endereço."""
        current_street = self.street_input.text().strip()
        current_number = self.number_input.text().strip()
        current_reference = self.reference_input.text().strip()

        return (current_street != self.original_street or
                current_number != self.original_number or
                current_reference != self.original_reference)

    def save_address_changes(self):
        """Salva mudanças no endereço do cliente."""
        if not self.has_address_changes():
            return True

        try:
            customer_id = self.customer_data.get('id')
            if not customer_id:
                LOGGER.error("ID do cliente não encontrado")
                return False

            # Mantém os dados originais que não mudaram
            name = self.customer_data.get('name', '')
            phone = self.customer_data.get('phone', '')

            # Novos dados de endereço
            street = self.street_input.text().strip()
            number = self.number_input.text().strip()
            reference = self.reference_input.text().strip()
            neighborhood_id = self.selected_neighborhood_id

            update_customer(customer_id, name, phone, street, number,
                            neighborhood_id, reference)

            LOGGER.info(f"Endereço do cliente {customer_id} atualizado")
            return True

        except Exception as e:
            LOGGER.error(f"Erro ao atualizar endereço: {e}")
            QMessageBox.warning(self, "Erro",
                                f"Erro ao atualizar endereço: {str(e)}")
            return False

    def save_order_to_database(self):
        """Salva o pedido no banco de dados. Se cliente não existir, cria antes."""
        try:
            from database.db import add_customer
            customer_id = self.customer_data.get('id')
            # Se não existe, cria o cliente
            if not customer_id:
                name = self.customer_data.get('name', '')
                phone = self.customer_data.get('phone', '')
                street = None
                number = None
                neighborhood_id = None
                reference = None
                if self.delivery_checkbox.isChecked():
                    street = self.street_input.text().strip()
                    number = self.number_input.text().strip()
                    neighborhood_id = self.selected_neighborhood_id
                    reference = self.reference_input.text().strip()
                # Cria o cliente e busca o novo id
                try:
                    add_customer(name, phone, street, number,
                                 neighborhood_id, reference)
                except Exception as e:
                    LOGGER.error(f"Erro ao criar cliente: {e}")
                    QMessageBox.warning(
                        self, "Erro", f"Erro ao criar cliente: {str(e)}")
                    return False
                # Busca o cliente recém-criado
                from database.db import get_customers
                all_customers = get_customers()
                for c in all_customers:
                    if c[1] == name and c[2] == phone:
                        customer_id = c[0]
                        self.customer_data['id'] = customer_id
                        # Não emite sinal para atualizar sugestões
                        break
                if not customer_id:
                    LOGGER.error("Não foi possível obter o ID do novo cliente")
                    QMessageBox.warning(
                        self, "Erro", "Não foi possível obter o ID do novo cliente.")
                    return False

            # Prepara dados dos itens para o banco
            items_data = []
            for item in self.order_items:
                item_data = {
                    'menu_item_id': item['item_data'][0],  # ID do item
                    'quantity': item.get('qty', 1),
                    'unit_price': item['item_data'][2],  # Preço do item
                    'additions': [add.get('id') for add in item.get('additions', [])]
                }
                items_data.append(item_data)

            # Determina tipo de pedido
            order_notes = ""
            total_to_save = self.total_amount
            if self.delivery_checkbox.isChecked():
                order_notes = "Entrega"
                fee = 0.0
                neighborhoods = get_neighborhoods()
                for n in neighborhoods:
                    if n[0] == self.selected_neighborhood_id:
                        fee = n[2]
                        break
                total_to_save += fee
            elif self.pickup_checkbox.isChecked():
                order_notes = "Retirada"

            # Salva o pedido
            order_id = save_order(customer_id, items_data,
                                  total_to_save, order_notes)
            LOGGER.info(f"Pedido {order_id} salvo com sucesso")
            return True

        except Exception as e:
            LOGGER.error(f"Erro ao salvar pedido: {e}")
            QMessageBox.warning(
                self, "Erro", f"Erro ao salvar pedido: {str(e)}")
            return False

    def accept(self):
        """Finaliza o pedido."""
        # Valida se um tipo foi selecionado
        if not self.delivery_checkbox.isChecked() and not self.pickup_checkbox.isChecked():
            QMessageBox.warning(
                self, "Aviso", "Selecione Entrega ou Retirada!")
            return

        # Se entrega está marcada, valida campos obrigatórios
        if self.delivery_checkbox.isChecked():
            if not self.street_input.text().strip():
                QMessageBox.warning(
                    self, "Aviso", "Preencha o nome da rua para entrega!")
                self.street_input.setFocus()
                return

        # Salva mudanças no endereço se necessário
        if self.delivery_checkbox.isChecked() and self.has_address_changes():
            if not self.save_address_changes():
                return

        # Salva o pedido no banco
        if not self.save_order_to_database():
            return

        # Imprime o pedido
        self.print_order()

        # Toca som de notificação se configurado
        if should_play_notification_sound():
            try:
                import winsound
                winsound.Beep(1000, 200)  # Freq 1000Hz por 200ms
            except ImportError:
                # Se não estiver no Windows, usa print como fallback
                print("\a")  # Bell character
            except Exception as e:
                LOGGER.warning(f"Erro ao tocar som de notificação: {e}")

        self.result = True
        if self.event_loop:
            self.event_loop.quit()
        super().accept()

    def print_order(self):
        """Gera o PDF do pedido e envia para impressão."""
        try:
            # Preparar dados do pedido
            if self.delivery_checkbox.isChecked():
                street = self.street_input.text().strip()
                number = self.number_input.text().strip()
                neighborhood = None
                neighborhoods = get_neighborhoods()
                for n in neighborhoods:
                    if n[0] == self.selected_neighborhood_id:
                        neighborhood = n[1]
                        break
                reference = self.reference_input.text().strip()
                order_notes = [street, number, neighborhood, reference]
            elif self.pickup_checkbox.isChecked():
                order_notes = "Retirada"
            else:
                order_notes = ""

            # Calcular total com taxa de entrega
            total_amount = self.total_amount
            delivery_fee = 0.0
            if self.delivery_checkbox.isChecked():
                neighborhoods = get_neighborhoods()
                for n in neighborhoods:
                    if n[0] == self.selected_neighborhood_id:
                        delivery_fee = n[2]
                        break
                total_amount += delivery_fee

            # Obter forma de pagamento e troco
            payment_method = self.payment_method if hasattr(
                self, 'payment_method') else None
            change_value = 0.0
            if payment_method == "Dinheiro":
                change_text = self.change_input.text().replace(
                    "R$", "").replace(",", ".").strip()
                try:
                    change_value = float(change_text) if change_text else 0.0
                except Exception:
                    change_value = 0.0

            # Gerar linhas do recibo
            from utils.print_settings import format_order_for_print
            linhas = format_order_for_print(
                self.customer_data,
                self.order_items,
                total_amount,
                order_notes,
                delivery_fee,
                payment_method,
                change_value
            )

            # Gerar PDF temporário
            import os
            import tempfile
            pdf_fd, pdf_path = tempfile.mkstemp(suffix="_pedido.pdf")
            os.close(pdf_fd)
            default_printer = get_default_printer()
            printer_name = default_printer.name if default_printer else "Sistema de Impressão"
            printer = Printer(printer_name)
            printer.generate_order_pdf(pdf_path, linhas)

            # Imprimir PDF
            printer.print_pdf(pdf_path)

            # Opcional: remover o PDF após imprimir
            # os.remove(pdf_path)

        except Exception as e:
            LOGGER.error(f"Erro durante preparação da impressão: {e}")
            self.on_print_error(
                f"Erro durante preparação da impressão: {str(e)}")

    def on_print_finished(self, printer_name):
        """Callback quando a impressão é concluída."""
        LOGGER.info(f"Impressão concluída em: {printer_name}")

        # Se for salvamento em arquivo, mostra mensagem específica
        if printer_name == "Salvar em Arquivo TXT":
            QMessageBox.information(
                self, "Pedido Salvo",
                "O pedido foi salvo como arquivo TXT na pasta "
                "'pedidos_impressos'.\nVocê pode imprimir este arquivo "
                "posteriormente.")
        elif "Simulando" in printer_name or "dispositivo:" in printer_name:
            # Para impressão simulada ou em dispositivo USB
            pass  # Não mostra mensagem adicional
        else:
            # Para impressão real em impressora
            QMessageBox.information(
                self, "Impressão Concluída",
                f"Pedido impresso com sucesso em {printer_name}")

    def on_print_error(self, error_message):
        """Callback quando há erro na impressão."""
        LOGGER.error(f"Erro na impressão: {error_message}")

        # Verificar se é um erro de impressora não inicializada
        if (
            "não pôde ser inicializada" in error_message or
            "não foi encontrada" in error_message
        ):
            QMessageBox.warning(
                self, "Problema com a Impressora",
                f"{error_message}\n\n"
                "Possíveis soluções:\n"
                "• Verifique se a impressora está ligada\n"
                "• Verifique se o cabo USB está conectado\n"
                "• Reinicie a impressora\n"
                "• Verifique se não há outro programa usando a impressora\n\n"
                "Deseja salvar o pedido em arquivo TXT para imprimir depois?"
            )

            reply = QMessageBox.question(
                self, "Salvar em Arquivo",
                "Deseja salvar o pedido em arquivo TXT para imprimir depois?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self, "Erro de Impressão",
                f"Não foi possível imprimir o pedido:\n{error_message}\n\n"
                "Deseja salvar o pedido em arquivo TXT para imprimir depois?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Salvar como arquivo
                from utils.printer import Printer
                file_printer = Printer("Salvar em Arquivo TXT")

                # Recalcular os dados do pedido para salvar
                order_notes = ""
                if self.delivery_checkbox.isChecked():
                    order_notes = "Entrega"
                    street = self.street_input.text().strip()
                    number = self.number_input.text().strip()
                    reference = self.reference_input.text().strip()

                    if street:
                        address_parts = [street]
                        if number:
                            address_parts.append(f"nº {number}")
                        if reference:
                            address_parts.append(f"Ref: {reference}")
                        order_notes += f" - {', '.join(address_parts)}"
                elif self.pickup_checkbox.isChecked():
                    order_notes = "Retirada"

                total_amount = self.total_amount
                if self.delivery_checkbox.isChecked():
                    fee = 0.0
                    neighborhoods = get_neighborhoods()
                    for n in neighborhoods:
                        if n[0] == self.selected_neighborhood_id:
                            fee = n[2]
                            break
                    total_amount += fee

                print_text = format_order_for_print(
                    self.customer_data,
                    self.order_items,
                    total_amount,
                    order_notes
                )

                if file_printer.print(print_text):
                    QMessageBox.information(
                        self, "Arquivo Salvo",
                        "Pedido salvo como arquivo TXT na pasta "
                        "'pedidos_impressos'.")
                else:
                    QMessageBox.warning(
                        self, "Erro", "Não foi possível salvar o arquivo.")

            except Exception as e:
                LOGGER.error(f"Erro ao salvar arquivo: {e}")
                QMessageBox.warning(
                    self, "Erro", f"Erro ao salvar arquivo: {str(e)}")

    def reject(self):
        """Cancela o modal."""
        self.result = False
        if self.event_loop:
            self.event_loop.quit()
        super().reject()

    def exec(self):
        """Executa o modal de forma síncrona."""
        self.show()
        self.event_loop = QEventLoop()
        self.event_loop.exec()
        return self.result

    def closeEvent(self, event):
        """Gerencia o fechamento do modal."""
        if self.event_loop and self.event_loop.isRunning():
            self.event_loop.quit()
        super().closeEvent(event)

    def checkbox_key_handler(self, event, checkbox):
        if event.key() in (
            Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space
        ):
            checkbox.setChecked(not checkbox.isChecked())
            event.accept()
        else:
            QCheckBox.keyPressEvent(checkbox, event)
