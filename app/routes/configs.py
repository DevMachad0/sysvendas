from flask import Blueprint, session, render_template, redirect, jsonify
from app.services import verificar_permissao_acesso

configs_bp = Blueprint('configs', __name__)

@configs_bp.route('/configs', methods=['GET'])
def configs():
    """
    Rota para exibir a página de configurações gerais do sistema.

    Esta rota apenas renderiza o template 'configs.html'. 
    É necessário que o usuário esteja autenticado.

    Retorno:
        Template HTML 'configs.html'.
    """
    try:
        user = session.get('user')
        if not user or not verificar_permissao_acesso(username=user.get('username')):
            return redirect('/index.html')

        return render_template('configs.html')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
