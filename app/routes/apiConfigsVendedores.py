from flask import Blueprint, jsonify
from app.models import usuarios_collection

api_configs_vendedores_bp = Blueprint('api_configs_vendedores', __name__)

@api_configs_vendedores_bp.route('/api/configs/vendedores')
def api_configs_vendedores():
    """
    API para listar todos os vendedores ativos.

    Retorna uma lista de vendedores com os campos "_id" (como string) e "nome_completo".
    Apenas vendedores do tipo "vendedor" ou "Vendedor" são retornados.

    Retorno:
        JSON contendo a lista de vendedores.
    """
    try:
        # Busca todos os vendedores ativos do banco de dados
        vendedores = list(usuarios_collection.find(
            {"tipo": {"$in": ["vendedor", "Vendedor"]}},
            {"_id": 1, "nome_completo": 1}
        ))
        # Converte o ObjectId para string para ser serializável em JSON
        for v in vendedores:
            v["_id"] = str(v["_id"])
        return jsonify(vendedores)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
