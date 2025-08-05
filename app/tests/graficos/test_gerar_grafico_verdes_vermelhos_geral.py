import pytest
from datetime import datetime
from app.graficos import gerar_grafico_verdes_vermelhos_geral

def test_grafico_verdes_vermelhos_geral_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
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
    html = gerar_grafico_verdes_vermelhos_geral(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"]

def test_grafico_verdes_vermelhos_geral_todos(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # 3 verdes, 2 vermelhos, 1 outro
            return [
                {"tipo_cliente": "verde"},
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "vermelho"},
                {"tipo_cliente": "Vermelho"},
                {"tipo_cliente": "azul"},
            ]
    def fake_to_html(fig, **kwargs):
        # Garantir que tem 3 verdes e 2 vermelhos
        pie = fig.data[0]
        label_valor = dict(zip(pie.labels, pie.values))
        assert label_valor["Verde"] == 3
        assert label_valor["Vermelho"] == 2
        assert set(pie.labels) == {"Verde", "Vermelho"}
        return "<div>grafico-pizza</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_geral(2025, 7)
    assert html == "<div>grafico-pizza</div>"

def test_grafico_verdes_vermelhos_geral_todos_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # 3 verdes, 2 vermelhos, 1 outro
            return [
                {"tipo_cliente": "verde"},
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "Verde"},
                {"tipo_cliente": "vermelho"},
                {"tipo_cliente": "Vermelho"},
                {"tipo_cliente": "azul"},
            ]
    def fake_to_html(fig, **kwargs):
        # Garantir que tem 3 verdes e 2 vermelhos
        pie = fig.data[0]
        label_valor = dict(zip(pie.labels, pie.values))
        assert label_valor["Verde"] == 3
        assert label_valor["Vermelho"] == 2
        assert set(pie.labels) == {"Verde", "Vermelho"}
        return "<div>grafico-pizza</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_geral(2025, 12)
    assert html == "<div>grafico-pizza</div>"

def test_grafico_verdes_vermelhos_geral_sem_verde_e_vermelho(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # 3 verdes, 2 vermelhos, 1 outro
            return [
                {"tipo_cliente": "azul"},
                {"tipo_cliente": "azul"},
                {"tipo_cliente": "azul"},
                {"tipo_cliente": "azul"},
                {"tipo_cliente": "azul"},
                {"tipo_cliente": "azul"},
            ]
    def fake_to_html(fig, **kwargs):
        assert fig.layout.xaxis.title.text == 'Sem dados'
        return "<div>grafico-pizza</div>"
    
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_geral(2025, 12)
    assert html == "<div>grafico-pizza</div>"

def test_grafico_verdes_vermelhos_geral_somente_verde(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"tipo_cliente": "verde"} for _ in range(5)]
    def fake_to_html(fig, **kwargs):
        pie = fig.data[0]
        label_valor = dict(zip(pie.labels, pie.values))
        assert label_valor["Verde"] == 5
        assert "Vermelho" not in label_valor or label_valor["Vermelho"] == 0
        return "<div>grafico-verde</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_geral(2025, 7)
    assert html == "<div>grafico-verde</div>"

def test_grafico_verdes_vermelhos_geral_somente_vermelho(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"tipo_cliente": "vermelho"} for _ in range(4)]
    def fake_to_html(fig, **kwargs):
        pie = fig.data[0]
        label_valor = dict(zip(pie.labels, pie.values))
        assert label_valor["Vermelho"] == 4
        assert "Verde" not in label_valor or label_valor["Verde"] == 0
        return "<div>grafico-vermelho</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_geral(2025, 7)
    assert html == "<div>grafico-vermelho</div>"
