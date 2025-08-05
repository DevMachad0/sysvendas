from flask import Blueprint, session, jsonify, request
from app.models import notificacoes_collection
from bson import ObjectId

api_notificacoes_marcar_lida_bp = Blueprint('api_notificacoes_marcar_lida', __name__)

@api_notificacoes_marcar_lida_bp.route('/api/notificacoes/marcar_lida', methods=['POST'])
def api_notificacoes_marcar_lida():
    """
    Marca uma ou várias notificações como lidas pelo usuário logado.

    Espera:
        - id: pode ser uma string (ID único) ou uma lista de IDs (notificações a serem marcadas como lidas).

    Adiciona o username do usuário logado ao campo 'lida_por' da(s) notificação(ões).

    Retorna:
        - {"success": True} em caso de sucesso
        - {"success": False} se não houver usuário logado
    """
    try:
        user = session.get('user')
        if not user:
            return jsonify({"success": False})
        username = user.get('username')
        notif_ids = request.json.get('id')
        

        # Marca como lida, suportando tanto um único ID quanto uma lista de IDs
        if isinstance(notif_ids, list):
            notificacoes_collection.update_many(
                {"_id": {"$in": [ObjectId(i) for i in notif_ids]}},
                {"$addToSet": {"lida_por": username}}
            )
        else:
            notificacoes_collection.update_one(
                {"_id": ObjectId(notif_ids)},
                {"$addToSet": {"lida_por": username}}
            )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
