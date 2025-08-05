from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template
from app.models import usuarios_collection
from datetime import datetime
from app.graficos import gerar_grafico_banco_vendedor_individual, gerar_grafico_metas_diarias_vendedor_individual, gerar_grafico_metas_semanais_vendedor_individual, gerar_grafico_prazo_vendedor_individual, gerar_grafico_vendas_vendedor_individual

usuario_edicao_bp = Blueprint('usuario_edicao', __name__)

@usuario_edicao_bp.route('/usuario_edicao', methods=['GET', 'POST'])
def usuario_edicao():
    """
    Rota de edição de usuário.

    - GET: Exibe o formulário de edição com os dados do usuário e gráficos individuais.
    - POST: Salva o username do usuário a ser editado na sessão e retorna status.

    Retorna a página de edição de usuário com os campos preenchidos e gráficos relacionados.
    """
    hoje = datetime.today()
    ano = request.args.get("ano", type=int) or hoje.year
    mes = request.args.get("mes", type=int) or hoje.month

    # Se for POST, salva username na sessão
    if request.method == 'POST':
        username = request.json.get('username') or request.form.get('username')
        session['usuario_edicao_username'] = username
        return jsonify({"success": True})

    # Busca username na sessão
    username = session.get('usuario_edicao_username')
    if not username:
        return redirect(url_for('usuarios.usuarios'))

    # Busca dados do usuário
    usuario = usuarios_collection.find_one({"username": username})
    if not usuario:
        return "Usuário não encontrado", 404

    # Monta os campos para o template
    usuario['_id'] = str(usuario.get('_id', ''))
    usuario['nome'] = usuario.get('nome_completo', '') or usuario.get('nome', '')
    usuario['username'] = usuario.get('username', '')
    usuario['email'] = usuario.get('email', '')
    usuario['senha_email'] = usuario.get('senha_email', '')
    usuario['contato'] = usuario.get('fone', '')
    usuario['pos_vendas'] = usuario.get('pos_vendas', '')
    usuario['meta_mes'] = usuario.get('meta_mes', '')
    usuario['tipo'] = usuario.get('tipo', '')
    usuario['status'] = usuario.get('status', '')

    # Corrige campo foto se necessário
    foto = usuario.get('foto', '')
    if isinstance(foto, bytes):
        import base64
        usuario['foto'] = base64.b64encode(foto).decode('utf-8')
    elif foto is None:
        usuario['foto'] = ''
    else:
        usuario['foto'] = str(foto)

    # Gera gráficos individuais do usuário
    grafico_vendas_vendedor_individual = gerar_grafico_vendas_vendedor_individual(ano=ano, mes=mes, username=usuario['username'])
    grafico_banco_vendedor_individual = gerar_grafico_banco_vendedor_individual(ano=ano, mes=mes, username=usuario['username'])
    grafico_metas_diarias_vendedor_individual = gerar_grafico_metas_diarias_vendedor_individual(username=usuario['username'])
    grafico_metas_semanais_vendedor_individual = gerar_grafico_metas_semanais_vendedor_individual(username=usuario['username'])
    grafico_prazo_vendedor_individual = gerar_grafico_prazo_vendedor_individual(username=usuario['username'])

    # Lista de usuários pós-vendas para dropdown/select
    pos_vendas_usuarios = list(usuarios_collection.find(
        {"tipo": "pos_vendas"},
        {"username": 1, "nome_completo": 1, "nome": 1}
    ))

    # Renderiza template com todos os dados necessários
    return render_template(
        'usuario_edicao.html',
        usuario=usuario,
        pos_vendas_usuarios=pos_vendas_usuarios,
        grafico_vendas_vendedor_individual=grafico_vendas_vendedor_individual,
        grafico_banco_vendedor_individual=grafico_banco_vendedor_individual,
        grafico_metas_diarias_vendedor_individual=grafico_metas_diarias_vendedor_individual,
        grafico_metas_semanais_vendedor_individual=grafico_metas_semanais_vendedor_individual,
        grafico_prazo_vendedor_individual=grafico_prazo_vendedor_individual
    )
