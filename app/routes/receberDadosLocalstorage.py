from flask import Blueprint, request, jsonify, session

recebe_dados_ls_bp = Blueprint('recebe_dados_ls', __name__)

@recebe_dados_ls_bp.route('/receber-dados-localstorage', methods=['POST'])
def receber_dados_localstorage():
    """
    Rota para receber dados do usuário vindos do localStorage do frontend.

    Recebe um JSON via POST e armazena os dados na sessão do Flask (`session['user']`).
    Usado para persistência de dados do usuário autenticado entre páginas ou após login.
    """
    # Obtém o JSON enviado pelo frontend e salva na sessão do Flask
    session['user'] = request.get_json(silent=True)
    return jsonify({'status': 'ok'})
