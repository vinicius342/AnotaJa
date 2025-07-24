import json
import os
import platform
import subprocess
import tempfile
import time
from typing import List

from utils.log_utils import get_logger

# Importar win32print apenas no Windows
if platform.system() == "Windows":
    try:
        import win32api
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
    """Classe para gerenciar impressoras do sistema."""

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
                        f"[LIST_PRINTERS] {len(impressoras_win32)} impressoras detectadas")

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

                                # Verificar se é uma impressora real
                                if Printer._is_real_printer_win32(nome, driver_name, port_name, status):
                                    printers.append(Printer(nome))
                                    LOGGER.info(
                                        f"[LIST_PRINTERS] Impressora REAL adicionada: {nome}")
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
            # Tentar encontrar impressora térmica funcional
            thermal_printer = Printer.find_working_thermal_printer()
            if thermal_printer:
                printers.append(thermal_printer)
                LOGGER.info(
                    f"[LIST_PRINTERS] Impressora térmica funcional encontrada: {thermal_printer.name}")

            # Sempre adicionar opção de salvar em arquivo
            printers.append(Printer("Salvar em Arquivo TXT"))

        LOGGER.info(
            f"[LIST_PRINTERS] Total de impressoras reais: {len(printers)}")
        return printers

    @staticmethod
    def _is_real_printer_win32(name: str, driver_name: str, port_name: str, status: int) -> bool:
        """
        Verifica se uma impressora é real usando dados do win32print.

        Args:
            name: Nome da impressora
            driver_name: Nome do driver
            port_name: Nome da porta
            status: Status da impressora (inteiro)

        Returns:
            bool: True se a impressora é real, False se virtual
        """
        LOGGER.info(f"[IS_REAL_WIN32] Verificando: {name}")

        # Impressoras virtuais comuns para ignorar
        virtual_keywords = [
            'Microsoft Print to PDF',
            'Microsoft XPS Document Writer',
            'Fax',
            'OneNote',
            'Send To OneNote',
            'CutePDF',
            'PDFCreator',
            'Foxit',
            'Adobe PDF'
        ]

        # Verificar se é impressora virtual por nome
        for keyword in virtual_keywords:
            if keyword.lower() in name.lower():
                LOGGER.info(f"[IS_REAL_WIN32] Virtual por nome: {keyword}")
                return False

        # Verificar portas virtuais
        virtual_ports = [
            'PORTPROMPT:',
            'FILE:',
            'Microsoft Shared Fax',
            'nul:',
            'XPSPort:'
        ]

        for vport in virtual_ports:
            if vport.lower() in port_name.lower():
                LOGGER.info(f"[IS_REAL_WIN32] Virtual por porta: {port_name}")
                return False

        # Para impressoras Elgin, fazer teste adicional
        if 'ELGIN' in name.upper():
            try:
                LOGGER.info(
                    f"[IS_REAL_WIN32] Testando impressora Elgin: {name}")
                # Tentar imprimir um teste simples
                result = Printer._test_printer_connectivity_win32(name)
                if not result:
                    LOGGER.warning(
                        f"[IS_REAL_WIN32] Elgin {name} falhou no teste")
                    return False
                else:
                    LOGGER.info(
                        f"[IS_REAL_WIN32] Elgin {name} passou no teste")
            except Exception as e:
                LOGGER.warning(f"[IS_REAL_WIN32] Erro ao testar {name}: {e}")
                return False

        LOGGER.info(f"[IS_REAL_WIN32] {name} identificada como REAL")
        return True

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
            job_id = win32print.StartDocPrinter(handle, 1, job_info)

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

    @staticmethod
    def _is_real_printer(name: str, driver_name: str, port_name: str, status: str) -> bool:
        """
        Verifica se uma impressora é real (física) ou virtual/fake.

        Args:
            name: Nome da impressora
            driver_name: Nome do driver
            port_name: Nome da porta
            status: Status da impressora

        Returns:
            bool: True se a impressora parece ser real, False caso contrário
        """
        # Impressoras virtuais comuns para ignorar
        virtual_keywords = [
            'Microsoft Print to PDF',
            'Microsoft XPS Document Writer',
            'Fax',
            'OneNote',
            'Send To OneNote',
            'CutePDF',
            'PDFCreator',
            'Foxit',
            'Adobe PDF'
        ]

        # Se o nome contém palavras-chave virtuais, é virtual
        for keyword in virtual_keywords:
            if keyword.lower() in name.lower():
                LOGGER.info(
                    f"[IS_REAL] {name} identificada como virtual (keyword: {keyword})")
                return False

        # Verificar portas virtuais
        virtual_ports = [
            'PORTPROMPT:',
            'FILE:',
            'Microsoft Shared Fax',
            'nul:',
            'XPSPort:'
        ]

        for vport in virtual_ports:
            if vport.lower() in port_name.lower():
                LOGGER.info(
                    f"[IS_REAL] {name} identificada como virtual (porta: {port_name})")
                return False

        # Verificar se é uma impressora Elgin específica que pode estar com problemas
        if 'ELGIN' in name.upper() and 'USB' in port_name.upper():
            # Tentar testar se a impressora responde
            try:
                LOGGER.info(
                    f"[IS_REAL] Testando conectividade da impressora {name}")
                # Testar com um comando simples de print
                test_file = tempfile.NamedTemporaryFile(
                    mode='w', suffix='.txt', delete=False)
                test_file.write("TESTE")
                test_file.close()

                test_cmd = f'print /D:"{name}" "{test_file.name}"'
                result = subprocess.run(
                    test_cmd, shell=True, capture_output=True, text=True, timeout=5)

                # Limpar arquivo de teste
                try:
                    os.unlink(test_file.name)
                except:
                    pass

                if result.returncode == 0 and result.stdout:
                    if "Não é possível inicializar" in result.stdout:
                        LOGGER.warning(
                            f"[IS_REAL] {name} não consegue inicializar - marcando como virtual")
                        return False
                    elif "não encontrado" in result.stdout.lower():
                        LOGGER.warning(
                            f"[IS_REAL] {name} não encontrada - marcando como virtual")
                        return False

                LOGGER.info(
                    f"[IS_REAL] {name} passou no teste de conectividade")

            except Exception as e:
                LOGGER.warning(f"[IS_REAL] Erro ao testar {name}: {e}")
                # Se falhar no teste, considera como suspeita mas não remove completamente
                LOGGER.info(
                    f"[IS_REAL] {name} falhou no teste mas será mantida")

        # Se chegou até aqui, considera como real
        LOGGER.info(f"[IS_REAL] {name} identificada como real")
        return True

    @staticmethod
    def find_working_thermal_printer() -> 'Printer':
        """
        Tenta encontrar uma impressora térmica que realmente funciona.

        Returns:
            Printer: Impressora funcional ou None se não encontrar
        """
        LOGGER.info("[FIND_THERMAL] Procurando impressora térmica funcional")

        # Estratégia 1: Tentar encontrar dispositivos USB diretos
        usb_devices = []
        try:
            # Usar PowerShell para encontrar dispositivos USB
            ps_cmd = '''
            Get-WmiObject -Class Win32_USBHub | 
            Where-Object {$_.Description -like "*print*" -or $_.Description -like "*ELGIN*"} |
            Select-Object Description, DeviceID
            '''
            result = subprocess.run(["powershell", "-Command", ps_cmd],
                                    capture_output=True, text=True)
            if result.stdout:
                LOGGER.info(
                    f"[FIND_THERMAL] Dispositivos USB encontrados: {result.stdout}")
        except Exception as e:
            LOGGER.warning(f"[FIND_THERMAL] Erro ao buscar USB: {e}")

        # Estratégia 2: Tentar portas COM
        com_ports = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6']
        for port in com_ports:
            try:
                # Verificar se a porta existe
                import serial
                try:
                    ser = serial.Serial(port, timeout=1)
                    ser.close()
                    LOGGER.info(f"[FIND_THERMAL] Porta {port} disponível")
                    return Printer(f"Impressora Térmica ({port})", is_thermal=True)
                except:
                    continue
            except ImportError:
                # Se pyserial não estiver disponível, tentar método alternativo
                try:
                    test_file = tempfile.NamedTemporaryFile(
                        mode='w', suffix='.txt', delete=False)
                    test_file.write("TESTE")
                    test_file.close()

                    result = subprocess.run(f'copy "{test_file.name}" {port}',
                                            shell=True, capture_output=True, text=True, timeout=2)

                    os.unlink(test_file.name)

                    if result.returncode == 0:
                        LOGGER.info(f"[FIND_THERMAL] Porta {port} responsiva")
                        return Printer(f"Impressora Térmica ({port})", is_thermal=True)

                except Exception:
                    continue

        # Estratégia 3: Tentar usar dispositivos USB diretos
        usb_paths = [
            r"\\.\USB001",
            r"\\.\USB002",
            r"\\.\USB003"
        ]

        for usb_path in usb_paths:
            try:
                test_file = tempfile.NamedTemporaryFile(
                    mode='w', suffix='.txt', delete=False)
                test_file.write("TESTE")
                test_file.close()

                # Tentar copiar para o dispositivo USB
                result = subprocess.run(f'copy "{test_file.name}" "{usb_path}"',
                                        shell=True, capture_output=True, text=True, timeout=2)

                os.unlink(test_file.name)

                if result.returncode == 0:
                    LOGGER.info(
                        f"[FIND_THERMAL] Dispositivo {usb_path} responsivo")
                    return Printer(f"Impressora USB Direta ({usb_path})", is_thermal=True)

            except Exception:
                continue

        LOGGER.warning(
            "[FIND_THERMAL] Nenhuma impressora térmica funcional encontrada")
        return None

    def print(self, text: str) -> bool:
        """
        Imprime o texto especificado.

        Args:
            text (str): Texto a ser impresso

        Returns:
            bool: True se a impressão foi bem-sucedida, False caso contrário
        """
        try:
            LOGGER.info(
                f"[PRINT] Iniciando impressão na impressora: {self.name}")
            LOGGER.info(f"[PRINT] Tipo térmica: {self.is_thermal}")
            LOGGER.info(f"[PRINT] Sistema operacional: {platform.system()}")
            LOGGER.info(f"[PRINT] Tamanho do texto: {len(text)} caracteres")

            # Opção especial para salvar em arquivo
            if self.name == "Salvar em Arquivo TXT":
                LOGGER.info("[PRINT] Método selecionado: salvar em arquivo")
                return self._save_to_file(text)

            if platform.system() == "Windows" and PYWIN32_AVAILABLE:
                LOGGER.info("[PRINT] Usando win32print para impressão")
                return self._print_win32(text)
            elif platform.system() == "Windows":
                LOGGER.info("[PRINT] Sistema Windows - usando método fallback")
                # Para impressoras térmicas, usar impressão direta
                if self.is_thermal:
                    return self._print_thermal_windows(text)
                else:
                    # Impressora comum - usar notepad
                    return self._print_common_windows(text)
            else:
                LOGGER.info("[PRINT] Sistema não-Windows detectado")
                # Linux/Unix: tentar usar lp para imprimir
                try:
                    subprocess.run(
                        ["lp", "-d", self.name],
                        input=text,
                        text=True,
                        check=True
                    )
                    LOGGER.info("[PRINT] Comando lp executado com sucesso")
                    return True
                except subprocess.CalledProcessError as e:
                    LOGGER.error(f"[PRINT] Erro no comando lp: {e}")
                    # Se falhar, tentar métodos alternativos para térmicas
                    if self.is_thermal:
                        return self._print_thermal_linux(text)
                    raise
            return True
        except (subprocess.CalledProcessError, FileNotFoundError,
                PermissionError) as e:
            # Em caso de erro, mostrar no console para debug
            LOGGER.error(f"[PRINT] Erro ao imprimir em {self.name}: {e}")
            LOGGER.warning("[PRINT] Simulando impressão devido a erro:")
            print(f"Erro ao imprimir em {self.name}: {e}")
            print("Simulando impressão:")
            print("-" * 40)
            print(text)
            print("-" * 40)
            LOGGER.info("[PRINT] Simulação de impressão concluída")
            return True

    def _print_win32(self, text: str) -> bool:
        """
        Imprime usando win32print - método mais direto e confiável.

        Args:
            text: Texto a ser impresso

        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            LOGGER.info(f"[WIN32_PRINT] Iniciando impressão em: {self.name}")

            # Abrir impressora
            handle = win32print.OpenPrinter(self.name)

            # Configurar trabalho de impressão
            job_info = ("Pedido Anotaja", None, "RAW")
            job_id = win32print.StartDocPrinter(handle, 1, job_info)

            LOGGER.info(f"[WIN32_PRINT] Job ID: {job_id}")

            # Iniciar página
            win32print.StartPagePrinter(handle)

            # Formatar texto para impressora térmica se necessário
            if self.is_thermal:
                formatted_text = self._format_for_thermal(text)
                LOGGER.info(
                    "[WIN32_PRINT] Texto formatado para impressora térmica")
            else:
                formatted_text = text

            # Enviar dados para impressão
            bytes_written = win32print.WritePrinter(
                handle, formatted_text.encode('utf-8'))
            LOGGER.info(f"[WIN32_PRINT] Bytes enviados: {bytes_written}")

            # Finalizar página e documento
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            win32print.ClosePrinter(handle)

            LOGGER.info(
                f"[WIN32_PRINT] Impressão concluída com sucesso em: {self.name}")
            return True

        except Exception as e:
            LOGGER.error(f"[WIN32_PRINT] Erro na impressão: {e}")
            error_str = str(e).lower()

            # Verificar erros específicos
            if "não é possível inicializar" in error_str or "cannot initialize" in error_str:
                print(
                    f"ERRO: A impressora {self.name} não pode ser inicializada.")
                print("Verifique se está ligada e conectada corretamente.")
                return False
            elif "acesso negado" in error_str or "access denied" in error_str:
                print(f"ERRO: Acesso negado à impressora {self.name}.")
                print(
                    "Verifique as permissões ou se outro programa está usando a impressora.")
                return False
            else:
                print(f"Erro inesperado na impressão: {e}")
                return False

    def _save_to_file(self, text: str) -> bool:
        """Salva o pedido em arquivo TXT."""
        try:
            # Criar diretório de pedidos se não existir
            orders_dir = os.path.join(os.getcwd(), "pedidos_impressos")
            os.makedirs(orders_dir, exist_ok=True)

            # Nome do arquivo com timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pedido_{timestamp}.txt"
            filepath = os.path.join(orders_dir, filename)

            # Salvar arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"Pedido salvo em: {filepath}")
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return False

    def _print_thermal_linux(self, text: str) -> bool:
        """Tentativas de impressão térmica no Linux."""
        try:
            # Tentar encontrar dispositivos USB de impressoras térmicas
            usb_devices = [
                "/dev/usb/lp0", "/dev/usb/lp1", "/dev/usb/lp2",
                "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2",
                "/dev/ttyACM0", "/dev/ttyACM1"
            ]

            for device in usb_devices:
                if os.path.exists(device):
                    try:
                        with open(device, 'w', encoding='latin-1') as f:
                            formatted_text = self._format_for_thermal(text)
                            f.write(formatted_text)
                        print(f"Impresso em dispositivo: {device}")
                        return True
                    except (OSError, PermissionError):
                        continue

            # Se não conseguir imprimir, salvar em arquivo
            return self._save_to_file(text)

        except Exception as e:
            print(f"Erro na impressão térmica Linux: {e}")
            return self._save_to_file(text)

    def _print_thermal_windows(self, text: str) -> bool:
        """Imprime em impressora térmica no Windows."""
        try:
            LOGGER.info(
                f"[THERMAL_WIN] Iniciando impressão térmica para: {self.name}")
            # Para impressoras térmicas, vamos usar uma abordagem direta
            # Criar arquivo temporário e enviar para impressora

            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                             delete=False,
                                             encoding='utf-8') as f:
                # Formatar texto para impressora térmica (80mm = ~42 chars)
                formatted_text = self._format_for_thermal(text)
                LOGGER.info(
                    f"[THERMAL_WIN] Texto formatado: {len(formatted_text)} chars")
                f.write(formatted_text)
                temp_file = f.name
                LOGGER.info(
                    f"[THERMAL_WIN] Arquivo temporário criado: {temp_file}")

            try:
                # Tentar imprimir usando copy para porta
                if "COM" in self.name.upper():
                    port = self.name.split("(")[-1].split(")")[0]
                    command = f'copy "{temp_file}" {port}'
                    LOGGER.info(f"[THERMAL_WIN] Usando comando COM: {command}")
                    result = subprocess.run(
                        command,
                        shell=True, check=True, capture_output=True, text=True
                    )
                    LOGGER.info(
                        f"[THERMAL_WIN] Resultado COM: {result.returncode}")
                    if result.stdout:
                        LOGGER.info(f"[THERMAL_WIN] Stdout: {result.stdout}")
                    if result.stderr:
                        LOGGER.warning(
                            f"[THERMAL_WIN] Stderr: {result.stderr}")
                else:
                    # Usar print command do Windows
                    command = f'print /D:"{self.name}" "{temp_file}"'
                    LOGGER.info(
                        f"[THERMAL_WIN] Usando comando print: {command}")
                    result = subprocess.run(
                        command,
                        shell=True, check=True, capture_output=True, text=True
                    )
                    LOGGER.info(
                        f"[THERMAL_WIN] Resultado print: {result.returncode}")
                    if result.stdout:
                        LOGGER.info(f"[THERMAL_WIN] Stdout: {result.stdout}")
                        # Verificar se há mensagens de erro específicas
                        if "Não é possível inicializar o dispositivo" in result.stdout:
                            LOGGER.error(
                                "[THERMAL_WIN] Erro: impressora não inicializou")
                            # Tentar método alternativo com PowerShell
                            return self._try_powershell_print(temp_file)
                        elif "não encontrado" in result.stdout.lower() or "not found" in result.stdout.lower():
                            error_msg = f"A impressora {self.name} não foi encontrada."
                            LOGGER.error(f"[THERMAL_WIN] {error_msg}")
                            print(error_msg)
                            return False
                    if result.stderr:
                        LOGGER.warning(
                            f"[THERMAL_WIN] Stderr: {result.stderr}")

                LOGGER.info("[THERMAL_WIN] Comando executado com sucesso")
            except subprocess.CalledProcessError as e:
                LOGGER.error(f"[THERMAL_WIN] Erro no subprocess: {e}")
                LOGGER.error(f"[THERMAL_WIN] Return code: {e.returncode}")
                if hasattr(e, 'stdout') and e.stdout:
                    LOGGER.error(
                        f"[THERMAL_WIN] Subprocess stdout: {e.stdout}")
                if hasattr(e, 'stderr') and e.stderr:
                    LOGGER.error(
                        f"[THERMAL_WIN] Subprocess stderr: {e.stderr}")
                raise
            finally:
                # Limpar arquivo temporário
                try:
                    os.unlink(temp_file)
                    LOGGER.info(
                        f"[THERMAL_WIN] Arquivo temporário removido: {temp_file}")
                except OSError as e:
                    LOGGER.warning(
                        f"[THERMAL_WIN] Erro ao remover arquivo: {e}")

            LOGGER.info(
                "[THERMAL_WIN] Impressão térmica concluída com sucesso")
            return True
        except Exception as e:
            LOGGER.error(f"[THERMAL_WIN] Erro na impressão térmica: {e}")
            print(f"Erro na impressão térmica: {e}")
            return False

    def _try_powershell_print(self, temp_file: str) -> bool:
        """Tenta imprimir usando PowerShell como método alternativo."""
        try:
            LOGGER.info("[POWERSHELL] Tentando impressão com PowerShell")
            # Comando PowerShell para imprimir diretamente
            ps_command = f'''
            $printer = Get-Printer -Name "{self.name}"
            if ($printer.PrinterStatus -eq "Normal") {{
                Start-Process -FilePath "notepad.exe" -ArgumentList "/p", "{temp_file}" -Wait
            }} else {{
                Write-Output "Impressora não está pronta"
                exit 1
            }}
            '''

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, text=True, check=True
            )

            LOGGER.info(f"[POWERSHELL] Resultado: {result.returncode}")
            if result.stdout:
                LOGGER.info(f"[POWERSHELL] Stdout: {result.stdout}")
            if result.stderr:
                LOGGER.warning(f"[POWERSHELL] Stderr: {result.stderr}")

            return True

        except subprocess.CalledProcessError as e:
            LOGGER.error(f"[POWERSHELL] Erro no PowerShell: {e}")
            if e.stdout:
                LOGGER.error(f"[POWERSHELL] Stdout: {e.stdout}")
            if e.stderr:
                LOGGER.error(f"[POWERSHELL] Stderr: {e.stderr}")
            return False
        except Exception as e:
            LOGGER.error(f"[POWERSHELL] Erro geral: {e}")
            return False

    def _print_common_windows(self, text: str) -> bool:
        """Imprime em impressora comum no Windows."""
        try:

            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                             delete=False,
                                             encoding='utf-8') as f:
                f.write(text)
                temp_file = f.name

            try:
                # Usar notepad para abrir diálogo de impressão
                subprocess.run(["notepad", "/p", temp_file], check=True)
            finally:
                # Limpar arquivo temporário após um delay
                time.sleep(2)  # Aguardar notepad processar
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

            return True
        except Exception as e:
            print(f"Erro na impressão comum: {e}")
            return False

    def _format_for_thermal(self, text: str) -> str:
        """Formata texto para impressora térmica (42 colunas) e aplica negrito se configurado."""
        from utils.print_settings import get_print_settings
        settings = get_print_settings()
        bold_enabled = settings.get('bold', False)
        bold_on = '\x1B\x45\x01'
        bold_off = '\x1B\x45\x00'
        font_size = settings.get('font_size', 12)
        paper_columns = settings.get('paper_columns', 42)
        margin = settings.get('margin', 0)
        # ESC/POS font size commands
        # 12 = normal, 24 = double height, 48 = double width+height
        if font_size >= 48:
            size_cmd = '\x1D\x21\x11'  # Double width + height
        elif font_size >= 24:
            size_cmd = '\x1D\x21\x01'  # Double height
        else:
            size_cmd = '\x1D\x21\x00'  # Normal
        # ESC/POS comando para margem esquerda (offset)
        # \x1B\x6C\xNN onde NN é o número de pontos (cada ponto ~0.125mm)
        # Exemplo: 0 = sem margem, 20 = ~2.5mm
        offset_cmd = f'\x1B\x6C{chr(margin)}' if margin > 0 else ''
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            if len(line) <= paper_columns:
                formatted_lines.append(line)
            else:
                # Quebrar linhas longas
                while len(line) > paper_columns:
                    formatted_lines.append(line[:paper_columns])
                    line = line[paper_columns:]
                if line:
                    formatted_lines.append(line)

        result = '\n'.join(formatted_lines)
        # Aplica margem, tamanho e negrito
        result = offset_cmd + size_cmd + \
            (bold_on if bold_enabled else '') + \
            result + (bold_off if bold_enabled else '')
        # Adicionar comando de corte para impressoras térmicas
        result += '\x1D\x56\x42\x00'  # ESC/POS corte
        return result

    def __str__(self) -> str:
        return f"Printer({self.name})"

    def __repr__(self) -> str:
        return self.__str__()
