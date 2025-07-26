import os
import subprocess
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def gerar_pdf(caminho_pdf, linhas):
    largura = 72 * mm  # 72mm de largura (bobina Elgin i9)
    # 841.89 pt (A4) – pode ajustar conforme o conteúdo
    altura = 297 * (72 / 25.4)
    c = canvas.Canvas(caminho_pdf, pagesize=(largura, altura))

    c.translate(largura, altura)
    c.rotate(180)

    altura_linha = 5 * mm
    margem_topo = 10 * mm
    margem_base = 10 * mm

    # Altura ajustada dinamicamente conforme quantidade de linhas
    altura = margem_topo + margem_base + len(linhas) * altura_linha

    c.setFont("Helvetica-Bold", 12)

    y = altura - margem_topo
    for linha in linhas:
        c.drawString(5 * mm, y, linha)
        y -= altura_linha

    c.save()


def imprimir_com_sumatra(caminho_pdf, nome_impressora):
    sumatra_path = Path(__file__).parent / 'utils' / "SumatraPDF.exe"
    if not sumatra_path.exists():
        raise FileNotFoundError(
            "SumatraPDF.exe não encontrado no caminho especificado.")

    args = [str(sumatra_path), "-print-to", nome_impressora, caminho_pdf]
    print("Executando:", args)
    subprocess.run(args, shell=False)


def abrir_pdf(caminho_pdf):
    os.startfile(caminho_pdf)  # Abre com visualizador padrão do Windows


# === Configuração ===
linhas = [
    "Recibo de Pagamento",
    "Cliente: João da Silva",
    "Produto: Impressora Elgin i9",
    "Valor: R$ 499,00",
    "Data: 25/07/2025",
] + [f"Item extra {i}" for i in range(10)]  # Simulando conteúdo maior

pdf_path = os.path.abspath("saida_dinamica.pdf")
nome_impressora = "ELGIN i9(USB)"  # Use exatamente o nome da sua impressora

# === Execução ===
gerar_pdf(pdf_path, linhas)
# abrir_pdf(pdf_path)  # Visualização para conferência
# Descomente para imprimir direto
imprimir_com_sumatra(pdf_path, nome_impressora)
