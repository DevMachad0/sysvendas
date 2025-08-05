import pytest
from app.download import gerar_fig_vendas_fim_de_semana

def test_fig_vendas_fim_de_semana_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_fim_de_semana()
    import plotly.graph_objs as go
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text.startswith("Vendas por Status no Fim de Semana")
    assert fig.layout.xaxis.title.text.startswith("Vendedor")

def test_fig_vendas_fim_de_semana_um_status(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"dia": 6, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Faturado"}, "total": 10000.00}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_fim_de_semana()
    barras = [t for t in fig.data if t.type == "bar"]
    assert any(t.name == "Faturado" for t in barras)
    for t in barras:
        if t.name == "Faturado":
            assert "Maria (06/07)" in t.x
            assert 10000 in t.y or 10000.00 in t.y
    assert fig.layout.barmode == "stack"

def test_fig_vendas_fim_de_semana_varios_status(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"dia": 7, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Faturado"}, "total": 10000.00},
                {"_id": {"dia": 7, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Aprovada"}, "total": 5000.00},
                {"_id": {"dia": 7, "mes": 7, "ano": 2025, "vendedor": "João", "status": "Aguardando"}, "total": 8000.00}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_fim_de_semana()
    nomes = set()
    for t in fig.data:
        nomes.add(t.name)
        if t.name == "Faturado":
            assert any("Maria (07/07)" in t.x for _ in t.x)
            assert any(y in [10000, 10000.0] for y in t.y)
        if t.name == "Aprovada":
            assert any("Maria (07/07)" in t.x for _ in t.x)
            assert any(y in [5000, 5000.0] for y in t.y)
        if t.name == "Aguardando":
            assert any("João (07/07)" in t.x for _ in t.x)
            assert any(y in [8000, 8000.0] for y in t.y)
    assert nomes == {"Faturado", "Aprovada", "Aguardando"}

def test_fig_vendas_fim_de_semana_multiplos_dias(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"dia": 6, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Faturado"}, "total": 8000.00},
                {"_id": {"dia": 7, "mes": 7, "ano": 2025, "vendedor": "Maria", "status": "Faturado"}, "total": 9000.00}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_vendas_fim_de_semana()
    for t in fig.data:
        if t.name == "Faturado":
            assert "Maria (06/07)" in t.x
            assert "Maria (07/07)" in t.x
            assert 8000 in t.y or 8000.0 in t.y
            assert 9000 in t.y or 9000.0 in t.y
