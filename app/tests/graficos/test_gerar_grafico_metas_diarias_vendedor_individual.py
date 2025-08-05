import pytest
from datetime import datetime
from app.graficos import gerar_grafico_metas_diarias_vendedor_individual

def test_grafico_metas_diarias_usuario_inexistente(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    html = gerar_grafico_metas_diarias_vendedor_individual("nao_existe")
    assert "Usuário não encontrado" in html

def test_grafico_metas_diarias_bateu_meta_valor(monkeypatch):
    hoje = datetime.today()
    data_criacao = datetime(hoje.year, hoje.month, hoje.day, 8, 0)
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "João Silva"}]
    class FakeConfigsCollection:
        def find_one(self, filtro):
            return {"meta_dia_quantidade": 3, "meta_dia_valor": 100.0, "vendedor_nome": "João Silva"}
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Totaliza 150 (meta era 100)
            return [{"valor_real": "150.0", "data_criacao": data_criacao}]
    def fake_to_html(fig, **kwargs):
        bar = fig.data[0]
        assert bar.marker.color[0] == "green"
        texto = bar.text[0]
        assert "Meta batida" in texto
        assert "Qtd: 1 (meta 3)" in texto  # meta por quantidade não batida
        assert "Valor: R$ 150,00 (meta R$ 100,00)" in texto
        return "<div>grafico-meta-valor-ok</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_diarias_vendedor_individual("joao123")
    assert html == "<div>grafico-meta-valor-ok</div>"

def test_grafico_metas_diarias_nao_bateu(monkeypatch):
    hoje = datetime.today()
    data_criacao = datetime(hoje.year, hoje.month, hoje.day, 8, 0)
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Ana"}]
    class FakeConfigsCollection:
        def find_one(self, filtro):
            return {"meta_dia_quantidade": 2, "meta_dia_valor": 300.0, "vendedor_nome": "Ana"}
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # 1 venda de R$100
            return [{"valor_real": "100", "data_criacao": data_criacao}]
    def fake_to_html(fig, **kwargs):
        bar = fig.data[0]
        assert bar.marker.color[0] == "red"
        texto = bar.text[0]
        assert "Meta não batida" in texto
        return "<div>grafico-meta-nao-bateu</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_metas_diarias_vendedor_individual("ana")
    assert html == "<div>grafico-meta-nao-bateu</div>"

def test_grafico_metas_diarias_bateu_meta_quantidade(monkeypatch):
    hoje = datetime.today()
    data_criacao = datetime(hoje.year, hoje.month, hoje.day, 9, 0)
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Carlos"}]
    class FakeConfigsCollection:
        def find_one(self, filtro):
            return {"meta_dia_quantidade": 2, "meta_dia_valor": 5000, "vendedor_nome": "Carlos"}
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # 2 vendas pequenas, meta por qtd batida
            return [
                {"valor_real": "10", "data_criacao": data_criacao},
                {"valor_real": "15", "data_criacao": data_criacao}
            ]
    def fake_to_html(fig, **kwargs):
        bar = fig.data[0]
        assert bar.marker.color[0] == "green"
        texto = bar.text[0]
        assert "Meta batida" in texto
        assert "Qtd: 2 (meta 2)" in texto
        return "<div>grafico-meta-qtd-ok</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_metas_diarias_vendedor_individual("carlos")
    assert html == "<div>grafico-meta-qtd-ok</div>"
