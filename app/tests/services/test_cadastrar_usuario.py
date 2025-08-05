import pytest

from app.services import cadastrar_usuario

def test_cadastrar_usuario_chama_criar_usuario(monkeypatch):
    # Dados de entrada simulados
    data = {
        "nome_completo": "João Teste",
        "username": "joaoteste",
        "email": "joao@teste.com",
        "senha": "abc123",
        "n_vendedor": "11999990000",
        "tipo": "admin",
        "pos_vendas": "Marina",
        "meta_mes": 5000
    }
    foto = "base64string"

    chamado = {}

    # Mock da função criar_usuario
    def fake_criar_usuario(**kwargs):
        chamado.update(kwargs)
        return "resultado_insert"

    # Faz monkeypatch
    monkeypatch.setattr("app.services.criar_usuario", fake_criar_usuario)

    retorno = cadastrar_usuario(data, foto=foto)

    # Checa se chamou criar_usuario com os dados corretos
    assert chamado["nome_completo"] == "João Teste"
    assert chamado["username"] == "joaoteste"
    assert chamado["email"] == "joao@teste.com"
    assert chamado["senha"] == "abc123"
    assert chamado["fone"] == "11999990000"
    assert chamado["tipo"] == "admin"
    assert chamado["foto"] == "base64string"
    assert chamado["pos_vendas"] == "Marina"
    assert chamado["meta_mes"] == 5000

    # Checa se retorna o resultado da função fake
    assert retorno == "resultado_insert"

def test_cadastrar_usuario_sem_foto(monkeypatch):
    data = {
        "nome_completo": "Maria",
        "username": "maria",
        "email": "maria@teste.com",
        "senha": "senha123",
        "n_vendedor": "11988887777",
        "tipo": "vendedor"
    }
    chamado = {}

    def fake_criar_usuario(**kwargs):
        chamado.update(kwargs)
        return "ok"

    monkeypatch.setattr("app.services.criar_usuario", fake_criar_usuario)

    retorno = cadastrar_usuario(data)  # Sem foto

    assert chamado["foto"] is None
    assert retorno == "ok"
