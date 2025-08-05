import pytest
from app.download import gerar_fig_vendas_geral

def test_fig_vendas_geral_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return []

    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_vendas_geral(lambda: 0, 2025, 7)
    assert fig.layout.title.text == "Meta Mensal"
    assert fig.layout.xaxis.title.text == "Sem dados de vendas"
    assert fig.layout.width == 1600
    assert fig.layout.height == 600
    assert len(fig.data) == 0 or (hasattr(fig.data[0], "x") and len(fig.data[0].x) == 0)

def test_fig_vendas_geral_com_dados(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Simula 2 vendas com valor total 8000
            return [{}, {}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{'meta_empresa': 10000}]
    def soma_vendas(lista):
        return 8000
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_vendas_geral(soma_vendas, 2025, 7)
    barras = fig.data
    # Deve ter duas barras: vendido e faltando
    assert len(barras) == 2
    vendido_bar = barras[0]
    faltando_bar = barras[1]
    # A barra vendida deve ser verde, faltando vermelha
    assert vendido_bar.marker.color == "green"
    assert faltando_bar.marker.color == "#c34323"
    # O texto deve aparecer corretamente
    assert "R$ 8.000,00" in vendido_bar.text[0] or "R$ 8,000.00" in vendido_bar.text[0]
    assert "R$ 2.000,00" in faltando_bar.text[0] or "R$ 2,000.00" in faltando_bar.text[0]
    # O eixo X deve mostrar o total vendido
    assert fig.layout.xaxis.title.text.startswith("R$")

def test_fig_vendas_geral_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Simula 2 vendas com valor total 8000
            return [{}, {}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{'meta_empresa': 10000}]
    def soma_vendas(lista):
        return 8000
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_vendas_geral(soma_vendas, 2025, 12)
    assert fig.layout.title.text.startswith("Meta Mensal")

def test_fig_vendas_geral_bateu_meta(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{}, {}, {}, {}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{'meta_empresa': 10000}]
    def soma_vendas(lista):
        return 12000
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_vendas_geral(soma_vendas, 2025, 7)
    barras = fig.data
    # O valor faltando deve ser 0 (não negativo)
    assert barras[1].x[0] == 0
    # O texto do vendido deve mostrar R$ 12.000,00
    assert "12" in barras[0].text[0]
    # O gráfico deve continuar empilhado
    assert fig.layout.barmode == 'stack'
