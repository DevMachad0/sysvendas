import pytest
from collections import defaultdict
from datetime import datetime
from app.download import gerar_fig_tipo_vendas_por_vendedor

def test_fig_tipo_vendas_por_vendedor_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []

    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_por_vendedor()
    # Gráfico vazio: título correto, xaxis sem dados
    assert fig.layout.title.text.startswith("Meta Mensal")
    assert "Sem dados" in fig.layout.xaxis.title.text

def test_fig_tipo_vendas_por_vendedor_um_vendedor(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Um vendedor, duas vendas novas, uma atualização
            return [
                {"vendedor": "Carlos", "produto": "Produto X"},
                {"vendedor": "Carlos", "produto": "atualização"},
                {"vendedor": "Carlos", "produto": "produto y"}
            ]

    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_por_vendedor()
    # Deve ter duas barras para Carlos: 2 novas, 1 atualização
    assert fig.data[0].name == "Vendas Novas"
    assert fig.data[1].name == "Atualizações"
    idx = list(fig.data[0].x).index("Carlos")
    assert fig.data[0].y[idx] == 2  # novas
    assert fig.data[1].y[idx] == 1  # atualizacoes

def test_fig_tipo_vendas_por_vendedor_um_vendedor_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Um vendedor, duas vendas novas, uma atualização
            return [
                {"vendedor": "Carlos", "produto": "Produto X"},
                {"vendedor": "Carlos", "produto": "atualização"},
                {"vendedor": "Carlos", "produto": "produto y"}
            ]

    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_por_vendedor(mes=12)
    assert fig.layout.title.text.startswith('Vendas por Tipo')

def test_fig_tipo_vendas_por_vendedor_varios(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "produto": "produto abc"},
                {"vendedor": "Maria", "produto": "atualização"},
                {"vendedor": "João", "produto": "produto 1"},
                {"vendedor": "João", "produto": "produto 2"},
                {"vendedor": "João", "produto": "atualização"},
            ]

    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_por_vendedor()
    nomes = list(fig.data[0].x)
    assert set(nomes) == {"Maria", "João"}
    # Maria: 1 nova, 1 atualização; João: 2 novas, 1 atualização
    idx_maria = nomes.index("Maria")
    idx_joao = nomes.index("João")
    assert fig.data[0].y[idx_maria] == 1  # novas Maria
    assert fig.data[1].y[idx_maria] == 1  # atualizações Maria
    assert fig.data[0].y[idx_joao] == 2  # novas João
    assert fig.data[1].y[idx_joao] == 1  # atualizações João

def test_fig_tipo_vendas_por_vendedor_none_empty(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Casos estranhos: campo produto None ou em branco é considerado "nova"
            return [
                {"vendedor": "Fulano", "produto": None},
                {"vendedor": "Fulano", "produto": ""},
                {"vendedor": "Fulano"}  # faltando produto
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_por_vendedor()
    nomes = list(fig.data[0].x)
    assert nomes == []
