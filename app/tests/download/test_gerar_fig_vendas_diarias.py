import pytest
from datetime import datetime, timedelta
from app.download import gerar_fig_vendas_diarias

def test_fig_vendas_diarias_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_diarias(data_escolhida="2025-07-20")
    assert fig.layout.title.text.startswith("Total de Vendas por Vendedor")
    assert fig.layout.xaxis.title.text == "Sem dados"
    assert fig.layout.width == 1600
    assert fig.layout.height == 600
    assert len(fig.data) == 0 or (hasattr(fig.data[0], "x") and len(fig.data[0].x) == 0)

def test_fig_vendas_diarias_um_vendedor(monkeypatch):
    # O dia escolhido será 2025-07-20
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor': 'Maria', 'valor_real': '2500'},
                {'vendedor': 'Maria', 'valor_real': '200'},
            ]
    def soma_vendas(lista):
        return sum(float(v.get("valor_real", 0)) for v in lista)
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.soma_vendas", soma_vendas)
    fig = gerar_fig_vendas_diarias(data_escolhida="2025-07-20")
    bars = fig.data[0]
    assert bars.x[0] == "Maria"
    assert abs(float(bars.y[0]) - 2700) < 0.01
    assert bars.marker.color == "green"
    assert "R$ 2" in bars.text[0]  # Verifica formatação do texto
    assert fig.layout.title.text.endswith("20/07/2025)")

def test_fig_vendas_diarias_varios_vendedores(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor': 'Maria', 'valor_real': '800'},
                {'vendedor': 'João', 'valor_real': '1200'},
                {'vendedor': 'Maria', 'valor_real': '200'},
            ]
    def soma_vendas(lista):
        return sum(float(v.get("valor_real", 0)) for v in lista)
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.soma_vendas", soma_vendas)
    fig = gerar_fig_vendas_diarias(data_escolhida="2025-07-20")
    bars = fig.data[0]
    nomes = set(bars.x)
    assert nomes == {"Maria", "João"}
    idx_maria = bars.x.index("Maria")
    idx_joao = bars.x.index("João")
    assert abs(float(bars.y[idx_maria]) - 1000) < 0.01
    assert abs(float(bars.y[idx_joao]) - 1200) < 0.01
    assert bars.marker.color == "green"
    assert fig.layout.title.text.endswith("20/07/2025)")
    assert fig.layout.xaxis.title.text == "Vendedor"
    assert fig.layout.yaxis.title.text.startswith("Total de Vendas")

def test_fig_vendas_diarias_data_invalida(monkeypatch):
    """Se passar data_escolhida inválida, deve usar o dia atual."""
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_diarias(data_escolhida="data-errada")
    assert fig.layout.title.text.startswith("Total de Vendas por Vendedor")

def test_fig_vendas_diarias_data_vazia(monkeypatch):
    """Se passar data_escolhida inválida, deve usar o dia atual."""
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_vendas_diarias(data_escolhida="")
    assert fig.layout.title.text.startswith("Total de Vendas por Vendedor")

