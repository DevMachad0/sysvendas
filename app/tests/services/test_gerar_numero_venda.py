import pytest
from datetime import datetime

from app.services import gerar_numero_venda

@pytest.fixture
def fake_vendas_collection(monkeypatch):
    class FakeVendasCollection:
        def __init__(self, ultima_venda):
            self.ultima_venda = ultima_venda
        def find_one(self, filtro, sort=None):
            return self.ultima_venda
    return FakeVendasCollection

def test_gerar_numero_venda_primeira(monkeypatch, fake_vendas_collection):
    # Fixa o datetime
    data_fixa = datetime(2025, 7, 7, 14, 0, 0)
    monkeypatch.setattr("app.services.datetime", type("FakeDateTime", (), {"now": staticmethod(lambda: data_fixa), "strftime": datetime.strftime}))

    # Mocka vendas_collection.find_one para retornar None (sem vendas no mês)
    vendas_mock = fake_vendas_collection(ultima_venda=None)
    monkeypatch.setattr("app.services.vendas_collection", vendas_mock)

    numero = gerar_numero_venda()
    assert numero == "2025070001"  # yyyymm0001 para Julho de 2025

def test_gerar_numero_venda_incrementa(monkeypatch, fake_vendas_collection):
    data_fixa = datetime(2025, 7, 7, 14, 0, 0)
    monkeypatch.setattr("app.services.datetime", type("FakeDateTime", (), {"now": staticmethod(lambda: data_fixa), "strftime": datetime.strftime}))

    # Já existe uma venda 2025070025, próxima tem que ser 2025070026
    vendas_mock = fake_vendas_collection(ultima_venda={"numero_da_venda": "2025070025"})
    monkeypatch.setattr("app.services.vendas_collection", vendas_mock)

    numero = gerar_numero_venda()
    assert numero == "2025070026"

def test_gerar_numero_venda_outro_mes(monkeypatch, fake_vendas_collection):
    # Para testar que sempre monta prefixo correto
    data_fixa = datetime(2025, 8, 10, 10, 0, 0)
    monkeypatch.setattr("app.services.datetime", type("FakeDateTime", (), {"now": staticmethod(lambda: data_fixa), "strftime": datetime.strftime}))

    vendas_mock = fake_vendas_collection(ultima_venda=None)
    monkeypatch.setattr("app.services.vendas_collection", vendas_mock)

    numero = gerar_numero_venda()
    assert numero == "2025080001"
