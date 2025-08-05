import pytest
from app.graficos import gerar_grafico_quantidade_vendas_fim_de_semana

def test_grafico_quantidade_fds_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Vendas por Status no Fim de Semana")
        assert fig.layout.xaxis.title.text == "Vendedor / Dia"
        return "<div>grafico-quantidade-fds-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_quantidade_vendas_fim_de_semana(2025, 7)
    assert html == "<div>grafico-quantidade-fds-vazio</div>"

def test_grafico_quantidade_fds_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Maria vendeu 2 no sábado (1 aprovada, 1 faturado), João vendeu 1 no domingo (aguardando)
            return [
                {
                    "_id": {
                        "dia": 5, "mes": 7, "ano": 2025,
                        "vendedor": "Maria", "status": "Faturado"
                    },
                    "quantidade": 1
                },
                {
                    "_id": {
                        "dia": 5, "mes": 7, "ano": 2025,
                        "vendedor": "Maria", "status": "Aprovada"
                    },
                    "quantidade": 1
                },
                {
                    "_id": {
                        "dia": 6, "mes": 7, "ano": 2025,
                        "vendedor": "João", "status": "Aguardando"
                    },
                    "quantidade": 1
                }
            ]
    def fake_to_html(fig, **kwargs):
        x = list(fig.data[0].x)
        # Checa se as barras para vendedor/dia aparecem corretamente
        assert "Maria (05/07)" in x
        assert "João (06/07)" in x
        # Verifica valores por status
        y_faturado = list(fig.data[0].y)
        y_aprovada = list(fig.data[1].y)
        y_aguardando = list(fig.data[2].y)
        assert 1 in y_faturado
        assert 1 in y_aprovada
        assert 1 in y_aguardando
        assert fig.layout.title.text.startswith("Status das Vendas por Vendedor")
        return "<div>grafico-quantidade-fds-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_quantidade_vendas_fim_de_semana(2025, 7)
    assert html == "<div>grafico-quantidade-fds-dados</div>"

def test_grafico_quantidade_fds_um_vendedor_um_dia(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return [{
                "_id": {
                    "dia": 7, "mes": 7, "ano": 2025,
                    "vendedor": "Maria", "status": "Faturado"
                },
                "quantidade": 2
            }]
    def fake_to_html(fig, **kwargs):
        x = list(fig.data[0].x)
        y = list(fig.data[0].y)
        assert "Maria (07/07)" in x
        assert 2 in y
        return "<div>grafico-quantidade-fds-um-vendedor-um-dia</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_quantidade_vendas_fim_de_semana(2025, 7)
    assert html == "<div>grafico-quantidade-fds-um-vendedor-um-dia</div>"
