import pytest
from app.graficos import gerar_grafico_tipo_vendas_geral

def test_grafico_tipo_vendas_geral_sem_vendas(monkeypatch):
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
    html = gerar_grafico_tipo_vendas_geral(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"]

def test_grafico_tipo_vendas_geral_com_dados(monkeypatch):
    # 2 vendas novas, 1 atualização ("atualização" e "atualizacao")
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"produto": "X1"},               # nova
                {"produto": "atualização"},      # atualização
                {"produto": "Y2"},               # nova
                {"produto": "atualizacao"}       # atualização
            ]
    def fake_to_html(fig, **kwargs):
        pie = fig.data[0]
        labels = list(pie.labels)
        values = list(pie.values)
        # Os valores devem ser [2, 2]: 2 novas, 2 atualizações
        idx_novas = labels.index("Vendas Novas")
        idx_atual = labels.index("Atualizações")
        assert values[idx_novas] == 2
        assert values[idx_atual] == 2
        return "<div>grafico-pizza</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_geral(2025, 7)
    assert html == "<div>grafico-pizza</div>"

def test_grafico_tipo_vendas_geral_com_dados_dezembro(monkeypatch):
    # 2 vendas novas, 1 atualização ("atualização" e "atualizacao")
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"produto": "X1"},               # nova
                {"produto": "atualização"},      # atualização
                {"produto": "Y2"},               # nova
                {"produto": "atualizacao"}       # atualização
            ]
    def fake_to_html(fig, **kwargs):
        pie = fig.data[0]
        labels = list(pie.labels)
        values = list(pie.values)
        # Os valores devem ser [2, 2]: 2 novas, 2 atualizações
        idx_novas = labels.index("Vendas Novas")
        idx_atual = labels.index("Atualizações")
        assert values[idx_novas] == 2
        assert values[idx_atual] == 2
        return "<div>grafico-pizza</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_geral(2025, 12)
    assert html == "<div>grafico-pizza</div>"

def test_grafico_tipo_vendas_geral_so_novas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"produto": "Qualquer"} for _ in range(5)]
    def fake_to_html(fig, **kwargs):
        pie = fig.data[0]
        labels = list(pie.labels)
        values = list(pie.values)
        assert labels[0] == "Vendas Novas"
        assert values[0] == 5
        assert values[1] == 0
        return "<div>grafico-so-novas</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_geral(2025, 7)
    assert html == "<div>grafico-so-novas</div>"

def test_grafico_tipo_vendas_geral_so_atualizacoes(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"produto": "atualização"}, {"produto": "atualizacao"}]
    def fake_to_html(fig, **kwargs):
        pie = fig.data[0]
        labels = list(pie.labels)
        values = list(pie.values)
        assert labels[1] == "Atualizações"
        assert values[1] == 2
        assert values[0] == 0
        return "<div>grafico-so-atualizacoes</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_geral(2025, 7)
    assert html == "<div>grafico-so-atualizacoes</div>"
