import pytest

def test_usuarios_autenticado(client, monkeypatch):
    """Deve renderizar o template se usuário estiver autenticado e com permissão."""
    monkeypatch.setattr('app.routes.usuarios.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testuser'}
    resp = client.get('/usuarios')
    assert resp.status_code == 200
    assert b'usuarios.html' in resp.data or b'<!DOCTYPE html' in resp.data

def test_usuarios_sem_usuario_na_sessao(client):
    """Deve redirecionar para /index.html se não houver usuário na sessão."""
    resp = client.get('/usuarios', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/index.html')

def test_usuarios_sem_permissao(client, monkeypatch):
    """Deve redirecionar se o usuário NÃO tem permissão de acesso."""
    monkeypatch.setattr('app.routes.usuarios.verificar_permissao_acesso', lambda username: False)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testuser'}
    resp = client.get('/usuarios', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/index.html')

def test_usuarios_excecao(monkeypatch, client):
    """Se der erro inesperado ao verificar permissão, deve redirecionar."""
    def raise_erro(username):
        raise Exception("Erro de permissão!")
    monkeypatch.setattr('app.routes.usuarios.verificar_permissao_acesso', raise_erro)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testuser'}
    resp = client.get('/usuarios', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/index.html')
