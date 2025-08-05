import pytest
from flask import Flask
from app.routes.atualizarUsuario import atualizar_usuario_bp
from bson import ObjectId

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test'
    app.register_blueprint(atualizar_usuario_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def build_usuario(username, tipo='vendedor'):
    return {
        "_id": ObjectId(),
        "username": username,
        "nome_completo": "Nome Original",
        "email": "old@mail.com",
        "senha_email": "oldsenha",
        "fone": "1111-1111",
        "pos_vendas": False,
        "meta_mes": "20000",
        "tipo": tipo,
        "status": "ativo",
        "foto": "data:image/jpg;base64,xxx"
    }

def test_update_usuario_sucesso(monkeypatch, client):
    usuario = build_usuario("joao")
    def fake_find_one(query):
        return usuario if query.get("username") == "joao" else None
    def fake_update_one(query, update):
        assert query == {"username": "joao"}
        assert update["$set"]["nome_completo"] == "Novo Nome"
        return None
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.find_one", fake_find_one)
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.update_one", fake_update_one)
    resp = client.post("/atualizar_usuario", json={
        "username": "joao",
        "nome": "Novo Nome",
        "tipo": "vendedor"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]
    assert "sucesso" in data["msg"].lower()

def test_update_usuario_sem_username(client):
    resp = client.post("/atualizar_usuario", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert not data["success"]
    assert "username" in data["erro"].lower()

def test_update_usuario_usuario_nao_encontrado(monkeypatch, client):
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.find_one", lambda q: None)
    resp = client.post("/atualizar_usuario", json={"username": "xpto"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert not data["success"]
    assert "não encontrado" in data["erro"].lower()

def test_update_usuario_tipo_invalido(monkeypatch, client):
    usuario = build_usuario("jose", tipo="vendedor")
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.find_one", lambda q: usuario)
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.update_one", lambda q, u: None)
    resp = client.post("/atualizar_usuario", json={
        "username": "jose",
        "tipo": "tipo_invalido"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]

def test_update_usuario_com_senha(monkeypatch, client):
    usuario = build_usuario("carla", tipo="vendedor")
    def fake_update_one(query, update):
        assert "senha" in update["$set"]
        assert isinstance(update["$set"]["senha"], bytes)
        return None
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.find_one", lambda q: usuario)
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.update_one", fake_update_one)
    resp = client.post("/atualizar_usuario", json={
        "username": "carla",
        "senha": "novasenha"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]

def test_update_usuario_foto_base64(monkeypatch, client):
    usuario = build_usuario("ana", tipo="vendedor")
    def fake_update_one(query, update):
        assert "foto" in update["$set"]
        assert update["$set"]["foto"].startswith("data:image")
        return None
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.find_one", lambda q: usuario)
    monkeypatch.setattr("app.routes.atualizarUsuario.usuarios_collection.update_one", fake_update_one)
    resp = client.post("/atualizar_usuario", json={
        "username": "ana",
        "foto": "data:image/png;base64,AAAA"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]
