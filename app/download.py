# Importação das coleções (tabelas) do banco de dados MongoDB usadas no sistema
from app.models import usuarios_collection, vendas_collection, configs_collection, produtos_collection

# Importação dos principais módulos do Plotly para criação e manipulação de gráficos
import plotly.graph_objs as go  # Gráficos customizados com objetos (barras, linhas, etc)
import plotly.io as pio         # Manipulação de input/output de figuras Plotly
import plotly.express as px     # API de alto nível do Plotly para gráficos rápidos

# Pandas é utilizado para manipulação e análise de dados tabulares
import pandas as pd

# Módulos do Python para manipulação de arquivos e dados
import os     # Manipulação de caminhos, diretórios e arquivos
import json   # Leitura e escrita de arquivos JSON

# Ferramenta do BSON (formato do MongoDB) para ordenação de pipelines de agregação
from bson.son import SON

# Estrutura para criação de dicionários com valores padrão (ideal para contagem)
from collections import defaultdict

# Importa datetime e timedelta para manipulação de datas e períodos
from datetime import datetime, timedelta

# Função de serviço auxiliar para somar vendas (provavelmente soma valores de vendas filtradas)
from app.utils import soma_vendas


def gerar_fig_banco_vendedores(ano=None, mes=None):
    """
    Gera um gráfico de barras com o saldo do banco (limite) de cada vendedor,
    considerando as vendas faturadas no mês e eventuais descontos não autorizados.

    Parâmetros:
        ano (int, opcional): Ano de referência das vendas (padrão: ano atual).
        mes (int, opcional): Mês de referência das vendas (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura do Plotly com o gráfico de barras dos saldos dos vendedores.
    """
    # Define ano/mês do filtro, padrão é o mês/ano atual
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    # Define o primeiro e o último dia do mês consultado
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca vendas faturadas dentro do período filtrado
    vendas = list(vendas_collection.find(
        {'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes}, 'status': { '$in': ['Aprovada', 'Faturado'] }},
        {'_id': 0, 'vendedor': 1, 'valor_tabela': 1, 'valor_real': 1, 'desconto_autorizado': 1}
    ))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Saldo do Banco por Vendedor",
            xaxis_title="Sem dados de vendas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Busca limites atuais dos bancos dos vendedores
    banco = list(configs_collection.find(
        {'tipo': 'limite_vendedor'},
        {'_id': 0, 'vendedor_nome': 1, 'limite': 1}
    ))
    saldos_atuais = {b['vendedor_nome']: b['limite'] for b in banco}

    # Dicionário para calcular o impacto das vendas no banco de cada vendedor
    bancos_calculados = defaultdict(float)

    # Ajusta o saldo de cada vendedor conforme as vendas e descontos autorizados/não autorizados
    for venda in vendas:
        vendedor = venda['vendedor']
        valor_tabela = float(venda['valor_tabela'])
        valor_venda = float(venda['valor_real'])
        autorizado = venda.get('desconto_autorizado', False)

        diferenca = valor_venda - valor_tabela

        # Se houve desconto não autorizado, reduz o banco; se houve ganho, aumenta
        if diferenca < 0 and not autorizado:
            bancos_calculados[vendedor] -= abs(diferenca)
        elif diferenca > 0:
            bancos_calculados[vendedor] += diferenca

    resultado = []
    # Monta a lista final com saldo atual, calculado e novo de cada vendedor
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

    # Prepara os dados do gráfico
    x = [d['vendedor'] for d in resultado]
    y = [d['saldo_novo'] for d in resultado]
    cores = []
    textos = []

    # Define a cor da barra conforme o saldo novo
    for d in resultado:
        if d['saldo_novo'] < d['saldo_atual'] and d['saldo_novo'] > 0:
            cores.append("blue")
        elif d['saldo_novo'] > d['saldo_atual']:
            cores.append("green")
        elif d['saldo_novo'] <= 0:
            cores.append("red")
        textos.append(f"Saldo: R$ {d['saldo_novo']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))

    # Cria a figura de barras do Plotly
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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_vendas_geral(soma_vendas, ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando o valor total vendido no mês
    versus o valor que ainda falta para atingir a meta geral da empresa.

    Parâmetros:
        soma_vendas (callable): Função utilizada para somar o valor total das vendas faturadas.
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico da meta mensal geral.
    """
    # Define ano e mês de referência, usando atuais se não forem passados
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    # Define o primeiro e o último dia do mês consultado
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca todas as vendas faturadas no período
    vendas = list(vendas_collection.find(
        {'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes}, 'status': { '$in': ['Aprovada', 'Faturado'] }},
        {'_id': 0}
    ))
    # Busca a meta mensal geral da empresa (deve haver apenas um documento tipo 'geral')
    metas = list(configs_collection.find(
        {'tipo': 'geral'},
        {'_id': 0, 'meta_empresa': 1}
    ))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig
    
    # Calcula o total vendido e quanto falta para bater a meta
    total = soma_vendas(vendas)
    meta = float(metas[0]['meta_empresa'])
    vendido = total
    faltando = max(0, meta - total)  # Nunca retorna valor negativo

    # Cria gráfico de barras empilhadas: Vendido (verde), Faltando (vermelho)
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
        barmode='stack',   # Empilha as barras na horizontal
        title=f"Meta Mensal de {meta:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
        xaxis_title=f"R${total:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
        showlegend=True,
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_vendas_vendedor(soma_vendas, ano=None, mes=None):
    """
    Gera um gráfico de barras mostrando o total de vendas (em valor) por vendedor
    no mês e ano informados.

    Parâmetros:
        soma_vendas (callable): Função utilizada para somar o valor das vendas de cada vendedor.
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico de vendas por vendedor.
    """
    # Define ano e mês do filtro, padrão é o mês/ano atual
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    # Define o primeiro e o último dia do mês consultado
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca todas as vendas faturadas no período
    vendas = list(vendas_collection.find(
        {'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes}, 'status': { '$in': ['Aprovada', 'Faturado'] }},
        {'_id': 0}
    ))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Total de Vendas por Vendedor",
            xaxis_title="Sem dados",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Descobre todos os nomes únicos de vendedores nas vendas do período
    nomes = list(set(v['vendedor'] for v in vendas))
    totais = []

    # Calcula o total vendido por cada vendedor
    for vendedor in nomes:
        valores_vendedor = [v for v in vendas if v['vendedor'] == vendedor]
        total = soma_vendas(valores_vendedor)
        totais.append(total)

    # Cria o gráfico de barras, uma barra por vendedor
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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_vendas_diarias(ano=None, mes=None, data_escolhida=None):
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
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_status_vendas_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando a quantidade de vendas por status (Aguardando, Aprovada, Refazer, Cancelada, Faturado)
    para cada vendedor, no mês e ano informados.

    Parâmetros:
        ano (int, opcional): Ano para o filtro (padrão: ano atual).
        mes (int, opcional): Mês para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico de barras empilhadas de status por vendedor.
    """
    # Define ano e mês do filtro, usando os atuais se não forem informados
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    # Define o primeiro e o último dia do mês consultado
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Pipeline de agregação MongoDB para agrupar quantidade de vendas por status para cada vendedor
    pipeline = [
        {
            "$addFields": {
                "data": {"$toDate": "$data_criacao"}  # Converte campo para data
            }
        },
        {
            "$match": {
                "data": {"$gte": primeiro_dia, "$lt": proximo_mes},
                "vendedor": {"$ne": ""},
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
                "quantidade": {"$sum": 1}  # Conta quantas vendas para cada status/vendedor
            }
        },
        {
            "$sort": SON([("_id.vendedor", 1), ("_id.status", 1)])
        }
    ]

    # Executa o pipeline de agregação
    resultados = list(vendas_collection.aggregate(pipeline))

    # Se não houver resultados, retorna gráfico vazio
    if not resultados:
        fig = go.Figure()
        fig.update_layout(
            title="Vendas por Status e Vendedor",
            xaxis_title="Sem dados",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Organiza os dados do pipeline em uma lista de dicionários
    dados = [
        {
            "vendedor": r["_id"]["vendedor"],
            "status": r["_id"]["status"],
            "quantidade": r["quantidade"]
        }
        for r in resultados
    ]

    # Cria DataFrame do pandas para facilitar manipulação dos dados
    df = pd.DataFrame(dados)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    df["vendedor"] = df["vendedor"].str.strip()
    df["status"] = df["status"].str.strip().str.capitalize()
    df["quantidade"] = pd.to_numeric(df["quantidade"]).astype(int)

    # Gera gráfico de barras empilhadas (com Plotly Express) agrupando por vendedor e status
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
        barmode="stack",  # Barras empilhadas
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )
    return fig


def gerar_fig_metas_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras horizontais empilhadas mostrando o progresso de vendas de cada vendedor
    em relação à sua meta mensal.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico do progresso de vendas por vendedor.
    """
    # Define ano e mês de referência (padrão: mês/ano atual)
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    # Define o primeiro e o último dia do mês consultado
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca vendas faturadas do período
    vendas = list(vendas_collection.find(
        {'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes}, 'status': { '$in': ['Aprovada', 'Faturado'] }},
        {'_id': 0, 'vendedor': 1, 'valor_real': 1, 'status': 1}
    ))

    # Busca metas mensais dos vendedores cadastrados
    metas = list(usuarios_collection.find(
        {'tipo': 'vendedor'},
        {'_id': 0, 'meta_mes': 1, 'nome_completo': 1}
    ))

    # Monta dicionário {nome_vendedor: meta_mensal}
    dict_metas = {}
    for vendedor in metas:
        dict_metas[vendedor['nome_completo']] = float(vendedor['meta_mes'])

    # Se não houver metas cadastradas, retorna gráfico vazio
    if not dict_metas:
        fig = go.Figure()
        fig.update_layout(
            title="Progresso de Vendas por Vendedor",
            xaxis_title="Sem metas cadastradas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Agrupa o total vendido por vendedor (desconsiderando vendas canceladas)
    totais = {}
    for venda in vendas:
        status = venda.get('status', '').strip()
        if status == 'Cancelada':
            continue
        vendedor = venda.get('vendedor', '').strip()
        valor = float(str(venda.get('valor_real', '0')).replace(',', '.'))
        if vendedor in dict_metas:
            totais[vendedor] = totais.get(vendedor, 0) + valor

    # Prepara listas para o gráfico
    vendedores = []
    vendidos = []
    faltando = []

    for vendedor, meta in dict_metas.items():
        vendido = totais.get(vendedor, 0)
        falta = max(0, meta - vendido)

        vendedores.append(vendedor)
        vendidos.append(vendido)
        faltando.append(falta)

    # Cria gráfico de barras horizontais empilhadas:
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
        barmode='stack',  # Barras empilhadas horizontalmente
        title="Progresso de Vendas por Vendedor",
        xaxis_title="Valor (R$)",
        yaxis_title="Vendedor",
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_metas_diarias_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de "mini-cards" (scatter) para cada vendedor, mostrando se bateu ou não a meta diária
    (em quantidade ou valor) em cada dia do mês.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com os mini-cards diários por vendedor.
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

    # Busca vendas faturadas do período
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] }
    }, {'_id': 0, 'vendedor': 1, 'valor_real': 1, 'data_criacao': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Metas Diárias dos Vendedores (Mini-Cards)<br><sup>Verde: meta batida (quantidade OU valor), Vermelho: não</sup>",
            xaxis_title="Sem metas cadastradas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Busca metas diárias de cada vendedor
    metas = list(configs_collection.find(
        {'tipo': 'meta_vendedor'},
        {'_id': 0, 'vendedor_nome': 1, 'meta_dia_quantidade': 1, 'meta_dia_valor': 1}
    ))
    vendedores = [v['vendedor_nome'] for v in metas]
    dict_metas = {
        v['vendedor_nome']: {
            'quantidade': int(v.get('meta_dia_quantidade', 5)),
            'valor': float(v.get('meta_dia_valor', 21000))
        } for v in metas
    }

    # Gera lista de todos os dias do mês no formato dd/mm
    dias_do_mes = [(primeiro_dia + pd.Timedelta(days=i)).strftime("%d/%m")
                   for i in range((proximo_mes - primeiro_dia).days)]

    # Inicializa estrutura para armazenar vendas de cada dia, por vendedor
    vendas_por_dia = {
        vendedor: {dia: {'qtd': 0, 'valor': 0.0} for dia in dias_do_mes}
        for vendedor in vendedores
    }

    # Preenche vendas_por_dia com a quantidade e o valor vendido em cada dia por cada vendedor
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

    # Monta os dados para o gráfico scatter de mini-cards
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
            bateu = (qtd >= meta_qtd) or (val >= meta_val)  # Considera meta batida se quantidade OU valor atingidos
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

    # Gera o gráfico (scatter plot) simulando mini-cards coloridos
    fig = go.Figure(data=go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=30,  # Tamanho dos mini-cards
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
        width=1600,
        margin=dict(l=20, r=20, t=60, b=60),
        font=dict(size=22)
    )

    return fig


def gerar_fig_metas_semanais_vendedor(ano=None, mes=None):
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
        return fig

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
        width=1600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60),
        legend_title_text='Legenda',
        barmode='group'
    )

    return fig

def gerar_fig_verdes_vermelhos_geral(ano=None, mes=None):
    """
    Gera um gráfico de pizza mostrando a proporção de clientes classificados como 'Verde' e 'Vermelho'
    entre as vendas faturadas do mês selecionado.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico de pizza da distribuição de clientes.
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

    # Busca vendas faturadas do período, trazendo só a classificação do cliente
    vendas = list(vendas_collection.find(
        {'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes}, 'status': { '$in': ['Aprovada', 'Faturado'] }},
        {'_id': 0, 'tipo_cliente': 1}
    ))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig
    
    # Conta quantos clientes são "Verde" e quantos são "Vermelho"
    total_verde = 0
    total_vermelho = 0
    for venda in vendas:
        status = venda.get('tipo_cliente', '').strip().capitalize()
        if status == 'Verde':
            total_verde += 1
        elif status == 'Vermelho':
            total_vermelho += 1

    # Se não houver nenhum cliente dessas categorias, retorna gráfico vazio
    if total_verde == 0 and total_vermelho == 0:
        fig = go.Figure()
        fig.update_layout(
            title="Distribuição de Clientes: Verde x Vermelho",
            xaxis_title="Sem dados",
            width=1600,
            height=600,
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Monta gráfico de pizza com a contagem de cada grupo
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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_verdes_vermelhos_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando, para cada vendedor,
    a quantidade de clientes classificados como 'Verde' e 'Vermelho' nas vendas faturadas do período.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico de barras empilhadas de clientes por vendedor.
    """
    # Define ano e mês do filtro, padrão é o mês/ano atual
    hoje = datetime.today()
    ano = ano or hoje.year
    mes = mes or hoje.month
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        proximo_mes = datetime(ano + 1, 1, 1)
    else:
        proximo_mes = datetime(ano, mes + 1, 1)

    # Busca vendas faturadas do período
    vendas = list(vendas_collection.find(
        {'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes}, 'status': { '$in': ['Aprovada', 'Faturado'] }},
        {'_id': 0, 'vendedor': 1, 'tipo_cliente': 1}
    ))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Dicionário: {vendedor: {"Verde": X, "Vermelho": Y}}
    contagem = {}

    # Conta quantos clientes verdes e vermelhos cada vendedor tem
    for venda in vendas:
        if venda.get('vendedor') == None or venda.get('tipo_cliente') == None:
            continue
        vendedor = venda.get('vendedor', '').strip()
        status = venda.get('tipo_cliente', '').strip().capitalize()

        # Ignora vendas sem vendedor ou sem status válido
        if vendedor == "" or status not in ["Verde", "Vermelho"]:
            continue

        if vendedor not in contagem:
            contagem[vendedor] = {"Verde": 0, "Vermelho": 0}

        contagem[vendedor][status] += 1

    # Se não houver nenhum vendedor com clientes, retorna gráfico vazio
    if not contagem:
        fig = go.Figure()
        fig.update_layout(
            title="Clientes Verdes x Vermelhos por Vendedor",
            xaxis_title="Sem dados",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Prepara dados para o gráfico
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
        barmode='stack',  # Barras empilhadas
        title="Clientes Verdes x Vermelhos por Vendedor",
        xaxis_title="Vendedor",
        yaxis_title="Quantidade de Vendas",
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_tipo_vendas_geral(ano=None, mes=None):
    """
    Gera um gráfico de pizza mostrando a proporção entre vendas novas e atualizações
    entre as vendas faturadas do mês selecionado.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico de pizza de tipos de vendas.
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

    # Busca vendas faturadas do mês, trazendo apenas o tipo do produto vendido
    vendas_mes = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] }
    }, {'_id': 0, 'produto': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas_mes:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Conta quantas vendas são novas e quantas são atualizações
    total_novas = 0
    total_atualizacoes = 0
    for venda in vendas_mes:
        if venda.get('produto') == None:
            continue
        produto = venda.get('produto', '')
        if not isinstance(produto, str):
            produto = str(produto) if produto is not None else ''
        produto = produto.strip().lower()
        if produto == "atualização" or produto == "atualizacao":
            total_atualizacoes += 1
        elif produto != '' or produto != None:
            total_novas += 1

    # Dados para o gráfico de pizza
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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_tipo_vendas_por_vendedor(ano=None, mes=None):
    """
    Gera um gráfico de barras empilhadas mostrando, para cada vendedor,
    a quantidade de vendas novas e de atualizações realizadas no mês selecionado.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o gráfico de barras empilhadas por vendedor e tipo de venda.
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

    # Busca vendas faturadas do mês, trazendo o vendedor e o tipo de produto
    vendas_mes = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] }
    }, {'_id': 0, 'produto': 1, 'vendedor': 1}))

    # Se não houver vendas, retorna gráfico vazio
    if not vendas_mes:
        fig = go.Figure()
        fig.update_layout(
            title="Meta Mensal",
            xaxis_title="Sem dados de vendas",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

    # Contadores por vendedor: {vendedor: {"novas": X, "atualizacoes": Y}}
    dados_vendedor = defaultdict(lambda: {'novas': 0, 'atualizacoes': 0})

    for venda in vendas_mes:
        if venda.get('produto') == None or venda.get('produto') == '':
            continue
        vendedor = venda.get('vendedor', 'Desconhecido')
        produto = venda.get('produto', '').strip().lower()

        if produto == "atualização":
            dados_vendedor[vendedor]['atualizacoes'] += 1
        else:
            dados_vendedor[vendedor]['novas'] += 1

    # Prepara os dados para o gráfico
    vendedores = list(dados_vendedor.keys())
    vendas_novas = [dados_vendedor[v]['novas'] for v in vendedores]
    atualizacoes = [dados_vendedor[v]['atualizacoes'] for v in vendedores]

    # Monta o gráfico de barras empilhadas
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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def gerar_fig_mapa_vendas_por_estado(ano=None, mes=None):
    """
    Gera um mapa coroplético (choropleth) do Brasil mostrando a quantidade de vendas faturadas
    por estado, considerando apenas vendedores ativos no mês/ano informados.

    Parâmetros:
        ano (int, opcional): Ano de referência para o filtro (padrão: ano atual).
        mes (int, opcional): Mês de referência para o filtro (padrão: mês atual).

    Retorna:
        plotly.graph_objs.Figure: Figura Plotly com o mapa de vendas por estado.
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

    # Busca nomes dos vendedores ativos
    vendedores_ativos = list(usuarios_collection.find({'status': {'$in': ['ativo', 'bloqueado']}}, {'_id': 0, 'nome_completo': 1}))
    nomes_ativos = [v['nome_completo'] for v in vendedores_ativos]

    # Busca vendas faturadas do período, apenas dos vendedores ativos
    vendas = list(vendas_collection.find({
        'data_criacao': {'$gte': primeiro_dia, '$lt': proximo_mes},
        'status': { '$in': ['Aprovada', 'Faturado'] },
        'vendedor': {'$in': nomes_ativos}
    }, {'_id': 0, 'endereco': 1}))

    # Mapeamento das siglas dos estados do Brasil (UF)
    estados_brasil = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia', 'CE': 'Ceará',
        'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso',
        'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    siglas_estados = set(estados_brasil.keys())

    # Conta quantas vendas foram realizadas em cada estado
    contagem_estados = defaultdict(int)
    for venda in vendas:
        estado = None
        endereco = venda.get('endereco', {})
        # Tenta extrair a sigla do estado do campo endereço
        if isinstance(endereco, dict):
            estado = endereco.get('estado', '').strip().upper()
        elif isinstance(endereco, str):
            estado = endereco.strip().upper()
        if estado in siglas_estados:
            contagem_estados[estado] += 1
        else:
            contagem_estados['Estrangeira'] += 1  # Contabiliza vendas para fora do Brasil (ou endereço não identificado)

    # Prepara listas de siglas e quantidade de vendas para o DataFrame
    estados = []
    vendas_estados = []
    for sigla in siglas_estados:
        estados.append(sigla)
        vendas_estados.append(contagem_estados.get(sigla, 0))

    vendas_estrangeiras = contagem_estados.get('Estrangeira', 0)

    # Cria DataFrame para o Plotly Express
    df = pd.DataFrame({
        'sigla': estados,
        'vendas': vendas_estados
    })

    # Carrega o GeoJSON dos estados brasileiros (utilizado para desenhar o mapa)
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        geojson_path = os.path.join(BASE_DIR, 'static', 'data', 'brazil-states.geojson')
        with open(geojson_path, encoding='utf-8') as f:
            geojson = json.load(f)
    except Exception  as e:
        print(f'Erro: {e}')
        geojson = {"type": "FeatureCollection", "features": []} 

    # Gera o mapa coroplético usando Plotly Express
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations='sigla',
        featureidkey='properties.sigla',  # Campo do GeoJSON correspondente à sigla do estado
        color='vendas',
        color_continuous_scale='Blues',  # Escala de cor azul
        range_color=(0, df['vendas'].max() if len(df) and df['vendas'].max() > 0 else 1),
        scope="south america",
        title="Vendas por Estado (Brasil)"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    # Adiciona anotação para vendas estrangeiras, caso existam
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

    return fig

def gerar_fig_prazo_vendas_vendedor(ano=None, mes=None):
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

    resultados = list(vendas_collection.aggregate(pipeline))

    if not resultados:
        df_vazio = pd.DataFrame(columns=["faixa_prazo", "quantidade"])
        fig = px.bar(
            data_frame=df_vazio,
            x="faixa_prazo",
            y="quantidade",
            title=f"Vendas por Prazo e Vendedor",
            labels={"quantidade": "Quantidade", "faixa_prazo": "Prazo (dias)"}
        )
        fig.update_layout(
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={"responsive": True})

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

    fig.update_layout(
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
        )
    return fig

def gerar_fig_produtos_mais_vendidos(ano=None, mes=None):
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

    # Remove produtos sem nenhuma venda faturadas, se quiser mostrar só os vendidos
    dados = [
        {"produto": nome, "quantidade": qtde}
        for nome, qtde in contagem_produtos.items() if qtde > 0
    ]

    # Se quiser mostrar TODOS os produtos, mesmo com zero vendas, troque o if acima por: if True

    # Se não houver vendas faturadas, retorna gráfico vazio
    if not dados:
        fig = go.Figure()
        fig.update_layout(
            title="Produtos mais Vendidos",
            xaxis_title="Quantidade",
            yaxis_title="Produto",
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig

def gerar_fig_vendas_diarias_linhas(ano=None, mes=None):
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
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

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
        textfont=dict(size=12)
    ))

    fig.update_layout(
        title="Vendas por Dia do Mês",
        xaxis_title="Dia",
        yaxis_title="Total de Vendas (R$)",
        yaxis_tickprefix="R$ ",
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    # Retorna HTML do gráfico para renderização web
    return fig

def gerar_fig_quantidade_vendas_diarias(ano=None, mes=None):
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
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

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
        textfont=dict(size=12)
    ))

    fig.update_layout(
        title="Quantidade de Vendas por Dia",
        xaxis_title="Dia",
        yaxis_title="Quantidade de Vendas",
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig

def gerar_fig_vendas_fim_de_semana(ano=None, mes=None):
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
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig

def gerar_fig_quantidade_vendas_fim_de_semana(ano=None, mes=None):
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
            width=1600,
            height=600,
            font=dict(size=30),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        return fig

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
        width=1600,
        height=600,
        font=dict(size=30),
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig
