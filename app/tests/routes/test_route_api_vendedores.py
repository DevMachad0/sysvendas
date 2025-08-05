import pytest
from flask import Flask
from bson import ObjectId
from app.routes.apiVendedores import api_vendedores_bp

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = "test"
    app.register_blueprint(api_vendedores_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def build_vendedor(_id, nome, email, fone, status):
    return {
        "_id": ObjectId() if not isinstance(_id, ObjectId) else _id,
        "nome_completo": nome,
        "email": email,
        "fone": fone,
        "status": status,
    }

def test_get_vendedores_sucesso(monkeypatch, client):
    vendedores = [
        build_vendedor("1", "João Silva", "joao@email.com", "9999-0000", "ativo"),
        build_vendedor("2", "Maria Souza", "maria@email.com", "8888-0000", "inativo"),
    ]
    monkeypatch.setattr("app.routes.apiVendedores.usuarios_collection.find", lambda *a, **k: vendedores)
    resp = client.get("/api/vendedores")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    for v in data:
        assert "_id" in v and isinstance(v["_id"], str)
        assert "nome_completo" in v
        assert "email" in v
        assert "fone" in v
        assert "status" in v

def test_get_vendedores_erro_banco(monkeypatch, client):
    def fake_find(*a, **k): raise Exception("Falha no banco")
    monkeypatch.setattr("app.routes.apiVendedores.usuarios_collection.find", fake_find)
    resp = client.get("/api/vendedores")
    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data
    assert "banco" in data["error"].lower() or "falha" in data["error"].lower()
