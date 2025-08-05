import pytest
from flask import Flask
from app.routes.apiProdutoDetalhe import api_produto_detalhe_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test'
    app.register_blueprint(api_produto_detalhe_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_produto_detalhe_existente(monkeypatch, client):
    # Produto mockado encontrado
    fake_produto = {
        "codigo": "PROD123",
        "nome": "Produto Teste",
        "preco": 100
    }
    def fake_find_one(filtro, proj):
        assert filtro == {"codigo": "PROD123"}
        return fake_produto
    monkeypatch.setattr(
        "app.routes.apiProdutoDetalhe.produtos_collection.find_one",
        fake_find_one
    )
    resp = client.get('/api/produto_detalhe/PROD123')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["codigo"] == "PROD123"
    assert data["nome"] == "Produto Teste"
    assert data["preco"] == 100

def test_produto_detalhe_nao_encontrado(monkeypatch, client):
    # Produto não existe
    def fake_find_one(filtro, proj):
        return None
    monkeypatch.setattr(
        "app.routes.apiProdutoDetalhe.produtos_collection.find_one",
        fake_find_one
    )
    resp = client.get('/api/produto_detalhe/INEXISTENTE')
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["erro"] == "Produto não encontrado"

def test_produto_detalhe_erro(monkeypatch, client):
    # Força erro inesperado
    def fake_find_one(*a, **k):
        raise Exception("Erro MongoDB")
    monkeypatch.setattr(
        "app.routes.apiProdutoDetalhe.produtos_collection.find_one",
        fake_find_one
    )
    resp = client.get('/api/produto_detalhe/QUALQUER')
    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data
    assert "Erro MongoDB" in data["error"]
