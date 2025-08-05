import pytest
from app.graficos import gerar_grafico_produtos_mais_vendidos

def test_grafico_produtos_mais_vendidos_vazio(monkeypatch):
    # Nenhum produto cadastrado, nenhuma venda
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return []
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Produtos mais Vendidos")
        # Não deve ter nenhuma barra
        assert len(fig.data) == 1
        assert len(fig.data[0].x) == 0
        return "<div>grafico-produtos-vazio</div>"

    monkeypatch.setattr("app.graficos.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_produtos_mais_vendidos(2025, 7)
    assert html == "<div>grafico-produtos-vazio</div>"

def test_grafico_produtos_mais_vendidos_com_dados(monkeypatch):
    # Dois produtos cadastrados, um vendido duas vezes, outro uma vez
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Produto A"}, {"nome": "Produto B"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Produto A vendido duas vezes, Produto B uma vez, um produto inexistente ignorado
            return [
                {"produto": "Produto A"},
                {"produto": "Produto A"},
                {"produto": "Produto B"},
                {"produto": "Inexistente"}
            ]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        produtos = list(bars.y)
        quantidades = list(bars.x)
        assert "Produto A" in produtos
        assert "Produto B" in produtos
        assert 2 in quantidades
        assert 1 in quantidades
        assert len(produtos) == 2
        # Produto A tem mais vendas que Produto B
        assert quantidades[produtos.index("Produto A")] == 2
        return "<div>grafico-produtos-dados</div>"

    monkeypatch.setattr("app.graficos.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_produtos_mais_vendidos(2025, 7)
    assert html == "<div>grafico-produtos-dados</div>"

def test_grafico_produtos_mais_vendidos_com_dados_dezembro(monkeypatch):
    # Dois produtos cadastrados, um vendido duas vezes, outro uma vez
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Produto A"}, {"nome": "Produto B"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Produto A vendido duas vezes, Produto B uma vez, um produto inexistente ignorado
            return [
                {"produto": "Produto A"},
                {"produto": "Produto A"},
                {"produto": "Produto B"},
                {"produto": "Inexistente"}
            ]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        produtos = list(bars.y)
        quantidades = list(bars.x)
        assert "Produto A" in produtos
        assert "Produto B" in produtos
        assert 2 in quantidades
        assert 1 in quantidades
        assert len(produtos) == 2
        # Produto A tem mais vendas que Produto B
        assert quantidades[produtos.index("Produto A")] == 2
        return "<div>grafico-produtos-dados</div>"

    monkeypatch.setattr("app.graficos.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_produtos_mais_vendidos(2025, 12)
    assert html == "<div>grafico-produtos-dados</div>"

def test_grafico_produtos_sem_venda(monkeypatch):
    # Produtos cadastrados mas ninguém vendeu nada no mês
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Produto X"}, {"nome": "Produto Y"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    def fake_to_html(fig, **kwargs):
        assert fig.layout.title.text.startswith("Produtos mais Vendidos")
        # Não há barras
        assert len(fig.data) == 1
        assert len(fig.data[0].x) == 0
        return "<div>grafico-produtos-sem-venda</div>"

    monkeypatch.setattr("app.graficos.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_produtos_mais_vendidos(2025, 7)
    assert html == "<div>grafico-produtos-sem-venda</div>"

def test_grafico_produtos_apenas_um_vendido(monkeypatch):
    # Só um produto foi vendido, o outro não
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Produto X"}, {"nome": "Produto Y"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"produto": "Produto X"}]
    def fake_to_html(fig, **kwargs):
        bars = fig.data[0]
        produtos = list(bars.y)
        quantidades = list(bars.x)
        assert produtos == ["Produto X"]
        assert quantidades == [1]
        return "<div>grafico-produtos-um-vendido</div>"

    monkeypatch.setattr("app.graficos.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_produtos_mais_vendidos(2025, 7)
    assert html == "<div>grafico-produtos-um-vendido</div>"

def test_grafico_produtos_produto_nao_cadastrado(monkeypatch):
    # Tem vendas de um produto que não está cadastrado
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Produto X"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"produto": "Desconhecido"}]
    def fake_to_html(fig, **kwargs):
        # Não deve ter nenhuma barra, pois só produto não cadastrado foi vendido
        assert len(fig.data[0].x) == 0
        return "<div>grafico-produtos-nao-cadastrado</div>"

    monkeypatch.setattr("app.graficos.produtos_collection", FakeProdutosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_produtos_mais_vendidos(2025, 7)
    assert html == "<div>grafico-produtos-nao-cadastrado</div>"
