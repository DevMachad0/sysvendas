import pytest
from app.graficos import gerar_grafico_status_vendas_vendedor

def test_gerar_grafico_status_vendas_vendedor_sem_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        return "<div>grafico-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_status_vendas_vendedor(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"] is True

def test_gerar_grafico_status_vendas_vendedor_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    # Simula resultado da agregação do MongoDB
    def fake_aggregate(pipeline):
        return [
            {"_id": {"vendedor": "Maria", "status": "Aprovada"}, "quantidade": 3},
            {"_id": {"vendedor": "Maria", "status": "Faturado"}, "quantidade": 1},
            {"_id": {"vendedor": "João", "status": "Cancelada"}, "quantidade": 2}
        ]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return fake_aggregate(pipeline)
    def fake_to_html(fig, **kwargs):
        # Espera os vendedores e os status (stacked bar)
        # Checa se existem as barras esperadas
        data = fig.data
        nomes_vendedores = set(trace.x[0] for trace in data if trace.x)
        assert "Maria" in nomes_vendedores or "João" in nomes_vendedores
        return "<div>grafico-status</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_status_vendas_vendedor(2025, 7)
    assert html == "<div>grafico-status</div>"

def test_gerar_grafico_status_vendas_vendedor_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    # Simula resultado da agregação do MongoDB
    def fake_aggregate(pipeline):
        return [
            {"_id": {"vendedor": "Maria", "status": "Aprovada"}, "quantidade": 3},
            {"_id": {"vendedor": "Maria", "status": "Faturado"}, "quantidade": 1},
            {"_id": {"vendedor": "João", "status": "Cancelada"}, "quantidade": 2}
        ]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return fake_aggregate(pipeline)
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text == 'Vendas por Status e Vendedor'
        return "<div>grafico-status</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_status_vendas_vendedor(2025, 12)
    assert html == "<div>grafico-status</div>"
