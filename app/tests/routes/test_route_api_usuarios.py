import pytest
from flask import Flask
from bson import ObjectId
from app.routes.apiUsuarios import api_usuarios_bp

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test'
    app.register_blueprint(api_usuarios_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def build_usuario(_id, username, nome_completo, tipo, status, foto=None, pos_vendas=None):
    return {
        "_id": ObjectId() if not isinstance(_id, ObjectId) else _id,
        "username": username,
        "nome_completo": nome_completo,
        "tipo": tipo,
        "status": status,
        "foto": foto,
        "pos_vendas": pos_vendas,
    }

def test_get_usuarios_sem_filtro(monkeypatch, client):
    usuarios = [
        build_usuario("1", "joao", "João da Silva", "vendedor", "ativo"),
        build_usuario("2", "maria", "Maria Souza", "admin", "ativo"),
    ]
    monkeypatch.setattr("app.routes.apiUsuarios.usuarios_collection.find", lambda *a, **k: usuarios)
    resp = client.get("/api/usuarios")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    for item in data:
        assert "_id" in item and "nome" in item

def test_get_usuarios_com_filtro_nome(monkeypatch, client):
    usuarios = [
        build_usuario("3", "carlos", "Carlos Mendes", "vendedor", "ativo"),
    ]
    def fake_find(filtro, campos):
        assert "$or" in filtro
        return usuarios
    monkeypatch.setattr("app.routes.apiUsuarios.usuarios_collection.find", fake_find)
    resp = client.get("/api/usuarios?nome=Carlos")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["nome"] == "Carlos Mendes"

def test_get_usuarios_com_filtro_tipo(monkeypatch, client):
    usuarios = [
        build_usuario("4", "ana", "Ana Clara", "admin", "ativo"),
    ]
    def fake_find(filtro, campos):
        assert filtro.get("tipo") == "admin"
        return usuarios
    monkeypatch.setattr("app.routes.apiUsuarios.usuarios_collection.find", fake_find)
    resp = client.get("/api/usuarios?tipo=admin")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["tipo"] == "admin"

def test_get_usuarios_com_filtro_status(monkeypatch, client):
    usuarios = [
        build_usuario("5", "paulo", "Paulo Lima", "vendedor", "inativo"),
    ]
    def fake_find(filtro, campos):
        assert filtro.get("status") == "inativo"
        return usuarios
    monkeypatch.setattr("app.routes.apiUsuarios.usuarios_collection.find", fake_find)
    resp = client.get("/api/usuarios?status=inativo")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["status"] == "inativo"

def test_get_usuarios_filtro_composto(monkeypatch, client):
    usuarios = [
        build_usuario("6", "roberto", "Roberto Carlos", "vendedor", "ativo"),
    ]
    def fake_find(filtro, campos):
        assert "$or" in filtro and filtro.get("tipo") == "vendedor" and filtro.get("status") == "ativo"
        return usuarios
    monkeypatch.setattr("app.routes.apiUsuarios.usuarios_collection.find", fake_find)
    resp = client.get("/api/usuarios?nome=roberto&tipo=vendedor&status=ativo")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["nome"] == "Roberto Carlos"

def test_get_usuarios_erro_banco(monkeypatch, client):
    def fake_find(*a, **k): raise Exception("Erro banco")
    monkeypatch.setattr("app.routes.apiUsuarios.usuarios_collection.find", fake_find)
    resp = client.get("/api/usuarios")
    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data
    assert "banco" in data["error"].lower()
