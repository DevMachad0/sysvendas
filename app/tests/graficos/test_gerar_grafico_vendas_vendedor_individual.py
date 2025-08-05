import pytest
from app.graficos import gerar_grafico_vendas_vendedor_individual

def test_grafico_individual_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            # Simula meta de 3000 para o vendedor "maria123"
            return [{"meta_mes": 3000.0, "nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        # Garante que o gráfico está vazio (sem barras de venda)
        return "<div>grafico-vazio-individual</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-vazio-individual</div>"
    assert chamado["foi"]

def test_grafico_individual_com_vendas_atingiu_meta(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"meta_mes": 1500.0, "nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Maria vendeu 2000 > meta 1500
            return [{"valor_real": "1000", "status": "Aprovada"}, {"valor_real": "1000", "status": "Faturado"}]
    def fake_soma_vendas(vendas):
        # Simula soma correta independente do tipo dos valores
        return sum(float(v["valor_real"]) for v in vendas)

    def fake_to_html(fig, **kwargs):
        bars = fig.data
        vendido = bars[0].x[0]
        faltando = bars[1].x[0]
        assert vendido == 2000
        assert faltando == 0
        assert bars[0].marker.color == "green"
        assert bars[1].marker.color == "#c34323"
        return "<div>grafico-meta-batida</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.soma_vendas", fake_soma_vendas)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-meta-batida</div>"

def test_grafico_individual_com_vendas_atingiu_meta_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"meta_mes": 1500.0, "nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Maria vendeu 2000 > meta 1500
            return [{"valor_real": "1000", "status": "Aprovada"}, {"valor_real": "1000", "status": "Faturado"}]
    def fake_soma_vendas(vendas):
        # Simula soma correta independente do tipo dos valores
        return sum(float(v["valor_real"]) for v in vendas)

    def fake_to_html(fig, **kwargs):
        bars = fig.data
        vendido = bars[0].x[0]
        faltando = bars[1].x[0]
        assert vendido == 2000
        assert faltando == 0
        assert bars[0].marker.color == "green"
        assert bars[1].marker.color == "#c34323"
        return "<div>grafico-meta-batida</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.soma_vendas", fake_soma_vendas)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_vendedor_individual(2025, 12, "maria123")
    assert html == "<div>grafico-meta-batida</div>"

def test_grafico_individual_com_vendas_nao_atingiu_meta(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"meta_mes": 3000.0, "nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Maria vendeu só 1200 < meta 3000
            return [{"valor_real": "1200", "status": "Aprovada"}]
    def fake_soma_vendas(vendas):
        return sum(float(v["valor_real"]) for v in vendas)
    def fake_to_html(fig, **kwargs):
        bars = fig.data
        vendido = bars[0].x[0]
        faltando = bars[1].x[0]
        assert vendido == 1200
        assert faltando == 1800
        assert bars[0].marker.color == "green"
        assert bars[1].marker.color == "#c34323"
        return "<div>grafico-meta-nao-batida</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.soma_vendas", fake_soma_vendas)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-meta-nao-batida</div>"

