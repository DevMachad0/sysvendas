import pytest
from datetime import datetime, timedelta
from app.graficos import gerar_grafico_metas_semanais_vendedor_individual

def test_grafico_meta_semanal_usuario_inexistente(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    html = gerar_grafico_metas_semanais_vendedor_individual("nao_existe")
    assert "Usuário não encontrado" in html

def test_grafico_meta_semanal_bateu_meta(monkeypatch):
    hoje = datetime.today()
    data_criacao = hoje  # venda é feita na semana atual
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "João Silva"}]
    class FakeConfigsCollection:
        def find_one(self, filtro):
            return {"meta_semana": 2000.0, "vendedor_nome": "João Silva"}
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # valor total vendido: 2500 (meta era 2000)
            return [{"valor_real": "2500", "data_criacao": data_criacao}]
    def fake_to_html(fig, **kwargs):
        bar = fig.data[0]
        assert bar.marker.color[0] == "green"
        texto = bar.text[0]
        assert "Meta batida" in texto
        assert "R$ 2.500,00 (meta R$ 2.000,00)" in texto
        return "<div>grafico-meta-semanal-ok</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_metas_semanais_vendedor_individual("joao123")
    assert html == "<div>grafico-meta-semanal-ok</div>"

def test_grafico_meta_semanal_nao_bateu(monkeypatch):
    hoje = datetime.today()
    data_criacao = hoje
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Ana"}]
    class FakeConfigsCollection:
        def find_one(self, filtro):
            return {"meta_semana": 3000.0, "vendedor_nome": "Ana"}
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # valor total vendido: 1000 (meta era 3000)
            return [{"valor_real": "1000", "data_criacao": data_criacao}]
    def fake_to_html(fig, **kwargs):
        bar = fig.data[0]
        assert bar.marker.color[0] == "red"
        texto = bar.text[0]
        assert "Meta não batida" in texto
        assert "R$ 1.000,00 (meta R$ 3.000,00)" in texto
        return "<div>grafico-meta-semanal-nao-bateu</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_metas_semanais_vendedor_individual("ana")
    assert html == "<div>grafico-meta-semanal-nao-bateu</div>"

def test_grafico_meta_semanal_zero_vendas(monkeypatch):
    hoje = datetime.today()
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Carlos"}]
    class FakeConfigsCollection:
        def find_one(self, filtro):
            return {"meta_semana": 1500.0, "vendedor_nome": "Carlos"}
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    def fake_to_html(fig, **kwargs):
        bar = fig.data[0]
        assert bar.marker.color[0] == "red"
        texto = bar.text[0]
        assert "Meta não batida" in texto
        assert "R$ 0,00 (meta R$ 1.500,00)" in texto
        return "<div>grafico-meta-semanal-zerada</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_metas_semanais_vendedor_individual("carlos")
    assert html == "<div>grafico-meta-semanal-zerada</div>"
