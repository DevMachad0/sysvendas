import pytest
from flask import Flask
from app.routes.apiListaProdutos import api_lista_produtos_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_lista_produtos_bp)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_api_lista_produtos_ok(monkeypatch, client):
    # Mocka retorno de produtos_collection
    fake_produtos = [
        {"codigo": "001", "nome": "Produto 1"},
        {"codigo": "002", "nome": "Produto 2"},
    ]
    monkeypatch.setattr(
        "app.routes.apiListaProdutos.produtos_collection.find",
        lambda *a, **kw: fake_produtos
    )
    resp = client.get("/api/lista_produtos")
    data = resp.get_json()
    assert resp.status_code == 200
    assert isinstance(data, list)
    assert data == fake_produtos

def test_api_lista_produtos_erro(monkeypatch, client):
    # Mock para lançar exceção
    monkeypatch.setattr(
        "app.routes.apiListaProdutos.produtos_collection.find",
        lambda *a, **kw: (_ for _ in ()).throw(Exception("Erro de banco"))
    )
    resp = client.get("/api/lista_produtos")
    data = resp.get_json()
    assert resp.status_code == 500
    assert "error" in data
    assert "Erro de banco" in data["error"]
