import pytest
import mongomock

from app.models import consultar_metas_vendedores

@pytest.fixture
def fake_configs_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.configs_collection", mock_db.configs)
    return mock_db.configs

def test_consultar_metas_vendedores_lista(fake_configs_collection):
    # Insere metas
    fake_configs_collection.insert_many([
        {
            "tipo": "meta_vendedor",
            "vendedor_id": "v1",
            "vendedor_nome": "Joana",
            "meta_dia_quantidade": 5,
            "meta_dia_valor": 700.0,
            "meta_semana": 3500.0
        },
        {
            "tipo": "meta_vendedor",
            "vendedor_id": "v2",
            "vendedor_nome": "Paulo",
            "meta_dia_quantidade": 2,
            "meta_dia_valor": 200.0,
            "meta_semana": 1000.0
        }
    ])
    metas = consultar_metas_vendedores()
    esperado = [
        {
            "tipo": "meta_vendedor",
            "vendedor_id": "v1",
            "vendedor_nome": "Joana",
            "meta_dia_quantidade": 5,
            "meta_dia_valor": 700.0,
            "meta_semana": 3500.0
        },
        {
            "tipo": "meta_vendedor",
            "vendedor_id": "v2",
            "vendedor_nome": "Paulo",
            "meta_dia_quantidade": 2,
            "meta_dia_valor": 200.0,
            "meta_semana": 1000.0
        }
    ]
    assert isinstance(metas, list)
    assert metas == esperado
    for meta in metas:
        assert "_id" not in meta

def test_consultar_metas_vendedores_vazio(fake_configs_collection):
    metas = consultar_metas_vendedores()
    assert metas == []
