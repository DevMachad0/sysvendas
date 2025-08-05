import pytest
from app.download import gerar_fig_verdes_vermelhos_vendedor

def test_fig_verdes_vermelhos_vendedor_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return []
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Meta Mensal") or "Sem dados" in fig.layout.xaxis.title.text

def test_fig_verdes_vermelhos_vendedor_somente_verdes(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"vendedor": "Maria", "tipo_cliente": "Verde"},
                {"vendedor": "Maria", "tipo_cliente": "verde"},
                {"vendedor": "Maria", "tipo_cliente": " VerDe "},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=7)
    assert fig.data[0].name == 'Verde'
    assert "Maria" in list(fig.data[0].x)
    assert sum(fig.data[0].y) == 3

def test_fig_verdes_vermelhos_vendedor_somente_verdes_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"vendedor": "Maria", "tipo_cliente": "Verde"},
                {"vendedor": "Maria", "tipo_cliente": "verde"},
                {"vendedor": "Maria", "tipo_cliente": " VerDe "},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text.startswith('Clientes Verdes')

def test_fig_verdes_vermelhos_vendedor_vendedor_nao_existe(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"vendedor": None, "tipo_cliente": "Verde"}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text.startswith('Clientes Verdes')

def test_fig_verdes_vermelhos_vendedor_tipo_cliente_nao_existe(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"vendedor": "Maria", "tipo_cliente": None}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text.startswith('Clientes Verdes')

def test_fig_verdes_vermelhos_vendedor_somente_vermelhos(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"vendedor": "João", "tipo_cliente": "vermelho"},
                {"vendedor": "João", "tipo_cliente": "Vermelho"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=7)
    assert fig.data[1].name == 'Vermelho'
    assert "João" in list(fig.data[1].x)
    assert sum(fig.data[1].y) == 2

def test_fig_verdes_vermelhos_vendedor_misto(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"vendedor": "Maria", "tipo_cliente": "verde"},
                {"vendedor": "Maria", "tipo_cliente": "Vermelho"},
                {"vendedor": "João", "tipo_cliente": "verDe"},
                {"vendedor": "João", "tipo_cliente": "vermelho"},
                {"vendedor": "Maria", "tipo_cliente": "Verde"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=7)
    # Confirma que ambos vendedores aparecem e contagens corretas
    verdes = dict(zip(fig.data[0].x, fig.data[0].y))
    vermelhos = dict(zip(fig.data[1].x, fig.data[1].y))
    assert verdes["Maria"] == 2
    assert verdes["João"] == 1
    assert vermelhos["Maria"] == 1
    assert vermelhos["João"] == 1

def test_fig_verdes_vermelhos_vendedor_ignora_sem_status(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"vendedor": "Maria", "tipo_cliente": ""},
                {"vendedor": "Maria", "tipo_cliente": "azul"},
                {"vendedor": "João", "tipo_cliente": None},
                {"vendedor": "", "tipo_cliente": "Verde"},
                {"vendedor": "Maria", "tipo_cliente": "Verde"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_vendedor(ano=2025, mes=7)
    assert sum(fig.data[0].y) == 1  # Só uma venda verde válida para Maria
