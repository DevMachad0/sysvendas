from flask import Blueprint, jsonify, request
from app.models import usuarios_collection
from bson import ObjectId

usuario_edicao_dados_bp = Blueprint('usuario_edicao_dados', __name__)

@usuario_edicao_dados_bp.route('/usuario_edicao_dados', methods=['POST'])
def usuario_edicao_dados():
    """
    Recebe o ID de um usuário via requisição POST e retorna os dados do usuário em formato JSON.

    Esta rota é utilizada para buscar os dados completos de um usuário para exibição e edição
    no frontend. Caso o usuário não seja encontrado, retorna erro 404.

    Returns:
        JSON contendo os dados do usuário para edição ou mensagem de erro.
    """
    usuario_id = request.json.get('usuario_id')
    if not usuario_id:
        return jsonify({"success": False, "erro": "Usuário não cadastrado"}), 500

    usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    if not usuario:
        return jsonify({"success": False, "erro": "Usuário não encontrado"}), 404

    # Monta o dicionário do usuário para o frontend
    usuario['_id'] = str(usuario['_id'])
    usuario['nome'] = usuario.get('nome_completo', '') or usuario.get('nome', '')
    usuario['username'] = usuario.get('username', '')
    usuario['email'] = usuario.get('email', '')
    usuario['senha_email'] = usuario.get('senha_email', '')
    usuario['contato'] = usuario.get('fone', '')
    usuario['pos_vendas'] = usuario.get('pos_vendas', '')
    usuario['meta_mes'] = usuario.get('meta_mes', '')
    usuario['tipo'] = usuario.get('tipo', '')
    usuario['status'] = usuario.get('status', '')

    # Converte campos em bytes (ex: foto) para string base64
    import base64
    for k, v in list(usuario.items()):
        if isinstance(v, bytes):
            usuario[k] = base64.b64encode(v).decode('utf-8')
        elif v is None:
            usuario[k] = ''

    return jsonify({"success": True, "usuario": usuario})
