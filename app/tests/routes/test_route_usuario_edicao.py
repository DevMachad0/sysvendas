import pytest

@pytest.fixture
def usuario_mock():
    """Mock de usuário para edição."""
    return {
        "_id": "fakeid123",
        "username": "userteste",
        "nome_completo": "Usuário Teste",
        "nome": "Usuário Teste",
        "email": "teste@exemplo.com",
        "senha_email": "abc123",
        "fone": "11999999999",
        "pos_vendas": "pv1,pv2",
        "meta_mes": "10000",
        "tipo": "vendedor",
        "status": "ativo",
        "foto": "fotoemstringbase64",
    }

def test_usuario_edicao_post_salva_username_na_sessao(client):
    """POST salva username na sessão e retorna sucesso."""
    resp = client.post('/usuario_edicao', json={'username': 'userteste'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    # A session não é persistida aqui, então só testa o retorno

def test_usuario_edicao_get_sem_username_na_sessao(client):
    """GET sem username na sessão redireciona para /usuarios."""
    resp = client.get('/usuario_edicao')
    # Redireciona (302) para url_for('usuarios.usuarios')
    assert resp.status_code == 302
    assert '/usuarios' in resp.headers['Location']

def test_usuario_edicao_get_usuario_nao_encontrado(client, monkeypatch):
    """GET com username inexistente retorna 404 e mensagem adequada."""
    with client.session_transaction() as sess:
        sess['usuario_edicao_username'] = 'nao_existe'
    monkeypatch.setattr('app.routes.usuarioEdicao.usuarios_collection.find_one', lambda q: None)
    resp = client.get('/usuario_edicao')
    assert resp.status_code == 404
    assert "Usuário não encontrado" in resp.get_data(as_text=True)

def test_usuario_edicao_get_sucesso_renderiza_template(client, monkeypatch, usuario_mock):
    """GET com username válido preenche dados e renderiza o template."""
    with client.session_transaction() as sess:
        sess['usuario_edicao_username'] = usuario_mock["username"]
    monkeypatch.setattr('app.routes.usuarioEdicao.usuarios_collection.find_one', lambda q: usuario_mock)
    monkeypatch.setattr('app.routes.usuarioEdicao.usuarios_collection.find', lambda f, *a, **k: [{"username": "pv1", "nome_completo": "PV Um", "nome": "PV Um"}])
    # Mock dos gráficos individuais
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_vendas_vendedor_individual', lambda **k: "<div>grafico vendas</div>")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_banco_vendedor_individual', lambda **k: "<div>grafico banco</div>")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_metas_diarias_vendedor_individual', lambda **k: "<div>grafico meta diaria</div>")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_metas_semanais_vendedor_individual', lambda **k: "<div>grafico meta semana</div>")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_prazo_vendedor_individual', lambda **k: "<div>grafico prazo</div>")
    resp = client.get('/usuario_edicao')
    assert resp.status_code == 200
    # Confirma presença do template e dos gráficos no HTML renderizado
    assert "<div>grafico vendas</div>" in resp.get_data(as_text=True)
    assert "<div>grafico banco</div>" in resp.get_data(as_text=True)
    assert "<div>grafico meta diaria</div>" in resp.get_data(as_text=True)

def test_usuario_edicao_get_trata_foto_bytes(client, monkeypatch, usuario_mock):
    """GET trata corretamente o campo foto como bytes (gera base64)."""
    from base64 import b64encode
    usuario = usuario_mock.copy()
    usuario['foto'] = b'1234'
    with client.session_transaction() as sess:
        sess['usuario_edicao_username'] = usuario["username"]
    monkeypatch.setattr('app.routes.usuarioEdicao.usuarios_collection.find_one', lambda q: usuario)
    monkeypatch.setattr('app.routes.usuarioEdicao.usuarios_collection.find', lambda f, *a, **k: [])
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_vendas_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_banco_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_metas_diarias_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_metas_semanais_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_prazo_vendedor_individual', lambda **k: "")
    resp = client.get('/usuario_edicao')
    assert resp.status_code == 200
    # Checa se a base64 gerada aparece no HTML
    assert b64encode(b'1234').decode('utf-8') in resp.get_data(as_text=True)

def test_usuario_edicao_get_trata_foto_none(client, monkeypatch, usuario_mock):
    """GET trata corretamente o campo foto como None (string vazia)."""
    usuario = usuario_mock.copy()
    usuario['foto'] = None
    with client.session_transaction() as sess:
        sess['usuario_edicao_username'] = usuario["username"]
    monkeypatch.setattr('app.routes.usuarioEdicao.usuarios_collection.find_one', lambda q: usuario)
    monkeypatch.setattr('app.routes.usuarioEdicao.usuarios_collection.find', lambda f, *a, **k: [])
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_vendas_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_banco_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_metas_diarias_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_metas_semanais_vendedor_individual', lambda **k: "")
    monkeypatch.setattr('app.routes.usuarioEdicao.gerar_grafico_prazo_vendedor_individual', lambda **k: "")
    resp = client.get('/usuario_edicao')
    assert resp.status_code == 200

