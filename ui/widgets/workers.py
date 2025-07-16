"""
Workers para filtragem de dados em threads separadas.
"""

from PySide6.QtCore import QObject, Signal


class ItemFilterWorker(QObject):
    """
    Worker que executa a filtragem de itens em uma thread separada.
    """
    finished = Signal(
        list, str)  # Sinal emitido com a lista filtrada e o texto original

    def __init__(self, items):
        super().__init__()
        self.items = items

    def filter_items(self, text):
        """Filtra a lista de itens com base no texto."""
        if not text:
            self.finished.emit([], text)
            return

        filtered_items = [
            item for item in self.items
            if text.lower() in item[1].lower()  # item[1] é o nome do item
        ]
        self.finished.emit(filtered_items, text)

    def set_items(self, items):
        """Atualiza a lista de itens no worker."""
        self.items = items


class CustomerFilterWorker(QObject):
    """
    Worker que executa a filtragem de clientes em uma thread separada.
    """
    finished = Signal(
        list, str)  # Sinal emitido com a lista filtrada e o texto original

    def __init__(self, customers):
        super().__init__()
        self.customers = customers

    def filter_customers(self, text):
        """Filtra a lista de clientes com base no texto."""
        if not text:
            self.finished.emit([], text)
            return

        filtered_customers = [
            c for c in self.customers
            if text in c[0].lower() or text in c[1]
        ]
        self.finished.emit(filtered_customers, text)

    def set_customers(self, customers):
        """Atualiza a lista de clientes no worker."""
        self.customers = customers
