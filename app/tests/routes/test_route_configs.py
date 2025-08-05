import pytest

@pytest.fixture
def authenticated_session(client):
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

def test_configs_ok(client, monkeypatch, authenticated_session):
    # Mocka permissão como True no namespace correto!
    monkeypatch.setattr(
        'app.routes.configs.verificar_permissao_acesso',
        lambda username: True
    )
    resp = client.get('/configs')
    assert resp.status_code == 200
    assert b'configs' in resp.data or b'Configura' in resp.data  # palavra esperada do template

def test_configs_sem_permissao(client, monkeypatch, authenticated_session):
    # Mocka permissão como False
    monkeypatch.setattr(
        'app.routes.configs.verificar_permissao_acesso',
        lambda username: False
    )
    resp = client.get('/configs', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/index.html')

def test_configs_nao_autenticado(client, monkeypatch):
    # Não coloca user na sessão
    monkeypatch.setattr(
        'app.routes.configs.verificar_permissao_acesso',
        lambda username: True
    )
    resp = client.get('/configs', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/index.html')

def test_configs_erro_permissao(client, monkeypatch, authenticated_session):
    # Simula erro inesperado na permissão
    def raise_exception(username):
        raise Exception("erro inesperado!")
    monkeypatch.setattr(
        'app.routes.configs.verificar_permissao_acesso',
        raise_exception
    )
    resp = client.get('/configs', follow_redirects=False)
    # Se não tem handler, Flask retorna 500
    assert resp.status_code == 500
