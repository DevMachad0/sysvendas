import pytest
from app.download import gerar_fig_metas_vendedor

def test_fig_metas_vendedor_sem_metas(monkeypatch):
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return []
    class FakeUsuariosCollection:
        def find(self, *args, **kwargs):
            return []  # Sem vendedores cadastrados
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    fig = gerar_fig_metas_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text == "Progresso de Vendas por Vendedor"
    assert fig.layout.xaxis.title.text == "Sem metas cadastradas"
    assert fig.layout.width == 1600
    assert fig.layout.height == 600
    assert len(fig.data) == 0

def test_fig_metas_vendedor_zerado(monkeypatch):
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return []
    class FakeUsuariosCollection:
        def find(self, *args, **kwargs):
            return [
                {"nome_completo": "Maria", "meta_mes": 10000},
                {"nome_completo": "João", "meta_mes": 8000}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    fig = gerar_fig_metas_vendedor(ano=2025, mes=7)
    # Ambos sem vendas, então faltando = meta, vendido = 0
    nomes = [bar.y for bar in fig.data if bar.name == "Vendido"][0]
    assert set(nomes) == {"Maria", "João"}
    # Todos vendidos são zero
    vendidos = list([bar.x for bar in fig.data if bar.name == "Vendido"][0])
    assert vendidos == [0, 0]
    # Todos faltando é o valor da meta
    faltando = list([bar.x for bar in fig.data if bar.name == "Faltando"][0])
    assert faltando == [10000, 8000]

def test_fig_metas_vendedor_com_dados(monkeypatch):
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor": "Maria", "valor_real": 6000, "status": "Aprovada"},
                {"vendedor": "João", "valor_real": 5000, "status": "Faturado"},
                {"vendedor": "Maria", "valor_real": 4000, "status": "Aprovada"},
            ]
    class FakeUsuariosCollection:
        def find(self, *args, **kwargs):
            return [
                {"nome_completo": "Maria", "meta_mes": 10000},
                {"nome_completo": "João", "meta_mes": 7000}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    fig = gerar_fig_metas_vendedor(ano=2025, mes=7)
    # Maria bateu a meta, João vendeu 5000 (faltam 2000)
    nomes = list(fig.data[0].y)
    assert set(nomes) == {"Maria", "João"}
    vendidos = {v: fig.data[0].x[i] for i, v in enumerate(nomes)}
    faltando = {v: fig.data[1].x[i] for i, v in enumerate(nomes)}
    assert vendidos["Maria"] == 10000
    assert vendidos["João"] == 5000
    assert faltando["Maria"] == 0
    assert faltando["João"] == 2000

def test_fig_metas_vendedor_com_dados_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor": "Maria", "valor_real": 6000, "status": "Aprovada"},
                {"vendedor": "João", "valor_real": 5000, "status": "Faturado"},
                {"vendedor": "Maria", "valor_real": 4000, "status": "Aprovada"},
            ]
    class FakeUsuariosCollection:
        def find(self, *args, **kwargs):
            return [
                {"nome_completo": "Maria", "meta_mes": 10000},
                {"nome_completo": "João", "meta_mes": 7000}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    fig = gerar_fig_metas_vendedor(ano=2025, mes=12)
    assert fig.layout.title.text == "Progresso de Vendas por Vendedor"

def test_fig_metas_vendedor_ignora_cancelada(monkeypatch):
    class FakeVendasCollection:
        def find(self, *args, **kwargs):
            return [
                {"vendedor": "Maria", "valor_real": 2000, "status": "Cancelada"},
                {"vendedor": "Maria", "valor_real": 3000, "status": "Aprovada"}
            ]
    class FakeUsuariosCollection:
        def find(self, *args, **kwargs):
            return [
                {"nome_completo": "Maria", "meta_mes": 5000},
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    fig = gerar_fig_metas_vendedor(ano=2025, mes=7)
    vendidos = list(fig.data[0].x)
    faltando = list(fig.data[1].x)
    # Só conta a aprovada, ignorando a cancelada
    assert vendidos == [3000]
    assert faltando == [2000]
