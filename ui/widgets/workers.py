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
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.info(
            f"[CustomerFilterWorker.__init__] Lista recebida: {self.customers}")

    def filter_customers(self, text):
        """Filtra a lista de clientes com base no texto."""
        import logging
        logging.info(
            f"[CustomerFilterWorker.filter_customers] Lista atual: {self.customers}")
        if not text:
            self.finished.emit([], text)
            return

        text_lower = text.lower()
        filtered_customers = []
        for c in self.customers:
            nome = c[0] if len(c) > 0 else ""
            telefone = c[1] if len(c) > 1 else ""
            nome_ok = isinstance(nome, str) and text_lower in nome.lower()
            telefone_ok = isinstance(
                telefone, str) and text_lower in telefone.replace(' ', '').lower()
            if nome_ok or telefone_ok:
                filtered_customers.append(c)
        logging.info(
            f"[CustomerFilterWorker.filter_customers] Filtrados: {filtered_customers}")
        self.finished.emit(filtered_customers, text)

    def set_customers(self, customers):
        """Atualiza a lista de clientes no worker."""
        self.customers = customers
