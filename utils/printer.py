import json
import os
import platform
import subprocess
import tempfile
from typing import List

from database.db import get_system_setting
from utils.log_utils import get_logger

# Importar win32print apenas no Windows
if platform.system() == "Windows":
    try:
        import win32print
        PYWIN32_AVAILABLE = True
    except ImportError:
        PYWIN32_AVAILABLE = False
        LOGGER = get_logger(__name__)
        LOGGER.warning("pywin32 não disponível, usando método fallback")
else:
    PYWIN32_AVAILABLE = False

LOGGER = get_logger(__name__)


class Printer:
    def generate_order_pdf(self, pdf_path, linhas):
        """
        Gera um PDF do pedido no formato bobina térmica.
        Args:
            pdf_path (str): Caminho onde salvar o PDF
            linhas (list): Linhas de texto para o recibo
        """
        # import getpass
        # import shutil

        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas

        # Lê configuração de girar nota
        rotate_receipt = get_system_setting('rotate_receipt', 'true') == 'true'
        largura = 80 * mm  # 80mm de largura (bobina padrão)
        altura_linha = 6 * mm
        margem_topo = 10 * mm
        margem_base = 5 * mm
        # Altura ajustada dinamicamente conforme quantidade de linhas
        altura = margem_topo + margem_base + len(linhas) * altura_linha
        c = canvas.Canvas(pdf_path, pagesize=(largura, altura))
        if rotate_receipt:
            c.translate(largura, altura)
            c.rotate(180)
        c.setFont("Helvetica-Bold", 12)
        y = altura - margem_topo
        for linha in linhas:
            c.drawString(5 * mm, y, linha)
            y -= altura_linha
        c.save()

        # Salva uma cópia do PDF na área de trabalho do usuário para análise
        # try:
        #     user = getpass.getuser()
        #     desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        #     dest_path = os.path.join(desktop, "recibo_ultimo.pdf")
        #     shutil.copy2(pdf_path, dest_path)
        #     LOGGER.info(f"Cópia do PDF salva em: {dest_path}")
        # except Exception as e:
        #     LOGGER.warning(
        #         f"Não foi possível salvar cópia do PDF na área de trabalho: {e}")

    def print_pdf(self, pdf_path, printer_name=None):
        """
        Imprime um PDF usando SumatraPDF.
        Args:
            pdf_path (str): Caminho do PDF
            printer_name (str): Nome da impressora (opcional, usa self.name)
        """
        import subprocess
        import sys
        from pathlib import Path

        sumatra_path = None
        # 1. Se rodando empacotado pelo PyInstaller, buscar em _internal
        if hasattr(sys, '_MEIPASS'):
            internal_path = Path(sys._MEIPASS) / '_internal' / 'SumatraPDF.exe'
            if internal_path.exists():
                sumatra_path = internal_path
        # 2. Fallback: buscar em utils/ (desenvolvimento)
        if sumatra_path is None:
            dev_path = Path(__file__).parent / "SumatraPDF.exe"
            if dev_path.exists():
                sumatra_path = dev_path

        if not sumatra_path or not sumatra_path.exists():
            raise FileNotFoundError(
                "SumatraPDF.exe não encontrado em _internal ou utils/. Certifique-se que está empacotado corretamente.")

        if not printer_name:
            printer_name = self.name
        args = [str(sumatra_path), "-print-to", printer_name, str(pdf_path)]
        LOGGER.info(f"Imprimindo PDF: {args}")
        subprocess.run(args, shell=False)

    @staticmethod
    def get_print_settings():
        """
        Obtém as configurações de impressão do sistema.
        Returns:
            dict: Dicionário com as configurações de impressão
        """
        from database.db import get_system_setting
        from utils.log_utils import get_logger
        LOGGER = get_logger(__name__)
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

    @staticmethod
    def should_play_notification_sound():
        """
        Verifica se deve tocar som de notificação.
        Returns:
            bool: True se deve tocar som, False caso contrário
        """
        from database.db import get_system_setting
        from utils.log_utils import get_logger
        LOGGER = get_logger(__name__)
        try:
            return get_system_setting('notification_sound', 'false') == 'true'
        except Exception as e:
            LOGGER.error(f"Erro ao verificar configuração de som: {e}")
            return False

    @staticmethod
    def format_order_for_print(customer_data, order_items, total_amount, order_notes=""):
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
        from datetime import datetime
        try:
            company_info = Printer.get_company_info()
            print_settings = Printer.get_print_settings()

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
            customer_phone = customer_data.get(
                'phone', 'Telefone não informado')
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

            # Endereço do cliente (após o total)
            address = customer_data.get('address')
            if address:
                lines.append(f"Endereço: {address}")

            # Observações do pedido
            if order_notes:
                lines.append("")
                lines.append(f"{order_notes}")

            lines.append("-" * 40)

            # Data/hora
            lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            lines.append("")

            return "\n".join(lines)

        except Exception as e:
            from utils.log_utils import get_logger
            LOGGER = get_logger(__name__)
            LOGGER.error(f"Erro ao formatar pedido para impressão: {e}")
            return f"Erro ao gerar impressão: {str(e)}"

    @staticmethod
    def get_default_printer():
        """
        Obtém a impressora padrão configurada no sistema.
        Returns:
            Printer: Instância da impressora padrão ou None se não configurada
        """
        try:
            printer_name = get_system_setting('default_printer', '')
            if printer_name:
                LOGGER.info(
                    f"Impressora configurada no sistema: {printer_name}")
                # Verificar se a impressora ainda existe no sistema
                available_printers = Printer.list_printers()
                for printer in available_printers:
                    if printer.name == printer_name:
                        LOGGER.info(
                            f"Impressora encontrada na lista: {printer.name}")
                        return printer

                LOGGER.warning(
                    f"Impressora {printer_name} não encontrada na lista")

                # Se não encontrar, retornar None para forçar nova seleção
                return None
            return None
        except Exception as e:
            LOGGER.error(f"Erro ao obter impressora padrão: {e}")
            return None

    # Classe para gerenciar impressoras do sistema.

    def __init__(self, name: str, is_thermal: bool = False):
        """
        Inicializa uma impressora com o nome especificado.

        Args:
            name (str): Nome da impressora
            is_thermal (bool): Se é uma impressora térmica
        """
        self.name = name
        self.is_thermal = is_thermal
        # Detecta se é uma impressora térmica baseado no nome
        thermal_keywords = ['elgin', 'i9', 'thermal', 'termica', 'pos',
                            'bematech', 'epson']
        if any(keyword in name.lower() for keyword in thermal_keywords):
            self.is_thermal = True

    @staticmethod
    def list_printers() -> List['Printer']:
        """
        Lista todas as impressoras disponíveis no sistema.

        Returns:
            List[Printer]: Lista de impressoras disponíveis
        """
        printers = []

        try:
            if platform.system() == "Windows" and PYWIN32_AVAILABLE:
                LOGGER.info(
                    "[LIST_PRINTERS] Usando pywin32 para listar impressoras")

                # Usar win32print para obter impressoras reais
                try:
                    impressoras_win32 = win32print.EnumPrinters(
                        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                    )

                    LOGGER.info(
                        f"[LIST_PRINTERS] {len(impressoras_win32)} impressoras detectadas"
                    )

                    for impressora_info in impressoras_win32:
                        nome = impressora_info[2]  # Nome da impressora

                        if nome:
                            LOGGER.info(f"[LIST_PRINTERS] Processando: {nome}")

                            # Obter detalhes da impressora
                            try:
                                handle = win32print.OpenPrinter(nome)
                                info = win32print.GetPrinter(handle, 2)

                                driver_name = info['pDriverName']
                                port_name = info['pPortName']
                                status = info['Status']

                                LOGGER.info(
                                    f"[LIST_PRINTERS] Driver: {driver_name}")
                                LOGGER.info(
                                    f"[LIST_PRINTERS] Porta: {port_name}")
                                LOGGER.info(
                                    f"[LIST_PRINTERS] Status: {status}")

                                win32print.ClosePrinter(handle)

                                # Filtrar impressoras virtuais por nome
                                if not Printer._is_virtual_printer_name(nome):
                                    printers.append(Printer(nome))
                                    LOGGER.info(
                                        f"[LIST_PRINTERS] Impressora adicionada: {nome}")
                                else:
                                    LOGGER.warning(
                                        f"[LIST_PRINTERS] Impressora VIRTUAL ignorada: {nome}")
                            except Exception as e:
                                LOGGER.error(
                                    f"[LIST_PRINTERS] Erro ao obter detalhes de {nome}: {e}")

                except Exception as e:
                    LOGGER.error(f"[LIST_PRINTERS] Erro no win32print: {e}")
                    # Fallback para método PowerShell
                    return Printer._list_printers_fallback()

            elif platform.system() == "Windows":
                LOGGER.warning(
                    "[LIST_PRINTERS] pywin32 não disponível, usando fallback")
                return Printer._list_printers_fallback()
            else:
                # Linux/Unix: usar lpstat e cups para listar impressoras
                try:
                    result = subprocess.run(
                        ["lpstat", "-p"],
                        capture_output=True, text=True, check=True
                    )
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith("printer "):
                            parts = line.split()
                            if len(parts) >= 2:
                                printers.append(Printer(parts[1]))
                except subprocess.CalledProcessError:
                    # Tentar com cups-config se disponível
                    try:
                        result = subprocess.run(
                            ["lpinfo", "-v"],
                            capture_output=True, text=True, check=True
                        )
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if "://" in line:
                                # Extrai nome da impressora da URI
                                parts = line.split()
                                if len(parts) >= 2:
                                    name = parts[1].split('/')[-1]
                                    if name:
                                        printers.append(Printer(name))
                    except subprocess.CalledProcessError:
                        pass

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            LOGGER.error(f"Erro ao listar impressoras: {e}")

        # Se nenhuma impressora real foi encontrada, adicionar apenas opções essenciais
        if not printers:
            LOGGER.warning(
                "[LIST_PRINTERS] Nenhuma impressora real encontrada")

            # Sempre adicionar opção de salvar em arquivo
            printers.append(Printer("Salvar em Arquivo TXT"))

        LOGGER.info(
            f"[LIST_PRINTERS] Total de impressoras reais: {len(printers)}")
        return printers

    @staticmethod
    def _test_printer_connectivity_win32(printer_name: str) -> bool:
        """
        Testa se uma impressora pode realmente imprimir usando win32print.

        Args:
            printer_name: Nome da impressora

        Returns:
            bool: True se conseguiu enviar dados, False caso contrário
        """
        try:
            LOGGER.info(f"[TEST_WIN32] Testando conectividade: {printer_name}")

            # Tentar abrir a impressora e enviar dados de teste
            handle = win32print.OpenPrinter(printer_name)

            # Criar um trabalho de teste
            job_info = ("Teste Conectividade", None, "RAW")
            win32print.StartDocPrinter(handle, 1, job_info)

            # Apenas iniciar e cancelar imediatamente - não queremos imprimir de verdade
            win32print.EndDocPrinter(handle)
            win32print.ClosePrinter(handle)

            LOGGER.info(f"[TEST_WIN32] {printer_name} passou no teste")
            return True

        except Exception as e:
            LOGGER.warning(f"[TEST_WIN32] {printer_name} falhou: {e}")
            # Verificar mensagens específicas de erro
            error_str = str(e).lower()
            if "não é possível inicializar" in error_str or "cannot initialize" in error_str:
                return False
            if "não encontrado" in error_str or "not found" in error_str:
                return False
            # Para outros erros, ainda considera como real (pode ser problema temporário)
            return True

    @staticmethod
    def _list_printers_fallback():
        """Método fallback para listar impressoras quando pywin32 não está disponível."""
        LOGGER.info("[FALLBACK] Usando método PowerShell como fallback")
        printers = []

        try:
            cmd = ["powershell", "-Command",
                   "Get-Printer | Select-Object Name, DriverName, PortName | ConvertTo-Json"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            printer_data = json.loads(result.stdout)
            if isinstance(printer_data, dict):
                printer_data = [printer_data]

            for printer_info in printer_data:
                name = printer_info.get('Name', '')
                if name and not Printer._is_virtual_printer_name(name):
                    printers.append(Printer(name))

        except Exception as e:
            LOGGER.error(f"[FALLBACK] Erro: {e}")

        return printers

    @staticmethod
    def _is_virtual_printer_name(name: str) -> bool:
        """Verifica se um nome de impressora indica uma impressora virtual."""
        virtual_keywords = [
            'Microsoft Print to PDF',
            'Microsoft XPS Document Writer',
            'Fax', 'OneNote', 'CutePDF', 'PDFCreator'
        ]
        return any(keyword.lower() in name.lower() for keyword in virtual_keywords)
