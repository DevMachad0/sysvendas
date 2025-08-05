import pytest
from datetime import datetime
from app.download import gerar_fig_metas_semanais_vendedor

def test_fig_metas_semanais_vendedor_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, *a, **k): return []
    class FakeConfigsCollection:
        def find(self, *a, **k): return []
    class FakeVendasCollection:
        def find(self, *a, **k): return []

    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_metas_semanais_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Vendas Semana Atual")
    assert fig.layout.xaxis.title.text == "Sem metas cadastradas"
    assert fig.layout.width == 1600
    assert fig.layout.height >= 600
    assert len(fig.data) == 0

def test_fig_metas_semanais_vendedor_todos_vermelho(monkeypatch):
    # 2 vendedores, nenhum bate meta semanal (meta = 2000, venderam menos)
    class FakeUsuariosCollection:
        def find(self, *a, **k): return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, *a, **k): return [
            {"vendedor_nome": "Maria", "meta_semana": 2000},
            {"vendedor_nome": "João", "meta_semana": 1000}
        ]
    class FakeVendasCollection:
        def find(self, *a, **k):
            semana = datetime.today().isocalendar()[1]  # Use semana do meio do mês
            return [
                {"vendedor": "Maria", "valor_real": "1500", "data_criacao": datetime.now()},
                {"vendedor": "João", "valor_real": "900", "data_criacao": datetime.now()},
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_metas_semanais_vendedor(ano=2025, mes=7)
    cores = fig.data[0].marker.color
    assert set(cores) == {"red"}
    # Garante que há uma linha de meta semanal para cada vendedor
    assert len(fig.data) == 2  # barras + linha

def test_fig_metas_semanais_vendedor_misto(monkeypatch):
    # Maria bate a meta, João não
    class FakeUsuariosCollection:
        def find(self, *a, **k): return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, *a, **k): return [
            {"vendedor_nome": "Maria", "meta_semana": 1000},
            {"vendedor_nome": "João", "meta_semana": 1000}
        ]
    class FakeVendasCollection:
        def find(self, *a, **k):
            semana = datetime.today().isocalendar()[1]
            return [
                {"vendedor": "Maria", "valor_real": "1200", "data_criacao": datetime.now()},
                {"vendedor": "João", "valor_real": "900", "data_criacao": datetime.now()},
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_metas_semanais_vendedor(ano=2025, mes=7)
    cores = fig.data[0].marker.color
    assert "green" in cores and "red" in cores
    # Confere textos de cada barra (formatação de valor)
    textos = fig.data[0].text
    assert any("R$ 1.200,00" in t or "R$ 1,200.00" in t for t in textos)

def test_fig_metas_semanais_vendedor_linha_meta(monkeypatch):
    # Garante que a linha de meta corresponde ao valor correto de cada vendedor
    class FakeUsuariosCollection:
        def find(self, *a, **k): return [{"nome_completo": "Maria"}]
    class FakeConfigsCollection:
        def find(self, *a, **k): return [{"vendedor_nome": "Maria", "meta_semana": 4000}]
    class FakeVendasCollection:
        def find(self, *a, **k):
            semana = datetime.today().isocalendar()[1]
            return [
                {"vendedor": "Maria", "valor_real": "3800", "data_criacao": datetime.now()},
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_metas_semanais_vendedor(ano=2025, mes=7)
    # A linha de meta deve ser o valor correto para cada vendedor
    scatter = fig.data[1]
    assert list(scatter.y) == [4000]
    assert list(scatter.x) == ["Maria"]

def test_fig_metas_semanais_vendedor_vendedor_nao_existe(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, *a, **k): return [{"nome_completo": "Maria"}]
    class FakeConfigsCollection:
        def find(self, *a, **k): return [{"vendedor_nome": "Maria", "meta_semana": 4000}]
    class FakeVendasCollection:
        def find(self, *a, **k):
            semana = datetime.today().isocalendar()[1]
            return [
                {"vendedor": "Não Existe", "valor_real": "3800", "data_criacao": datetime.now()},
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_metas_semanais_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Vendas Semana Atual")

def test_fig_metas_semanais_vendedor_data_str(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, *a, **k): return [{"nome_completo": "Maria"}]
    class FakeConfigsCollection:
        def find(self, *a, **k): return [{"vendedor_nome": "Maria", "meta_semana": 4000}]
    class FakeVendasCollection:
        def find(self, *a, **k):
            semana = datetime.today().isocalendar()[1]
            return [
                {"vendedor": "Maria", "valor_real": "3800", "data_criacao": "2025-07-04"},
            ]
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())

    fig = gerar_fig_metas_semanais_vendedor(ano=2025, mes=7)
    assert fig.layout.title.text.startswith("Vendas Semana Atual")
