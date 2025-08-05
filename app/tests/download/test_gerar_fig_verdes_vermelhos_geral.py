import pytest
from app.download import gerar_fig_verdes_vermelhos_geral

def test_fig_verdes_vermelhos_geral_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return []
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Meta Mensal") or "Sem dados" in fig.layout.xaxis.title.text

def test_fig_verdes_vermelhos_geral_apenas_verdes(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "verde"},
                {"tipo_cliente": " VerDe "},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=7)
    pie = fig.data[0]
    labels = set(pie.labels)
    values = list(pie.values)
    assert "Verde" in labels
    assert sum(values) == 3

def test_fig_verdes_vermelhos_geral_apenas_vermelhos(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Vermelho"},
                {"tipo_cliente": "vermelho"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=7)
    pie = fig.data[0]
    labels = set(pie.labels)
    values = list(pie.values)
    assert "Vermelho" in labels
    assert sum(values) == 2

def test_fig_verdes_vermelhos_geral_misto(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "Vermelho"},
                {"tipo_cliente": "verde"},
                {"tipo_cliente": "vermelho"},
                {"tipo_cliente": "verDe"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=7)
    pie = fig.data[0]
    labels = set(pie.labels)
    values = {l: v for l, v in zip(pie.labels, pie.values)}
    assert values["Verde"] == 3
    assert values["Vermelho"] == 2
    assert set(labels) == {"Verde", "Vermelho"}

def test_fig_verdes_vermelhos_geral_ignora_outros(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": ""},
                {"tipo_cliente": "Azul"},
                {"tipo_cliente": " "},
                {"tipo_cliente": "vermelho"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=7)
    pie = fig.data[0]
    assert sum(pie.values) == 2
    assert set(pie.labels) == {"Verde", "Vermelho"}

def test_fig_verdes_vermelhos_geral_apenas_verdes_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "verde"},
                {"tipo_cliente": " VerDe "},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=12)
    assert fig.layout.title.text.startswith("Distribuição de Clientes")


def test_fig_verdes_vermelhos_geral_apenas_vermelhos_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Vermelho"},
                {"tipo_cliente": "vermelho"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=12)
    assert fig.layout.title.text.startswith("Distribuição de Clientes")

def test_fig_verdes_vermelhos_geral_misto_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "Vermelho"},
                {"tipo_cliente": "verde"},
                {"tipo_cliente": "vermelho"},
                {"tipo_cliente": "verDe"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=12)
    assert fig.layout.title.text.startswith("Distribuição de Clientes")

def test_fig_verdes_vermelhos_geral_ignora_outros_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": ""},
                {"tipo_cliente": "Azul"},
                {"tipo_cliente": " "},
                {"tipo_cliente": "vermelho"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=12)
    assert fig.layout.title.text.startswith("Distribuição de Clientes")

def test_fig_verdes_vermelhos_geral_total_zero(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"tipo_cliente": "Azul"},
                {"tipo_cliente": ""},
                {"tipo_cliente": "Azul"},
                {"tipo_cliente": " "},
                {"tipo_cliente": "Azul"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_verdes_vermelhos_geral(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Distribuição de Clientes")