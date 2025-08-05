import pytest
from app.download import gerar_fig_vendas_diarias_linhas

def test_fig_vendas_diarias_linhas_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_diarias_linhas()
    import plotly.graph_objs as go
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text.startswith("Vendas por Dia do Mês")
    assert "Sem dados" in fig.layout.xaxis.title.text

def test_fig_vendas_diarias_linhas_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 1}, "total": 1000.0},
                {"_id": {"ano": 2025, "mes": 7, "dia": 2}, "total": 2345.5}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_diarias_linhas()
    linhas = fig.data[0]
    assert hasattr(linhas, "x")
    assert "01/07" in linhas.x
    assert "02/07" in linhas.x
    assert 1000.0 in linhas.y
    assert 2345.5 in linhas.y
    assert fig.layout.title.text.startswith("Vendas por Dia do Mês")
    assert fig.layout.xaxis.title.text == "Dia"

def test_fig_vendas_diarias_linhas_com_dados_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 1}, "total": 1000.0},
                {"_id": {"ano": 2025, "mes": 7, "dia": 2}, "total": 2345.5}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_diarias_linhas(mes=12)
    assert fig.layout.title.text.startswith("Vendas por Dia do Mês")

def test_fig_vendas_diarias_linhas_um_dia(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Único"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [{"_id": {"ano": 2025, "mes": 7, "dia": 3}, "total": 555.0}]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_diarias_linhas()
    linhas = fig.data[0]
    assert list(linhas.x) == ["03/07"]
    assert list(linhas.y) == [555.0]
    assert fig.layout.title.text.startswith("Vendas por Dia do Mês")

def test_fig_vendas_diarias_linhas_dias_nao_sequenciais(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 1}, "total": 10},
                {"_id": {"ano": 2025, "mes": 7, "dia": 15}, "total": 25},
                {"_id": {"ano": 2025, "mes": 7, "dia": 30}, "total": 40},
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_diarias_linhas()
    linhas = fig.data[0]
    assert "01/07" in linhas.x
    assert "15/07" in linhas.x
    assert "30/07" in linhas.x
    assert 40 in linhas.y
    assert fig.layout.title.text.startswith("Vendas por Dia do Mês")
