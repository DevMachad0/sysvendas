import pytest
import pandas as pd
from app.download import gerar_fig_status_vendas_vendedor

def test_fig_status_vendas_vendedor_vazio(monkeypatch):
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_status_vendas_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text == "Vendas por Status e Vendedor"
    assert fig.layout.xaxis.title.text == "Sem dados"
    assert fig.layout.width == 1600
    assert fig.layout.height == 600
    assert len(fig.data) == 0 or (hasattr(fig.data[0], "x") and len(fig.data[0].x) == 0)

def test_fig_status_vendas_vendedor_um_vendedor_varios_status(monkeypatch):
    # Simula Maria com 1 venda Aguardando, 2 aprovadas e 1 Faturado
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"vendedor": "Maria", "status": "Aguardando"}, "quantidade": 1},
                {"_id": {"vendedor": "Maria", "status": "Aprovada"}, "quantidade": 2},
                {"_id": {"vendedor": "Maria", "status": "Faturado"}, "quantidade": 1},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_status_vendas_vendedor(ano=2025, mes=7)
    # Garante que as barras estejam lá e agrupadas corretamente
    todos_status = set()
    for bar in fig.data:
        todos_status.add(bar.name)
        if bar.name == "Aguardando":
            assert bar.marker.color == "#FFA500"
            assert sum(bar.y) == 1
        if bar.name == "Aprovada":
            assert bar.marker.color == "#28a745"
            assert sum(bar.y) == 2
        if bar.name == "Faturado":
            assert bar.marker.color == "#8E44AD"
            assert sum(bar.y) == 1
    assert todos_status >= {"Aguardando", "Aprovada", "Faturado"}
    assert fig.layout.title.text == "Vendas por Status e Vendedor"

def test_fig_status_vendas_vendedor_varios_vendedores(monkeypatch):
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"vendedor": "Maria", "status": "Faturado"}, "quantidade": 1},
                {"_id": {"vendedor": "João", "status": "Aguardando"}, "quantidade": 2},
                {"_id": {"vendedor": "João", "status": "Cancelada"}, "quantidade": 1},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_status_vendas_vendedor(ano=2025, mes=7)
    xlabels = set()
    for bar in fig.data:
        for v in bar.x:
            xlabels.add(v)
    assert xlabels == {"Maria", "João"}
    nomes = set(bar.name for bar in fig.data)
    assert nomes >= {"Aguardando", "Faturado", "Cancelada"}
    # Checa cores
    cores = {bar.name: bar.marker.color for bar in fig.data}
    assert cores["Cancelada"] == "#dc3545"
    assert cores["Aguardando"] == "#FFA500"
    assert cores["Faturado"] == "#8E44AD"

def test_fig_status_vendas_vendedor_um_vendedor_varios_status_dezembro(monkeypatch):
    # Simula Maria com 1 venda Aguardando, 2 aprovadas e 1 Faturado
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"vendedor": "Maria", "status": "Aguardando"}, "quantidade": 1},
                {"_id": {"vendedor": "Maria", "status": "Aprovada"}, "quantidade": 2},
                {"_id": {"vendedor": "Maria", "status": "Faturado"}, "quantidade": 1},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_status_vendas_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text == "Vendas por Status e Vendedor"

def test_fig_status_vendas_vendedor_varios_vendedores_dezembro(monkeypatch):
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"vendedor": "Maria", "status": "Faturado"}, "quantidade": 1},
                {"_id": {"vendedor": "João", "status": "Aguardando"}, "quantidade": 2},
                {"_id": {"vendedor": "João", "status": "Cancelada"}, "quantidade": 1},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_status_vendas_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text == "Vendas por Status e Vendedor"
    
def test_fig_status_vendas_vendedor_status_desconhecido(monkeypatch):
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"vendedor": "Maria", "status": "Desconhecido"}, "quantidade": 3}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_status_vendas_vendedor(ano=2025, mes=7)
    # Status não mapeado não ganha cor personalizada
    nomes = [bar.name for bar in fig.data]
    assert "Desconhecido" in nomes
    for bar in fig.data:
        if bar.name == "Desconhecido":
            # Plotly define cor padrão, não personalizada
            assert bar.marker.color is not None

