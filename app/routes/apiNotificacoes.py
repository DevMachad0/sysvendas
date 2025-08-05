from flask import Blueprint, session, jsonify
from app.services import desligar_permissao_acesso_usuarios
from app.models import notificacoes_collection
from pymongo import DESCENDING

api_notificacoes_bp = Blueprint('api_notificacoes', __name__)

@api_notificacoes_bp.route('/api/notificacoes')
def api_notificacoes():
    """
    Retorna as notificações recentes NÃO lidas para o usuário logado.
    Também executa a rotina de desligar permissão de acesso dos usuários em horários definidos.
    """
    try:
        # --- Chama a rotina de desligamento de permissão de acesso a cada requisição ---
        desligar_permissao_acesso_usuarios()
        # --- Fim da rotina de desligamento ---

        user = session.get('user')
        if not user:
            return jsonify([])

        username = user.get('username')
        tipo = user.get('tipo')
        filtro = {}

        if tipo == 'admin':
            # Admin vê todas as notificações
            filtro = {}
        elif tipo == 'vendedor':
            filtro = {"envolvidos": username}
        elif tipo == 'pos_vendas':
            filtro = {"envolvidos": username}
        else:
            filtro = {"envolvidos": username}

        # Busca as notificações filtrando pelo tipo de usuário
        notificacoes = list(
            notificacoes_collection
            .find(filtro)
            .sort("data_hora", DESCENDING)
            .limit(20)
        )

        # Só retorna notificações não lidas por esse usuário
        notificacoes = [
            n for n in notificacoes if username not in n.get('lida_por', [])
        ]

        # Serializa ObjectId e datas para o frontend
        for n in notificacoes:
            n["_id"] = str(n["_id"])
            n["data_hora"] = n["data_hora"].strftime('%d/%m/%Y %H:%M')

        return jsonify(notificacoes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
