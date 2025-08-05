import pytest
from datetime import datetime, time as time_obj

from app.services import desligar_permissao_acesso_usuarios

def test_desliga_permissao_acesso_no_horario(monkeypatch):
    # Simula o horário EXATO da lista (ex: 19:30:05)
    class FakeDatetime(datetime):
        @classmethod
        def now(cls):
            return datetime(2025, 7, 10, 19, 30, 5)
    # Mocka a collection para checar se update foi chamado
    chamado = {}
    class FakeUsuariosCollection:
        def update_many(self, filtro, update):
            chamado["filtro"] = filtro
            chamado["update"] = update
            return "atualizado"

    monkeypatch.setattr("app.services.datetime", FakeDatetime)
    monkeypatch.setattr("app.services.usuarios_collection", FakeUsuariosCollection())
    
    resultado = desligar_permissao_acesso_usuarios()
    assert resultado is True
    # Checa que fez o update
    assert chamado["filtro"] == {"permissa_acesso": {"$ne": "desligado"}}
    assert chamado["update"] == {"$set": {"permissa_acesso": "desligado"}}

def test_desliga_permissao_acesso_fora_do_horario(monkeypatch):
    # Simula um horário que NÃO está na lista
    class FakeDatetime(datetime):
        @classmethod
        def now(cls):
            return datetime(2025, 7, 10, 19, 29, 59)
    chamado = {}
    class FakeUsuariosCollection:
        pass
    
    monkeypatch.setattr("app.services.datetime", FakeDatetime)
    monkeypatch.setattr("app.services.usuarios_collection", FakeUsuariosCollection())
    
    resultado = desligar_permissao_acesso_usuarios()
    assert resultado is False
    # Não deve chamar update_many
    assert "update" not in chamado
