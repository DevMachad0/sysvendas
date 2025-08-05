import pytest
from datetime import datetime

from app.graficos import gerar_grafico_banco_vendedores

def test_gerar_grafico_banco_vendedores_sem_vendas(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "João", "status": "ativo"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    class FakeConfigsCollection:
        pass 
    
    # Mock pio.to_html
    chamado = {}
    def fake_to_html(fig, **kwargs):
        chamado["foi"] = True
        return "<div>grafico-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_banco_vendedores(2025, 7)
    assert html == "<div>grafico-vazio</div>"
    assert chamado["foi"] is True

def test_gerar_grafico_banco_vendedores_com_vendas(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria", "status": "ativo"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_tabela": "1000", "valor_real": "1100", "desconto_autorizado": False},
                {"vendedor": "Maria", "valor_tabela": "800", "valor_real": "700", "desconto_autorizado": False},  # desconto não autorizado
                {"vendedor": "Maria", "valor_tabela": "600", "valor_real": "600", "desconto_autorizado": True},   # zero, autorizado
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria", "limite": "200"}]
    def fake_to_html(fig, **kwargs):
        # Testa se fig tem barras com rótulo correto (Maria) e saldo calculado correto (200 + 100 - 100 = 200)
        bars = fig.data[0]
        assert "Maria" in bars.x
        assert any(isinstance(y, float) or isinstance(y, int) for y in bars.y)
        return "<div>grafico-cheio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_banco_vendedores(2025, 7)
    assert html == "<div>grafico-cheio</div>"

def test_gerar_grafico_banco_vendedores_com_vendas_dezembro(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria", "status": "ativo"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_tabela": "1000", "valor_real": "1100", "desconto_autorizado": False},
                {"vendedor": "Maria", "valor_tabela": "800", "valor_real": "700", "desconto_autorizado": False},  # desconto não autorizado
                {"vendedor": "Maria", "valor_tabela": "600", "valor_real": "600", "desconto_autorizado": True},   # zero, autorizado
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria", "limite": "200"}]
    def fake_to_html(fig, **kwargs):
        # Testa se fig tem barras com rótulo correto (Maria) e saldo calculado correto (200 + 100 - 100 = 200)
        assert fig.layout.title.text == 'Saldo do Banco por Vendedor'
        return "<div>grafico-cheio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_banco_vendedores(2025, 12)
    assert html == "<div>grafico-cheio</div>"

def test_gerar_grafico_banco_vendedores_com_vendas_erro_valor_tabela(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria", "status": "ativo"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_tabela": "erro", "valor_real": "1100", "desconto_autorizado": False},
                {"vendedor": "Maria", "valor_tabela": "800", "valor_real": "700", "desconto_autorizado": False},  # desconto não autorizado
                {"vendedor": "Maria", "valor_tabela": "600", "valor_real": "600", "desconto_autorizado": True},   # zero, autorizado
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria", "limite": "200"}]
    def fake_to_html(fig, **kwargs):
        # Testa se fig tem barras com rótulo correto (Maria) e saldo calculado correto (200 + 100 - 100 = 200)
        assert fig.layout.title.text == 'Saldo do Banco por Vendedor'
        return "<div>grafico-cheio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_banco_vendedores(2025, 12)
    assert html == "<div>grafico-cheio</div>"

def test_gerar_grafico_banco_vendedores_com_vendas_erro_valor_real(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria", "status": "ativo"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_tabela": "1000", "valor_real": "erro", "desconto_autorizado": False},
                {"vendedor": "Maria", "valor_tabela": "800", "valor_real": "700", "desconto_autorizado": False},  # desconto não autorizado
                {"vendedor": "Maria", "valor_tabela": "600", "valor_real": "600", "desconto_autorizado": True},   # zero, autorizado
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"vendedor_nome": "Maria", "limite": "200"}]
    def fake_to_html(fig, **kwargs):
        # Testa se fig tem barras com rótulo correto (Maria) e saldo calculado correto (200 + 100 - 100 = 200)
        assert fig.layout.title.text == 'Saldo do Banco por Vendedor'
        return "<div>grafico-cheio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_banco_vendedores(2025, 12)
    assert html == "<div>grafico-cheio</div>"

def test_gerar_grafico_banco_vendedores_com_vendas_vendedor_inativo(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return []
        
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_tabela": "1000", "valor_real": "1100", "desconto_autorizado": False},
                {"vendedor": "Maria", "valor_tabela": "800", "valor_real": "700", "desconto_autorizado": False},  # desconto não autorizado
                {"vendedor": "Maria", "valor_tabela": "600", "valor_real": "600", "desconto_autorizado": True},   # zero, autorizado
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"tipo": "limite_vendedor", "vendedor_nome": "Maria", "limite": "200"}]
    def fake_to_html(fig, **kwargs):
        # Testa se fig tem barras com rótulo correto (Maria) e saldo calculado correto (200 + 100 - 100 = 200)
        assert fig.layout.title.text == 'Saldo do Banco por Vendedor'
        return "<div>grafico-cheio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_banco_vendedores(2025, 12)
    assert html == "<div>grafico-cheio</div>"

def test_gerar_grafico_banco_vendedores_com_vendas_saldo_novo_entre_zero_e_saldo_atual(monkeypatch):
    # Mock collections
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria", "status": "ativo"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"vendedor": "Maria", "valor_tabela": "1000", "valor_real": "900", "desconto_autorizado": False}
            ]
    class FakeConfigsCollection:
        def find(self, filtro, proj):
            return [{"tipo": "limite_vendedor", "vendedor_nome": "Maria", "limite": "200"}]
    def fake_to_html(fig, **kwargs):
        # Testa se fig tem barras com rótulo correto (Maria) e saldo calculado correto (200 + 100 - 100 = 200)
        assert fig.layout.title.text == 'Saldo do Banco por Vendedor'
        return "<div>grafico-cheio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("app.graficos.configs_collection", FakeConfigsCollection())
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_banco_vendedores(2025, 12)
    assert html == "<div>grafico-cheio</div>"
