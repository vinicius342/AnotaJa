from PySide6.QtPrintSupport import QPrinterInfo  # type: ignore


class Printer:
    def __init__(self, name: str):
        self.name = name

    def print(self, text: str) -> None:
        print(f"{self.name} is printing: {text}")

    @staticmethod
    def list_printers() -> list["Printer"]:
        printers = QPrinterInfo.availablePrinters()
        return [Printer(p.printerName()) for p in printers]


if __name__ == "__main__":
    available_printers = Printer.list_printers()
    if not available_printers:
        print("Nenhuma impressora encontrada.")
    else:
        for printer in available_printers:
            print(f"Impressora disponível: {printer.name}")
