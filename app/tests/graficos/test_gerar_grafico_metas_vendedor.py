import pytest
from app.graficos import gerar_grafico_metas_vendedor

def test_gerar_grafico_metas_vendedor_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria", "meta_mes": "10000"}]
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

    html = gerar_grafico_metas_vendedor(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"] is True

def test_gerar_grafico_metas_vendedor_sem_metas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return []
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_real": "1000", "status": "Aprovada"}
            ]
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        return "<div>grafico-sem-meta</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_vendedor(2025, 7)
    assert html == "<div>grafico-sem-meta</div>"
    assert chamado["foi"] is True

def test_gerar_grafico_metas_vendedor_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [
                {"nome_completo": "Maria", "meta_mes": "5000"},
                {"nome_completo": "João", "meta_mes": "8000"}
            ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_real": "2000", "status": "Aprovada"},
                {"vendedor": "Maria", "valor_real": "2000", "status": "Faturado"},
                {"vendedor": "Maria", "valor_real": "1000", "status": "Faturado"},
                {"vendedor": "João", "valor_real": "1000", "status": "Aprovada"},
                {"vendedor": "João", "valor_real": "3000", "status": "Faturado"},
                {"vendedor": "João", "valor_real": "4000", "status": "Faturado"},
            ]
    def fake_to_html(fig, **kwargs):
        # Checa se nomes, vendidos e faltando estão corretos
        vendidos = fig.data[0].x
        vendedores = fig.data[0].y
        faltando = fig.data[1].x
        assert list(vendedores) == ["Maria", "João"]
        assert vendidos[vendedores.index("Maria")] == 5000
        assert faltando[vendedores.index("Maria")] == 0
        assert vendidos[vendedores.index("João")] == 8000
        assert faltando[vendedores.index("João")] == 0
        return "<div>grafico-metas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_vendedor(2025, 7)
    assert html == "<div>grafico-metas</div>"

def test_gerar_grafico_metas_vendedor_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [
                {"nome_completo": "Maria", "meta_mes": "5000"},
                {"nome_completo": "João", "meta_mes": "8000"}
            ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_real": "2000", "status": "Aprovada"},
                {"vendedor": "Maria", "valor_real": "2000", "status": "Faturado"},
                {"vendedor": "Maria", "valor_real": "1000", "status": "Faturado"},
                {"vendedor": "João", "valor_real": "1000", "status": "Aprovada"},
                {"vendedor": "João", "valor_real": "3000", "status": "Faturado"},
                {"vendedor": "João", "valor_real": "4000", "status": "Faturado"},
            ]
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text == 'Progresso de Vendas por Vendedor'
        return "<div>grafico-metas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_vendedor(2025, 12)
    assert html == "<div>grafico-metas</div>"

def test_gerar_grafico_metas_vendedor_status_cancelada(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [
                {"nome_completo": "Maria", "meta_mes": "5000"},
                {"nome_completo": "João", "meta_mes": "8000"}
            ]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_real": "2000", "status": "Cancelada"},
                {"vendedor": "João", "valor_real": "1000", "status": "Aprovada"},
                {"vendedor": "João", "valor_real": "3000", "status": "Faturado"},
                {"vendedor": "João", "valor_real": "4000", "status": "Faturado"},
            ]
    def fake_to_html(fig, **kwargs):
        vendidos = fig.data[0].x
        vendedores = fig.data[0].y
        assert list(vendedores) == ["Maria", "João"]
        assert vendidos[vendedores.index("Maria")] == 0
        assert fig.layout.title.text == 'Progresso de Vendas por Vendedor'
        return "<div>grafico-metas</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_vendedor(2025, 7)
    assert html == "<div>grafico-metas</div>"
