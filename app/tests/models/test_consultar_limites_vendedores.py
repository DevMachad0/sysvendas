import pytest
import mongomock

from app.models import consultar_limites_vendedores

@pytest.fixture
def fake_configs_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.configs_collection", mock_db.configs)
    return mock_db.configs

def test_consultar_limites_vendedores_lista(fake_configs_collection):
    # Insere dois limites
    fake_configs_collection.insert_many([
        {
            "tipo": "limite_vendedor",
            "vendedor_id": "v1",
            "vendedor_nome": "Ana",
            "limite": 1500.0
        },
        {
            "tipo": "limite_vendedor",
            "vendedor_id": "v2",
            "vendedor_nome": "Pedro",
            "limite": "0"
        }
    ])

    limites = consultar_limites_vendedores()
    # Lista esperada (sem _id)
    esperado = [
        {
            "tipo": "limite_vendedor",
            "vendedor_id": "v1",
            "vendedor_nome": "Ana",
            "limite": 1500.0
        },
        {
            "tipo": "limite_vendedor",
            "vendedor_id": "v2",
            "vendedor_nome": "Pedro",
            "limite": "0"
        }
    ]
    assert isinstance(limites, list)
    assert limites == esperado
    for limite in limites:
        assert "_id" not in limite

def test_consultar_limites_vendedores_vazio(fake_configs_collection):
    limites = consultar_limites_vendedores()
    assert limites == []
