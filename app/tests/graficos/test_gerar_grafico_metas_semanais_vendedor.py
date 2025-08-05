import pytest
from datetime import datetime
from app.graficos import gerar_grafico_metas_semanais_vendedor

def test_gerar_grafico_metas_semanais_vendedor_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria", "meta_semana": 3000.0}]
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
    html = gerar_grafico_metas_semanais_vendedor(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"]

def test_gerar_grafico_metas_semanais_vendedor_com_vendas(monkeypatch):
    # Semana do dia 14/07/2025 é 29 (isso só influencia visual)
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor_nome": "Maria", "meta_semana": 2000.0},
                {"vendedor_nome": "João", "meta_semana": 1000.0},
            ]
    def vendas():
        # Maria bate a meta na semana, João não
        data = datetime.today()  # Semana 29 de 2025
        return [
            {"vendedor": "Maria", "valor_real": "2500", "data_criacao": data, "status": "Aprovada"},
            {"vendedor": "João", "valor_real": "900", "data_criacao": data, "status": "Faturado"},
        ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return vendas()
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        nomes = list(bars.x)
        cores = list(bars.marker.color)
        mapa = dict(zip(nomes, cores))
        assert mapa["Maria"] == "green"   # Maria bateu a meta
        assert mapa["João"] == "red"      # João não bateu a meta

        # Checagem da linha de meta permanece igual
        scatter = fig.data[1]
        metas = {n: y for n, y in zip(scatter.x, scatter.y)}
        assert metas["Maria"] == 2000.0
        assert metas["João"] == 1000.0

        return "<div>grafico-semanal</div>"


    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_semanais_vendedor(2025, 7)
    assert html == "<div>grafico-semanal</div>"

def test_gerar_grafico_metas_semanais_vendedor_sem_metas(monkeypatch):
    # Semana do dia 14/07/2025 é 29 (isso só influencia visual)
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor_nome": "Maria", "meta_semana": 2000.0},
            ]
    def vendas():
        # Maria bate a meta na semana, João não
        data = datetime.today()  # Semana 29 de 2025
        return [
            {"vendedor": "Maria", "valor_real": "2500", "data_criacao": data, "status": "Aprovada"},
            {"vendedor": "João", "valor_real": "900", "data_criacao": data, "status": "Faturado"},
        ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return vendas()
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith('Vendas Semana Atual')

        return "<div>grafico-semanal</div>"


    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_semanais_vendedor(2025, 7)
    assert html == "<div>grafico-semanal</div>"

def test_gerar_grafico_metas_semanais_venda_data_str(monkeypatch):
    # Semana do dia 14/07/2025 é 29 (isso só influencia visual)
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor_nome": "Maria", "meta_semana": 2000.0},
                {"vendedor_nome": "João", "meta_semana": 1000.0},
            ]
    def vendas():
        # Maria bate a meta na semana, João não
        data = '2025-07-14'
        return [
            {"vendedor": "Maria", "valor_real": "2500", "data_criacao": data, "status": "Aprovada"},
            {"vendedor": "João", "valor_real": "900", "data_criacao": data, "status": "Faturado"},
        ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return vendas()
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith('Vendas Semana Atual')

        return "<div>grafico-semanal</div>"


    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_semanais_vendedor(2025, 7)
    assert html == "<div>grafico-semanal</div>"
