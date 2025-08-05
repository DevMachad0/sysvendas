from flask import Blueprint, jsonify, request
from app.models import usuarios_collection

api_usuarios_bp = Blueprint('api_usuarios', __name__)

@api_usuarios_bp.route('/api/usuarios')
def api_usuarios():
    """
    Endpoint que retorna uma lista de usuários cadastrados, permitindo filtro por nome, tipo e status via query string.

    Parâmetros GET opcionais:
        nome   - busca parcial por username ou nome_completo (case-insensitive)
        tipo   - filtra pelo tipo de usuário ('vendedor', 'admin', 'pos_vendas', etc)
        status - filtra por status do usuário ('ativo', 'inativo', etc)

    Retorna:
        JSON com lista de usuários, cada um com: _id, username, nome_completo, tipo, status, foto, pos_vendas, nome
    """
    try:
        # Recupera os filtros da query string
        nome = request.args.get('nome', '').strip()
        tipo = request.args.get('tipo', '').strip()
        status = request.args.get('status', '').strip()

        filtro = {}

        if nome:
            # Busca por username ou nome completo (insensitive)
            filtro['$or'] = [
                {'username': {'$regex': nome, '$options': 'i'}},
                {'nome_completo': {'$regex': nome, '$options': 'i'}}
            ]
        if tipo:
            filtro['tipo'] = tipo
        if status:
            filtro['status'] = status

        # Busca usuários no banco conforme o filtro
        usuarios = list(usuarios_collection.find(filtro, {
            "_id": 1,
            "username": 1,
            "nome_completo": 1,
            "tipo": 1,
            "status": 1,
            "foto": 1,
            "pos_vendas": 1
        }))
        # Serializa ObjectId e garante campo "nome" para o frontend
        for u in usuarios:
            u["_id"] = str(u["_id"])
            u["nome"] = u.get("nome_completo") or u.get("username") or ""
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({"error": str(e)}), 500