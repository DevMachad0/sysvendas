from flask import Blueprint, session, redirect, render_template, request
from app.services import verificar_permissao_acesso, cadastrar_usuario
from app.models import usuarios_collection
import base64

cadastra_bp = Blueprint('cadastra', __name__)

@cadastra_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """
    Rota para cadastrar novos usuários no sistema.

    - GET: Exibe o formulário de cadastro.
    - POST: Processa o cadastro, incluindo upload de foto (base64) e seleção de usuários pós-vendas.
    """
    user = session.get('user')
    if not user or not verificar_permissao_acesso(username=user.get('username')):
        return redirect('/index.html')
    if request.method == 'POST':
        # Pega os dados do formulário como dicionário
        dados = request.form.to_dict(flat=True)
        foto_base64 = None
        # Se foi enviada uma foto, converte para base64
        if 'foto' in request.files and request.files['foto']:
            foto_file = request.files['foto']
            if foto_file.filename:
                foto_bytes = foto_file.read()
                foto_base64 = base64.b64encode(foto_bytes).decode('utf-8')
        # Ajusta pos_vendas: converte para string separada por vírgula, caso haja múltiplos
        pos_vendas = request.form.getlist('pos_vendas')
        if pos_vendas:
            dados['pos_vendas'] = ','.join(pos_vendas)
        else:
            dados['pos_vendas'] = ''
        # Chama o serviço para cadastrar o usuário
        cadastrar_usuario(dados, foto_base64)
        # Aqui você pode adicionar um flash('Usuário cadastrado!') ou redirect, se desejar

    # Busca usuários do tipo 'pos_vendas' para popular o select no formulário
    pos_vendas_usuarios = list(
        usuarios_collection.find(
            {"tipo": "pos_vendas"},
            {"username": 1, "nome_completo": 1, "nome": 1, "tipo": 1}
        )
    )
    # Renderiza o template de cadastro, passando os usuários pós-vendas para o select
    return render_template('cadastrar.html', pos_vendas_usuarios=pos_vendas_usuarios)
