import pytest
from app.graficos import gerar_grafico_quantidade_vendas_diarias

def test_grafico_quantidade_vendas_diarias_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Quantidade de Vendas por Dia")
        assert fig.layout.xaxis.title.text == "Sem dados"
        return "<div>grafico-linha-qtd-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_quantidade_vendas_diarias(2025, 7)
    assert html == "<div>grafico-linha-qtd-vazio</div>"

def test_grafico_quantidade_vendas_diarias_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 3}, "quantidade": 2},
                {"_id": {"ano": 2025, "mes": 7, "dia": 4}, "quantidade": 4},
            ]
    def fake_to_html(fig, **kwargs):
        trace = fig.data[0]
        dias = list(trace.x)
        quantidades = list(trace.y)
        assert "03/07" in dias
        assert "04/07" in dias
        assert 2 in quantidades
        assert 4 in quantidades
        assert fig.layout.title.text.startswith("Quantidade de Vendas por Dia")
        return "<div>grafico-linha-qtd-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_quantidade_vendas_diarias(2025, 7)
    assert html == "<div>grafico-linha-qtd-dados</div>"

def test_grafico_quantidade_vendas_diarias_um_dia(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [{"_id": {"ano": 2025, "mes": 7, "dia": 11}, "quantidade": 5}]
    def fake_to_html(fig, **kwargs):
        trace = fig.data[0]
        assert trace.x == ("11/07",)
        assert trace.y == (5,)
        return "<div>grafico-linha-qtd-um-dia</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_quantidade_vendas_diarias(2025, 7)
    assert html == "<div>grafico-linha-qtd-um-dia</div>"
