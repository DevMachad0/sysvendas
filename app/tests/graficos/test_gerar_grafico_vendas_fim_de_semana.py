import pytest
from app.graficos import gerar_grafico_vendas_fim_de_semana

def test_grafico_fim_de_semana_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Vendas por Status no Fim de Semana")
        assert fig.layout.xaxis.title.text == "Vendedor / Dia"
        return "<div>grafico-fds-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_fim_de_semana(2025, 7)
    assert html == "<div>grafico-fds-vazio</div>"

def test_grafico_fim_de_semana_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Dois vendedores, dois dias, dois status
            return [
                {
                    "_id": {
                        "dia": 5, "mes": 7, "ano": 2025,
                        "vendedor": "Maria", "status": "Faturado"
                    },
                    "total": 1000.0
                },
                {
                    "_id": {
                        "dia": 6, "mes": 7, "ano": 2025,
                        "vendedor": "Maria", "status": "Aguardando"
                    },
                    "total": 500.0
                },
                {
                    "_id": {
                        "dia": 5, "mes": 7, "ano": 2025,
                        "vendedor": "João", "status": "Aprovada"
                    },
                    "total": 200.0
                }
            ]
    def fake_to_html(fig, **kwargs):
        # Testa a presença dos grupos e valores
        x = list(fig.data[0].x)  # Todas as labels X (vendedor (dia))
        # Os valores Y de cada status
        y_faturado = list(fig.data[0].y)
        y_aprovada = list(fig.data[1].y)
        y_aguardando = list(fig.data[2].y)
        # Checa se as barras estão presentes para cada status esperado
        assert any("Maria (05/07)" in xx for xx in x)
        assert any("Maria (06/07)" in xx for xx in x)
        assert any("João (05/07)" in xx for xx in x)
        # Checa valores das barras (a ordem depende do sort!)
        assert 1000.0 in y_faturado
        assert 200.0 in y_aprovada
        assert 500.0 in y_aguardando
        assert fig.layout.title.text.startswith("Total de Vendas (R$) por Vendedor")
        return "<div>grafico-fds-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_fim_de_semana(2025, 7)
    assert html == "<div>grafico-fds-dados</div>"

def test_grafico_fim_de_semana_um_vendedor_um_dia(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Só Maria, só um dia/status
            return [{
                "_id": {
                    "dia": 7, "mes": 7, "ano": 2025,
                    "vendedor": "Maria", "status": "Faturado"
                },
                "total": 333.0
            }]
    def fake_to_html(fig, **kwargs):
        x = list(fig.data[0].x)
        y = list(fig.data[0].y)
        assert "Maria (07/07)" in x
        assert 333.0 in y
        return "<div>grafico-fds-um-vendedor-um-dia</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_vendas_fim_de_semana(2025, 7)
    assert html == "<div>grafico-fds-um-vendedor-um-dia</div>"
