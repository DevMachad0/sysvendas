import pytest
import plotly.graph_objs as go
from app.download import gerar_fig_prazo_vendas_vendedor

def test_fig_prazo_vendas_vendedor_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Fulano"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    html = gerar_fig_prazo_vendas_vendedor()
    # Verifica que retorna Figure e o título padrão (vazio)
    assert isinstance(html, str) or isinstance(html, go.Figure)  # depende do include_plotlyjs
    if not hasattr(html, 'layout'):
        assert "Vendas por Prazo e Vendedor" in html

def test_fig_prazo_vendas_vendedor_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Maria tem 2 faixas, João tem só uma
            return [
                {"_id": {"vendedor": "Maria", "faixa_prazo": "≤ 30 dias"}, "quantidade": 2},
                {"_id": {"vendedor": "Maria", "faixa_prazo": "31-39 dias"}, "quantidade": 1},
                {"_id": {"vendedor": "João", "faixa_prazo": "50-150 dias"}, "quantidade": 3}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_prazo_vendas_vendedor()
    assert isinstance(fig, go.Figure)
    # Testa se todos vendedores aparecem no eixo X
    vendedores_plot = {x for trace in fig.data for x in getattr(trace, "x", [])}
    assert "Maria" in vendedores_plot
    assert "João" in vendedores_plot
    # Testa se as faixas esperadas aparecem no color axis
    faixas_usadas = set(trace.name for trace in fig.data if hasattr(trace, 'name'))
    assert "≤ 30 dias" in faixas_usadas or "31-39 dias" in faixas_usadas or "50-150 dias" in faixas_usadas

def test_fig_prazo_vendas_vendedor_com_dados_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Maria tem 2 faixas, João tem só uma
            return [
                {"_id": {"vendedor": "Maria", "faixa_prazo": "≤ 30 dias"}, "quantidade": 2},
                {"_id": {"vendedor": "Maria", "faixa_prazo": "31-39 dias"}, "quantidade": 1},
                {"_id": {"vendedor": "João", "faixa_prazo": "50-150 dias"}, "quantidade": 3}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_prazo_vendas_vendedor(mes=12)
    assert fig.layout.title.text.startswith('Vendas por Prazo')

def test_fig_prazo_vendas_vendedor_faixa_unica(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Zé"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"vendedor": "Zé", "faixa_prazo": "50-150 dias"}, "quantidade": 7}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_prazo_vendas_vendedor()
    # Verifica se existe pelo menos um vendedor e a faixa correta
    vendedores = [t for t in fig.data[0].x]
    assert "Zé" in vendedores
    faixas_usadas = set(trace.name for trace in fig.data if hasattr(trace, 'name'))
    assert "50-150 dias" in faixas_usadas

def test_fig_prazo_vendas_vendedor_so_outros(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "X"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Só retorna "Outro", que deve ser filtrado
            return [
                {"_id": {"vendedor": "X", "faixa_prazo": "Outro"}, "quantidade": 5}
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_prazo_vendas_vendedor()
    # Não deve trazer barras para "Outro", retorna gráfico vazio
    # Testa título e tipo
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text.startswith("Vendas por Prazo e Vendedor")

