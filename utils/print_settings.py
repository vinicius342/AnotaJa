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
            if 'ELGIN' in printer_name.upper() or 'i9' in printer_name.lower():
                LOGGER.info(
                    "Tentando encontrar impressora térmica funcional...")
                working_printer = Printer.find_working_thermal_printer()
                if working_printer:
                    LOGGER.info(
                        f"Impressora funcional encontrada: {working_printer.name}")
                    return working_printer

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
                           order_notes=""):
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

        # Cabeçalho da empresa (se configurado)
        if print_settings['include_header'] and company_info['name']:
            lines.append("=" * 40)
            lines.append(company_info['name'].center(40))
            if company_info['document']:
                lines.append(company_info['document'].center(40))
            if company_info['address']:
                lines.append(company_info['address'].center(40))
            if company_info['phone']:
                lines.append(company_info['phone'].center(40))
            lines.append("=" * 40)
            lines.append("")

        # Informações do cliente
        lines.append("PEDIDO")
        lines.append("-" * 40)
        customer_name = customer_data.get('name', 'Cliente não informado')
        customer_phone = customer_data.get('phone', 'Telefone não informado')
        lines.append(f"Cliente: {customer_name}")
        lines.append(f"Telefone: {customer_phone}")
        lines.append("")

        # Itens do pedido
        lines.append("ITENS:")
        lines.append("-" * 40)

        for item in order_items:
            qty = item.get('qty', 1)
            item_data = item['item_data']
            item_name = item_data[1] if len(item_data) > 1 else 'Item'
            item_price = item_data[2] if len(item_data) > 2 else 0.0

            lines.append(f"{qty}x {item_name}")
            lines.append(f"   R$ {item_price:.2f}")

            # Adicionais se existirem
            if item.get('additions'):
                for addition in item['additions']:
                    add_name = addition.get('name', 'Adicional')
                    add_qty = addition.get('qty', 1)
                    add_price = addition.get('price', 0.0)
                    addition_line = (f"   + {add_qty}x {add_name} - "
                                     f"R$ {add_price:.2f}")
                    lines.append(addition_line)

            # Observações do item se existirem
            if item.get('observations'):
                lines.append(f"   Obs: {item['observations']}")

            lines.append("")

        # Total
        lines.append("-" * 40)
        lines.append(f"TOTAL: R$ {total_amount:.2f}")
        lines.append("-" * 40)

        # Observações do pedido
        if order_notes:
            lines.append("")
            lines.append(f"{order_notes}")

        lines.append("-" * 40)

        # Data/hora
        from datetime import datetime
        lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        lines.append("")

        return "\n".join(lines)

    except Exception as e:
        LOGGER.error(f"Erro ao formatar pedido para impressão: {e}")
        return f"Erro ao gerar impressão: {str(e)}"
