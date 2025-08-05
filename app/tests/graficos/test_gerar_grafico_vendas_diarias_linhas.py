import pytest
from app.graficos import gerar_grafico_vendas_diarias_linhas

def test_grafico_vendas_diarias_linhas_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Vendas por Dia do Mês")
        assert fig.layout.xaxis.title.text == "Sem dados"
        return "<div>grafico-linha-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_diarias_linhas(2025, 7)
    assert html == "<div>grafico-linha-vazio</div>"

def test_grafico_vendas_diarias_linhas_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # 2 dias: 01/07 e 02/07, Maria vendeu 100, João vendeu 250
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 1}, "total": 100.0},
                {"_id": {"ano": 2025, "mes": 7, "dia": 2}, "total": 250.0},
            ]
    def fake_to_html(fig, **kwargs):
        trace = fig.data[0]
        dias = list(trace.x)
        totais = list(trace.y)
        assert "01/07" in dias
        assert "02/07" in dias
        assert 100.0 in totais
        assert 250.0 in totais
        assert fig.layout.title.text.startswith("Vendas por Dia do Mês")
        return "<div>grafico-linha-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_diarias_linhas(2025, 7)
    assert html == "<div>grafico-linha-dados</div>"

def test_grafico_vendas_diarias_linhas_com_dados_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # 2 dias: 01/07 e 02/07, Maria vendeu 100, João vendeu 250
            return [
                {"_id": {"ano": 2025, "mes": 7, "dia": 1}, "total": 100.0},
                {"_id": {"ano": 2025, "mes": 7, "dia": 2}, "total": 250.0},
            ]
    def fake_to_html(fig, **kwargs):
        trace = fig.data[0]
        dias = list(trace.x)
        totais = list(trace.y)
        assert "01/07" in dias
        assert "02/07" in dias
        assert 100.0 in totais
        assert 250.0 in totais
        assert fig.layout.title.text.startswith("Vendas por Dia do Mês")
        return "<div>grafico-linha-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_diarias_linhas(2025, 12)
    assert html == "<div>grafico-linha-dados</div>"

def test_grafico_vendas_diarias_linhas_apenas_um_dia(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [{"_id": {"ano": 2025, "mes": 7, "dia": 10}, "total": 99.5}]
    def fake_to_html(fig, **kwargs):
        trace = fig.data[0]
        assert trace.x == ("10/07",)
        assert trace.y == (99.5,)
        return "<div>grafico-linha-um-dia</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_diarias_linhas(2025, 7)
    assert html == "<div>grafico-linha-um-dia</div>"
