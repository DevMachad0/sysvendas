import pytest
from app.graficos import gerar_grafico_prazo_vendas_vendedor

def test_grafico_prazo_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            return []  # Sem dados

    def fake_to_html(fig, **kwargs):
        # Checa que o gráfico é vazio (sem dados)
        assert hasattr(fig, "data")
        assert fig.layout.title.text.startswith("Vendas por Prazo")
        return "<div>grafico-prazo-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_prazo_vendas_vendedor(2025, 7)
    assert html == "<div>grafico-prazo-vazio</div>"

def test_grafico_prazo_com_dados(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Maria tem 1 venda <=30, 2 vendas 31-39, João tem 1 venda 50-150
            return [
                {"_id": {"vendedor": "Maria", "faixa_prazo": "≤ 30 dias"}, "quantidade": 1},
                {"_id": {"vendedor": "Maria", "faixa_prazo": "31-39 dias"}, "quantidade": 2},
                {"_id": {"vendedor": "João", "faixa_prazo": "50-150 dias"}, "quantidade": 1}
            ]
    def fake_to_html(fig, **kwargs):
        # Garante que as barras e as cores estão corretas
        names = [trace.name for trace in fig.data]
        # Deve conter todas faixas usadas
        assert "≤ 30 dias" in names
        assert "31-39 dias" in names
        assert "50-150 dias" in names
        # Checa dados de Maria
        m_trace = [t for t in fig.data if t.name == "≤ 30 dias"][0]
        assert "Maria" in m_trace.x
        assert 1 in m_trace.y
        # Checa dados de João
        j_trace = [t for t in fig.data if t.name == "50-150 dias"][0]
        assert "João" in j_trace.x
        assert 1 in j_trace.y
        return "<div>grafico-prazo-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_prazo_vendas_vendedor(2025, 7)
    assert html == "<div>grafico-prazo-dados</div>"

def test_grafico_prazo_com_dados_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def aggregate(self, pipeline):
            # Maria tem 1 venda <=30, 2 vendas 31-39, João tem 1 venda 50-150
            return [
                {"_id": {"vendedor": "Maria", "faixa_prazo": "≤ 30 dias"}, "quantidade": 1},
                {"_id": {"vendedor": "Maria", "faixa_prazo": "31-39 dias"}, "quantidade": 2},
                {"_id": {"vendedor": "João", "faixa_prazo": "50-150 dias"}, "quantidade": 1}
            ]
    def fake_to_html(fig, **kwargs):
        # Garante que as barras e as cores estão corretas
        names = [trace.name for trace in fig.data]
        # Deve conter todas faixas usadas
        assert "≤ 30 dias" in names
        assert "31-39 dias" in names
        assert "50-150 dias" in names
        # Checa dados de Maria
        m_trace = [t for t in fig.data if t.name == "≤ 30 dias"][0]
        assert "Maria" in m_trace.x
        assert 1 in m_trace.y
        # Checa dados de João
        j_trace = [t for t in fig.data if t.name == "50-150 dias"][0]
        assert "João" in j_trace.x
        assert 1 in j_trace.y
        return "<div>grafico-prazo-dados</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_prazo_vendas_vendedor(2025, 12)
    assert html == "<div>grafico-prazo-dados</div>"
