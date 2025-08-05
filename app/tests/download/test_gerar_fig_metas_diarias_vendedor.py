import pytest
import pandas as pd
from datetime import datetime, timedelta
from app.download import gerar_fig_metas_diarias_vendedor

def test_fig_metas_diarias_vendedor_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return []
    class FakeConfigsCollection:
        pass

    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Metas Diárias dos Vendedores")
    assert fig.layout.xaxis.title.text == "Sem metas cadastradas"
    assert fig.layout.width == 1600
    assert fig.layout.height == 600
    assert len(fig.data) == 0

def test_fig_metas_diarias_vendedor_todos_vermelho(monkeypatch):
    # 2 vendedores, 2 dias, nenhum bate meta (meta quantidade = 2, meta valor = 200)
    vendas = [
        # Só 1 venda para Maria no dia 01
        {"vendedor": "Maria", "valor_real": 100, "data_criacao": datetime.now()},
        # Nenhuma venda para João
    ]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return vendas
    class FakeConfigsCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 200},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 200}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=7)
    # Só deve ter as cores vermelhas
    assert set(fig.data[0].marker.color) == {"red"}

def test_fig_metas_diarias_vendedor_vendedor_nao_existe(monkeypatch):
    # 2 vendedores, 2 dias, nenhum bate meta (meta quantidade = 2, meta valor = 200)
    vendas = [
        # Só 1 venda para Maria no dia 01
        {"vendedor": "Não Existe", "valor_real": 100, "data_criacao": datetime.now()},
        # Nenhuma venda para João
    ]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return vendas
    class FakeConfigsCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 200},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 200}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Metas Diárias dos Vendedores")

def test_fig_metas_diarias_vendedor_verde_e_vermelho(monkeypatch):
    # Maria bate quantidade, João bate valor, nos dias diferentes
    vendas = [
        {"vendedor": "Maria", "valor_real": 50, "data_criacao": datetime.now()},
        {"vendedor": "Maria", "valor_real": 60, "data_criacao": datetime.now()},
        {"vendedor": "João", "valor_real": 250, "data_criacao": datetime.now()},
    ]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return vendas
    class FakeConfigsCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 200},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 200}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=7)
    # Vai ter pelo menos um verde
    assert "green" in set(fig.data[0].marker.color)
    assert "red" in set(fig.data[0].marker.color)
    # Confere a quantidade de pontos (n_vendedores * n_dias)
    # Julho sempre tem 31 dias
    assert len(fig.data[0].x) == 2 * 31

def test_fig_metas_diarias_vendedor_todos_vermelho_dezembro(monkeypatch):
    # 2 vendedores, 2 dias, nenhum bate meta (meta quantidade = 2, meta valor = 200)
    vendas = [
        # Só 1 venda para Maria no dia 01
        {"vendedor": "Maria", "valor_real": 100, "data_criacao": datetime.now()},
        # Nenhuma venda para João
    ]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return vendas
    class FakeConfigsCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 200},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 200}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text.startswith("Metas Diárias dos Vendedores")


def test_fig_metas_diarias_vendedor_verde_e_vermelho_dezembro(monkeypatch):
    # Maria bate quantidade, João bate valor, nos dias diferentes
    vendas = [
        {"vendedor": "Maria", "valor_real": 50, "data_criacao": datetime.now()},
        {"vendedor": "Maria", "valor_real": 60, "data_criacao": datetime.now()},
        {"vendedor": "João", "valor_real": 250, "data_criacao": datetime.now()},
    ]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return vendas
    class FakeConfigsCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 200},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 200}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text.startswith("Metas Diárias dos Vendedores")

def test_fig_metas_diarias_vendedor_verde_e_vermelho_dezembro_data_str(monkeypatch):
    # Maria bate quantidade, João bate valor, nos dias diferentes
    vendas = [
        {"vendedor": "Maria", "valor_real": 50, "data_criacao": "2025-12-04"},
        {"vendedor": "Maria", "valor_real": 60, "data_criacao": "2025-12-04"},
        {"vendedor": "João", "valor_real": 250, "data_criacao": "2025-12-04"},
    ]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return vendas
    class FakeConfigsCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 200},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 200}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text.startswith("Metas Diárias dos Vendedores")

def test_fig_metas_diarias_vendedor_correspondencia(monkeypatch):
    # Maria bate a meta no dia 01, não bate nos outros dias
    vendas = [
        {"vendedor": "Maria", "valor_real": 12000, "data_criacao": datetime.now()},
        {"vendedor": "Maria", "valor_real": 12000, "data_criacao": datetime.now()},
    ]
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return vendas
    class FakeConfigsCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 15000},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_metas_diarias_vendedor(ano=2025, mes=7)
    # Deve existir um verde (bateu por quantidade) e outros pontos vermelhos
    cores = fig.data[0].marker.color
    assert "green" in cores
    assert "red" in cores
