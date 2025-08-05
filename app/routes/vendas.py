from flask import Blueprint, request, session, render_template, redirect, jsonify
from app.models import vendas_collection
from app.services import verificar_permissao_acesso
from datetime import datetime, date
from bson import ObjectId
from pymongo import DESCENDING

vendas_bp = Blueprint('vendas', __name__)

@vendas_bp.route('/vendas')
def vendas():
    """
    Rota de listagem de vendas, com filtros por perfil de usuário, busca e data.

    - Se for vendedor: mostra apenas as vendas do próprio usuário.
    - Se for pós-vendas: mostra as vendas em que está envolvido (campo 'posvendas' contém seu username).
    - Admin (ou outro): mostra todas as vendas (pode ser ajustado para mais perfis).

    Aceita filtros por busca (CNPJ/CPF ou nome do vendedor) e por data (YYYY-MM-DD).
    Agora aceita também data de início e fim para busca por período.

    Retorna a página 'vendas.html' renderizada com a lista de vendas filtrada.
    """
    try:
        user = session.get('user')
        if not user or not verificar_permissao_acesso(username=user.get('username')):
            return redirect('/index.html')

        busca = request.args.get('busca', '').strip()
        data_inicio = request.args.get('data_inicio', '').strip()
        data_fim = request.args.get('data_fim', '').strip()
        data = request.args.get('data', '').strip()  # compatibilidade com filtro antigo
        status_filtro = request.args.get('status', '').strip()  # NOVO: filtro por status

        filtro_base = {}

        # --- NOVO: Filtro padrão para o dia atual ---
        # Se ambos data_inicio e data_fim estão vazios e NÃO há parâmetro 'ver_todas', filtra pelo dia de hoje
        if not data_inicio and not data_fim and not request.args.get('ver_todas'):
            hoje = date.today()
            data_inicio = hoje.isoformat()
            data_fim = hoje.isoformat()
        # Se ambos data_inicio e data_fim estão vazios E há parâmetro 'ver_todas', mostra tudo (não filtra por data)
        # (Nada a fazer, filtro de data não será aplicado)

        # Filtro de acordo com o perfil do usuário
        if user.get('tipo') == 'vendedor':
            filtro_base['usuario_id'] = ObjectId(user.get('user_id', ''))
        elif user.get('tipo') == 'pos_vendas':
            username_pv = user.get('username', '')
            filtro_base['posvendas'] = {"$regex": r"(?:^|,)\s*%s\s*(?:,|$)" % username_pv}

        # Filtro por busca (CNPJ/CPF ou nome do vendedor ou nome do cliente ou número da venda)
        if busca:
            filtro_texto = {
                '$or': [
                    {'cnpj_cpf': {'$regex': busca, '$options': 'i'}},
                    {'vendedor': {'$regex': busca, '$options': 'i'}},
                    {'nome': {'$regex': busca, '$options': 'i'}},  # <-- Adicionado filtro por nome do cliente
                    {'numero_da_venda': {'$regex': busca, '$options': 'i'}}  # <-- NOVO: filtro por número da venda
                ]
            }
            if filtro_base:
                filtro_base = {'$and': [filtro_base, filtro_texto]}
            else:
                filtro_base = filtro_texto

        # Filtro por período (data_inicio e data_fim)
        filtro_periodo = None
        if data_inicio and data_fim:
            try:
                dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
                dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
                # Inclui o dia final inteiro
                dt_fim = dt_fim.replace(hour=23, minute=59, second=59)
                filtro_periodo = {
                    'data_criacao': {
                        '$gte': dt_inicio,
                        '$lte': dt_fim
                    }
                }
            except Exception:
                filtro_periodo = None
        elif data_inicio:
            try:
                dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
                # Se só data_inicio, filtra apenas aquele dia (das 00:00 até 23:59)
                dt_fim = dt_inicio.replace(hour=23, minute=59, second=59)
                filtro_periodo = {
                    'data_criacao': {
                        '$gte': dt_inicio,
                        '$lte': dt_fim
                    }
                }
            except Exception:
                filtro_periodo = None
        elif data_fim:
            filtro_periodo = None

        # Filtro por data única (formato antigo)
        filtro_data = None
        if data:
            try:
                data_obj = datetime.strptime(data, "%Y-%m-%d")
                filtro_data = {
                    'data_criacao': {
                        '$gte': datetime(data_obj.year, data_obj.month, data_obj.day),
                        '$lt': datetime(data_obj.year, data_obj.month, data_obj.day + 1)
                    }
                }
            except Exception:
                filtro_data = None

        # Monta filtro final
        if filtro_periodo:
            if filtro_base:
                filtro_base = {'$and': [filtro_base, filtro_periodo]}
            else:
                filtro_base = filtro_periodo
        elif filtro_data:
            if filtro_base:
                filtro_base = {'$and': [filtro_base, filtro_data]}
            else:
                filtro_base = filtro_data

        # Filtro por status (novo)
        if status_filtro:
            # Se já existe um $and, adiciona, senão cria
            if "$and" in filtro_base:
                filtro_base["$and"].append({"status": status_filtro})
            elif filtro_base:
                filtro_base = {"$and": [filtro_base, {"status": status_filtro}]}
            else:
                filtro_base = {"status": status_filtro}

        # Pós-vendas: filtra em Python por múltiplos usernames no campo 'posvendas'
        if user.get('tipo') == 'pos_vendas':
            todas_vendas = list(vendas_collection.find({}, {'_id': 0}))
            username_pv = user.get('username', '')
            vendas = []
            for venda in todas_vendas:
                posvendas = venda.get('posvendas', '')
                posvendas_list = [x.strip() for x in posvendas.split(',')] if posvendas else []
                if username_pv and username_pv in posvendas_list:
                    if not status_filtro or venda.get('status', '') == status_filtro:
                        vendas.append(venda)
            # Ordena em Python (mais novos primeiro)
            vendas = sorted(vendas, key=lambda v: v.get('data_criacao', ''), reverse=True)
            # Filtro de busca (em Python)
            if busca:
                vendas = [
                    v for v in vendas if
                    busca.lower() in (v.get('cnpj_cpf', '').lower()) or
                    busca.lower() in (v.get('vendedor', '').lower()) or
                    busca.lower() in (v.get('nome', '').lower()) or
                    busca.lower() in (str(v.get('numero_da_venda', '')).lower())  # <-- NOVO: filtro por número da venda
                ]
            # Filtro de período (em Python)
            if filtro_periodo:
                vendas = [
                    v for v in vendas
                    if 'data_criacao' in v and
                    isinstance(v['data_criacao'], datetime) and
                    v['data_criacao'] >= filtro_periodo['data_criacao'].get('$gte', datetime.min) and
                    v['data_criacao'] <= filtro_periodo['data_criacao'].get('$lte', datetime.max)
                ]
            # Filtro de data única (em Python)
            elif filtro_data:
                vendas = [
                    v for v in vendas
                    if 'data_criacao' in v and
                    hasattr(v['data_criacao'], 'date') and
                    v['data_criacao'].date() == data_obj.date()
                ]
        else:
            vendas = list(
                vendas_collection.find(filtro_base, {'_id': 0}).sort("data_criacao", DESCENDING)
            )

        return render_template(
            'vendas.html',
            vendas=vendas,
            status_lista=["Aguardando", "Aprovada", "Faturado", "Cancelada", "Refazer", "Finalizada"],
            status_filtro=status_filtro,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ver_todas=request.args.get('ver_todas', False)
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
