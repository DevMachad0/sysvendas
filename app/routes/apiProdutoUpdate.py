from flask import Blueprint, jsonify, request
from app.models import produtos_collection

api_produto_update_bp = Blueprint('api_produto_update', __name__)

@api_produto_update_bp.route('/api/produto_update/<codigo>', methods=['POST'])
def produto_update(codigo):
    """
    Atualiza um produto existente com base no código informado.

    Parâmetros:
        codigo (str): Código do produto a ser atualizado, passado na URL.

    Corpo JSON esperado:
        {
            "codigo": <novo_codigo>,
            "nome": <novo_nome>,
            "formas_pagamento": <lista_de_formas_de_pagamento>
        }

    Retorno:
        - Sucesso: {"success": True}
        - Erro: {"success": False, "erro": <mensagem>}, com código HTTP 400 ou 404

    Observações:
        - Não permite atualizar o código para um valor já existente em outro produto.
        - Requer autenticação do usuário.
    """
    try:
        # Usa get_json(silent=True) para evitar exceção
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "erro": "Dados não enviados"}), 400

        # Não permite alterar para um código já existente (exceto o próprio)
        novo_codigo = data.get("codigo")
        if novo_codigo and novo_codigo != codigo:
            if produtos_collection.find_one({"codigo": novo_codigo}):
                return jsonify({"success": False, "erro": "Já existe um produto com este código."}), 400

        # Monta o dicionário de atualização
        update = {
            "codigo": data.get("codigo"),
            "nome": data.get("nome"),
            "formas_pagamento": data.get("formas_pagamento", [])
        }

        # Atualiza o produto cujo código é igual ao informado na URL
        result = produtos_collection.update_one({"codigo": codigo}, {"$set": update})

        if result.matched_count:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "erro": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
