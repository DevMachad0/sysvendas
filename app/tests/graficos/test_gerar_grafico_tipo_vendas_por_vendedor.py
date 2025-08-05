import pytest
from collections import defaultdict
from app.graficos import gerar_grafico_tipo_vendas_por_vendedor

def test_grafico_tipo_vendas_sem_vendas(monkeypatch):
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
    html = gerar_grafico_tipo_vendas_por_vendedor(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"]

def test_grafico_tipo_vendas_novas_e_atualizacoes(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Maria faz 2 novas e 1 atualização, João só 1 nova
            return [
                {"vendedor": "Maria", "produto": "Produto X"},
                {"vendedor": "Maria", "produto": "Atualização"},
                {"vendedor": "Maria", "produto": "Produto Y"},
                {"vendedor": "João", "produto": "Produto Z"},
                {"vendedor": "João", "produto": "Atualizacao"},  # variação sem acento
            ]
    def fake_to_html(fig, **kwargs):
        barras_novas = fig.data[0]
        barras_atualiz = fig.data[1]
        # Mapear vendedor para valores (ordem não garantida)
        d_novas = dict(zip(barras_novas.x, barras_novas.y))
        d_atu = dict(zip(barras_atualiz.x, barras_atualiz.y))
        # Maria: 2 novas, 1 atualização; João: 1 nova, 1 atualização
        assert d_novas["Maria"] == 2
        assert d_atu["Maria"] == 1
        assert d_novas["João"] == 1
        assert d_atu["João"] == 1
        return "<div>grafico-misto</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_por_vendedor(2025, 7)
    assert html == "<div>grafico-misto</div>"

def test_grafico_tipo_vendas_novas_e_atualizacoes_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Maria faz 2 novas e 1 atualização, João só 1 nova
            return [
                {"vendedor": "Maria", "produto": "Produto X"},
                {"vendedor": "Maria", "produto": "Atualização"},
                {"vendedor": "Maria", "produto": "Produto Y"},
                {"vendedor": "João", "produto": "Produto Z"},
                {"vendedor": "João", "produto": "Atualizacao"},  # variação sem acento
            ]
    def fake_to_html(fig, **kwargs):
        barras_novas = fig.data[0]
        barras_atualiz = fig.data[1]
        # Mapear vendedor para valores (ordem não garantida)
        d_novas = dict(zip(barras_novas.x, barras_novas.y))
        d_atu = dict(zip(barras_atualiz.x, barras_atualiz.y))
        # Maria: 2 novas, 1 atualização; João: 1 nova, 1 atualização
        assert d_novas["Maria"] == 2
        assert d_atu["Maria"] == 1
        assert d_novas["João"] == 1
        assert d_atu["João"] == 1
        return "<div>grafico-misto</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_por_vendedor(2025, 12)
    assert html == "<div>grafico-misto</div>"

def test_grafico_tipo_vendas_produto_none(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Maria faz 2 novas e 1 atualização, João só 1 nova
            return [
                {"vendedor": "Maria", "produto": None},
                {"vendedor": "Maria", "produto": "Atualização"},
                {"vendedor": "Maria", "produto": "Produto Y"},
                {"vendedor": "João", "produto": "Produto Z"},
                {"vendedor": "João", "produto": "Atualizacao"},  # variação sem acento
            ]
    def fake_to_html(fig, **kwargs):
        barras_novas = fig.data[0]
        barras_atualiz = fig.data[1]
        # Mapear vendedor para valores (ordem não garantida)
        d_novas = dict(zip(barras_novas.x, barras_novas.y))
        d_atu = dict(zip(barras_atualiz.x, barras_atualiz.y))
        # Maria: 2 novas, 1 atualização; João: 1 nova, 1 atualização
        assert d_novas["Maria"] == 1
        assert d_atu["Maria"] == 1
        assert d_novas["João"] == 1
        assert d_atu["João"] == 1
        return "<div>grafico-misto</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_por_vendedor(2025, 12)
    assert html == "<div>grafico-misto</div>"

def test_grafico_tipo_vendas_somente_novas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "produto": "Produto X"},
                {"vendedor": "Maria", "produto": "Produto Y"},
            ]
    def fake_to_html(fig, **kwargs):
        barras_novas = fig.data[0]
        barras_atualiz = fig.data[1]
        assert barras_novas.y == (2,)
        assert barras_atualiz.y == (0,)
        return "<div>grafico-novas</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_por_vendedor(2025, 7)
    assert html == "<div>grafico-novas</div>"

def test_grafico_tipo_vendas_somente_atualizacoes(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "produto": "Atualização"},
                {"vendedor": "Maria", "produto": "Atualizacao"},
            ]
    def fake_to_html(fig, **kwargs):
        barras_novas = fig.data[0]
        barras_atualiz = fig.data[1]
        assert barras_novas.y == (0,)
        assert barras_atualiz.y == (2,)
        return "<div>grafico-atualizacoes</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_tipo_vendas_por_vendedor(2025, 7)
    assert html == "<div>grafico-atualizacoes</div>"

