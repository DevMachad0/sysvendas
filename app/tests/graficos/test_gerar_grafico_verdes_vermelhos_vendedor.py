import pytest
from app.graficos import gerar_grafico_verdes_vermelhos_vendedor

def test_grafico_verdes_vermelhos_vendedor_sem_vendas(monkeypatch):
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
    html = gerar_grafico_verdes_vermelhos_vendedor(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"]

def test_grafico_verdes_vermelhos_vendedor_com_vendas(monkeypatch):
    # Maria: 2 verdes, 1 vermelho; João: 1 verde, 2 vermelhos
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "tipo_cliente": "verde"},
                {"vendedor": "Maria", "tipo_cliente": "Verde"},
                {"vendedor": "Maria", "tipo_cliente": "vermelho"},
                {"vendedor": "João", "tipo_cliente": "verde"},
                {"vendedor": "João", "tipo_cliente": "vermelho"},
                {"vendedor": "João", "tipo_cliente": "vermelho"},
                {"vendedor": "Maria", "tipo_cliente": "azul"}, # ignorado
                {"vendedor": "", "tipo_cliente": "verde"},      # ignorado
            ]
    def fake_to_html(fig, **kwargs):
        # A ordem das barras depende da ordem dos vendedores na função
        # Vamos montar um dicionário {vendedor: (verdes, vermelhos)}
        barra_verde = fig.data[0]
        barra_vermelha = fig.data[1]
        assert barra_verde.name == 'Verde'
        assert barra_vermelha.name == 'Vermelho'

        dados = {}
        for ix, vendedor in enumerate(barra_verde.x):
            v = vendedor
            verdes = barra_verde.y[ix]
            vermelhos = barra_vermelha.y[ix]
            dados[v] = (verdes, vermelhos)

        assert dados["Maria"] == (2, 1)
        assert dados["João"] == (1, 2)
        return "<div>grafico-barras</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_vendedor(2025, 7)
    assert html == "<div>grafico-barras</div>"

def test_grafico_verdes_vermelhos_vendedor_com_vendas_dezembro(monkeypatch):
    # Maria: 2 verdes, 1 vermelho; João: 1 verde, 2 vermelhos
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "tipo_cliente": "verde"},
                {"vendedor": "Maria", "tipo_cliente": "Verde"},
                {"vendedor": "Maria", "tipo_cliente": "vermelho"},
                {"vendedor": "João", "tipo_cliente": "verde"},
                {"vendedor": "João", "tipo_cliente": "vermelho"},
                {"vendedor": "João", "tipo_cliente": "vermelho"},
                {"vendedor": "Maria", "tipo_cliente": "azul"}, # ignorado
                {"vendedor": "", "tipo_cliente": "verde"},      # ignorado
            ]
    def fake_to_html(fig, **kwargs):
        # A ordem das barras depende da ordem dos vendedores na função
        # Vamos montar um dicionário {vendedor: (verdes, vermelhos)}
        barra_verde = fig.data[0]
        barra_vermelha = fig.data[1]
        assert barra_verde.name == 'Verde'
        assert barra_vermelha.name == 'Vermelho'

        dados = {}
        for ix, vendedor in enumerate(barra_verde.x):
            v = vendedor
            verdes = barra_verde.y[ix]
            vermelhos = barra_vermelha.y[ix]
            dados[v] = (verdes, vermelhos)

        assert dados["Maria"] == (2, 1)
        assert dados["João"] == (1, 2)
        return "<div>grafico-barras</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_vendedor(2025, 12)
    assert html == "<div>grafico-barras</div>"

def test_grafico_verdes_vermelhos_vendedor_com_vendas_sem_verde_e_vermelho(monkeypatch):
    # Maria: 2 verdes, 1 vermelho; João: 1 verde, 2 vermelhos
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "tipo_cliente": "azul"},
                {"vendedor": "Maria", "tipo_cliente": "azul"},
                {"vendedor": "Maria", "tipo_cliente": "azul"},
                {"vendedor": "João", "tipo_cliente": "azul"},
                {"vendedor": "João", "tipo_cliente": "azul"},
                {"vendedor": "João", "tipo_cliente": "azul"},
                {"vendedor": "Maria", "tipo_cliente": "azul"},
                {"vendedor": "", "tipo_cliente": "azul"},
            ]
    def fake_to_html(fig, **kwargs):
        assert fig.layout.xaxis.title.text == 'Sem dados'
        return "<div>grafico-barras</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_vendedor(2025, 12)
    assert html == "<div>grafico-barras</div>"

def test_grafico_verdes_vermelhos_vendedor_somente_um_tipo(monkeypatch):
    # Só Maria, só verdes
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"vendedor": "Maria", "tipo_cliente": "verde"} for _ in range(3)]
    def fake_to_html(fig, **kwargs):
        barra_verde = fig.data[0]
        barra_vermelha = fig.data[1]
        assert barra_verde.y == (3,)
        assert barra_vermelha.y == (0,)
        return "<div>grafico-somente-verde</div>"
    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)
    html = gerar_grafico_verdes_vermelhos_vendedor(2025, 7)
    assert html == "<div>grafico-somente-verde</div>"
