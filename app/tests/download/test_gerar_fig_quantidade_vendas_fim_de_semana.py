import pytest
from app.download import gerar_fig_quantidade_vendas_fim_de_semana

def test_fig_quantidade_vendas_fim_de_semana_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_fim_de_semana()
    import plotly.graph_objs as go
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text.startswith("Vendas por Status") or fig.layout.title.text.startswith("Status das Vendas")
    assert fig.layout.xaxis.title.text.startswith("Vendedor")

def test_fig_quantidade_vendas_fim_de_semana_um_status(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"dia": 6, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Aprovada"}, "quantidade": 2}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_fim_de_semana()
    barras = [t for t in fig.data if t.type == "bar"]
    assert any(t.name == "Aprovada" for t in barras)
    for t in barras:
        if t.name == "Aprovada":
            assert "Maria (06/07)" in t.x
            assert 2 in t.y

def test_fig_quantidade_vendas_fim_de_semana_varios_status(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"dia": 6, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Faturado"}, "quantidade": 1},
                {"_id": {"dia": 6, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Aguardando"}, "quantidade": 3},
                {"_id": {"dia": 7, "mes": 7, "ano": 2025, "vendedor": "João", "status": "Aprovada"}, "quantidade": 2}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_fim_de_semana()
    nomes = set()
    for t in fig.data:
        nomes.add(t.name)
        if t.name == "Faturado":
            assert "Maria (06/07)" in t.x
            assert 1 in t.y
        if t.name == "Aguardando":
            assert "Maria (06/07)" in t.x
            assert 3 in t.y
        if t.name == "Aprovada":
            assert "João (07/07)" in t.x
            assert 2 in t.y
    assert nomes == {"Faturado", "Aprovada", "Aguardando"}

def test_fig_quantidade_vendas_fim_de_semana_multiplos_dias(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"dia": 6, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Faturado"}, "quantidade": 2},
                {"_id": {"dia": 7, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Faturado"}, "quantidade": 1}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_quantidade_vendas_fim_de_semana()
    for t in fig.data:
        if t.name == "Faturado":
            assert "Maria (06/07)" in t.x
            assert "Maria (07/07)" in t.x
            assert 2 in t.y
            assert 1 in t.y
