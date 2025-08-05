import pytest

from app.services import incrementar_tentativas_login

@pytest.fixture
def fake_usuarios_collection(monkeypatch):
    state = {}
    # Simula um banco de usuários: username -> dict
    usuarios = {
        "teste1": {"username": "teste1", "tentativas_login": 0, "status": "ativo"},
        "teste2": {"username": "teste2", "tentativas_login": 2, "status": "ativo"},
    }

    def fake_find_one(query):
        username = query.get("username")
        return usuarios.get(username)

    def fake_update_one(query, update):
        username = query.get("username")
        # Guarda o último update aplicado
        state["last_update"] = {"username": username, "update": update}
        # Aplica na base fake
        if username in usuarios:
            for k, v in update["$set"].items():
                usuarios[username][k] = v

    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)
    monkeypatch.setattr("app.services.usuarios_collection.update_one", fake_update_one)
    state["usuarios"] = usuarios
    return state

def test_incrementar_tentativas_incrementa(fake_usuarios_collection):
    incrementar_tentativas_login("teste1")
    # Checa que tentativas_login virou 1
    user = fake_usuarios_collection["usuarios"]["teste1"]
    assert user["tentativas_login"] == 1
    # Não bloqueia ainda
    assert user["status"] == "ativo"

def test_incrementar_tentativas_bloqueia(fake_usuarios_collection):
    incrementar_tentativas_login("teste2")
    # Checa que tentativas_login virou 3 e status "bloqueado"
    user = fake_usuarios_collection["usuarios"]["teste2"]
    assert user["tentativas_login"] == 3
    assert user["status"] == "bloqueado"

def test_incrementar_tentativas_usuario_nao_existe(fake_usuarios_collection):
    # Não deve fazer nada, pois usuário não existe
    incrementar_tentativas_login("inexistente")
    # last_update não muda
    assert "last_update" not in fake_usuarios_collection
