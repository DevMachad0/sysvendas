from flask import Blueprint, session, redirect, render_template
from app.services import verificar_permissao_acesso

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuarios')
def usuarios():
    """
    Rota para exibir a página de gerenciamento de usuários.

    Retorna:
        Renderiza o template 'usuarios.html' para visualização e administração dos usuários do sistema.
    """
    try:
        user = session.get('user')
        if not user or not verificar_permissao_acesso(username=user.get('username')):
            return redirect('/index.html')
        return render_template('usuarios.html')
    except Exception as e:
        return redirect('/index.html')
