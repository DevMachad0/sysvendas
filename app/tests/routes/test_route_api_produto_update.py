import pytest
from flask import Flask
from app.routes.apiProdutoUpdate import api_produto_update_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test'
    app.register_blueprint(api_produto_update_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_produto_update_ok(monkeypatch, client):
    """Atualiza produto normalmente"""
    class FakeResult:
        matched_count = 1
    def fake_find_one(filtro):
        # Não existe código duplicado
        return None
    def fake_update_one(filtro, update):
        return FakeResult()
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.find_one", fake_find_one)
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.update_one", fake_update_one)
    payload = {
        "codigo": "NOVO123",
        "nome": "Produto Teste Editado",
        "formas_pagamento": ["PIX", "Boleto"]
    }
    resp = client.post('/api/produto_update/PROD1', json=payload)
    assert resp.status_code == 200
    assert resp.get_json() == {"success": True}

def test_produto_update_codigo_ja_existe(monkeypatch, client):
    """Não permite código duplicado"""
    def fake_find_one(filtro):
        # Simula código já cadastrado em outro produto
        return {"codigo": "NOVO123"}
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.find_one", fake_find_one)
    payload = {"codigo": "NOVO123"}
    resp = client.post('/api/produto_update/VELHO', json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False
    assert "Já existe um produto com este código" in resp.get_json()["erro"]

def test_produto_update_codigo_igual(monkeypatch, client):
    """Permite atualizar mantendo o mesmo código"""
    class FakeResult:
        matched_count = 1
        
    def fake_update_one(filtro, update):
        return FakeResult()
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.find_one", lambda x: x)
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.update_one", fake_update_one)
    payload = {"codigo": "MESMO123", "nome": "A"}
    resp = client.post('/api/produto_update/MESMO123', json=payload)
    assert resp.status_code == 200
    assert resp.get_json() == {"success": True}

def test_produto_update_nao_encontrado(monkeypatch, client):
    """Produto não encontrado"""
    class FakeResult:
        matched_count = 0
        
    def fake_update_one(filtro, update):
        return FakeResult()
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.find_one", lambda x: x)
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.update_one", fake_update_one)
    payload = {"codigo": "NADA", "nome": "x"}
    resp = client.post('/api/produto_update/NADA', json=payload)
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False
    assert "Produto não encontrado" in resp.get_json()["erro"]

def test_produto_update_sem_body(client):
    """Dados não enviados"""
    resp = client.post('/api/produto_update/PROD', data={})  # Nenhum JSON/body
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False
    assert "Dados não enviados" in resp.get_json()["erro"]

def test_produto_update_erro_interno(monkeypatch, client):
    """Erro inesperado"""
    def fake_update_one(*a, **k):
        raise Exception("Falha DB")
    monkeypatch.setattr("app.routes.apiProdutoUpdate.produtos_collection.update_one", fake_update_one)
    payload = {"codigo": "X"}
    resp = client.post('/api/produto_update/X', json=payload)
    assert resp.status_code == 500
    assert "Falha DB" in resp.get_json()["error"]
