from flask import Blueprint, jsonify
from app.models import usuarios_collection

api_vendedores_bp = Blueprint('api_vendedores', __name__)

@api_vendedores_bp.route('/api/vendedores')
def api_vendedores():
    """
    Endpoint que retorna uma lista de vendedores cadastrados (ativos e inativos).
    Permite que o admin escolha vendedores em cadastros ou filtros.

    Retorna:
        JSON com lista de vendedores (campos: _id, nome_completo, email, fone, status)
    """
    try:
        # Busca todos os usuários do tipo "vendedor" (case-insensitive)
        vendedores = list(usuarios_collection.find(
            {"tipo": {"$in": ["vendedor", "Vendedor"]}},
            {"_id": 1, "nome_completo": 1, "email": 1, "fone": 1, "status": 1}
        ))
        # Serializa o ObjectId para string
        for v in vendedores:
            v["_id"] = str(v["_id"])
        return jsonify(vendedores)
    except Exception as e:
        return jsonify({"error": str(e)}), 500