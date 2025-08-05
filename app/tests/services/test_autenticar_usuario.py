import pytest
from flask import session
import bcrypt

from app.services import autenticar_usuario

@pytest.fixture
def fake_usuario():
    senha_hash = bcrypt.hashpw("senha_correta".encode(), bcrypt.gensalt())
    return {
        "username": "joao",
        "senha": senha_hash,
        "status": "ativo"
    }

def test_autenticar_usuario_sucesso(app, monkeypatch, fake_usuario):
    # Mocks
    def fake_find_one(query):
        return fake_usuario

    def fake_checkpw(senha, senha_hash):
        return senha == b"senha_correta"

    def fake_resetar(username):
        session["resetou"] = username

    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)
    monkeypatch.setattr("app.services.bcrypt.checkpw", fake_checkpw)
    monkeypatch.setattr("app.services.resetar_tentativas_login", fake_resetar)

    with app.test_request_context():
        usuario = autenticar_usuario("joao", "senha_correta")
        assert usuario == fake_usuario
        # Tentativas zeradas
        assert "tentativas_login_sessao" not in session
        assert "resetou" in session
        
def test_autenticar_usuario_senha_errada(app, monkeypatch, fake_usuario):
    def fake_find_one(query):
        return fake_usuario

    def fake_checkpw(senha, senha_hash):
        return False

    def fake_incrementar(username):
        session["incrementou"] = username

    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)
    monkeypatch.setattr("app.services.bcrypt.checkpw", fake_checkpw)
    monkeypatch.setattr("app.services.incrementar_tentativas_login", fake_incrementar)

    with app.test_request_context():
        usuario = autenticar_usuario("joao", "errada")
        assert usuario is None
        assert session["incrementou"] == "joao"

def test_autenticar_usuario_inativo(app, monkeypatch, fake_usuario):
    usuario_inativo = fake_usuario.copy()
    usuario_inativo["status"] = "inativo"
    def fake_find_one(query):
        return usuario_inativo

    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)

    with app.test_request_context():
        usuario = autenticar_usuario("joao", "senha_correta")
        assert usuario is None

def test_autenticar_usuario_bloqueado(app, monkeypatch, fake_usuario):
    usuario_bloqueado = fake_usuario.copy()
    usuario_bloqueado["status"] = "bloqueado"
    def fake_find_one(query):
        return usuario_bloqueado

    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)

    with app.test_request_context():
        usuario = autenticar_usuario("joao", "senha_correta")
        assert usuario is None

def test_autenticar_usuario_nao_existe_sessao_bloqueada(app, monkeypatch):
    # Simula usuário não existente
    def fake_find_one(query):
        return None
    def fake_registrar_tentativa():
        return True, 120  # Sessão bloqueada, 2min restantes
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)
    monkeypatch.setattr("app.services.registrar_tentativa_sessao", fake_registrar_tentativa)

    with app.test_request_context():
        resp = autenticar_usuario("inexistente", "qualquer")
        assert resp["sessao_bloqueada"] is True
        assert resp["tempo"] == 120

def test_autenticar_usuario_nao_existe_incrementa_tentativas(app, monkeypatch):
    def fake_find_one(query):
        return None
    def fake_registrar_tentativa():
        return False, 0
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)
    monkeypatch.setattr("app.services.registrar_tentativa_sessao", fake_registrar_tentativa)

    with app.test_request_context():
        resp = autenticar_usuario("naoexiste", "qualquer")
        assert resp is None
        assert session["usuario_tentativa_login"] == "naoexiste"
