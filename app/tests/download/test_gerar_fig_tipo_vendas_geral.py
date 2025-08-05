import pytest
from app.download import gerar_fig_tipo_vendas_geral

def test_fig_tipo_vendas_geral_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return []
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_geral(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Meta Mensal") or "Sem dados" in fig.layout.xaxis.title.text

def test_fig_tipo_vendas_geral_apenas_novas(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"produto": "Contrato"},
                {"produto": "Módulo"},
                {"produto": "Produto qualquer"}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_geral(ano=2025, mes=7)
    labels = set(fig.data[0].labels)
    values = list(fig.data[0].values)
    assert "Vendas Novas" in labels
    assert "Atualizações" in labels
    assert values[0] == 3  # 3 vendas novas
    assert values[1] == 0  # 0 atualizações

def test_fig_tipo_vendas_geral_apenas_novas_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"produto": "Contrato"},
                {"produto": "Módulo"},
                {"produto": "Produto qualquer"}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_geral(ano=2025, mes=12)
    assert fig.layout.title.text.startswith('Distribuição de Vendas')

def test_fig_tipo_vendas_geral_produto_nao_eh_str(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"produto": 123}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_geral(ano=2025, mes=12)
    assert fig.layout.title.text.startswith('Distribuição de Vendas')

def test_fig_tipo_vendas_geral_apenas_atualizacoes(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"produto": "atualização"},
                {"produto": "Atualizacao"},
                {"produto": " atualização "}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_geral(ano=2025, mes=7)
    labels = set(fig.data[0].labels)
    values = list(fig.data[0].values)
    assert "Vendas Novas" in labels
    assert "Atualizações" in labels
    assert values[0] == 0
    assert values[1] == 3

def test_fig_tipo_vendas_geral_misto(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"produto": "Contrato"},
                {"produto": "atualização"},
                {"produto": "Atualizacao"},
                {"produto": "produto"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_geral(ano=2025, mes=7)
    values = list(fig.data[0].values)
    assert values[0] == 2  # 2 novas
    assert values[1] == 2  # 2 atualizações

def test_fig_tipo_vendas_geral_casos_estranhos(monkeypatch):
    class FakeVendasCollection:
        def find(self, *a, **k):
            return [
                {"produto": ""},
                {"produto": None},
                {},
                {"produto": "atualização"},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    fig = gerar_fig_tipo_vendas_geral(ano=2025, mes=7)
    values = list(fig.data[0].values)
    assert values[0] == 1  # 1 novas
    assert values[1] == 1  # 1 atualização
