"""
Módulo de gráficos para dashboard de vendas.
Realiza importações de bibliotecas de manipulação de dados, geração de gráficos (Plotly),
modelos do banco de dados MongoDB e funções auxiliares do sistema.

Este módulo provê funções para geração de gráficos de vendas por vendedor, por status,
metas, distribuição geográfica, entre outros.
"""

# Importa coleções (collections) de usuários, vendas e configs do MongoDB
from app.models import usuarios_collection, vendas_collection, configs_collection, produtos_collection

# Importa objetos para gráficos Plotly (gráficos customizados)
import plotly.graph_objs as go

# Importa utilitários para renderização estática de gráficos Plotly
import plotly.io as pio

# Importa Plotly Express para gráficos de alto nível (rápida criação)
import plotly.express as px

# Pandas para manipulação de DataFrames (organização/tabulação de dados)
import pandas as pd

# SON para ordenar corretamente comandos de agregação no MongoDB
from bson.son import SON

# defaultdict para facilitar contagens e agrupamentos de dados
from collections import defaultdict

# Importa datetime e timedelta para manipulação de datas e períodos
from datetime import datetime, timedelta

# json para ler arquivos GeoJSON e outros dados estruturados
import json

# os para operações de caminho e arquivos do sistema operacional
import os

# Função de serviço auxiliar para somar vendas (provavelmente soma valores de vendas filtradas)
from app.services import soma_vendas



def gerar_grafico_banco_vendedores(ano=None, mes=None):
    """
    Gera um gráfico de barras mostrando o saldo do banco de cada vendedor ativo,
    considerando apenas vendas faturadas do período selecionado. O saldo novo é
    calculado com base nas diferenças entre valor da venda e valor de tabela,
    respeitando autorizações de desconto.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # 1. Buscar todos os vendedores com status 'ativo'
    vendedores_ativos = list(usuarios_collection.find(
        {'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}
    ))
    nomes_ativos = {v['nome_completo'] for v in vendedores_ativos}

    # 2. Buscar vendas faturadas APENAS dos vendedores ativos no período selecionado
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': list(nomes_ativos)}
    }, {'_id': 0, 'vendedor': 1, 'valor_tabela': 1, 'valor_real': 1, 'desconto_autorizado': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})
    
    # 3. Buscar limites atuais do banco de cada vendedor (configs_collection)
    banco = list(configs_collection.find({'tipo': 'limite_vendedor'}, {'_id': 0, 'vendedor_nome': 1, 'limite': 1}))
    saldos_atuais = {b['vendedor_nome']: b['limite'] for b in banco}
    bancos_calculados = defaultdict(float)

    # 4. Calcular diferença entre valor da venda e valor de tabela
    for venda in vendas:
        vendedor = venda['vendedor']
        try:
            valor_tabela = float(venda['valor_tabela']) if venda['valor_tabela'] is not None else 0.0
        except (ValueError, TypeError):
            valor_tabela = 0.0
        try:
            valor_venda = float(venda['valor_real']) if venda['valor_real'] is not None else 0.0
        except (ValueError, TypeError):
            valor_venda = 0.0
        autorizado = venda.get('desconto_autorizado', False)

        diferenca = valor_venda - valor_tabela

        # Se houve desconto não autorizado, desconta do banco do vendedor
        if diferenca < 0 and not autorizado:
            bancos_calculados[vendedor] -= abs(diferenca)
        # Se houve venda acima do valor de tabela, soma ao banco
        elif diferenca > 0:
            bancos_calculados[vendedor] += diferenca

    # 5. Gera lista de resultados finais, só para vendedores ativos
    resultado = []
    for vendedor, banco_calculado in bancos_calculados.items():
        if vendedor not in nomes_ativos:
            continue  # Garante que só vendedores ativos entram no gráfico
        saldo_atual = float(saldos_atuais.get(vendedor, 0))
        saldo_calculado = round(banco_calculado, 2)
        saldo_novo = float(saldo_atual) + saldo_calculado
        resultado.append({
            "vendedor": vendedor,
            "saldo_atual": saldo_atual,
            "saldo_calculado": saldo_calculado,
            "saldo_novo": saldo_novo
        })

    # 6. Prepara listas para plotagem
    x = [d['vendedor'] for d in resultado]
    y = [d['saldo_novo'] for d in resultado]
    cores = []
    textos = []

    for d in resultado:
        if d['saldo_novo'] < d['saldo_atual'] and d['saldo_novo'] > 0:
            cores.append("blue")
        elif d['saldo_novo'] > d['saldo_atual']:
            cores.append("green")
        elif d['saldo_novo'] <= 0:
            cores.append("red")
        textos.append(f"Saldo: R$ {d['saldo_novo']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))

    # 7. Monta gráfico de barras
    fig = go.Figure(go.Bar(
        x=x,
        y=y,
        marker_color=cores,
        text=textos,
        textposition="auto"
    ))

    fig.update_layout(
        title="Saldo do Banco por Vendedor",
        xaxis_title="Vendedor",
        yaxis_title="Saldo Calculado",
        showlegend=True,
        height=400
    )
    
    # 8. Retorna o HTML do gráfico já pronto para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_vendas_geral(ano=None, mes=None):
    """
    Gera um gráfico horizontal de barras empilhadas mostrando o total vendido no mês,
    comparando com a meta da empresa, considerando apenas vendas faturadas de vendedores ativos.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca apenas vendedores ativos no sistema
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = {v['nome_completo'] for v in vendedores_ativos}

    # Busca vendas faturadas do mês, apenas de vendedores ativos
    pipeline = [
        {
            '$match': {
                'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
                'status': { '$in': ['Aprovada', 'Faturado'] },
                'vendedor': {'$in': list(nomes_ativos)}
            }
        },
        {
            '$addFields': {
                'valor_real': {
                    '$cond': {
                        'if': { '$isNumber': '$valor_real' },
                        'then': '$valor_real',
                        'else': { '$toDouble': '$valor_real' }
                    }
                }
            }
        }
    ]
    vendas = list(vendas_collection.aggregate(pipeline))

    # Busca meta geral da empresa nas configs
    metas = list(configs_collection.find({'tipo': 'geral'}, {'_id': 0, 'meta_empresa': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})
    
    # Soma o total vendido no período
    total = soma_vendas(vendas)
    meta = float(metas[0]['meta_empresa'])
    vendido = total
    faltando = max(0, meta - total)

    # Monta gráfico horizontal de barras empilhadas
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Vendido',
        x=[vendido],
        y=['Vendido'],
        orientation='h',
        marker_color='green',
        text=[f"R$ {vendido:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')],
    ))
    fig.add_trace(go.Bar(
        name='Faltando',
        x=[faltando],
        y=['Faltando'],
        orientation='h',
        marker_color='#c34323',
        text=[f"R$ {faltando:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')]
    ))

    fig.update_layout(
        barmode='stack',
        title=f"Meta Mensal de {meta:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
        xaxis_title=f"R${total:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
        showlegend=True,
        height=400
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_vendas_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras mostrando o total de vendas (em valor R$) por vendedor,
    considerando apenas vendas faturadas dos vendedores ativos no período selecionado.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência, padrão: mês/ano atual
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca apenas nomes dos vendedores com status 'ativo'
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = {v['nome_completo'] for v in vendedores_ativos}

    # Busca vendas faturadas do período apenas de vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': list(nomes_ativos)}
    }, {'_id': 0}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Total de Vendas por Vendedor",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Lista todos os nomes únicos de vendedores que tiveram vendas faturadas
    nomes = list(set(v['vendedor'] for v in vendas))
    totais = []
    for vendedor in nomes:
        # Filtra as vendas do vendedor e soma o valor
        valores_vendedor = [v for v in vendas if v['vendedor'] == vendedor]
        total = soma_vendas(valores_vendedor)
        totais.append(total)

    # Monta gráfico de barras com valores somados
    fig = go.Figure(go.Bar(
        x=nomes,
        y=totais,
        marker_color='green',
        text=[f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') for valor in totais],
        textposition='auto'
    ))

    fig.update_layout(
        title="Total de Vendas por Vendedor",
        xaxis_title="Vendedor",
        yaxis_title="Total de Vendas (R$)",
        yaxis_tickprefix="R$ ",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40)
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_vendas_diarias(data_escolhida=None):
    """
    Gera um gráfico de barras mostrando o total de vendas (R$) por vendedor no dia escolhido.
    Se nenhuma data for fornecida, usa o dia atual.

    Parâmetros:
        data_escolhida (str): Data no formato 'YYYY-MM-DD'. Opcional.

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    hoje = datetime.now()

    if data_escolhida:
        try:
            dia_ref = datetime.strptime(data_escolhida, "%Y-%m-%d")
        except ValueError:
            dia_ref = datetime(hoje.year, hoje.month, hoje.day)
    else:
        dia_ref = datetime(hoje.year, hoje.month, hoje.day)

    proximo_dia = dia_ref + timedelta(days=1)

    # Busca vendedores ativos
    vendedores_ativos = list(usuarios_collection.find(
        {'status': {'$in': ['ativo', 'bloqueado']}},
        {'_id': 0, 'nome_completo': 1}
    ))
    nomes_ativos = {v['nome_completo'] for v in vendedores_ativos}

    # Busca vendas do dia informado
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': dia_ref, '$lt': proximo_dia},
        'status': {'$in': ['Aprovada', 'Faturado']},
        'vendedor': {'$in': list(nomes_ativos)}
    }, {'_id': 0}))

    # Verifica se há vendas
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title=f"Total de Vendas por Vendedor ({dia_ref.strftime('%d/%m/%Y')})",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

    # Totaliza vendas por vendedor
    nomes = list(set(v['vendedor'] for v in vendas))
    totais = []
    for vendedor in nomes:
        vendas_vendedor = [v for v in vendas if v['vendedor'] == vendedor]
        total = soma_vendas(vendas_vendedor)
        totais.append(total)

    fig = go.Figure(go.Bar(
        x=nomes,
        y=totais,
        marker_color='green',
        text=[f"R$ {v:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') for v in totais],
        textposition='auto'
    ))

    fig.update_layout(
        title=f"Total de Vendas por Vendedor ({dia_ref.strftime('%d/%m/%Y')})",
        xaxis_title="Vendedor",
        yaxis_title="Total de Vendas (R$)",
        yaxis_tickprefix="R$ ",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40)
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

def gerar_grafico_status_vendas_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando a quantidade de vendas por status
    (Aguardando, Aprovada, Refazer, Cancelada, Faturado) para cada vendedor ativo, no período selecionado.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Pipeline de agregação para contar vendas por status para cada vendedor ativo
    pipeline = [
        {
            "$addFields": {
                "data": {"$toDate": "$data_criacao"}
            }
        },
        {
            "$match": {
                "data": {"$gte": primeiro_dia, "$lt": proximo_mes},
                "vendedor": {"$in": nomes_ativos},
                "status": {"$ne": ""}
            }
        },
        {
            "$project": {
                "vendedor": {"$trim": {"input": {"$ifNull": ["$vendedor", ""]}}},
                "status": {"$trim": {"input": {"$ifNull": ["$status", ""]}}}
            }
        },
        {
            "$group": {
                "_id": {
                    "vendedor": "$vendedor",
                    "status": "$status"
                },
                "quantidade": {"$sum": 1}
            }
        },
        {
            "$sort": SON([("_id.vendedor", 1), ("_id.status", 1)])
        }
    ]

    # Executa a agregação no banco de dados
    resultados = list(vendas_collection.aggregate(pipeline))

    # Se não houver dados, retorna gráfico vazio
    if not resultados:
        fig = go.Figure()
        fig.update_layout(
            title="Vendas por Status e Vendedor",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Monta lista de dicionários com os dados agrupados por vendedor e status
    dados = [
        {
            "vendedor": r["_id"]["vendedor"],
            "status": r["_id"]["status"],
            "quantidade": r["quantidade"]
        }
        for r in resultados
    ]

    # Cria DataFrame para facilitar a plotagem com Plotly Express
    df = pd.DataFrame(dados)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    df["vendedor"] = df["vendedor"].str.strip()
    df["status"] = df["status"].str.strip().str.capitalize()
    df["quantidade"] = pd.to_numeric(df["quantidade"]).astype(int)

    # Gera gráfico de barras empilhadas (por status para cada vendedor)
    fig = px.bar(
        df,
        x="vendedor",
        y="quantidade",
        color="status",
        title="Vendas por Status e Vendedor",
        labels={"quantidade": "Quantidade", "vendedor": "Vendedor"},
        text="quantidade",
        color_discrete_map={
            "Aguardando": "#FFA500",
            "Aprovada": "#28a745",
            "Refazer": "#007bff",
            "Cancelada": "#dc3545",
            "Faturado": "#8E44AD"
        }
    )

    fig.update_layout(
        barmode="stack",  # barras empilhadas
        height=400
    )
    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_metas_vendedor(ano=None, mes=None):
    """
    Gera um gráfico horizontal de barras empilhadas mostrando para cada vendedor ativo:
    - quanto ele já vendeu no mês (barra 'Vendido')
    - quanto falta para bater a meta do mês (barra 'Faltando').

    Considera apenas vendas faturadas de vendedores ativos.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca apenas vendedores ativos do tipo "vendedor"
    vendedores_ativos = list(usuarios_collection.find(
        {'status': {'$in': ['ativo', 'bloqueado']}, 'tipo': 'vendedor'},
        {'_id': 0, 'meta_mes': 1, 'nome_completo': 1}
    ))
    nomes_ativos = {v['nome_completo'] for v in vendedores_ativos}

    # Busca vendas faturadas do mês, apenas desses vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': list(nomes_ativos)}
    }, {'_id': 0, 'vendedor': 1, 'valor_real': 1, 'status': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Monta dicionário {vendedor: meta_mensal}
    dict_metas = {}
    for vendedor in vendedores_ativos:
        dict_metas[vendedor['nome_completo']] = float(vendedor['meta_mes'])

    # Se não houver metas cadastradas, retorna gráfico vazio
    if not dict_metas:
        fig = go.Figure()
        fig.update_layout(
            title="Progresso de Vendas por Vendedor",
            xaxis_title="Sem metas cadastradas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Agrupa vendas faturadas por vendedor, somando o valor vendido
    totais = {}
    for venda in vendas:
        status = venda.get('status', '').strip()
        if status == 'Cancelada':
            continue  # Ignora vendas canceladas

        vendedor = venda.get('vendedor', '').strip()
        valor = float(str(venda.get('valor_real', '0')).replace(',', '.'))
        if vendedor in dict_metas:
            totais[vendedor] = totais.get(vendedor, 0) + valor

    # Prepara listas para plotar o gráfico
    vendedores = []
    vendidos = []
    faltando = []

    for vendedor, meta in dict_metas.items():
        vendido = totais.get(vendedor, 0)
        falta = max(0, meta - vendido)

        vendedores.append(vendedor)
        vendidos.append(vendido)
        faltando.append(falta)

    # Monta gráfico de barras horizontais empilhadas
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Vendido',
        x=vendidos,
        y=vendedores,
        orientation='h',
        marker_color='green',
        text=[f"R$ {v:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') for v in vendidos],
        textposition='auto'
    ))
    fig.add_trace(go.Bar(
        name='Faltando',
        x=faltando,
        y=vendedores,
        orientation='h',
        marker_color='#c34323',
        text=[f"R$ {f:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') for f in faltando],
        textposition='auto'
    ))

    fig.update_layout(
        barmode='stack',
        title="Progresso de Vendas por Vendedor",
        xaxis_title="Valor (R$)",
        yaxis_title="Vendedor",
        height=400
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_metas_diarias_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de 'mini-cards' (scatter plot customizado) que mostra para cada vendedor ativo,
    a cada dia do mês, se a meta diária foi batida (por quantidade ou valor).
    Verde indica meta batida, vermelho indica meta não batida.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência, padrão: mês/ano atual
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca todos os vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = {v['nome_completo'] for v in vendedores_ativos}

    # Busca metas diárias de cada vendedor ativo
    metas = list(configs_collection.find(
        {'tipo': 'meta_vendedor', 'vendedor_nome': {'$in': list(nomes_ativos)}},
        {'_id': 0, 'vendedor_nome': 1, 'meta_dia_quantidade': 1, 'meta_dia_valor': 1}
    ))
    vendedores = [v['vendedor_nome'] for v in metas]
    dict_metas = {
        v['vendedor_nome']: {
            'quantidade': int(v.get('meta_dia_quantidade', 5)),
            'valor': float(v.get('meta_dia_valor', 21000))
        } for v in metas
    }

    # Busca vendas faturadas do mês, apenas de vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': list(nomes_ativos)}
    }, {'_id': 0, 'vendedor': 1, 'valor_real': 1, 'data_criacao': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Metas Diárias dos Vendedores (Mini-Cards)<br><sup>Verde: meta batida (quantidade OU valor), Vermelho: não</sup>",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Gera lista com todos os dias do mês no formato dd/mm
    dias_do_mes = [(primeiro_dia + pd.Timedelta(days=i)).strftime("%d/%m")
                   for i in range((proximo_mes - primeiro_dia).days)]

    # Inicializa estrutura para contabilizar quantidade e valor vendidos por dia/vendedor
    vendas_por_dia = {
        vendedor: {dia: {'qtd': 0, 'valor': 0.0} for dia in dias_do_mes}
        for vendedor in vendedores
    }
    # Preenche a estrutura com dados das vendas
    for venda in vendas:
        vendedor = venda.get('vendedor', '').strip()
        if vendedor not in dict_metas:
            continue
        data = venda['data_criacao']
        if isinstance(data, str):
            data = datetime.fromisoformat(data)
        dia = data.strftime("%d/%m")
        if dia in vendas_por_dia[vendedor]:
            vendas_por_dia[vendedor][dia]['qtd'] += 1
            vendas_por_dia[vendedor][dia]['valor'] += float(venda['valor_real'])

    # Monta listas para plotar o scatter: x = dia, y = vendedor, color = verde/vermelho
    x = []
    y = []
    color = []
    texts = []
    for i_v, vendedor in enumerate(vendedores):
        meta_qtd = dict_metas[vendedor]['quantidade']
        meta_val = dict_metas[vendedor]['valor']
        for i_d, dia in enumerate(dias_do_mes):
            qtd = vendas_por_dia[vendedor][dia]['qtd']
            val = vendas_por_dia[vendedor][dia]['valor']
            bateu = (qtd >= meta_qtd) or (val >= meta_val)
            x.append(dia)
            y.append(vendedor)
            color.append('green' if bateu else 'red')
            texto = (
                f"<b>{vendedor}</b><br>"
                f"Dia: {dia}<br>"
                f"Qtd: {qtd} (meta {meta_qtd})<br>"
                f"Valor: R$ {val:,.2f} (meta R$ {meta_val:,.2f})".replace(',', '_').replace('.', ',').replace('_', '.')
            )
            if bateu:
                texto += "<br><b>Meta batida!</b>"
            else:
                texto += "<br>Meta não batida"
            texts.append(texto)

    # Monta scatter plot com "mini-cards" coloridos por vendedor/dia
    fig = go.Figure(data=go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=30,  # tamanho dos mini-cards
            color=color,
            line=dict(color='black', width=1),
            symbol='square'
        ),
        text=texts,
        hoverinfo='text'
    ))

    fig.update_layout(
        title="Metas Diárias dos Vendedores (Mini-Cards)<br><sup>Verde: meta batida (quantidade OU valor), Vermelho: não</sup>",
        xaxis_title="Dia do Mês",
        yaxis_title="Vendedor",
        yaxis=dict(autorange='reversed'),  # Vendedores de cima pra baixo
        height=max(350, 45 * len(vendedores)),
        margin=dict(t=80, l=60, r=20, b=60),
        font=dict(size=13)
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_metas_semanais_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras mostrando o total vendido por vendedor na semana atual,
    com cor verde se bateu a meta e vermelha se não bateu. Também mostra uma linha horizontal
    representando a meta semanal de cada vendedor.

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    semana_atual = hoje.isocalendar()[1]

    primeiro_dia = datetime(ano, mes, 1)
    proximo_mes = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)

    # Vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = {v['nome_completo'] for v in vendedores_ativos}

    # Metas semanais
    metas = list(configs_collection.find(
        {'tipo': 'meta_vendedor', 'vendedor_nome': {'$in': list(nomes_ativos)}},
        {'_id': 0, 'vendedor_nome': 1, 'meta_semana': 1}
    ))
    vendedores = [v['vendedor_nome'] for v in metas]
    dict_metas = {
        v['vendedor_nome']: float(v.get('meta_semana', 90000))
        for v in metas
    }

    # Vendas aprovadas ou faturadas do mês
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': list(nomes_ativos)}
    }, {'_id': 0, 'vendedor': 1, 'valor_real': 1, 'data_criacao': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title=f"Vendas Semana Atual (Semana {semana_atual}) - Por Vendedor",
            xaxis_title="Sem metas cadastradas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Agrupar por semana do ano
    from collections import defaultdict
    vendas_semanais = defaultdict(float)
    for venda in vendas:
        vendedor = venda.get('vendedor', '').strip()
        if vendedor not in dict_metas:
            continue
        data = venda['data_criacao']
        if isinstance(data, str):
            data = datetime.fromisoformat(data)
        if data.isocalendar()[1] == semana_atual:
            vendas_semanais[vendedor] += float(venda['valor_real'])

    nomes = []
    totais = []
    cores = []
    textos = []
    metas_linha = []

    for vendedor in dict_metas:
        vendido = vendas_semanais.get(vendedor, 0)
        meta = dict_metas[vendedor]
        cor = 'green' if vendido >= meta else 'red'
        texto = f"R$ {vendido:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
        nomes.append(vendedor)
        totais.append(vendido)
        cores.append(cor)
        textos.append(texto)
        metas_linha.append(meta)

    fig = go.Figure()

    # Barras coloridas
    fig.add_trace(go.Bar(
        x=nomes,
        y=totais,
        marker_color=cores,
        text=textos,
        textposition='auto',
        name="Vendido"
    ))

    # Linha de metas (horizontal individual para cada vendedor)
    fig.add_trace(go.Scatter(
        x=nomes,
        y=metas_linha,
        mode='lines+markers',
        line=dict(dash='dash', color='black'),
        marker=dict(symbol='diamond'),
        name='Meta semanal'
    ))

    fig.update_layout(
        title=f"Vendas Semana Atual (Semana {semana_atual}) - Por Vendedor",
        xaxis_title="Vendedor",
        yaxis_title="Total de Vendas (R$)",
        yaxis_tickprefix="R$ ",
        height=400 + 40 * len(vendedores),
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title_text='Legenda',
        barmode='group'
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_verdes_vermelhos_geral(ano=None, mes=None):
    """
    Gera um gráfico de pizza (donut chart) mostrando a distribuição de vendas faturadas do mês
    entre clientes do tipo 'Verde' e 'Vermelho', considerando apenas vendedores ativos.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Busca vendas faturadas do mês, apenas desses vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': nomes_ativos}
    }, {'_id': 0, 'tipo_cliente': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})
    
    # Contadores de clientes verdes e vermelhos
    total_verde = 0
    total_vermelho = 0

    for venda in vendas:
        status = venda.get('tipo_cliente', '').strip().capitalize()
        if status == 'Verde':
            total_verde += 1
        elif status == 'Vermelho':
            total_vermelho += 1

    # Se não houver nenhum cliente verde/vermelho, retorna gráfico vazio
    if total_verde == 0 and total_vermelho == 0:
        fig = go.Figure()
        fig.update_layout(
            title="Distribuição de Clientes: Verde x Vermelho",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Monta dados para o gráfico de pizza (donut)
    labels = ['Verde', 'Vermelho']
    valores = [total_verde, total_vermelho]
    cores = ['green', 'red']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=valores,
        marker=dict(colors=cores),
        textinfo='label+percent+value',
        hole=0.4
    )])

    fig.update_layout(
        title="Distribuição de Clientes: Verde x Vermelho",
        height=400
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_verdes_vermelhos_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando, para cada vendedor ativo,
    a quantidade de vendas faturadas do mês para clientes do tipo 'Verde' e 'Vermelho'.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Busca vendas faturadas do mês, apenas desses vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': nomes_ativos}
    }, {'_id': 0, 'vendedor': 1, 'tipo_cliente': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Dicionário para contar vendas 'Verde' e 'Vermelho' por vendedor
    contagem = {}

    for venda in vendas:
        vendedor = venda.get('vendedor', '').strip()
        status = venda.get('tipo_cliente', '').strip().capitalize()

        # Só contabiliza se ambos os campos estiverem válidos
        if vendedor == "" or status not in ["Verde", "Vermelho"]:
            continue

        # Inicializa se o vendedor ainda não estiver no dicionário
        if vendedor not in contagem:
            contagem[vendedor] = {"Verde": 0, "Vermelho": 0}

        contagem[vendedor][status] += 1

    # Se não houver dados válidos, retorna gráfico vazio
    if not contagem:
        fig = go.Figure()
        fig.update_layout(
            title="Clientes Verdes x Vermelhos por Vendedor",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Monta listas para o gráfico
    vendedores = list(contagem.keys())
    verdes = [contagem[v]["Verde"] for v in vendedores]
    vermelhos = [contagem[v]["Vermelho"] for v in vendedores]

    # Gráfico de barras empilhadas
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Verde',
        x=vendedores,
        y=verdes,
        marker_color='green',
        text=verdes,
        textposition='auto'
    ))
    fig.add_trace(go.Bar(
        name='Vermelho',
        x=vendedores,
        y=vermelhos,
        marker_color='red',
        text=vermelhos,
        textposition='auto'
    ))

    fig.update_layout(
        barmode='stack',
        title="Clientes Verdes x Vermelhos por Vendedor",
        xaxis_title="Vendedor",
        yaxis_title="Quantidade de Vendas",
        height=400
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_verdes_vermelhos_vendedor_canceladas(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando, para cada vendedor ativo,
    a quantidade de vendas faturadas do mês para clientes do tipo 'Verde' e 'Vermelho'.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Busca vendas faturadas do mês, apenas desses vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Cancelada'] },
        'vendedor': {'$in': nomes_ativos}
    }, {'_id': 0, 'vendedor': 1, 'tipo_cliente': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Dicionário para contar vendas 'Verde' e 'Vermelho' por vendedor
    contagem = {}

    for venda in vendas:
        vendedor = venda.get('vendedor', '').strip()
        status = venda.get('tipo_cliente', '').strip().capitalize()

        # Só contabiliza se ambos os campos estiverem válidos
        if vendedor == "" or status not in ["Verde", "Vermelho"]:
            continue

        # Inicializa se o vendedor ainda não estiver no dicionário
        if vendedor not in contagem:
            contagem[vendedor] = {"Verde": 0, "Vermelho": 0}

        contagem[vendedor][status] += 1

    # Se não houver dados válidos, retorna gráfico vazio
    if not contagem:
        fig = go.Figure()
        fig.update_layout(
            title="Clientes Verdes x Vermelhos por Vendedor",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Monta listas para o gráfico
    vendedores = list(contagem.keys())
    verdes = [contagem[v]["Verde"] for v in vendedores]
    vermelhos = [contagem[v]["Vermelho"] for v in vendedores]

    # Gráfico de barras empilhadas
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Verde',
        x=vendedores,
        y=verdes,
        marker_color='green',
        text=verdes,
        textposition='auto'
    ))
    fig.add_trace(go.Bar(
        name='Vermelho',
        x=vendedores,
        y=vermelhos,
        marker_color='red',
        text=vermelhos,
        textposition='auto'
    ))

    fig.update_layout(
        barmode='stack',
        title="Clientes Verdes x Vermelhos por Vendedor",
        xaxis_title="Vendedor",
        yaxis_title="Quantidade de Vendas",
        height=400
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_tipo_vendas_geral(ano=None, mes=None):
    """
    Gera um gráfico de pizza mostrando a proporção entre vendas novas e vendas de atualização
    faturadas no mês, considerando apenas vendedores ativos.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Busca vendas faturadas do mês, apenas desses vendedores ativos
    vendas_mes = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': nomes_ativos}
    }, {'_id': 0, 'produto': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas_mes:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Contadores para vendas novas e atualizações
    total_novas = 0
    total_atualizacoes = 0

    for venda in vendas_mes:
        produto = venda.get('produto', '').strip().lower()
        # Considera ambas grafias de "atualização"
        if produto == "atualização" or produto == "atualizacao":
            total_atualizacoes += 1
        else:
            total_novas += 1

    # Monta dados do gráfico
    labels = ["Vendas Novas", "Atualizações"]
    valores = [total_novas, total_atualizacoes]
    cores = ["#1f77b4", "#ff7f0e"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=valores,
        marker=dict(colors=cores),
        textinfo='label+percent',
        hoverinfo='label+value'
    )])

    fig.update_layout(
        title="Distribuição de Vendas no Mês Atual",
        height=400
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_tipo_vendas_por_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando, para cada vendedor ativo,
    a quantidade de vendas faturadas do mês do tipo "Vendas Novas" e "Atualizações".

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Busca vendas faturadas do mês, apenas desses vendedores ativos
    vendas_mes = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': nomes_ativos}
    }, {'_id': 0, 'produto': 1, 'vendedor': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas_mes:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Inicializa contadores por vendedor
    # Estrutura: {vendedor: {'novas': int, 'atualizacoes': int}}
    dados_vendedor = defaultdict(lambda: {'novas': 0, 'atualizacoes': 0})

    # Conta vendas novas e atualizações por vendedor
    for venda in vendas_mes:
        if venda.get('produto') == None:
            continue
        vendedor = venda.get('vendedor', 'Desconhecido')
        produto = venda.get('produto', '').strip().lower()

        # Considera ambas grafias de "atualização"
        if produto == "atualização" or produto == "atualizacao":
            dados_vendedor[vendedor]['atualizacoes'] += 1
        else:
            dados_vendedor[vendedor]['novas'] += 1

    # Prepara dados para o gráfico
    vendedores = list(dados_vendedor.keys())
    vendas_novas = [dados_vendedor[v]['novas'] for v in vendedores]
    atualizacoes = [dados_vendedor[v]['atualizacoes'] for v in vendedores]

    # Gráfico de barras empilhadas
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=vendedores,
        y=vendas_novas,
        name='Vendas Novas',
        marker_color='#1f77b4',
        text=vendas_novas
    ))

    fig.add_trace(go.Bar(
        x=vendedores,
        y=atualizacoes,
        name='Atualizações',
        marker_color='#ff7f0e',
        text=atualizacoes
    ))

    fig.update_layout(
        barmode='stack',
        title='Vendas por Tipo e Vendedor (Mês Atual)',
        xaxis_title='Vendedor',
        yaxis_title='Quantidade de Vendas',
        height=450
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_vendas_vendedor_individual(ano=None, mes=None, username=None):
    """
    Gera um gráfico de barras horizontal para um vendedor específico, mostrando
    quanto ele já vendeu no mês em relação à sua meta mensal.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).
        username (str): Username do vendedor (chave única na base de usuários).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca a meta mensal e o nome completo do vendedor pelo username
    metas = list(usuarios_collection.find({'username': username}, {'_id': 0, 'meta_mes': 1, 'nome_completo': 1}))

    # Busca vendas faturadas do mês desse vendedor
    vendas = list(vendas_collection.find(
        {
            'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
            'vendedor': metas[0]['nome_completo'],
            'status': { '$in': ['Aprovada', 'Faturado'] }
        },
        {'_id': 0}
    ))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Sua Meta Mensal",
            xaxis_title="Sem dados de vendas",
            width=350,
            height=250
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

    # Calcula valores para o gráfico
    total = soma_vendas(vendas)
    meta = float(metas[0]['meta_mes'])
    vendido = total
    faltando = max(0, meta - total)

    # Monta o gráfico de barras horizontal (barmode stack)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Vendido',
        x=[vendido],
        y=['Vendido'],
        orientation='h',
        marker_color='green',
        text=[f"R$ {vendido:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')],
    ))
    fig.add_trace(go.Bar(
        name='Faltando',
        x=[faltando],
        y=['Meta do Mês'],
        orientation='h',
        marker_color='#c34323',
        text=[f"R$ {faltando:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')]
    ))

    fig.update_layout(
        barmode='stack',
        title="Sua Meta Mensal",
        xaxis_title=f"R${total:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
        showlegend=True,
        width=350,
        height=250
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

def gerar_grafico_banco_vendedor_individual(ano=None, mes=None, username=None):
    """
    Gera um gráfico de barras exibindo o saldo do banco de um vendedor específico no mês selecionado,
    considerando descontos, acréscimos e saldo atual, para visualização individual no dashboard.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).
        username (str): Username do vendedor.

    Retorna:
        str: HTML do gráfico Plotly pronto para embed (via pio.to_html).
    """
    # Define ano/mês de referência, se não informado pega o mês/ano atual
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)
    
    # Busca o nome completo do usuário pelo username
    usuario = list(usuarios_collection.find(
        {'username': username}, {'_id': 0, 'nome_completo': 1}
    ))

    # Busca vendas faturadas desse vendedor no mês selecionado
    vendas = list(vendas_collection.find(
        {
            'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
            'vendedor': usuario[0]['nome_completo'],
            'status': { '$in': ['Aprovada', 'Faturado'] }
        },
        {'_id': 0, 'vendedor': 1, 'valor_tabela': 1, 'valor_real': 1, 'desconto_autorizado': 1}
    ))

    # Se não houver vendas, retorna um gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Seu Banco Mensal",
            xaxis_title="Sem dados de vendas",
            width=350,
            height=250
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})
    
    # Busca o saldo atual configurado para o vendedor
    banco = list(configs_collection.find(
        {'tipo': 'limite_vendedor', 'vendedor_nome': usuario[0]['nome_completo']},
        {'_id': 0, 'vendedor_nome': 1, 'limite': 1}
    ))

    # Dicionário: {nome_vendedor: saldo_atual}
    saldos_atuais = {b['vendedor_nome']: b['limite'] for b in banco}

    # Calcula o saldo do mês (descontos, acréscimos, etc)
    bancos_calculados = defaultdict(float)
    for venda in vendas:
        vendedor = venda['vendedor']
        valor_tabela = float(venda['valor_tabela'])
        valor_venda = float(venda['valor_real'])
        autorizado = venda.get('desconto_autorizado', False)
        diferenca = valor_venda - valor_tabela

        if diferenca < 0 and not autorizado:
            bancos_calculados[vendedor] -= abs(diferenca)
        elif diferenca > 0:
            bancos_calculados[vendedor] += diferenca

    # Prepara lista final de resultados para plotar
    resultado = []
    for vendedor, banco_calculado in bancos_calculados.items():
        saldo_atual = float(saldos_atuais.get(vendedor, 0))
        saldo_calculado = round(banco_calculado, 2)
        saldo_novo = float(saldo_atual) + saldo_calculado
        resultado.append({
            "vendedor": vendedor,
            "saldo_atual": saldo_atual,
            "saldo_calculado": saldo_calculado,
            "saldo_novo": saldo_novo
        })

    # Monta listas de valores para plotagem
    x = [d['vendedor'] for d in resultado]
    y = [d['saldo_novo'] for d in resultado]
    cores = []
    textos = []

    # Cores para indicar saldo positivo, negativo ou igual
    for d in resultado:
        if d['saldo_novo'] < d['saldo_atual'] and d['saldo_novo'] > 0:
            cores.append("blue")
        elif d['saldo_novo'] > d['saldo_atual']:
            cores.append("green")
        elif d['saldo_novo'] <= 0:
            cores.append("red")
        textos.append(f"Saldo: R$ {d['saldo_novo']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))

    # Monta o gráfico de barras
    fig = go.Figure(go.Bar(
        x=x,
        y=y,
        marker_color=cores,
        text=textos,
        textposition="auto"
    ))

    fig.update_layout(
        title="Saldo do Banco por Vendedor",
        xaxis_title="Vendedor",
        yaxis_title="Saldo Calculado",
        showlegend=True,
        width=350,
        height=250
    )
    
    # Retorna o HTML pronto do gráfico para embed
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

def gerar_grafico_metas_diarias_vendedor_individual(username=None):
    """
    Gera um gráfico individual mostrando o progresso diário do vendedor em relação à meta diária (quantidade e valor).
    Exibe um card/gráfico para o vendedor logado, indicando se ele bateu a meta de hoje.

    Parâmetros:
        username (str): Username do vendedor para exibir a meta do dia.

    Retorna:
        str: HTML do gráfico Plotly pronto para embed (via pio.to_html).
    """

    # Obtém o dia atual (início e fim para filtrar as vendas de hoje)
    hoje = datetime.today()
    dia_inicio = datetime(hoje.year, hoje.month, hoje.day)
    dia_fim = dia_inicio + timedelta(days=1)

    # Busca o nome completo do vendedor pelo username
    usuario = list(usuarios_collection.find({'username': username}, {'_id': 0, 'nome_completo': 1}))
    if not usuario:
        return "<div>Usuário não encontrado.</div>"
    nome_vendedor = usuario[0]['nome_completo']

    # Busca metas diárias do vendedor (quantidade e valor)
    metas = configs_collection.find_one({'tipo': 'meta_vendedor', 'vendedor_nome': nome_vendedor})
    meta_qtd = int(metas.get('meta_dia_quantidade', 5)) if metas else 5
    meta_val = float(metas.get('meta_dia_valor', 21000)) if metas else 21000

    # Busca vendas faturadas do dia para o vendedor
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': dia_inicio, '$lt': dia_fim},
        'vendedor': nome_vendedor,
        'status': { '$in': ['Aprovada', 'Faturado'] }
    }, {'_id': 0, 'valor_real': 1, 'data_criacao': 1}))

    # Calcula quantidade e valor total vendido no dia
    qtd = len(vendas)
    val = sum(float(v['valor_real']) for v in vendas)

    # Determina se a meta foi batida (por quantidade ou valor)
    bateu = (qtd >= meta_qtd) or (val >= meta_val)
    cor = 'green' if bateu else 'red'
    texto = (
        f"<b>{nome_vendedor}</b><br>"
        f"Dia: {hoje.strftime('%d/%m/%Y')}<br>"
        f"Qtd: {qtd} (meta {meta_qtd})<br>"
        f"Valor: R$ {val:,.2f} (meta R$ {meta_val:,.2f})".replace(',', '_').replace('.', ',').replace('_', '.')
    )
    texto = texto
    if bateu:
        texto += "<br><b>Meta batida!</b>"
    else:
        texto += "<br>Meta não batida"

    # Cria gráfico de barra para o valor vendido, colorido conforme meta
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Hoje"],
        y=[val],
        marker_color=[cor],
        text=[texto],
        hoverinfo='text',
        name='Valor Vendido',
    ))
    # Adiciona linha de referência para a meta de valor diária
    fig.add_trace(go.Scatter(
        x=["Hoje"],
        y=[meta_val],
        mode='lines+markers',
        name='Meta diária (valor)',
        line=dict(dash='dash', color='black'),
        marker=dict(size=10),
        hoverinfo='skip'
    ))

    fig.update_layout(
        title="Sua Meta Diária Hoje<br><sup>Verde: meta batida (quantidade OU valor)</sup>",
        xaxis_title="Data",
        yaxis_title="Valor vendido (R$)",
        yaxis_tickprefix="R$ ",
        width=350,
        height=250,
        margin=dict(t=80, l=60, r=20, b=60),
        font=dict(size=13),
        showlegend=True
    )

    # Retorna HTML do gráfico pronto para embutir na página
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

def gerar_grafico_metas_semanais_vendedor_individual(username=None):
    """
    Gera um gráfico individual para o vendedor logado mostrando o progresso semanal em relação à meta semanal de vendas (valor).
    Exibe um card/gráfico para o vendedor, indicando se ele bateu a meta da semana atual.

    Parâmetros:
        username (str): Username do vendedor para exibir a meta semanal.

    Retorna:
        str: HTML do gráfico Plotly pronto para embed (via pio.to_html).
    """
    # Obtém a data de hoje
    hoje = datetime.today()
    # Calcula o início da semana (segunda-feira)
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana = datetime(inicio_semana.year, inicio_semana.month, inicio_semana.day)
    # Calcula o final da semana (domingo à meia-noite)
    fim_semana = inicio_semana + timedelta(days=7)

    # Busca o nome completo do vendedor pelo username
    usuario = list(usuarios_collection.find({'username': username}, {'_id': 0, 'nome_completo': 1}))
    if not usuario:
        return "<div>Usuário não encontrado.</div>"
    nome_vendedor = usuario[0]['nome_completo']

    # Busca meta semanal de valor para o vendedor (default 90000)
    metas = configs_collection.find_one({'tipo': 'meta_vendedor', 'vendedor_nome': nome_vendedor})
    if not metas:
        meta_val = 80000  # valor default para quem não tem meta cadastrada
    else:
        meta_val = float(metas.get('meta_semana', 80000) or 80000)

    # Busca vendas faturadas do vendedor dentro da semana
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': inicio_semana, '$lt': fim_semana},
        'vendedor': nome_vendedor,
        'status': { '$in': ['Aprovada', 'Faturado'] }
    }, {'_id': 0, 'valor_real': 1, 'data_criacao': 1}))

    # Soma o valor vendido na semana
    val = float(sum(float(v.get('valor_real', 0) or 0) for v in vendas))

    # Verifica se a meta semanal foi batida
    bateu = float(val) >= float(meta_val)
    cor = 'green' if bateu else 'red'

    # Texto para exibir no hover/tooltip
    texto = (
        f"<b>{nome_vendedor}</b><br>"
        f"Semana: {inicio_semana.strftime('%d/%m')} - {(fim_semana - timedelta(days=1)).strftime('%d/%m')}<br>"
        f"Valor: R$ {val:,.2f} (meta R$ {meta_val:,.2f})".replace(',', '_').replace('.', ',').replace('_', '.')
    )
    if bateu:
        texto += "<br><b>Meta batida!</b>"
    else:
        texto += "<br>Meta não batida"

    # Cria o gráfico (barra do valor vendido + linha da meta)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Esta semana"],
        y=[val],
        marker_color=[cor],
        text=[texto],
        hoverinfo='text',
        name='Valor Vendido',
    ))
    fig.add_trace(go.Scatter(
        x=["Esta semana"],
        y=[meta_val],
        mode='lines+markers',
        name='Meta semanal (valor)',
        line=dict(dash='dash', color='black'),
        marker=dict(size=10),
        hoverinfo='skip'
    ))

    fig.update_layout(
        title="Sua Meta Semanal<br><sup>Verde = meta batida (valor), Vermelho = não</sup>",
        xaxis_title="Semana",
        yaxis_title="Valor vendido (R$)",
        yaxis_tickprefix="R$ ",
        width=350,
        height=250,
        margin=dict(t=80, l=60, r=20, b=60),
        font=dict(size=13),
        showlegend=True
    )

    # Retorna o HTML do gráfico para embutir na página
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

def gerar_grafico_mapa_vendas_por_estado(ano=None, mes=None):
    """
    Gera um gráfico de mapa coroplético mostrando a distribuição de vendas faturadas por estado brasileiro,
    considerando apenas vendas dos vendedores ativos no mês/ano especificados.

    Parâmetros:
        ano (int, opcional): Ano das vendas. Default = ano atual.
        mes (int, opcional): Mês das vendas. Default = mês atual.

    Retorna:
        str: HTML embutível do gráfico Plotly, pronto para uso em templates Flask.
    """
    # 1. Determina o intervalo do mês desejado
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # 2. Busca apenas vendedores ativos para considerar nas vendas
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # 3. Busca vendas faturadas do mês, feitas por vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': nomes_ativos}
    }, {'_id': 0, 'endereco': 1}))

    # 4. Define as siglas dos estados do Brasil
    estados_brasil = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia', 'CE': 'Ceará',
        'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso',
        'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    siglas_estados = set(estados_brasil.keys())

    # 5. Conta vendas por estado, considerando também casos estrangeiros
    contagem_estados = defaultdict(int)
    for venda in vendas:
        estado = None
        endereco = venda.get('endereco', {})
        # Endereço pode ser dict (MongoDB) ou str (dados legados)
        if isinstance(endereco, dict):
            estado = endereco.get('estado', '').strip().upper()
        elif isinstance(endereco, str):
            estado = endereco.strip().upper()
        if estado in siglas_estados:
            contagem_estados[estado] += 1
        else:
            contagem_estados['Estrangeira'] += 1

    # 6. Prepara DataFrame para plotagem
    estados = []
    vendas_estados = []
    for sigla in siglas_estados:
        estados.append(sigla)
        vendas_estados.append(contagem_estados.get(sigla, 0))

    vendas_estrangeiras = contagem_estados.get('Estrangeira', 0)

    df = pd.DataFrame({
        'sigla': estados,
        'vendas': vendas_estados
    })

    # 7. Lê o arquivo GeoJSON do mapa do Brasil (deve existir no projeto)
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        geojson_path = os.path.join(BASE_DIR, 'static', 'data', 'brazil-states.geojson')
        with open(geojson_path, encoding='utf-8') as f:
            geojson = json.load(f)
    except Exception  as e:
        print(f'Erro: {e}')
        geojson = {"type": "FeatureCollection", "features": []} 

    # 8. Cria o mapa coroplético (choropleth) com Plotly Express
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations='sigla',
        featureidkey='properties.sigla',
        color='vendas',
        color_continuous_scale='Blues',  # Escala de cor azul
        range_color=(0, df['vendas'].max() if len(df) and df['vendas'].max() > 0 else 1),
        scope="south america",
        title="Vendas por Estado (Brasil)"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(l=30, r=30, t=70, b=30),
        height=520
    )

    # 9. Adiciona anotação para vendas estrangeiras, se houver
    if vendas_estrangeiras > 0:
        fig.add_annotation(
            text=f"Vendas Estrangeiras: {vendas_estrangeiras}",
            x=0.5,
            y=1.08,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16, color="crimson")
        )

    # 10. Retorna HTML para embutir o gráfico na página
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

def gerar_grafico_prazo_vendas_vendedor(ano=None, mes=None):
    """
    Gera um gráfico mostrando a quantidade de vendas por vendedor agrupadas pelo prazo (em dias)
    entre a data de criação da venda e a data de prestação inicial.

    Faixas:
        - <= 30 dias
        - 31-39 dias
        - 40-49 dias
        - 50-150 dias

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir.
    """
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Pipeline de agregação para calcular diferença de dias e agrupar por faixa e vendedor
    pipeline = [
        {
            "$addFields": {
                "data_criacao_dt": {"$toDate": "$data_criacao"}
            }
        },
        {
            "$match": {
                "data_prestacao_inicial": {"$type": "string", "$ne": ""}
            }
        },
        {
            "$addFields": {
                "data_prestacao_inicial_dt": {
                    "$dateFromString": {
                        "dateString": "$data_prestacao_inicial",
                        "format": "%Y-%m-%d"
                    }
                }
            }
        },
        {
            "$addFields": {
                "dias": {
                    "$divide": [
                        {"$subtract": ["$data_prestacao_inicial_dt", "$data_criacao_dt"]},
                        1000 * 60 * 60 * 24
                    ]
                }
            }
        },
        {
            "$match": {
                "data_criacao_dt": {"$gte": primeiro_dia, "$lt": proximo_mes},
                "vendedor": {"$in": nomes_ativos},
                "status": { "$in": ["Aprovada", "Faturado"] }
            }
        },
        {
            "$addFields": {
                "faixa_prazo": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$lte": ["$dias", 30]},
                                "then": "≤ 30 dias"
                            },
                            {
                                "case": {"$and": [{"$gt": ["$dias", 30]}, {"$lte": ["$dias", 39]}]},
                                "then": "31-39 dias"
                            },
                            {
                                "case": {"$and": [{"$gt": ["$dias", 39]}, {"$lte": ["$dias", 49]}]},
                                "then": "40-49 dias"
                            },
                            {
                                "case": {"$and": [{"$gt": ["$dias", 49]}, {"$lte": ["$dias", 150]}]},
                                "then": "50-150 dias"
                            }
                        ],
                        "default": "Outro"
                    }
                }
            }
        },
        {
            "$match": {
                "faixa_prazo": {"$ne": "Outro"}
            }
        },
        {
            "$group": {
                "_id": {
                    "vendedor": "$vendedor",
                    "faixa_prazo": "$faixa_prazo"
                },
                "quantidade": {"$sum": 1}
            }
        },
        {
            "$sort": SON([("_id.vendedor", 1), ("_id.faixa_prazo", 1)])
        }
    ]

    # Executa a agregação no banco de dados
    resultados = list(vendas_collection.aggregate(pipeline))

    # Se não houver dados, retorna gráfico vazio
    if not resultados:
        fig = go.Figure()
        fig.update_layout(
            title="Vendas por Prazo e Vendedor",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    dados = [
        {
            "vendedor": r["_id"]["vendedor"],
            "faixa_prazo": r["_id"]["faixa_prazo"],
            "quantidade": r["quantidade"]
        }
        for r in resultados
    ]

    df = pd.DataFrame(dados)
    # Organiza as faixas na ordem correta
    faixa_order = ["≤ 30 dias", "31-39 dias", "40-49 dias", "50-150 dias"]
    df["faixa_prazo"] = pd.Categorical(df["faixa_prazo"], categories=faixa_order, ordered=True)

    fig = px.bar(
        df,
        x="vendedor",
        y="quantidade",
        color="faixa_prazo",
        barmode="stack",
        title="Vendas por Prazo e Vendedor",
        labels={"quantidade": "Quantidade", "vendedor": "Vendedor", "faixa_prazo": "Prazo (dias)"},
        text="quantidade"
    )

    fig.update_layout(height=400)
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_prazo_vendedor_individual(mes=None, username=None):
    """
    Gera um gráfico para UM vendedor mostrando a quantidade de vendas agrupadas por prazo (em dias)
    entre a data de criação da venda e a data de prestação inicial.

    Faixas:
        - <= 30 dias
        - 31-39 dias
        - 40-49 dias
        - 50-150 dias

    Parâmetros:
        username (str): Nome do vendedor (como salvo no campo "vendedor" da venda)

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir.
    """
    hoje = datetime.today()
    ano = hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca o nome completo do vendedor pelo username
    usuario = list(usuarios_collection.find({'username': username}, {'_id': 0, 'nome_completo': 1}))
    if not usuario:
        return "<div>Usuário não encontrado.</div>"
    nome_vendedor = usuario[0]['nome_completo']

    pipeline = [
        {
            "$addFields": {
                "data_criacao_dt": {"$toDate": "$data_criacao"},
                "data_prestacao_inicial_dt": {
                    "$dateFromString": {
                        "dateString": "$data_prestacao_inicial",
                        "format": "%Y-%m-%d"
                    }
                }
            }
        },
        {
            "$addFields": {
                "dias": {
                    "$divide": [
                        {"$subtract": ["$data_prestacao_inicial_dt", "$data_criacao_dt"]},
                        1000 * 60 * 60 * 24
                    ]
                }
            }
        },
        {
            "$match": {
                "data_criacao_dt": {"$gte": primeiro_dia, "$lt": proximo_mes},
                "vendedor": nome_vendedor,
                "status": { "$in": ["Aprovada", "Faturado"] }
            }
        },
        {
            "$addFields": {
                "faixa_prazo": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$lte": ["$dias", 30]},
                                "then": "≤ 30 dias"
                            },
                            {
                                "case": {"$and": [{"$gt": ["$dias", 30]}, {"$lte": ["$dias", 39]}]},
                                "then": "31-39 dias"
                            },
                            {
                                "case": {"$and": [{"$gt": ["$dias", 39]}, {"$lte": ["$dias", 49]}]},
                                "then": "40-49 dias"
                            },
                            {
                                "case": {"$and": [{"$gt": ["$dias", 49]}, {"$lte": ["$dias", 150]}]},
                                "then": "50-150 dias"
                            }
                        ],
                        "default": "Outro"
                    }
                }
            }
        },
        {
            "$match": {
                "faixa_prazo": {"$ne": "Outro"}
            }
        },
        {
            "$group": {
                "_id": "$faixa_prazo",
                "quantidade": {"$sum": 1}
            }
        },
        {
            "$sort": SON([("_id", 1)])
        }
    ]

    resultados = list(vendas_collection.aggregate(pipeline))

    if not resultados:
        df_vazio = pd.DataFrame(columns=["faixa_prazo", "quantidade"])
        fig = px.bar(
            df_vazio,
            x="faixa_prazo",
            y="quantidade",
            title=f"Suas Vendas por Prazo",
            labels={"quantidade": "Quantidade", "faixa_prazo": "Prazo (dias)"}
        )
        fig.update_layout(
            width=350,
            height=250
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

    # Complete os dados para garantir todas as faixas
    faixa_order = ["≤ 30 dias", "31-39 dias", "40-49 dias", "50-150 dias"]
    quantidades_dict = {d["_id"]: d["quantidade"] for d in resultados}
    dados_completos = []
    for faixa in faixa_order:
        dados_completos.append({
            "faixa_prazo": faixa,
            "quantidade": quantidades_dict.get(faixa, 0)
        })

    df = pd.DataFrame(dados_completos)
    df["faixa_prazo"] = pd.Categorical(df["faixa_prazo"], categories=faixa_order, ordered=True)

    fig = px.bar(
        df,
        x="faixa_prazo",
        y="quantidade",
        color="faixa_prazo",
        title=f"Suas Vendas por Prazo",
        labels={"quantidade": "Quantidade", "faixa_prazo": "Prazo (dias)"},
        text="quantidade",
        barmode='stack'
    )

    fig.update_layout(
        showlegend=False,
        width=350,
        height=250
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

def gerar_grafico_produtos_mais_vendidos(ano=None, mes=None):
    """
    Gera um gráfico horizontal mostrando a quantidade de vendas faturadas por produto no mês atual.
    O eixo Y mostra os nomes dos produtos e o eixo X mostra a quantidade de vendas faturadas.

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define mês/ano atual
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes de todos os produtos cadastrados
    produtos_cadastrados = list(produtos_collection.find({}, {'_id': 0, 'nome': 1}))
    nomes_produtos = [p['nome'] for p in produtos_cadastrados]

    # Busca vendas faturadas no período
    vendas_faturadas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] }
    }, {'_id': 0, 'produto': 1}))

    # Contabiliza a quantidade de vendas faturadas por produto
    contagem_produtos = {nome: 0 for nome in nomes_produtos}
    for venda in vendas_faturadas:
        nome_produto = venda.get('produto', '').strip()
        if nome_produto in contagem_produtos:
            contagem_produtos[nome_produto] += 1

    # Remove produtos sem nenhuma venda faturada, se quiser mostrar só os vendidos
    dados = [
        {"produto": nome, "quantidade": qtde}
        for nome, qtde in contagem_produtos.items() if qtde > 0
    ]

    # Se quiser mostrar TODOS os produtos, mesmo com zero vendas, troque o if acima por: if True

    # Se não houver vendas faturadas, retorna gráfico vazio
    if not dados:
        df_vazio = pd.DataFrame(columns=["produto", "quantidade"])
        fig = px.bar(
            df_vazio,
            y="produto",
            x="quantidade",
            orientation='h',
            title="Produtos mais Vendidos",
            labels={"quantidade": "Quantidade", "produto": "Produto"}
        )
        fig.update_layout(height=400)
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Ordena por quantidade (opcional)
    dados.sort(key=lambda x: x["quantidade"], reverse=True)

    # Prepara listas para o gráfico
    produtos = [d["produto"] for d in dados]
    quantidades = [d["quantidade"] for d in dados]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=produtos,
        x=quantidades,
        orientation='h',
        marker_color='#4285F4',
        text=quantidades,
        textposition='auto',
        name='Aprovada'
    ))

    fig.update_layout(
        title="Produtos mais Vendidos",
        xaxis_title="Quantidade de Vendas Faturadas",
        yaxis_title="Produto",
        height=400
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_vendas_diarias_linhas(ano=None, mes=None):
    """
    Gera um gráfico de linha mostrando o total de vendas por dia do mês,
    considerando apenas vendas faturadas de vendedores ativos.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Pipeline de agregação para totalizar vendas faturadas por dia,
    # apenas de vendedores ativos, convertendo campos para os tipos corretos
    pipeline = [
        {
            "$addFields": {
                "data": {
                    "$toDate": "$data_criacao"
                },
                "valor_numerico": {
                    "$convert": {
                        "input": {
                            "$replaceOne": {
                                "input": "$valor_real",
                                "find": ",",
                                "replacement": "."
                            }
                        },
                        "to": "double",
                        "onError": 0,
                        "onNull": 0
                    }
                }
            }
        },
        {
            "$match": {
                "data": {"$gte": primeiro_dia, "$lt": proximo_mes},
                "status": { "$in": ["Aprovada", "Faturado"] },
                "vendedor": {"$in": nomes_ativos}  # Só vendas de ativos
            }
        },
        {
            "$group": {
                "_id": {
                    "ano": {"$year": "$data"},
                    "mes": {"$month": "$data"},
                    "dia": {"$dayOfMonth": "$data"}
                },
                "total": {"$sum": "$valor_numerico"}
            }
        },
        {
            "$sort": SON([("_id.ano", 1), ("_id.mes", 1), ("_id.dia", 1)])
        }
    ]

    # Executa a agregação no banco de dados
    resultados = list(vendas_collection.aggregate(pipeline=pipeline))

    # Se não houver dados, retorna gráfico vazio
    if not resultados:
        fig = go.Figure()
        fig.update_layout(
            title="Vendas por Dia do Mês",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Monta listas de dias e totais de vendas para plotagem
    dias = [f"{r['_id']['dia']:02d}/{r['_id']['mes']:02d}" for r in resultados]
    totais = [r['total'] for r in resultados]

    # Monta gráfico de linha com marcadores
    fig = go.Figure(go.Scatter(
        x=dias,
        y=totais,
        mode='lines+markers+text',
        line=dict(color='green', width=2),
        marker=dict(size=6),
        text=[f"R$ {v:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') for v in totais],
        textposition='top center',
        textfont=dict(size=12),
        hovertemplate="Dia: %{x}<br>Total: %{text}<extra></extra>"
    ))

    fig.update_layout(
        title="Vendas por Dia do Mês",
        xaxis_title="Dia",
        yaxis_title="Total de Vendas (R$)",
        yaxis_tickprefix="R$ ",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40)
    )

    # Retorna HTML do gráfico para renderização web
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_quantidade_vendas_diarias(ano=None, mes=None):
    """
    Gera um gráfico de linha mostrando a quantidade de vendas por dia do mês,
    ignorando apenas vendas com status 'Cancelada'.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    proximo_mes = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Pipeline de agregação para contar vendas por dia, exceto canceladas
    pipeline = [
        {
            "$addFields": {
                "data": { "$toDate": "$data_criacao" }
            }
        },
        {
            "$match": {
                "data": { "$gte": primeiro_dia, "$lt": proximo_mes },
                "status": { "$ne": "Cancelada" },
                "vendedor": { "$in": nomes_ativos }
            }
        },
        {
            "$group": {
                "_id": {
                    "ano": { "$year": "$data" },
                    "mes": { "$month": "$data" },
                    "dia": { "$dayOfMonth": "$data" }
                },
                "quantidade": { "$sum": 1 }
            }
        },
        {
            "$sort": SON([("_id.ano", 1), ("_id.mes", 1), ("_id.dia", 1)])
        }
    ]

    resultados = list(vendas_collection.aggregate(pipeline))

    if not resultados:
        fig = go.Figure()
        fig.update_layout(
            title="Quantidade de Vendas por Dia",
            xaxis_title="Sem dados",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    dias = [f"{r['_id']['dia']:02d}/{r['_id']['mes']:02d}" for r in resultados]
    quantidades = [r['quantidade'] for r in resultados]

    fig = go.Figure(go.Scatter(
        x=dias,
        y=quantidades,
        mode='lines+markers+text',
        line=dict(color='blue', width=2),
        marker=dict(size=6),
        text=[f"{q}" for q in quantidades],
        textposition='top center',
        textfont=dict(size=12),
        hovertemplate="Dia: %{x}<br>Quantidades: %{text}<extra></extra>"
    ))

    fig.update_layout(
        title="Quantidade de Vendas por Dia",
        xaxis_title="Dia",
        yaxis_title="Quantidade de Vendas",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40)
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_vendas_fim_de_semana(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando o total de vendas (R$) por vendedor e por dia
    de fim de semana, agrupadas por status (Aguardando, Aprovada, Faturado), com base em data_real.

    Retorna:
        str: HTML do gráfico Plotly empilhado pronto para embutir (via pio.to_html).
    """
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    proximo_mes = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)

    vendedores_ativos = list(usuarios_collection.find(
        {'status': {'$in': ['ativo', 'bloqueado']}},
        {'_id': 0, 'nome_completo': 1}
    ))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    pipeline = [
        {
            "$addFields": {
                "data_real_dt": { "$toDate": "$data_real" },
                "valor_numerico": {
                    "$convert": {
                        "input": {
                            "$replaceOne": {
                                "input": "$valor_real",
                                "find": ",",
                                "replacement": "."
                            }
                        },
                        "to": "double",
                        "onError": 0,
                        "onNull": 0
                    }
                },
                "dia_semana": { "$dayOfWeek": { "$toDate": "$data_real" } }
            }
        },
        {
            "$match": {
                "data_real_dt": { "$gte": primeiro_dia, "$lt": proximo_mes },
                "status": { "$in": ["Aguardando", "Aprovada", "Faturado"] },
                "vendedor": { "$in": nomes_ativos },
                "dia_semana": { "$in": [1, 7] }
            }
        },
        {
            "$group": {
                "_id": {
                    "dia": { "$dayOfMonth": "$data_real_dt" },
                    "mes": { "$month": "$data_real_dt" },
                    "ano": { "$year": "$data_real_dt" },
                    "vendedor": "$vendedor",
                    "status": "$status"
                },
                "total": { "$sum": "$valor_numerico" }
            }
        },
        {
            "$sort": SON([
                ("_id.ano", 1),
                ("_id.mes", 1),
                ("_id.dia", 1),
                ("_id.vendedor", 1),
                ("_id.status", 1)
            ])
        }
    ]

    resultados = list(vendas_collection.aggregate(pipeline))

    if not resultados:
        fig = go.Figure()
        fig.update_layout(
            title="Vendas por Status no Fim de Semana (por Vendedor)",
            xaxis_title="Vendedor / Dia",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Organização: {status: {vendedor_dia: total}}
    dados = defaultdict(lambda: defaultdict(float))
    x_labels = set()

    for r in resultados:
        dia = f"{r['_id']['dia']:02d}/{r['_id']['mes']:02d}"
        vendedor = r['_id']['vendedor']
        status = r['_id']['status']
        chave = f"{vendedor} ({dia})"
        dados[status][chave] += r["total"]
        x_labels.add(chave)

    x_ordenado = sorted(x_labels, key=lambda x: x.split('(')[-1])

    status_ordem = ["Faturado", "Aprovada", "Aguardando"]
    cores = {
        "Faturado": "#8E44AD",
        "Aprovada": "#28a745",
        "Aguardando": "#FFA500"
    }

    fig = go.Figure()
    for status in status_ordem:
        valores = [dados[status].get(label, 0) for label in x_ordenado]
        fig.add_trace(go.Bar(
            x=x_ordenado,
            y=valores,
            name=status,
            marker_color=cores.get(status, None),
            text=[f"R$ {v:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') for v in valores],
            textposition="auto"
        ))

    fig.update_layout(
        title="Total de Vendas (R$) por Vendedor e Status (Fins de Semana)",
        xaxis_title="Vendedor / Dia",
        yaxis_title="Total (R$)",
        yaxis_tickprefix="R$ ",
        barmode="stack",
        height=500,
        margin=dict(l=40, r=20, t=50, b=40)
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

def gerar_grafico_quantidade_vendas_fim_de_semana(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas por vendedor mostrando a quantidade de vendas por status
    (Aguardando, Aprovada, Faturado) para cada dia de fim de semana (sábado ou domingo),
    considerando data_real e apenas vendedores ativos.

    Retorna:
        str: HTML do gráfico Plotly pronto para embutir (via pio.to_html).
    """
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    proximo_mes = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)

    # Busca vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    pipeline = [
        {
            "$addFields": {
                "data_real_dt": { "$toDate": "$data_real" },
                "dia_semana": { "$dayOfWeek": { "$toDate": "$data_real" } }
            }
        },
        {
            "$match": {
                "data_real_dt": { "$gte": primeiro_dia, "$lt": proximo_mes },
                "vendedor": { "$in": nomes_ativos },
                "status": { "$in": ["Aguardando", "Aprovada", "Faturado"] },
                "dia_semana": { "$in": [1, 7] }  # 1 = Domingo, 7 = Sábado
            }
        },
        {
            "$group": {
                "_id": {
                    "dia": { "$dayOfMonth": "$data_real_dt" },
                    "mes": { "$month": "$data_real_dt" },
                    "ano": { "$year": "$data_real_dt" },
                    "vendedor": "$vendedor",
                    "status": "$status"
                },
                "quantidade": { "$sum": 1 }
            }
        },
        {
            "$sort": SON([
                ("_id.ano", 1),
                ("_id.mes", 1),
                ("_id.dia", 1),
                ("_id.vendedor", 1),
                ("_id.status", 1)
            ])
        }
    ]

    resultados = list(vendas_collection.aggregate(pipeline))

    if not resultados:
        fig = go.Figure()
        fig.update_layout(
            title="Vendas por Status no Fim de Semana (por Vendedor)",
            xaxis_title="Vendedor / Dia",
            height=400
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    # Organização dos dados: {status: {vendedor_dia: quantidade}}
    dados = defaultdict(lambda: defaultdict(int))
    x_labels = set()

    for r in resultados:
        dia = f"{r['_id']['dia']:02d}/{r['_id']['mes']:02d}"
        vendedor = r['_id']['vendedor']
        status = r['_id']['status']
        chave = f"{vendedor} ({dia})"
        dados[status][chave] += r["quantidade"]
        x_labels.add(chave)

    x_ordenado = sorted(x_labels, key=lambda x: x.split('(')[-1])  # ordena por data dentro da label

    # Ordem desejada de status
    status_ordem = ["Faturado", "Aprovada", "Aguardando"]
    cores = {
        "Faturado": "#8E44AD",
        "Aprovada": "#28a745",
        "Aguardando": "#FFA500"
    }

    fig = go.Figure()
    for status in status_ordem:
        valores = [dados[status].get(label, 0) for label in x_ordenado]
        fig.add_trace(go.Bar(
            x=x_ordenado,
            y=valores,
            name=status,
            marker_color=cores.get(status, None),
            text=valores,
            textposition="auto"
        ))

    fig.update_layout(
        title="Status das Vendas por Vendedor (Fins de Semana)",
        xaxis_title="Vendedor / Dia",
        yaxis_title="Quantidade de Vendas",
        barmode="stack",
        height=500,
        margin=dict(l=40, r=20, t=50, b=40)
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})
