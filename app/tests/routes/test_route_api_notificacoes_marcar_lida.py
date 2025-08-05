import pytest
from flask import Flask
from app.routes.apiNotificacoesMarcarLida import api_notificacoes_marcar_lida_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test'
    app.config['TESTING'] = True
    app.register_blueprint(api_notificacoes_marcar_lida_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_marcar_lida_sem_usuario(client):
    resp = client.post('/api/notificacoes/marcar_lida', json={'id': 'aaaa'})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['success'] is False

def test_marcar_lida_id_unico(monkeypatch, client):
    # Mock update_one
    result_called = {}
    def fake_update_one(filtro, update):
        result_called['ok'] = (filtro, update)
        class Fake: pass
        return Fake()
    monkeypatch.setattr(
        "app.routes.apiNotificacoesMarcarLida.notificacoes_collection.update_one",
        fake_update_one
    )

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'fulano'}

    resp = client.post('/api/notificacoes/marcar_lida', json={'id': '5f5b5f5b5f5b5f5b5f5b5f5b'})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['success'] is True
    # Garante que o filtro e update foram chamados corretamente
    assert result_called['ok'][1] == {'$addToSet': {'lida_por': 'fulano'}}

def test_marcar_lida_lista(monkeypatch, client):
    # Mock update_many
    called = {}
    def fake_update_many(filtro, update):
        called['filtro'] = filtro
        called['update'] = update
        class Fake: pass
        return Fake()
    monkeypatch.setattr(
        "app.routes.apiNotificacoesMarcarLida.notificacoes_collection.update_many",
        fake_update_many
    )

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'joana'}

    ids = ['5f5b5f5b5f5b5f5b5f5b5f5b', '6a6a6a6a6a6a6a6a6a6a6a6a']
    resp = client.post('/api/notificacoes/marcar_lida', json={'id': ids})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['success'] is True
    # Garante que o filtro está com os dois ObjectIds
    assert called['update'] == {'$addToSet': {'lida_por': 'joana'}}
    assert '$in' in called['filtro']['_id']
    assert len(called['filtro']['_id']['$in']) == 2

def test_marcar_lida_erro(monkeypatch, client):
    # Força um erro durante o update
    def fake_update_one(*a, **kw):
        raise Exception("Erro no banco")
    monkeypatch.setattr(
        "app.routes.apiNotificacoesMarcarLida.notificacoes_collection.update_one",
        fake_update_one
    )

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'xpto'}

    resp = client.post('/api/notificacoes/marcar_lida', json={'id': '5f5b5f5b5f5b5f5b5f5b5f5b'})
    data = resp.get_json()
    assert resp.status_code == 500
    assert 'error' in data
