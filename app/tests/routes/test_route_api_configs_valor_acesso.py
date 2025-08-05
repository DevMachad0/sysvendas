import pytest
from flask import Flask
from app.routes.apiConfigsValorAcesso import api_configs_valor_acesso_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_configs_valor_acesso_bp)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# ---------- GET ----------

def test_get_valor_acesso_ok(monkeypatch, client):
    mock_doc = {"valor_acesso_nova_venda": "123", "valor_acesso_atualizacao": "321"}
    monkeypatch.setattr(
        "app.routes.apiConfigsValorAcesso.configs_collection.find_one",
        lambda filtro, proj: mock_doc
    )
    resp = client.get("/api/configs/valor_acesso")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["valor_acesso_nova_venda"] == "123"
    assert data["valor_acesso_atualizacao"] == "321"

def test_get_valor_acesso_vazio(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiConfigsValorAcesso.configs_collection.find_one",
        lambda filtro, proj: None
    )
    resp = client.get("/api/configs/valor_acesso")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["valor_acesso_nova_venda"] == ""
    assert data["valor_acesso_atualizacao"] == ""

def test_get_valor_acesso_erro(monkeypatch, client):
    def _raise(*a, **kw): raise Exception("Falha mongo")
    monkeypatch.setattr(
        "app.routes.apiConfigsValorAcesso.configs_collection.find_one",
        _raise
    )
    resp = client.get("/api/configs/valor_acesso")
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data
    assert "Falha mongo" in data["error"]

# ---------- POST ----------

def test_post_valor_acesso_ok(monkeypatch, client):
    chamado = {}
    def mock_update_one(filtro, update, upsert=None):
        chamado["called"] = True
        assert filtro == {"tipo": "valor_acesso"}
        assert update["$set"]["valor_acesso_nova_venda"] == "789"
        assert update["$set"]["valor_acesso_atualizacao"] == "456"
        assert update["$set"]["tipo"] == "valor_acesso"
        return None
    monkeypatch.setattr(
        "app.routes.apiConfigsValorAcesso.configs_collection.update_one",
        mock_update_one
    )
    resp = client.post(
        "/api/configs/valor_acesso",
        json={"valor_acesso_nova_venda": "789", "valor_acesso_atualizacao": "456"}
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data == {"success": True}
    assert chamado.get("called") is True

def test_post_valor_acesso_vazio(monkeypatch, client):
    chamado = {}
    def mock_update_one(filtro, update, upsert=None):
        chamado["called"] = True
        assert filtro == {"tipo": "valor_acesso"}
        assert update["$set"]["valor_acesso_nova_venda"] == "0"
        assert update["$set"]["valor_acesso_atualizacao"] == "0"
        assert update["$set"]["tipo"] == "valor_acesso"
        return None
    monkeypatch.setattr(
        "app.routes.apiConfigsValorAcesso.configs_collection.update_one",
        mock_update_one
    )
    resp = client.post(
        "/api/configs/valor_acesso",
        json={"valor_acesso_nova_venda": "", "valor_acesso_atualizacao": ""}
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data == {"success": True}
    assert chamado.get("called") is True

def test_post_valor_acesso_erro(monkeypatch, client):
    def _raise(*a, **kw): raise Exception("Erro update")
    monkeypatch.setattr(
        "app.routes.apiConfigsValorAcesso.configs_collection.update_one",
        _raise
    )
    resp = client.post(
        "/api/configs/valor_acesso",
        json={"valor_acesso_nova_venda": "10", "valor_acesso_atualizacao": "11"}
    )
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data
    assert "Erro update" in data["error"]
