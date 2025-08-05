from flask import Blueprint, request, send_file
from app.services import gerar_pdf_graficos
from datetime import datetime
import traceback
import sys
import importlib
import matplotlib

baixar_pdf_graficos_bp = Blueprint('baixar_pdf_graficos', __name__)

@baixar_pdf_graficos_bp.route('/baixar-pdf-graficos', methods=['POST', 'GET'])
def baixar_pdf_graficos():
    """
    Rota para gerar e baixar um PDF com os gráficos selecionados pelo usuário.
    """
    if request.method == 'POST':
        try:
            # Força o backend headless do matplotlib ANTES de qualquer import de pyplot
            if 'matplotlib.pyplot' not in sys.modules:
                matplotlib.use('Agg')

            # Se usar plotly, não precisa de display, mas se usar orca, precisa garantir que não está usando orca

            ano = request.form.get("ano", type=int) or datetime.today().year
            mes = request.form.get("mes", type=int) or datetime.today().month
            nome_base = request.form.get("nome", "relatorio")
            selecao = request.form.getlist("graficos")

            if not selecao or not nome_base:
                return "Selecione ao menos um gráfico e informe o nome do arquivo.", 400

            # --- DEBUG: LOG DE ENTRADA ---
            print(f"PDF DEBUG: ano={ano}, mes={mes}, nome_base={nome_base}, selecao={selecao}")

            buffer_pdf, nome_arquivo = gerar_pdf_graficos(selecao, nome_base, ano, mes)

            if isinstance(buffer_pdf, str):
                print("PDF DEBUG: Erro na geração do PDF:", buffer_pdf)
                return buffer_pdf, 400

            if hasattr(buffer_pdf, "seek"):
                buffer_pdf.seek(0)

            return send_file(
                buffer_pdf,
                as_attachment=True,
                download_name=nome_arquivo,
                mimetype="application/pdf"
            )
        except Exception as e:
            print("ERRO AO GERAR PDF DOS GRÁFICOS:", e)
            traceback.print_exc()
            return "Erro ao gerar o PDF dos gráficos. Verifique o log do servidor para detalhes.", 500

    return "Método não permitido.", 405
