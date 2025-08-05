import pytest
from app.services import resetar_tentativas_login

def test_resetar_tentativas_login(monkeypatch):
    chamado = {}

    def fake_update_one(query, update):
        chamado["query"] = query
        chamado["update"] = update

    monkeypatch.setattr("app.services.usuarios_collection.update_one", fake_update_one)

    resetar_tentativas_login("joao")

    assert chamado["query"] == {"username": "joao"}
    assert chamado["update"] == {"$set": {"tentativas_login": 0}}
