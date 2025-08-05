import pytest
from flask import Flask
from app.routes.apiConfigsMetasVendedores import api_configs_metas_vendedores_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_configs_metas_vendedores_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_metas_vendedores_ok(monkeypatch, client):
    mock_metas = [
        {
            "tipo": "meta_vendedor",
            "vendedor_id": "1",
            "vendedor_nome": "Maria",
            "meta_dia_quantidade": 10,
            "meta_dia_valor": 2000,
            "meta_semana": 8000
        },
        {
            "tipo": "meta_vendedor",
            "vendedor_id": "2",
            "vendedor_nome": "João",
            "meta_dia_quantidade": 5,
            "meta_dia_valor": 1000,
            "meta_semana": 4000
        }
    ]
    monkeypatch.setattr("app.routes.apiConfigsMetasVendedores.consultar_metas_vendedores", lambda: mock_metas)
    resp = client.get("/api/configs/metas_vendedores")
    data = resp.get_json()
    assert resp.status_code == 200
    assert isinstance(data, list)
    assert data == mock_metas

def test_get_metas_vendedores_vazio(monkeypatch, client):
    monkeypatch.setattr("app.routes.apiConfigsMetasVendedores.consultar_metas_vendedores", lambda: [])
    resp = client.get("/api/configs/metas_vendedores")
    data = resp.get_json()
    assert resp.status_code == 200
    assert isinstance(data, list)
    assert data == []

def test_get_metas_vendedores_erro(monkeypatch, client):
    monkeypatch.setattr("app.routes.apiConfigsMetasVendedores.consultar_metas_vendedores", lambda: (_ for _ in ()).throw(Exception("Erro banco")))
    resp = client.get("/api/configs/metas_vendedores")
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data
    assert "Erro banco" in data["error"]
