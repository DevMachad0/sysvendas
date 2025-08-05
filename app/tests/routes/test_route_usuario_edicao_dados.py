import pytest
from bson import ObjectId
import base64

@pytest.fixture
def usuario_id():
    return "60b8d2952f799d8128c80f01"

@pytest.fixture
def usuario_mongo(usuario_id):
    return {
        "_id": ObjectId(usuario_id),
        "nome_completo": "Fulano Teste",
        "username": "fulano",
        "email": "fulano@teste.com",
        "senha_email": "xpto123",
        "fone": "11999999999",
        "pos_vendas": "pv1",
        "meta_mes": "5000",
        "tipo": "vendedor",
        "status": "ativo",
        "foto": "fotostring"
    }

def test_usuario_edicao_dados_sucesso(client, monkeypatch, usuario_id, usuario_mongo):
    """POST retorna os dados do usuário para edição (com todos campos mapeados)."""
    # Mock find_one para retornar um dict igual ao mongo (inclusive _id é ObjectId)
    def fake_find_one(filtro):
        if filtro == {"_id": ObjectId(usuario_id)}:
            return usuario_mongo.copy()
        
    monkeypatch.setattr("app.routes.usuarioEdicaoDados.usuarios_collection.find_one", fake_find_one)

    resp = client.post("/usuario_edicao_dados", json={"usuario_id": usuario_id})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["usuario"]["_id"] == usuario_id
    assert data["usuario"]["nome"] == usuario_mongo["nome_completo"]
    assert data["usuario"]["username"] == usuario_mongo["username"]
    assert data["usuario"]["email"] == usuario_mongo["email"]
    assert data["usuario"]["contato"] == usuario_mongo["fone"]
    assert data["usuario"]["tipo"] == usuario_mongo["tipo"]
    assert data["usuario"]["status"] == usuario_mongo["status"]
    assert data["usuario"]["foto"] == usuario_mongo["foto"]

def test_usuario_edicao_dados_usuario_nao_encontrado(client, monkeypatch, usuario_id):
    """POST retorna 404 se usuário não for encontrado."""
    monkeypatch.setattr("app.routes.usuarioEdicaoDados.usuarios_collection.find_one", lambda f: None)
    resp = client.post("/usuario_edicao_dados", json={"usuario_id": usuario_id})
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False
    assert "Usuário não encontrado" in resp.get_json()["erro"]

def test_usuario_edicao_dados_foto_bytes(client, monkeypatch, usuario_id):
    """POST converte campo bytes em base64."""
    usuario = {
        "_id": ObjectId(usuario_id),
        "nome_completo": "Foto Bytes",
        "username": "userbytes",
        "email": "user@xpto.com",
        "senha_email": "senha",
        "fone": "111111111",
        "pos_vendas": "",
        "meta_mes": "",
        "tipo": "vendedor",
        "status": "ativo",
        "foto": b"foto_bytes"
    }
    def fake_find_one(filtro):
        return usuario.copy() if filtro == {"_id": ObjectId(usuario_id)} else None
    monkeypatch.setattr("app.routes.usuarioEdicaoDados.usuarios_collection.find_one", fake_find_one)
    resp = client.post("/usuario_edicao_dados", json={"usuario_id": usuario_id})
    assert resp.status_code == 200
    data = resp.get_json()
    base64_foto = base64.b64encode(b"foto_bytes").decode("utf-8")
    assert data["usuario"]["foto"] == base64_foto

def test_usuario_edicao_dados_campos_none(client, monkeypatch, usuario_id):
    """POST converte campos None para string vazia."""
    usuario = {
        "_id": ObjectId(usuario_id),
        "nome_completo": None,
        "username": "userteste",
        "email": None,
        "senha_email": None,
        "fone": None,
        "pos_vendas": None,
        "meta_mes": None,
        "tipo": None,
        "status": None,
        "foto": None
    }
    def fake_find_one(filtro):
        return usuario.copy() if filtro == {"_id": ObjectId(usuario_id)} else None
    monkeypatch.setattr("app.routes.usuarioEdicaoDados.usuarios_collection.find_one", fake_find_one)
    resp = client.post("/usuario_edicao_dados", json={"usuario_id": usuario_id})
    data = resp.get_json()
    for campo in ["nome", "email", "senha_email", "contato", "pos_vendas", "meta_mes", "tipo", "status", "foto"]:
        assert data["usuario"][campo] == ""

def test_usuario_edicao_dados_sem_usuario_id(client):
    """POST sem usuario_id dá erro 500 (KeyError no código real)."""
    resp = client.post("/usuario_edicao_dados", json={})
    # Como no código não há tratamento, ele vai levantar erro 500
    assert resp.status_code == 500 or resp.status_code == 400

