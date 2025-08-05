import pytest
from app.download import gerar_fig_produtos_mais_vendidos

def test_fig_produtos_mais_vendidos_vazio(monkeypatch):
    class FakeProdutosCollection:
        def find(self, *args, **kwargs):
            return [{"nome": "ProdA"}, {"nome": "ProdB"}]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return []
    monkeypatch.setattr("app.download.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_produtos_mais_vendidos()
    import plotly.graph_objs as go
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text.startswith("Produtos mais Vendidos")

def test_fig_produtos_mais_vendidos_com_vendas(monkeypatch):
    class FakeProdutosCollection:
        def find(self, *args, **kwargs):
            return [{"nome": "ProdA"}, {"nome": "ProdB"}, {"nome": "ProdC"}]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return [
                {"produto": "ProdA"},
                {"produto": "ProdA"},
                {"produto": "ProdC"},
            ]
    monkeypatch.setattr("app.download.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_produtos_mais_vendidos()
    barras = fig.data[0]
    produtos = list(barras.y)
    quantidades = list(barras.x)
    assert "ProdA" in produtos
    assert "ProdC" in produtos
    assert "ProdB" not in produtos  # Sem vendas, não aparece
    assert 2 in quantidades
    assert 1 in quantidades
    assert fig.layout.title.text.startswith("Produtos mais Vendidos")

def test_fig_produtos_mais_vendidos_so_um(monkeypatch):
    class FakeProdutosCollection:
        def find(self, *args, **kwargs):
            return [{"nome": "Unico"}]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return [{"produto": "Unico"}]
    monkeypatch.setattr("app.download.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_produtos_mais_vendidos()
    barras = fig.data[0]
    produtos = list(barras.y)
    assert produtos == ["Unico"]
    assert list(barras.x) == [1]
    assert fig.layout.title.text.startswith("Produtos mais Vendidos")

def test_fig_produtos_mais_vendidos_so_um_dezembro(monkeypatch):
    class FakeProdutosCollection:
        def find(self, *args, **kwargs):
            return [{"nome": "Unico"}]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return [{"produto": "Unico"}]
    monkeypatch.setattr("app.download.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_produtos_mais_vendidos(mes=12)
    assert fig.layout.title.text.startswith("Produtos mais Vendidos")

def test_fig_produtos_mais_vendidos_zero_produtos(monkeypatch):
    class FakeProdutosCollection:
        def find(self, *args, **kwargs):
            return []
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return []
    monkeypatch.setattr("app.download.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_produtos_mais_vendidos()
    assert hasattr(fig, 'layout')
    assert fig.layout.title.text.startswith("Produtos mais Vendidos")
