from flask import Blueprint, request, jsonify
from app.services import is_sessao_bloqueada, autenticar_usuario
from app.models import usuarios_collection

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    """
    Rota para autenticação de usuários.

    Recebe credenciais (username e senha) via JSON ou form-data.
    Se autenticado, retorna um JSON com os dados do usuário.
    Caso contrário, retorna erro 401 com mensagem apropriada.
    """
    # Aceita tanto JSON quanto form-data
    data = request.json or request.form
    username = data.get('username')
    senha = data.get('senha')

    bloqueado, tempo = is_sessao_bloqueada()
    if bloqueado:
        return jsonify({
            "success": False,
            "message": f"Sua sessão foi bloqueada por tentativas inválidas. Aguarde {int(tempo // 60)} minutos e tente novamente."
        }), 401

    usuario = autenticar_usuario(username.lower().strip(), senha.strip())

    if isinstance(usuario, dict) and usuario.get("sessao_bloqueada"):
        tempo = usuario.get("tempo", 0)
        return jsonify({
            "success": False,
            "message": f"Sua sessão foi bloqueada por tentativas inválidas. Aguarde {int(tempo // 60)} minutos e tente novamente."
        }), 401

    if usuario:
        # Atualiza/corrige o campo permissa_acesso para "aceito" no login
        usuarios_collection.update_one(
            {"username": usuario.get("username")},
            {"$set": {"permissa_acesso": "aceito"}}
        )
        
        # Retorna dados do usuário autenticado (pode ser salvo no localStorage ou session)
        return jsonify({
            "success": True,
            "user": {
                "_id": str(usuario.get("_id")),
                "username": usuario.get("username"),
                "nome_vendedor": usuario.get("nome_completo"),
                "tipo": usuario.get("tipo"),
                "foto": usuario.get("foto"),
                "email": usuario.get("email"),
                "fone_vendedor": usuario.get("fone"),
                "pos_vendas": usuario.get("pos_vendas"),
                "meta_mes": usuario.get("meta_mes")
            }
        })
    else:
        # Busca usuário para verificar se está bloqueado
        usuario_db = usuarios_collection.find_one({"username": username.lower().strip()})
        if usuario_db and usuario_db.get("status") == "bloqueado":
            return jsonify({"success": False, "message": "Usuário bloqueado por tentativas inválidas. Contate o administrador."}), 401
        return jsonify({"success": False, "message": "Usuário ou senha inválidos ou usuário inativo."}), 401
