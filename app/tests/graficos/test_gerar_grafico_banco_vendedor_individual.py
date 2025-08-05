import pytest
from app.graficos import gerar_grafico_banco_vendedor_individual

def test_grafico_banco_individual_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    class FakeConfigsCollection:
        pass
    
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        return "<div>grafico-banco-vazio</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_banco_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-banco-vazio</div>"
    assert chamado["foi"]

def test_grafico_banco_individual_crescimento(monkeypatch):
    """Vendedor ganhou saldo (vendeu acima do valor de tabela)."""
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # R$1200 vendido, tabela R$1000, autorizado True (não desconta), deve somar 200
            return [{"vendedor": "Maria Silva", "valor_tabela": "1000", "valor_real": "1200", "desconto_autorizado": True}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria Silva", "limite": 500.0}]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        nome = bars.x[0]
        valor = bars.y[0]
        cor = bars.marker.color[0]
        texto = bars.text[0]
        # Ganhou 200, saldo 700
        assert nome == "Maria Silva"
        assert valor == 700.0
        assert cor == "green"
        assert "700" in texto
        return "<div>grafico-banco-ganho</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_banco_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-banco-ganho</div>"

def test_grafico_banco_individual_diminui_dezembro(monkeypatch):
    """Vendedor ganhou saldo (vendeu acima do valor de tabela)."""
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"vendedor": "Maria Silva", "valor_tabela": "1000", "valor_real": "900", "desconto_autorizado": False}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria Silva", "limite": 500.0}]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        nome = bars.x[0]
        valor = bars.y[0]
        cor = bars.marker.color[0]
        texto = bars.text[0]
        # Ganhou 200, saldo 700
        assert nome == "Maria Silva"
        assert valor == 400.00
        assert cor == "blue"
        assert "400" in texto
        return "<div>grafico-banco-ganho</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_banco_vendedor_individual(2025, 12, "maria123")
    assert html == "<div>grafico-banco-ganho</div>"

def test_grafico_banco_individual_desconto_nao_autorizado(monkeypatch):
    """Vendedor perdeu saldo por desconto não autorizado."""
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # R$900 vendido, tabela R$1000, não autorizado: perde 100
            return [{"vendedor": "Maria Silva", "valor_tabela": "1000", "valor_real": "900", "desconto_autorizado": False}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria Silva", "limite": 100.0}]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        nome = bars.x[0]
        valor = bars.y[0]
        cor = bars.marker.color[0]
        texto = bars.text[0]
        # Perdeu 100, saldo zero
        assert nome == "Maria Silva"
        assert valor == 0.0
        assert cor == "red"
        assert "0,00" in texto
        return "<div>grafico-banco-desconto</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_banco_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-banco-desconto</div>"

def test_grafico_banco_individual_zerou(monkeypatch):
    """Saldo ficou zerado por soma de ganhos e perdas."""
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Ganha 200, perde 200
            return [
                {"vendedor": "Maria Silva", "valor_tabela": "1000", "valor_real": "1200", "desconto_autorizado": True},
                {"vendedor": "Maria Silva", "valor_tabela": "1000", "valor_real": "800", "desconto_autorizado": False}
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria Silva", "limite": 0.0}]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        valor = bars.y[0]
        cor = bars.marker.color[0]
        assert valor == 0.0
        assert cor == "red"
        return "<div>grafico-banco-zero</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_banco_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-banco-zero</div>"

def test_grafico_banco_individual_abaixou(monkeypatch):
    """Saldo ficou negativo."""
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria Silva"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Perdeu 200, saldo inicial era 50, saldo final -150
            return [{"vendedor": "Maria Silva", "valor_tabela": "1000", "valor_real": "800", "desconto_autorizado": False}]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria Silva", "limite": 50.0}]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        valor = bars.y[0]
        cor = bars.marker.color[0]
        assert valor == -150.0
        assert cor == "red"
        return "<div>grafico-banco-negativo</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_banco_vendedor_individual(2025, 7, "maria123")
    assert html == "<div>grafico-banco-negativo</div>"
