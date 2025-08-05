import pytest
from flask import Flask
from app.routes.apiConfigsVendedores import api_configs_vendedores_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_configs_vendedores_bp)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_vendedores_ok(monkeypatch, client):
    # Mock dos vendedores retornados do banco (ObjectId como int simulando string)
    vendedores_mock = [
        {"_id": 1, "nome_completo": "Alice"},
        {"_id": 2, "nome_completo": "Bob"},
    ]
    # Simula o find retornando os mocks acima
    monkeypatch.setattr(
        "app.routes.apiConfigsVendedores.usuarios_collection.find",
        lambda filtro, proj: vendedores_mock
    )
    resp = client.get("/api/configs/vendedores")
    data = resp.get_json()
    assert resp.status_code == 200
    assert type(data) is list
    assert data[0]["nome_completo"] == "Alice"
    assert isinstance(data[0]["_id"], str) or isinstance(data[0]["_id"], int)
    assert len(data) == 2

def test_get_vendedores_vazio(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.apiConfigsVendedores.usuarios_collection.find",
        lambda *a, **kw: []
    )
    resp = client.get("/api/configs/vendedores")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data == []

def test_get_vendedores_erro(monkeypatch, client):
    def _raise(*a, **kw): raise Exception("Erro banco vendedores")
    monkeypatch.setattr(
        "app.routes.apiConfigsVendedores.usuarios_collection.find",
        _raise
    )
    resp = client.get("/api/configs/vendedores")
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data
    assert "Erro banco vendedores" in data["error"]
