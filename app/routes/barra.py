from flask import render_template, Blueprint, request, redirect, session, url_for, jsonify
from datetime import datetime
from app.graficos import (
        gerar_grafico_vendas_diarias,
        gerar_grafico_vendas_geral,
        gerar_grafico_vendas_vendedor,
        gerar_grafico_status_vendas_vendedor,
        gerar_grafico_metas_vendedor,
        gerar_grafico_verdes_vermelhos_geral,
        gerar_grafico_verdes_vermelhos_vendedor,
        gerar_grafico_banco_vendedores,
        gerar_grafico_tipo_vendas_geral,
        gerar_grafico_tipo_vendas_por_vendedor,
        gerar_grafico_metas_diarias_vendedor,
        gerar_grafico_metas_semanais_vendedor,
        gerar_grafico_mapa_vendas_por_estado,
        gerar_grafico_prazo_vendas_vendedor,
        gerar_grafico_produtos_mais_vendidos,
        gerar_grafico_vendas_diarias_linhas,
        gerar_grafico_quantidade_vendas_diarias,
        gerar_grafico_vendas_fim_de_semana,
        gerar_grafico_quantidade_vendas_fim_de_semana
    )

barra_bp = Blueprint('barra', __name__)

@barra_bp.route('/grafico/<string:nome>', methods=['GET', 'POST'])
def obter_grafico(nome):
    ano = request.args.get("ano", type=int) or datetime.today().year
    mes = request.args.get("mes", type=int) or datetime.today().month

    funcoes = {
        "vendas_geral": lambda: gerar_grafico_vendas_geral(ano=ano, mes=mes),
        "vendas_vendedor": lambda: gerar_grafico_vendas_vendedor(ano=ano, mes=mes),
        "status_vendas": lambda: gerar_grafico_status_vendas_vendedor(ano=ano, mes=mes),
        "metas_vendedor": lambda: gerar_grafico_metas_vendedor(ano=ano, mes=mes),
        "verdes_vermelhos_geral": lambda: gerar_grafico_verdes_vermelhos_geral(ano=ano, mes=mes),
        "verdes_vermelhos_vendedor": lambda: gerar_grafico_verdes_vermelhos_vendedor(ano=ano, mes=mes),
        "banco_vendedores": lambda: gerar_grafico_banco_vendedores(ano=ano, mes=mes),
        "tipo_vendas_geral": lambda: gerar_grafico_tipo_vendas_geral(ano=ano, mes=mes),
        "tipo_vendas_por_vendedor": lambda: gerar_grafico_tipo_vendas_por_vendedor(ano=ano, mes=mes),
        "metas_diarias_vendedor": lambda: gerar_grafico_metas_diarias_vendedor(ano=ano, mes=mes),
        "metas_semanais_vendedor": lambda: gerar_grafico_metas_semanais_vendedor(ano=ano, mes=mes),
        "prazo_vendas_vendedor": lambda: gerar_grafico_prazo_vendas_vendedor(ano=ano, mes=mes),
        "produtos_mais_vendidos": lambda: gerar_grafico_produtos_mais_vendidos(ano=ano, mes=mes),
        "vendas_diarias_linhas": lambda: gerar_grafico_vendas_diarias_linhas(ano=ano, mes=mes),
        "quantidade_vendas_diarias": lambda: gerar_grafico_quantidade_vendas_diarias(ano=ano, mes=mes),
        "vendas_fim_de_semana": lambda: gerar_grafico_vendas_fim_de_semana(ano=ano, mes=mes),
        "quantidade_vendas_fim_de_semana": lambda: gerar_grafico_quantidade_vendas_fim_de_semana(ano=ano, mes=mes)
    }

    if nome not in funcoes:
        return jsonify({'erro': 'Gráfico não encontrado'}), 404

    try:
        html = funcoes[nome]()  # AGORA todas as funções são chamadas corretamente
        return jsonify({'grafico_html': html})
    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar gráfico: {str(e)}'}), 500


@barra_bp.route('/', methods=['GET', 'POST'])
def inicio():
    """
    Rota principal do sistema (dashboard). Exibe o painel inicial com todos os gráficos de vendas, metas e estatísticas.

    Esta rota é protegida por autenticação ().

    - Recebe parâmetros opcionais de ano e mês via query string para filtrar os dados exibidos (padrão: mês e ano atuais).
    - Gera todos os gráficos necessários para o dashboard utilizando funções específicas para cada visualização.
    - Renderiza o template 'inicio.html' passando todos os gráficos e filtros de período.
    """

    hoje = datetime.today()
    ano = request.args.get("ano", type=int) or hoje.year    # Ano a ser exibido (padrão: ano atual)
    mes = request.args.get("mes", type=int) or hoje.month   # Mês a ser exibido (padrão: mês atual)

    if request.method == 'POST':
        data = request.form.get('data')
        session['data_grafico_vendas_diarias'] = data
        return redirect(url_for('barra.inicio', data=data))  # <- Redireciona com GET
    
    data = request.args.get('data')
    session['data_grafico_vendas_diarias'] = data

    grafico_vendas_diarias = gerar_grafico_vendas_diarias(data_escolhida=data)
    grafico_mapa_vendas_por_estado = gerar_grafico_mapa_vendas_por_estado(ano=ano, mes=mes)

    # Renderiza o template HTML, passando todos os gráficos e filtros selecionados
    return render_template(
        'inicio.html',
        ano=ano,
        mes=mes,
        grafico_vendas_diarias=grafico_vendas_diarias,
        grafico_mapa_vendas_por_estado=grafico_mapa_vendas_por_estado
    )