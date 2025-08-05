import pytest
from flask import Flask
from app.routes.apiConfigsLimitesVendedores import api_configs_limites_vendedores_bp

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(api_configs_limites_vendedores_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_limites_vendedores_ok(client, monkeypatch):
    # Simula retorno da função consultar_limites_vendedores
    fake_limites = [
        {
            "tipo": "limite_vendedor",
            "vendedor_id": "abc123",
            "vendedor_nome": "João da Silva",
            "limite": 10000
        },
        {
            "tipo": "limite_vendedor",
            "vendedor_id": "def456",
            "vendedor_nome": "Maria Souza",
            "limite": 12000
        }
    ]
    monkeypatch.setattr(
        "app.routes.apiConfigsLimitesVendedores.consultar_limites_vendedores",
        lambda: fake_limites
    )

    resp = client.get("/api/configs/limites_vendedores")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert data == fake_limites

def test_get_limites_vendedores_vazio(client, monkeypatch):
    # Simula retorno vazio
    monkeypatch.setattr(
        "app.routes.apiConfigsLimitesVendedores.consultar_limites_vendedores",
        lambda: []
    )
    resp = client.get("/api/configs/limites_vendedores")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == []

def test_get_limites_vendedores_erro(client, monkeypatch):
    def fake_raise():
        raise Exception("Erro de banco")
    monkeypatch.setattr(
        "app.routes.apiConfigsLimitesVendedores.consultar_limites_vendedores",
        fake_raise
    )
    resp = client.get("/api/configs/limites_vendedores")
    assert resp.status_code == 500
    assert resp.is_json
    data = resp.get_json()
    assert "error" in data
    assert "Erro de banco" in data["error"]

