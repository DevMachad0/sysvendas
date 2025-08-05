import pytest
from datetime import datetime
from app.services import registrar_notificacao

def test_registrar_notificacao_com_venda(monkeypatch):
    chamado = {}
    class FakeNotificacoesCollection:
        def insert_one(self, doc):
            chamado["doc"] = doc
    monkeypatch.setattr("app.services.notificacoes_collection", FakeNotificacoesCollection())

    venda = {"numero_da_venda": "20250711-01"}
    envolvidos = ["joao", "maria"]
    registrar_notificacao("venda", "Nova venda realizada!", venda=venda, envolvidos=envolvidos)
    
    doc = chamado["doc"]
    assert doc["tipo"] == "venda"
    assert doc["mensagem"] == "Nova venda realizada!"
    assert isinstance(doc["data_hora"], datetime)
    assert doc["lida_por"] == []
    assert doc["envolvidos"] == envolvidos
    assert doc["venda_numero"] == "20250711-01"

def test_registrar_notificacao_sem_venda_ou_envolvidos(monkeypatch):
    chamado = {}
    class FakeNotificacoesCollection:
        def insert_one(self, doc):
            chamado["doc"] = doc
    monkeypatch.setattr("app.services.notificacoes_collection", FakeNotificacoesCollection())

    registrar_notificacao("edicao", "Venda editada.")
    
    doc = chamado["doc"]
    assert doc["tipo"] == "edicao"
    assert doc["mensagem"] == "Venda editada."
    assert doc["lida_por"] == []
    assert doc["envolvidos"] == []
    assert doc["venda_numero"] is None
    assert isinstance(doc["data_hora"], datetime)
