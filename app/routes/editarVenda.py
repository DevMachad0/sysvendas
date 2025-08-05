from flask import Blueprint, jsonify, request, session, redirect, render_template, url_for
from app.services import verificar_permissao_acesso, dados_valores_venda
from app.models import vendas_collection
from bson import ObjectId

editar_venda_bp = Blueprint('editar_venda', __name__)

@editar_venda_bp.route('/editar_venda', methods=['GET', 'POST'])
def editar_venda():
    """
    Tela e endpoint para edição de uma venda.

    - GET: Renderiza o formulário de edição de venda com dados armazenados em sessão.
    - POST: Recebe o número da venda, busca no banco, serializa os campos (inclusive ObjectId),
      armazena na sessão e responde {"success": True} para o frontend.

    Detalhes:
    - Serializa ObjectId para string.
    - Serializa ObjectId dentro de dicts (ex: endereco) e dentro do array 'logs'.
    - Se não encontrar a venda, retorna erro 404.
    - Carrega info_vendas para uso nos selects e campos do template.
    """
    try:
        user = session.get('user')
        if not user or not verificar_permissao_acesso(username=user.get('username')):
            return redirect('/index.html')
        info_vendas = dados_valores_venda()
        

        if request.method == 'POST':
            numero_da_venda = request.json.get('numero_da_venda') or request.form.get('numero_da_venda')
            venda = vendas_collection.find_one({"numero_da_venda": numero_da_venda})
            if not venda:
                return jsonify({"success": False, "erro": "Venda não encontrada"}), 404

            # Serializa ObjectId e remove qualquer campo não serializável
            venda_serializada = {}
            for k, v in venda.items():
                if isinstance(v, ObjectId):
                    venda_serializada[k] = str(v)
                elif isinstance(v, dict):
                    # Serializa ObjectId dentro de dicts (ex: endereco)
                    venda_serializada[k] = {ik: (str(iv) if isinstance(iv, ObjectId) else iv) for ik, iv in v.items()}
                else:
                    venda_serializada[k] = v
            # Serializa logs se houver ObjectId dentro
            if 'logs' in venda_serializada and isinstance(venda_serializada['logs'], list):
                for log in venda_serializada['logs']:
                    for lk, lv in log.items():
                        if isinstance(lv, ObjectId):
                            log[lk] = str(lv)

            session['venda_edicao'] = venda_serializada
            return jsonify({"success": True})

        venda = session.get('venda_edicao')
        if not venda:
            return redirect(url_for('vendas.vendas'))
        # NOVO: passa o tipo de usuário para o template
        user = session.get('user', {})
        return render_template('editar_venda.html', venda=venda, info_vendas=info_vendas, user_tipo=user.get('tipo', ''))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
