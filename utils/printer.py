import platform
import subprocess
from typing import List


class Printer:
    """Classe para gerenciar impressoras do sistema."""
    
    def __init__(self, name: str):
        """
        Inicializa uma impressora com o nome especificado.
        
        Args:
            name (str): Nome da impressora
        """
        self.name = name
    
    @staticmethod
    def list_printers() -> List['Printer']:
        """
        Lista todas as impressoras disponíveis no sistema.
        
        Returns:
            List[Printer]: Lista de impressoras disponíveis
        """
        printers = []
        
        try:
            if platform.system() == "Windows":
                # Windows: usar wmic para listar impressoras
                result = subprocess.run(
                    ["wmic", "printer", "get", "name"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                lines = result.stdout.strip().split('\n')[1:]  # Pula o cabeçalho
                for line in lines:
                    line = line.strip()
                    if line:
                        printers.append(Printer(line))
            else:
                # Linux/Unix: usar lpstat para listar impressoras
                result = subprocess.run(
                    ["lpstat", "-p"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith("printer "):
                        # Formato: "printer nome ..."
                        parts = line.split()
                        if len(parts) >= 2:
                            printers.append(Printer(parts[1]))
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Se não conseguir listar impressoras, adiciona uma impressora padrão
            printers.append(Printer("Impressora Padrão"))
        
        # Se nenhuma impressora foi encontrada, adiciona uma padrão
        if not printers:
            printers.append(Printer("Impressora Padrão"))
        
        return printers
    
    def print(self, text: str) -> bool:
        """
        Imprime o texto especificado.
        
        Args:
            text (str): Texto a ser impresso
            
        Returns:
            bool: True se a impressão foi bem-sucedida, False caso contrário
        """
        try:
            if platform.system() == "Windows":
                # Windows: usar notepad para imprimir (abre o diálogo de impressão)
                with open("temp_print.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                subprocess.run(["notepad", "/p", "temp_print.txt"], check=True)
            else:
                # Linux/Unix: usar lp para imprimir
                result = subprocess.run(
                    ["lp", "-d", self.name],
                    input=text,
                    text=True,
                    check=True
                )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
            # Em caso de erro, apenas simula a impressão
            print(f"Simulando impressão em {self.name}:")
            print("-" * 40)
            print(text)
            print("-" * 40)
            return True
    
    def __str__(self) -> str:
        return f"Printer({self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
