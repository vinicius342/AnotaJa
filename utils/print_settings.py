"""
Utilitários para gerenciamento de configurações do sistema.
"""


from database.db import get_system_setting
from utils.log_utils import get_logger
from utils.printer import Printer

LOGGER = get_logger(__name__)


def get_default_printer():
    """
    Obtém a impressora padrão configurada no sistema.

    Returns:
        Printer: Instância da impressora padrão ou None se não configurada
    """
    try:
        printer_name = get_system_setting('default_printer', '')
        if printer_name:
            LOGGER.info(f"Impressora configurada no sistema: {printer_name}")
            # Verificar se a impressora ainda existe no sistema
            available_printers = Printer.list_printers()
            for printer in available_printers:
                if printer.name == printer_name:
                    LOGGER.info(
                        f"Impressora encontrada na lista: {printer.name}")
                    return printer

            LOGGER.warning(
                f"Impressora {printer_name} não encontrada na lista")
            # Se não encontrar e for uma impressora Elgin, tentar encontrar uma funcional
            # if 'ELGIN' in printer_name.upper() or 'i9' in printer_name.lower():
            #     LOGGER.info(
            #         "Tentando encontrar impressora térmica funcional...")
            #     working_printer = Printer.find_working_thermal_printer()
            #     if working_printer:
            #         LOGGER.info(
            #             f"Impressora funcional encontrada: {working_printer.name}")
            #         return working_printer

            # Se não encontrar, retornar None para forçar nova seleção
            return None
        return None
    except Exception as e:
        LOGGER.error(f"Erro ao obter impressora padrão: {e}")
        return None


def get_print_settings():
    """
    Obtém as configurações de impressão do sistema.

    Returns:
        dict: Dicionário com as configurações de impressão
    """
    try:
        return {
            'margin': int(get_system_setting('print_margin', '5')),
            'include_header': (
                get_system_setting('print_header', 'true') == 'true'
            ),
            'bold': (get_system_setting('print_bold', 'false') == 'true')
        }
    except Exception as e:
        LOGGER.error(f"Erro ao obter configurações de impressão: {e}")
        return {
            'margin': 5,
            'include_header': True,
            'bold': False
        }


def set_print_settings(settings: dict):
    """
    Salva as configurações de impressão no sistema.
    Args:
        settings (dict): Dicionário com as configurações
    """
    from database.db import set_system_setting
    if 'bold' in settings:
        set_system_setting(
            'print_bold', 'true' if settings['bold'] else 'false')
    if 'margin' in settings:
        set_system_setting('print_margin', str(settings['margin']))
    if 'include_header' in settings:
        set_system_setting(
            'print_header', 'true' if settings['include_header'] else 'false')


def get_company_info():
    """
    Obtém as informações da empresa configuradas no sistema.

    Returns:
        dict: Dicionário com as informações da empresa
    """
    try:
        return {
            'name': get_system_setting('company_name', ''),
            'document': get_system_setting('company_document', ''),
            'address': get_system_setting('company_address', ''),
            'phone': get_system_setting('company_phone', '')
        }
    except Exception as e:
        LOGGER.error(f"Erro ao obter informações da empresa: {e}")
        return {
            'name': '',
            'document': '',
            'address': '',
            'phone': ''
        }


def should_confirm_delete():
    """
    Verifica se deve confirmar antes de excluir itens.

    Returns:
        bool: True se deve confirmar, False caso contrário
    """
    try:
        return get_system_setting('confirm_delete', 'true') == 'true'
    except Exception as e:
        LOGGER.error(f"Erro ao verificar configuração de confirmação: {e}")
        return True


def should_play_notification_sound():
    """
    Verifica se deve tocar som de notificação.

    Returns:
        bool: True se deve tocar som, False caso contrário
    """
    try:
        return get_system_setting('notification_sound', 'false') == 'true'
    except Exception as e:
        LOGGER.error(f"Erro ao verificar configuração de som: {e}")
        return False


def format_order_for_print(customer_data, order_items, total_amount,
                           order_notes="", delivery_fee=0.0, payment_method=None, change_value=0.0):
    def wrap_line(text, width=32):
        """Quebra uma string em múltiplas linhas de até 'width' caracteres."""
        import textwrap
        return textwrap.wrap(text, width=width)
    """
    Formata um pedido para impressão usando as configurações do sistema.

    Args:
        customer_data (dict): Dados do cliente
        order_items (list): Lista de itens do pedido
        total_amount (float): Valor total do pedido
        order_notes (str): Observações do pedido

    Returns:
        str: Texto formatado para impressão
    """
    try:
        company_info = get_company_info()
        print_settings = get_print_settings()

        lines = []
        separator_ = ["-" * 55]

        # Cabeçalho da empresa (se configurado)
        if print_settings['include_header'] and company_info['name']:
            for line in wrap_line(company_info['name']):
                lines.append(line.center(32))
            lines.append('')
            for field in ['document', 'address', 'phone']:
                value = company_info.get(field)
                if value:
                    wrapped = wrap_line(str(value))
                    for w in wrapped:
                        lines.append(w.center(32))

        # Data/hora
        from datetime import datetime
        for line in wrap_line(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}"):
            lines.append(line)

        # Informações do cliente
        customer_name = customer_data.get('name', 'Cliente não informado')
        customer_phone = customer_data.get('phone', 'Telefone não informado')
        for line in wrap_line(f"Cliente: {customer_name}"):
            lines.append(line)
        for line in wrap_line(f"Tel: {customer_phone}"):
            lines.append(line)

        # Itens do pedido
        lines.extend(separator_)

        for item in order_items:
            qty = item.get('qty', 1)
            item_data = item['item_data']
            item_name = item_data[1] if len(item_data) > 1 else 'Item'
            item_price = item_data[2] if len(item_data) > 2 else 0.0

            # Calcular total do item (base + obrigatórios + opcionais)
            item_total = qty * item_price
            # Soma obrigatórios
            for mand in item.get('mandatory_additions', []):
                mand_preco = mand.get('price', 0.0)
                item_total += mand_preco * qty
            # Soma opcionais
            for add in item.get('additions', []):
                add_qtd = add.get('qty', 1)
                add_preco = add.get('price', 0.0)
                item_total += add_qtd * add_preco

            for line in wrap_line(f"{qty}x | {item_name}"):
                lines.append(line)

            # Detalhes (complementos obrigatórios)
            mandatory_additions = item.get('mandatory_additions', [])
            if mandatory_additions:
                lines.append("      Detalhes:")
                for mand in mandatory_additions:
                    mand_name = mand.get('name', 'Detalhe')
                    mand_qty = mand.get('qty', 1)
                    mand_line = f"      + {mand_qty}x | {mand_name}"
                    for line in wrap_line(mand_line):
                        lines.append(line)

            # Adicionais opcionais
            if item.get('additions'):
                lines.append("      Adicionais:")
                for addition in item['additions']:
                    add_name = addition.get('name', 'Adicional')
                    add_qty = addition.get('qty', 1)
                    add_price = addition.get('price', 0.0)
                    addition_line = (f"      + {add_qty}x | {add_name} - "
                                     f"R$ {add_price:.2f}")
                    for line in wrap_line(addition_line):
                        lines.append(line)

            # Preço total do item
            for line in wrap_line(f"   Total item: R$ {item_total:.2f}"):
                lines.append(line)

            # Observações do item se existirem
            if item.get('observations'):
                for line in wrap_line(f"   Obs: {item['observations']}"):
                    lines.append(line)
            lines.extend(separator_)

        # Taxa de entrega (se houver)
        if delivery_fee and delivery_fee > 0:
            for line in wrap_line(f'Sub-total: R$ {total_amount - delivery_fee:.2f}'):
                lines.append(line)
            for line in wrap_line(f"Taxa de entrega: R$ {delivery_fee:.2f}"):
                lines.append(line)

        # Total
        for line in wrap_line(f"TOTAL: R$ {total_amount:.2f}"):
            lines.append(line)

        # Forma de pagamento
        if payment_method:
            if payment_method == "Dinheiro":
                for line in wrap_line(f"Troco para: R$ {change_value:.2f}"):
                    lines.append(line)
            for line in wrap_line(f"Pagamento: {payment_method}"):
                lines.append(line)
        lines.extend(separator_)

        # Observações do pedido
        if order_notes and not isinstance(order_notes, list):
            for line in wrap_line(f"{order_notes}"):
                lines.append(line)

        # Endereço (se não for retirada)
        if isinstance(order_notes, list):
            street, number, neighborhood, reference = order_notes
            if street:
                for line in wrap_line(f"Rua: {street}"):
                    lines.append(line)
            if number:
                for line in wrap_line(f"Número: {number}"):
                    lines.append(line)
            if neighborhood:
                for line in wrap_line(f"Bairro: {neighborhood}"):
                    lines.append(line)
            if reference:
                for line in wrap_line(f"Ref: {reference}"):
                    lines.append(line)
        lines.append("")

        return lines

    except Exception as e:
        LOGGER.error(f"Erro ao formatar pedido para impressão: {e}")
        return [f"Erro ao gerar impressão: {str(e)}"]


# Função auxiliar para obter o texto completo, se necessário
def format_order_for_print_text(*args, **kwargs):
    lines = format_order_for_print(*args, **kwargs)
    return "\n".join(lines)
