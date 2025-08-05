import pytest
from app.graficos import gerar_grafico_vendas_vendedor

def test_gerar_grafico_vendas_vendedor_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        return "<div>grafico-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_vendedor(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"] is True

def test_gerar_grafico_vendas_vendedor_com_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "status": "Aprovada", "valor_real": "1000"},
                {"vendedor": "Maria", "status": "Faturado", "valor_real": "500"},
                {"vendedor": "João", "status": "Aprovada", "valor_real": "300"},
            ]
    def fake_soma_vendas(vendas):
        return sum(float(v["valor_real"]) for v in vendas)

    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        nomes = list(bars.x)
        valores = list(bars.y)
        assert "Maria" in nomes and "João" in nomes
        assert valores[nomes.index("Maria")] == 1500
        assert valores[nomes.index("João")] == 300
        return "<div>grafico-vendas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.soma_vendas", fake_soma_vendas)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_vendedor(2025, 7)
    assert html == "<div>grafico-vendas</div>"

def test_gerar_grafico_vendas_vendedor_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "status": "Aprovada", "valor_real": "1000"},
                {"vendedor": "Maria", "status": "Faturado", "valor_real": "500"},
                {"vendedor": "João", "status": "Aprovada", "valor_real": "300"},
            ]
    def fake_soma_vendas(vendas):
        return sum(float(v["valor_real"]) for v in vendas)

    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text == 'Total de Vendas por Vendedor'
        return "<div>grafico-vendas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.soma_vendas", fake_soma_vendas)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_vendedor(2025, 12)
    assert html == "<div>grafico-vendas</div>"
