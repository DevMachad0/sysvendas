import pytest
from flask import Flask
from app.routes.apiExpedienteSabado import api_expediente_sabado_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_expediente_sabado_bp)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_expediente_sabado_trabalho_true(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.find_one",
        lambda filtro: {"tipo": "fim_expediente", "trabalho_sabado": True}
    )
    resp = client.get("/api/expediente_sabado")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["trabalho_sabado"] is True

def test_get_expediente_sabado_trabalho_false(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.find_one",
        lambda filtro: {"tipo": "fim_expediente", "trabalho_sabado": False}
    )
    resp = client.get("/api/expediente_sabado")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["trabalho_sabado"] is False

def test_get_expediente_sabado_nao_configurado(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.find_one",
        lambda filtro: None
    )
    resp = client.get("/api/expediente_sabado")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["trabalho_sabado"] is False

def test_post_expediente_sabado_true(monkeypatch, client):
    def update_one(filtro, update, upsert):
        assert filtro == {"tipo": "fim_expediente"}
        assert update["$set"]["trabalho_sabado"] is True
        assert upsert is True
        return None
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.update_one",
        update_one
    )
    resp = client.post("/api/expediente_sabado", json={"trabalho_sabado": True})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["trabalho_sabado"] is True

def test_post_expediente_sabado_false(monkeypatch, client):
    def update_one(filtro, update, upsert):
        assert filtro == {"tipo": "fim_expediente"}
        assert update["$set"]["trabalho_sabado"] is False
        assert upsert is True
        return None
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.update_one",
        update_one
    )
    resp = client.post("/api/expediente_sabado", json={"trabalho_sabado": False})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["trabalho_sabado"] is False

def test_post_expediente_sabado_padrao(monkeypatch, client):
    # Não manda o campo trabalho_sabado
    def update_one(filtro, update, upsert):
        assert update["$set"]["trabalho_sabado"] is False
        return None
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.update_one",
        update_one
    )
    resp = client.post("/api/expediente_sabado", json={})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["trabalho_sabado"] is False

def test_expediente_sabado_erro_banco_get(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.find_one",
        lambda filtro: (_ for _ in ()).throw(Exception("erro banco get"))
    )
    resp = client.get("/api/expediente_sabado")
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data

def test_expediente_sabado_erro_banco_post(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiExpedienteSabado.configs_collection.update_one",
        lambda *a, **kw: (_ for _ in ()).throw(Exception("erro banco post"))
    )
    resp = client.post("/api/expediente_sabado", json={"trabalho_sabado": True})
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data
