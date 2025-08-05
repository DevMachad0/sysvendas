from flask import Blueprint, jsonify, request
from app.models import usuarios_collection
import bcrypt

atualizar_usuario_bp = Blueprint('atualizar_usuario', __name__)

@atualizar_usuario_bp.route('/atualizar_usuario', methods=['POST'])
def atualizar_usuario():
    """
    Atualiza os dados de um usuário cadastrado no sistema.

    Espera receber via POST (JSON ou form):
      - username (obrigatório)
      - Campos opcionais: nome, email, senha_email, contato, pos_vendas, meta_mes, tipo, status, senha, foto

    Regras:
      - Só permite atualizar para tipos válidos: admin, vendedor, pos_vendas, faturamento
      - Se senha for informada, faz hash e atualiza.
      - Foto pode ser enviada em base64 e substitui a anterior.
      - Atualiza todos os campos, mantendo os antigos se não forem enviados novos valores.

    Retorna:
      - {"success": True, "msg": "Usuário atualizado com sucesso!"} em caso de sucesso.
      - {"success": False, "erro": "..."} com código 400 ou 404 se houver erro.
    """
    data = request.json or request.form
    username = data.get('username')
    if not username:
        return jsonify({"success": False, "erro": "Username não informado"}), 400

    usuario = usuarios_collection.find_one({"username": username})
    if not usuario:
        return jsonify({"success": False, "erro": "Usuário não encontrado"}), 404

    # Tipos permitidos conforme cadastro
    tipos_permitidos = ["admin", "vendedor", "pos_vendas", "faturamento"]

    tipo = data.get('tipo', usuario.get('tipo', ''))
    if tipo not in tipos_permitidos:
        tipo = usuario.get('tipo', '')

    # Monta dicionário de atualização com fallback nos dados atuais
    update = {
        "nome_completo": data.get('nome', usuario.get('nome_completo', '')),
        "email": data.get('email', usuario.get('email', '')),
        "senha_email": data.get('senha_email', usuario.get('senha_email', '')),
        "fone": data.get('contato', usuario.get('fone', '')),
        "pos_vendas": data.get('pos_vendas', usuario.get('pos_vendas', '')),
        "meta_mes": data.get('meta_mes', usuario.get('meta_mes', '')),
        "tipo": tipo,
        "status": data.get('status', usuario.get('status', '')),
        "username": username
    }

    # Atualiza senha se enviada e não vazia
    senha = data.get('senha')
    if senha:
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        update['senha'] = senha_hash

    # Atualiza a foto se enviada (base64)
    if 'foto' in data and data.get('foto'):
        update['foto'] = data.get('foto')

    usuarios_collection.update_one({"username": username}, {"$set": update})

    return jsonify({"success": True, "msg": "Usuário atualizado com sucesso!"})
