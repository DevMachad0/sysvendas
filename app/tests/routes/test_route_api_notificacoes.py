import pytest
from flask import Flask, session
from app.routes.apiNotificacoes import api_notificacoes_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "fake-key"
    app.register_blueprint(api_notificacoes_bp)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_api_notificacoes_sem_usuario(client):
    resp = client.get("/api/notificacoes")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data == []

def test_api_notificacoes_admin(monkeypatch, client):
    # Mock função de desligamento
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.desligar_permissao_acesso_usuarios",
        lambda: None
    )

    # Mock do cursor do MongoDB (simulando duas notificações, só uma não lida)
    class FakeCursor:
        def sort(self, *a, **kw): return self
        def limit(self, n): return [
            {"_id": 123, "envolvidos": ["admin"], "lida_por": [], "data_hora": __import__("datetime").datetime(2023, 7, 5, 9, 0)},
            {"_id": 124, "envolvidos": ["admin"], "lida_por": ["admin"], "data_hora": __import__("datetime").datetime(2023, 7, 4, 9, 0)},
        ]
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.notificacoes_collection.find",
        lambda filtro={}: FakeCursor()
    )

    # Setando sessão corretamente
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get("/api/notificacoes")
    data = resp.get_json()
    assert resp.status_code == 200
    assert isinstance(data, list)
    # Só uma notificação não lida
    assert len(data) == 1
    assert data[0]["_id"] == "123"

def test_api_notificacoes_vendedor(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.desligar_permissao_acesso_usuarios",
        lambda: None
    )
    class FakeCursor:
        def sort(self, *a, **kw): return self
        def limit(self, n): return [
            {"_id": 333, "envolvidos": ["joao"], "lida_por": [], "data_hora": __import__("datetime").datetime(2023, 7, 2, 9, 0)},
        ]
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.notificacoes_collection.find",
        lambda filtro={}: FakeCursor()
    )

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'joao', 'tipo': 'vendedor'}

    resp = client.get("/api/notificacoes")
    data = resp.get_json()
    assert resp.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["_id"] == "333"

def test_api_notificacoes_pos_vendas(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.desligar_permissao_acesso_usuarios",
        lambda: None
    )
    class FakeCursor:
        def sort(self, *a, **kw): return self
        def limit(self, n): return [
            {"_id": 333, "envolvidos": ["joao"], "lida_por": [], "data_hora": __import__("datetime").datetime(2023, 7, 2, 9, 0)},
        ]
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.notificacoes_collection.find",
        lambda filtro={}: FakeCursor()
    )

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'joao', 'tipo': 'pos_vendas'}

    resp = client.get("/api/notificacoes")
    data = resp.get_json()
    assert resp.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["_id"] == "333"

def test_api_notificacoes_outro(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.desligar_permissao_acesso_usuarios",
        lambda: None
    )
    class FakeCursor:
        def sort(self, *a, **kw): return self
        def limit(self, n): return [
            {"_id": 333, "envolvidos": ["joao"], "lida_por": [], "data_hora": __import__("datetime").datetime(2023, 7, 2, 9, 0)},
        ]
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.notificacoes_collection.find",
        lambda filtro={}: FakeCursor()
    )

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'joao', 'tipo': 'outro'}

    resp = client.get("/api/notificacoes")
    data = resp.get_json()
    assert resp.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["_id"] == "333"

def test_api_notificacoes_erro(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.desligar_permissao_acesso_usuarios",
        lambda: None
    )
    # Força erro ao chamar sort()
    class FakeCursor:
        def sort(self, *a, **kw):
            raise Exception("Falha BD")
    monkeypatch.setattr(
        "app.routes.apiNotificacoes.notificacoes_collection.find",
        lambda *a, **kw: FakeCursor()
    )

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get("/api/notificacoes")
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data
