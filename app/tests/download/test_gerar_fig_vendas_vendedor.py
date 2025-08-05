import pytest
from app.download import gerar_fig_vendas_vendedor

def test_fig_vendas_vendedor_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
        
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_vendedor(lambda: 0, 2025, 7)
    assert fig.layout.title.text == "Total de Vendas por Vendedor"
    assert fig.layout.xaxis.title.text == "Sem dados"
    assert fig.layout.width == 1600
    assert fig.layout.height == 600
    assert len(fig.data) == 0 or (hasattr(fig.data[0], "x") and len(fig.data[0].x) == 0)

def test_fig_vendas_vendedor_um_vendedor(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor': 'Maria', 'valor_real': '1000'},
                {'vendedor': 'Maria', 'valor_real': '1500'},
            ]
    def soma_vendas(lista):
        # Soma o campo valor_real, mesmo se string
        return sum(float(v.get("valor_real", 0)) for v in lista)
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_vendedor(soma_vendas, 2025, 7)
    bars = fig.data[0]
    assert len(bars.x) == 1
    assert bars.x[0] == "Maria"
    assert bars.marker.color == "green"
    assert abs(float(bars.y[0]) - 2500) < 0.01
    assert "R$ 2" in bars.text[0]

def test_fig_vendas_vendedor_varios_vendedores(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor': 'Maria', 'valor_real': '1000'},
                {'vendedor': 'João', 'valor_real': '700'},
                {'vendedor': 'Maria', 'valor_real': '250'},
            ]
    def soma_vendas(lista):
        return sum(float(v.get("valor_real", 0)) for v in lista)
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_vendedor(soma_vendas, 2025, 7)
    bars = fig.data[0]
    nomes = set(bars.x)
    assert nomes == {"Maria", "João"}
    # Checa se as quantidades batem
    idx_maria = bars.x.index("Maria")
    idx_joao = bars.x.index("João")
    assert abs(float(bars.y[idx_maria]) - 1250) < 0.01
    assert abs(float(bars.y[idx_joao]) - 700) < 0.01
    assert bars.marker.color == "green"
    assert fig.layout.title.text == "Total de Vendas por Vendedor"
    assert fig.layout.xaxis.title.text == "Vendedor"
    assert fig.layout.yaxis.title.text == "Total de Vendas (R$)"

def test_fig_vendas_vendedor_um_vendedor_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor': 'Maria', 'valor_real': '1000'},
                {'vendedor': 'Maria', 'valor_real': '1500'},
            ]
    def soma_vendas(lista):
        # Soma o campo valor_real, mesmo se string
        return sum(float(v.get("valor_real", 0)) for v in lista)
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_vendedor(soma_vendas, 2025, 12)
    assert fig.layout.title.text == "Total de Vendas por Vendedor"

def test_fig_vendas_vendedor_varios_vendedores_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor': 'Maria', 'valor_real': '1000'},
                {'vendedor': 'João', 'valor_real': '700'},
                {'vendedor': 'Maria', 'valor_real': '250'},
            ]
    def soma_vendas(lista):
        return sum(float(v.get("valor_real", 0)) for v in lista)
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_vendedor(soma_vendas, 2025, 12)
    assert fig.layout.title.text == "Total de Vendas por Vendedor"
