import pytest
from collections import defaultdict
import json
import builtins
from app.graficos import gerar_grafico_mapa_vendas_por_estado

def test_grafico_mapa_sem_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []
    def fake_open(path, encoding=None):
        class DummyFile:
            def __enter__(self):
                # GeoJSON mínimo
                return {"type": "FeatureCollection", "features": []}
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return DummyFile()
    def fake_json_load(f):
        return f
    def fake_to_html(fig, **kwargs):
        # Gráfico vazio, sem vendas
        assert hasattr(fig, "data")
        return "<div>grafico-mapa-vazio</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("app.graficos.json.load", fake_json_load)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_mapa_vendas_por_estado(2025, 7)
    assert html == "<div>grafico-mapa-vazio</div>"

def test_grafico_mapa_com_vendas(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Uma venda em SP, outra estrangeira
            return [
                {"endereco": {"estado": "SP"}},
                {"endereco": {"estado": "XX"}},
                {"endereco": "RJ"},  # string (legado)
            ]
    def fake_open(path, encoding=None):
        class DummyFile:
            def __enter__(self):
                # GeoJSON mínimo para SP e RJ
                return {
                    "type": "FeatureCollection",
                    "features": [
                        {"properties": {"sigla": "SP"}},
                        {"properties": {"sigla": "RJ"}},
                    ]
                }
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return DummyFile()
    def fake_json_load(f):
        return f
    def fake_to_html(fig, **kwargs):
        # Extrai as vendas por estado plotadas
        df = fig.data[0]
        # Checa se os dados batem: SP (1), RJ (1), Estrangeira (1)
        vendas = dict(zip(df.locations, df.z))
        assert vendas.get("SP", 0) == 1
        assert vendas.get("RJ", 0) == 1
        # Checa se a anotação de vendas estrangeiras existe (1 estrangeira)
        anots = [a.text for a in getattr(fig, "layout", {}).annotations or []]
        assert any("Vendas Estrangeiras: 1" in t for t in anots)
        return "<div>grafico-mapa-sp-rj-estrangeira</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("app.graficos.json.load", fake_json_load)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_mapa_vendas_por_estado(2025, 7)
    assert html == "<div>grafico-mapa-sp-rj-estrangeira</div>"

def test_grafico_mapa_com_vendas_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Maria"}, {"nome_completo": "João"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            # Uma venda em SP, outra estrangeira
            return [
                {"endereco": {"estado": "SP"}},
                {"endereco": {"estado": "XX"}},
                {"endereco": "RJ"},  # string (legado)
            ]
    def fake_open(path, encoding=None):
        return 'Erro'
    
    def fake_to_html(fig, **kwargs):
        # Extrai as vendas por estado plotadas
        df = fig.data[0]
        # Checa se os dados batem: SP (1), RJ (1), Estrangeira (1)
        vendas = dict(zip(df.locations, df.z))
        assert vendas.get("SP", 0) == 1
        assert vendas.get("RJ", 0) == 1
        # Checa se a anotação de vendas estrangeiras existe (1 estrangeira)
        anots = [a.text for a in getattr(fig, "layout", {}).annotations or []]
        assert any("Vendas Estrangeiras: 1" in t for t in anots)
        return "<div>grafico-mapa-sp-rj-estrangeira</div>"

    monkeypatch.setattr("app.graficos.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.graficos.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("app.graficos.json.load", lambda f: f)
    monkeypatch.setattr("app.graficos.pio.to_html", fake_to_html)

    html = gerar_grafico_mapa_vendas_por_estado(2025, 12)
    assert html == "<div>grafico-mapa-sp-rj-estrangeira</div>"
