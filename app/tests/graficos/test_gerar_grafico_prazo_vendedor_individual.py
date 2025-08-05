import pytest
from app.graficos import gerar_grafico_prazo_vendedor_individual

def test_grafico_prazo_individual_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}] if filtro.get('username') == 'maria' else []
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Suas Vendas por Prazo")
        return "<div>grafico-individual-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_prazo_vendedor_individual(username='maria')
    assert html == "<div>grafico-individual-vazio</div>"

def test_grafico_prazo_individual_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}] if filtro.get('username') == 'maria' else []
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # 1 venda <=30, 2 vendas 31-39, 1 venda 40-49
            return [
                {"_id": "≤ 30 dias", "quantidade": 1},
                {"_id": "31-39 dias", "quantidade": 2},
                {"_id": "40-49 dias", "quantidade": 1}
            ]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        # O plotly só inclui barras de valor > 0
        faixas_obtidas = list(bars.x)
        quantidades_obtidas = [int(q) for q in bars.y]
        esperados = {"≤ 30 dias": 1, "31-39 dias": 2, "40-49 dias": 1, "50-150 dias": 0}

        for faixa, quantidade in zip(faixas_obtidas, quantidades_obtidas):
            assert esperados[faixa] == quantidade
        
        return "<div>grafico-individual-prazo-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_prazo_vendedor_individual(username='maria')
    assert html == "<div>grafico-individual-prazo-dados</div>"

def test_grafico_prazo_individual_com_dados_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}] if filtro.get('username') == 'maria' else []
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # 1 venda <=30, 2 vendas 31-39, 1 venda 40-49
            return [
                {"_id": "≤ 30 dias", "quantidade": 1},
                {"_id": "31-39 dias", "quantidade": 2},
                {"_id": "40-49 dias", "quantidade": 1}
            ]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        # O plotly só inclui barras de valor > 0
        faixas_obtidas = list(bars.x)
        quantidades_obtidas = [int(q) for q in bars.y]
        esperados = {"≤ 30 dias": 1, "31-39 dias": 2, "40-49 dias": 1, "50-150 dias": 0}

        for faixa, quantidade in zip(faixas_obtidas, quantidades_obtidas):
            assert esperados[faixa] == quantidade
        
        return "<div>grafico-individual-prazo-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_prazo_vendedor_individual(mes=12, username='maria')
    assert html == "<div>grafico-individual-prazo-dados</div>"

def test_grafico_prazo_individual_usuario_nao_encontrado(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    html = gerar_grafico_prazo_vendedor_individual(username='fulano')
    assert "Usuário não encontrado" in html
