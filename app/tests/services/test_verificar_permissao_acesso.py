import pytest
from app.services import verificar_permissao_acesso

def test_verificar_permissao_acesso_aceito(monkeypatch):
    # Mock do banco
    def fake_find_one(filtro, proj):
        return {"permissa_acesso": "aceito"}
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)

    assert verificar_permissao_acesso("joao") is True

def test_verificar_permissao_acesso_bloqueado(monkeypatch):
    def fake_find_one(filtro, proj):
        return {"permissa_acesso": "logo"}  # qualquer valor diferente de 'aceito'
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)

    assert verificar_permissao_acesso("joao") is False

def test_verificar_permissao_acesso_usuario_nao_existe(monkeypatch):
    def fake_find_one(filtro, proj):
        return None
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one)

    assert verificar_permissao_acesso("naoexiste") is False

def test_verificar_permissao_acesso_username_vazio(monkeypatch):
    
    assert verificar_permissao_acesso("") is False
