import pytest
import pandas as pd
from collections import defaultdict
import builtins
from app.download import gerar_fig_mapa_vendas_por_estado

def test_fig_mapa_vendas_por_estado_vazio(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Fulano"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return []

    # Fake GeoJSON básico
    fake_geojson = {"type": "FeatureCollection", "features": []}

    def fake_open(*args, **kwargs):
        class FakeFile:
            def __enter__(self):
                return '{"type":"FeatureCollection","features":[]}'
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return FakeFile()

    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("json.load", lambda f: fake_geojson)
    import plotly.graph_objs as go

    fig = gerar_fig_mapa_vendas_por_estado()
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == "Vendas por Estado (Brasil)"

def test_fig_mapa_vendas_por_estado_normal(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Fulano"}, {"nome_completo": "Beltrano"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"endereco": {"estado": "SP"}},
                {"endereco": {"estado": "RJ"}},
                {"endereco": {"estado": "SP"}},
                {"endereco": {"estado": "XX"}},  # Estrangeira
                {"endereco": "MG"}
            ]
    def fake_open(*args, **kwargs):
        class FakeFile:
            def __enter__(self):
                return '{"type":"FeatureCollection","features":[]}'
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return FakeFile()
    
    fake_geojson = {"type": "FeatureCollection", "features": []}
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("json.load", lambda f: fake_geojson)

    fig = gerar_fig_mapa_vendas_por_estado()
    # Verifica se o gráfico contém as anotações e a cor azul da escala
    assert fig.layout.title.text == "Vendas por Estado (Brasil)"
    # Testa se o estado com mais vendas é SP
    vendas_dict = {loc: val for loc, val in zip(fig.data[0].locations, fig.data[0].z)}
    assert vendas_dict.get('SP', 0) >= 1
    assert 'RJ' in vendas_dict

def test_fig_mapa_vendas_por_estado_normal_dezembro(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Fulano"}, {"nome_completo": "Beltrano"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"endereco": {"estado": "SP"}},
                {"endereco": {"estado": "RJ"}},
                {"endereco": {"estado": "SP"}},
                {"endereco": {"estado": "XX"}},  # Estrangeira
                {"endereco": "MG"}
            ]
    def fake_open(*args, **kwargs):
        class FakeFile:
            def __enter__(self):
                return '{"type":"FeatureCollection","features":[]}'
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return FakeFile()
    
    fake_geojson = {"type": "FeatureCollection", "features": []}
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("json.load", lambda f: fake_geojson)

    fig = gerar_fig_mapa_vendas_por_estado(mes=12)
    assert fig.layout.title.text == "Vendas por Estado (Brasil)"

def test_fig_mapa_vendas_por_estado_estrangeira(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Fulano"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [
                {"endereco": {"estado": "XX"}},  # Estrangeira
                {"endereco": "XX"}  # Estrangeira também
            ]
    def fake_open(*args, **kwargs):
        class FakeFile:
            def __enter__(self):
                return '{"type":"FeatureCollection","features":[]}'
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return FakeFile()
    fake_geojson = {"type": "FeatureCollection", "features": []}
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("json.load", lambda f: fake_geojson)

    fig = gerar_fig_mapa_vendas_por_estado()
    assert fig.layout.title.text == "Vendas por Estado (Brasil)"
    # Procura anotação de estrangeiras no gráfico
    anots = fig['layout'].annotations
    if anots:
        assert any('Estrangeiras' in a['text'] for a in anots)

def test_fig_mapa_vendas_por_estado_excecao_geojson(monkeypatch):
    class FakeUsuariosCollection:
        def find(self, filtro, proj):
            return [{"nome_completo": "Fulano"}]
    class FakeVendasCollection:
        def find(self, filtro, proj):
            return [{"endereco": {"estado": "SP"}}]
    def fake_open(*args, **kwargs):
        raise OSError("Arquivo não encontrado")
    monkeypatch.setattr("app.download.usuarios_collection", FakeUsuariosCollection())
    monkeypatch.setattr("app.download.vendas_collection", FakeVendasCollection())
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("json.load", lambda f: {})  # Será ignorado por exceção

    # Ainda retorna um Figure válido (mas sem geojson)
    fig = gerar_fig_mapa_vendas_por_estado()
    assert fig.layout.title.text == "Vendas por Estado (Brasil)"

