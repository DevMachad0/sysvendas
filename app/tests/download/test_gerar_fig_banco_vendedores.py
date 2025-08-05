import pytest
from app.download import gerar_fig_banco_vendedores

def test_fig_banco_vendedores_vazio(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    class FakeConfigsCollection:
        pass
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    
    fig = gerar_fig_banco_vendedores(2025, 7)
    assert fig.layout.title.text == "Saldo do Banco por Vendedor"
    assert fig.layout.xaxis.title.text == "Sem dados de vendas"
    assert fig.layout.width == 1600
    assert fig.layout.height == 600
    # Gráfico vazio não deve ter barras
    assert len(fig.data) == 0 or (hasattr(fig.data[0], "x") and len(fig.data[0].x) == 0)

def test_fig_banco_vendedores_com_dados(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Maria tem desconto NÃO autorizado (-200), João teve ganho (+100)
            return [
                {'vendedor': 'Maria', 'valor_tabela': 1000, 'valor_real': 800, 'desconto_autorizado': False},
                {'vendedor': 'João', 'valor_tabela': 900, 'valor_real': 1000, 'desconto_autorizado': True}
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor_nome': 'Maria', 'limite': 1500},
                {'vendedor_nome': 'João', 'limite': 800}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())

    fig = gerar_fig_banco_vendedores(2025, 7)
    # Os nomes dos vendedores devem aparecer
    barras = fig.data[0]
    vendedores = list(barras.x)
    assert 'Maria' in vendedores
    assert 'João' in vendedores
    # Maria: saldo_novo = 1500 - 200 = 1300 (blue)
    # João: saldo_novo = 800 + 100 = 900 (green)
    idx_maria = vendedores.index('Maria')
    idx_joao = vendedores.index('João')
    assert abs(barras.y[idx_maria] - 1300) < 1e-4
    assert abs(barras.y[idx_joao] - 900) < 1e-4
    assert barras.marker.color[idx_maria] == "blue"
    assert barras.marker.color[idx_joao] == "green"
    assert "Saldo: R$ 1.300,00" in barras.text[idx_maria]
    assert "Saldo: R$ 900,00" in barras.text[idx_joao]
    # Checa se layout está correto
    assert fig.layout.title.text == "Saldo do Banco por Vendedor"

def test_fig_banco_vendedores_dezembro(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Não importa muito os dados, só queremos cobrir o if mes == 12
            return []
    class FakeConfigsCollection:
        pass
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    
    # Chama com mês=12
    fig = gerar_fig_banco_vendedores(2025, 12)
    assert fig.layout.title.text == "Saldo do Banco por Vendedor"

def test_fig_banco_vendedores_todos_negativos(monkeypatch):
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor': 'Maria', 'valor_tabela': 1000, 'valor_real': 200, 'desconto_autorizado': False},
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [
                {'vendedor_nome': 'Maria', 'limite': 100}
            ]
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.download.configs_collection", FakeConfigsCollection())
    fig = gerar_fig_banco_vendedores(2025, 7)
    barras = fig.data[0]
    vendedores = list(barras.x)
    assert vendedores == ['Maria']
    # Saldo novo: 100 - 800 = -700 (vermelho)
    assert barras.marker.color[0] == "red"
    assert "Saldo: R$ -700,00" in barras.text[0]

