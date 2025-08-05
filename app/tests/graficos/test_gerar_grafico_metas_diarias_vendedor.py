import pytest
from datetime import datetime
from app.graficos import gerar_grafico_metas_diarias_vendedor

def test_gerar_grafico_metas_diarias_vendedor_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria", "meta_dia_quantidade": 2, "meta_dia_valor": 1000.0}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        return "<div>grafico-vazio</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_metas_diarias_vendedor(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"]

def test_gerar_grafico_metas_diarias_vendedor_com_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 1, "meta_dia_valor": 2000.0},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 3000.0},
            ]
    # Maria bate a meta no primeiro dia, João não bate nenhuma
    def vendas():
        # Todas em 2025-07-01
        data = datetime(2025, 7, 1, 10, 0)
        return [
            {"vendedor": "Maria", "valor_real": "2500", "data_criacao": data, "status": "Aprovada"},
            {"vendedor": "João", "valor_real": "1500", "data_criacao": data, "status": "Aprovada"},
        ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return vendas()
    def fake_to_html(fig, **kwargs):
        # Testa se os mini-cards estão montados (um verde pra Maria, um vermelho pra João)
        # As cores vêm em fig.data[0].marker.color
        cores = fig.data[0].marker.color
        nomes = fig.data[0].y
        assert "Maria" in nomes and "João" in nomes
        assert "green" in cores
        assert "red" in cores
        return "<div>grafico-diario-metas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_diarias_vendedor(2025, 7)
    assert html == "<div>grafico-diario-metas</div>"

def test_gerar_grafico_metas_diarias_vendedor_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 1, "meta_dia_valor": 2000.0},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 3000.0},
            ]
    # Maria bate a meta no primeiro dia, João não bate nenhuma
    def vendas():
        # Todas em 2025-07-01
        data = datetime(2025, 7, 1, 10, 0)
        return [
            {"vendedor": "Maria", "valor_real": "2500", "data_criacao": data, "status": "Aprovada"},
            {"vendedor": "João", "valor_real": "1500", "data_criacao": data, "status": "Aprovada"},
        ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return vendas()
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith('Metas Diárias dos Vendedores')
        return "<div>grafico-diario-metas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_diarias_vendedor(2025, 12)
    assert html == "<div>grafico-diario-metas</div>"

def test_gerar_grafico_metas_diarias_vendedor_vendedor_sem_metas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 1, "meta_dia_valor": 2000.0},
            ]
    # Maria bate a meta no primeiro dia, João não bate nenhuma
    def vendas():
        # Todas em 2025-07-01
        data = datetime(2025, 7, 1, 10, 0)
        return [
            {"vendedor": "Maria", "valor_real": "2500", "data_criacao": data, "status": "Aprovada"},
            {"vendedor": "João", "valor_real": "1500", "data_criacao": data, "status": "Aprovada"},
        ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return vendas()
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith('Metas Diárias dos Vendedores')
        return "<div>grafico-diario-metas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_diarias_vendedor(2025, 12)
    assert html == "<div>grafico-diario-metas</div>"

def test_gerar_grafico_metas_diarias_vendedor_venda_data_str(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor_nome": "Maria", "meta_dia_quantidade": 1, "meta_dia_valor": 2000.0},
                {"vendedor_nome": "João", "meta_dia_quantidade": 2, "meta_dia_valor": 3000.0},
            ]
    # Maria bate a meta no primeiro dia, João não bate nenhuma
    def vendas():
        # Todas em 2025-07-01
        data = '2025-07-01'
        return [
            {"vendedor": "Maria", "valor_real": "2500", "data_criacao": data, "status": "Aprovada"},
            {"vendedor": "João", "valor_real": "1500", "data_criacao": data, "status": "Aprovada"},
        ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return vendas()
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith('Metas Diárias dos Vendedores')
        return "<div>grafico-diario-metas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_diarias_vendedor(2025, 12)
    assert html == "<div>grafico-diario-metas</div>"
