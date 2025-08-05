import pytest
from app.graficos import gerar_grafico_vendas_geral

def test_gerar_grafico_vendas_geral_sem_vendas(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Vendedor Ativo"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"meta_empresa": "100000"}]
    # Mock pio.to_html
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        return "<div>grafico-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_geral(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"] is True

def test_gerar_grafico_vendas_geral_com_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Dois valores de venda aprovados
            return [
                {"status": "Aprovada", "valor_real": "10000"},
                {"status": "Faturado", "valor_real": "5000"}
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"meta_empresa": "20000"}]

    def fake_to_html(fig, **kwargs):
        bars = fig.data
        nomes = [trace.name for trace in bars]
        xs = [trace.x[0] for trace in bars]
        # Esperado: Vendido = 15000, Faltando = 5000
        assert "Vendido" in nomes
        assert "Faltando" in nomes
        assert 15000 in xs
        assert 5000 in xs
        return "<div>grafico-meta</div>"

    def fake_soma_vendas(vendas):
        return sum(float(v["valor_real"]) for v in vendas)

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    monkeypatch.setattr("app.graficos.soma_vendas", fake_soma_vendas)

    html = gerar_grafico_vendas_geral(2025, 7)
    assert html == "<div>grafico-meta</div>"

def test_gerar_grafico_vendas_geral_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Dois valores de venda aprovados
            return [
                {"status": "Aprovada", "valor_real": "10000"},
                {"status": "Faturado", "valor_real": "5000"}
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"meta_empresa": "20000"}]

    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Meta Mensal")
        return "<div>grafico-meta</div>"

    def fake_soma_vendas(vendas):
        return sum(float(v["valor_real"]) for v in vendas)

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    monkeypatch.setattr("app.graficos.soma_vendas", fake_soma_vendas)

    html = gerar_grafico_vendas_geral(2025, 12)
    assert html == "<div>grafico-meta</div>"
