from flask import Blueprint, jsonify, request, session, redirect, render_template
from app.services import verificar_permissao_acesso, cadastrar_produto_service
from app.models import listar_produtos, produtos_collection

produtos_bp = Blueprint('produtos', __name__)

@produtos_bp.route('/produtos', methods=['GET', 'POST'])
def produtos():
    """
    Rota para exibição e cadastro de produtos.

    - GET: Renderiza a página de produtos com a lista atual.
    - POST: Cadastra um novo produto, validando código único.
      Aceita tanto JSON (via JS/AJAX) quanto dados de formulário.
    """
    user = session.get('user')
    if not user or not verificar_permissao_acesso(username=user.get('username')):
        return redirect('/index.html')

    if request.method == 'POST':
        # Força o Flask a tratar sempre como JSON se vier do JS
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form or {}

        codigo = data.get("codigo", "") or ''
        if not codigo:
            return jsonify({"success": False, "erro": "Produto não pode ser cadastrado sem código."}), 400

        # Verifica se já existe produto com o mesmo código
        if produtos_collection.find_one({"codigo": codigo}):
            return jsonify({"success": False, "erro": "Já existe um produto com este código."}), 400

        # Se as formas de pagamento já vierem em lista/dict (JSON via JS)
        if isinstance(data, dict) and 'formas_pagamento' in data:
            produto_data = {
                "codigo": codigo,
                "nome": data.get("nome"),
                "formas_pagamento": data.get("formas_pagamento")
            }
        else:
            # Monta as formas de pagamento a partir dos campos do formulário HTML
            formas = []
            for idx in range(1, 13):
                tipo = 'A/C' if idx == 1 else 'B/C'
                formas.append({
                    "tipo": tipo,
                    "valor_total": data.get(f"valor_total_{idx}", ""),
                    "parcelas": data.get(f"parcelas_{idx}", ""),
                    "valor_parcela": data.get(f"valor_parcela_{idx}", "")
                })
            produto_data = {
                "codigo": codigo,
                "nome": data.get("nome"),
                "formas_pagamento": formas
            }
        # Chama o serviço para cadastrar o produto no banco
        cadastrar_produto_service(produto_data)
        return jsonify({"success": True})

    # Se GET, retorna a página com a lista de produtos
    produtos = listar_produtos()
    return render_template('produtos.html', produtos=produtos)
