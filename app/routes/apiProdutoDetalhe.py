from flask import Blueprint, jsonify
from app.models import produtos_collection

api_produto_detalhe_bp = Blueprint('api_produto_detalhe', __name__)

@api_produto_detalhe_bp.route('/api/produto_detalhe/<codigo>')
def produto_detalhe(codigo):
    """
    Retorna os detalhes de um produto específico, identificado pelo código.

    Parâmetros:
        codigo (str): Código do produto a ser consultado (passado na URL).

    Retorno:
        - Sucesso: JSON com todos os campos do produto (exceto _id).
        - Erro: {"erro": "Produto não encontrado"}, com código HTTP 404.

    Observações:
        - Requer autenticação do usuário.
    """
    try:
        # Busca o produto pelo código, omitindo o campo "_id"
        produto = produtos_collection.find_one({"codigo": codigo}, {"_id": 0})

        # Se não encontrado, retorna erro
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        # Retorna os dados do produto em formato JSON
        return jsonify(produto)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
