from flask import Blueprint, jsonify
from app.models import produtos_collection

api_lista_produtos_bp = Blueprint('api_lista_produtos', __name__)

@api_lista_produtos_bp.route('/api/lista_produtos')
def api_lista_produtos():
    """
    Rota de API para retornar a lista de produtos cadastrados.

    Retorna um JSON apenas com o código e o nome de cada produto,
    sem incluir o campo _id do MongoDB.
    Requer autenticação do usuário.
    """
    # Busca todos os produtos e retorna somente os campos 'codigo' e 'nome'
    try:
        produtos = list(produtos_collection.find({}, {"_id": 0, "codigo": 1, "nome": 1}))
        return jsonify(produtos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
