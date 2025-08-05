import pytest
from app.download import gerar_fig_quantidade_vendas_diarias

def test_fig_quantidade_vendas_diarias_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_diarias()
    import plotly.graph_objs as go
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text.startswith("Quantidade de Vendas por Dia")
    assert "Sem dados" in fig.layout.xaxis.title.text

def test_fig_quantidade_vendas_diarias_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 1}, "quantidade": 3},
                {"_id": {"ano": 2025, "mes": 7, "dia": 2}, "quantidade": 2}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_diarias()
    linhas = fig.data[0]
    assert hasattr(linhas, "x")
    assert "01/07" in linhas.x
    assert "02/07" in linhas.x
    assert 3 in linhas.y
    assert 2 in linhas.y
    assert fig.layout.title.text.startswith("Quantidade de Vendas por Dia")
    assert fig.layout.xaxis.title.text == "Dia"

def test_fig_quantidade_vendas_diarias_um_dia(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Único"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [{"_id": {"ano": 2025, "mes": 7, "dia": 10}, "quantidade": 7}]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_diarias()
    linhas = fig.data[0]
    assert list(linhas.x) == ["10/07"]
    assert list(linhas.y) == [7]
    assert fig.layout.title.text.startswith("Quantidade de Vendas por Dia")

def test_fig_quantidade_vendas_diarias_dias_nao_sequenciais(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 1}, "quantidade": 1},
                {"_id": {"ano": 2025, "mes": 7, "dia": 15}, "quantidade": 4},
                {"_id": {"ano": 2025, "mes": 7, "dia": 30}, "quantidade": 9},
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_diarias()
    linhas = fig.data[0]
    assert "01/07" in linhas.x
    assert "15/07" in linhas.x
    assert "30/07" in linhas.x
    assert 9 in linhas.y
    assert fig.layout.title.text.startswith("Quantidade de Vendas por Dia")
