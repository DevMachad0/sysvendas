import pytest
import mongomock

from app.models import salvar_limite_vendedor

@pytest.fixture
def fake_configs_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.configs_collection", mock_db.configs)
    return mock_db.configs

def test_salvar_limite_vendedor_insercao(fake_configs_collection):
    salvar_limite_vendedor(
        vendedor_id="v1",
        vendedor_nome="João Vendas",
        limite=5000.0
    )
    doc = fake_configs_collection.find_one({"tipo": "limite_vendedor", "vendedor_id": "v1"})
    assert doc is not None
    assert doc["vendedor_nome"] == "João Vendas"
    assert doc["limite"] == 5000.0

def test_salvar_limite_vendedor_limite_zero(fake_configs_collection):
    salvar_limite_vendedor(
        vendedor_id="v2",
        vendedor_nome="Maria",
        limite=None  # Ou 0, ou '', qualquer valor "falso"
    )
    doc = fake_configs_collection.find_one({"tipo": "limite_vendedor", "vendedor_id": "v2"})
    assert doc is not None
    assert doc["limite"] == "0"

def test_salvar_limite_vendedor_update(fake_configs_collection):
    # Primeiro, salva limite antigo
    fake_configs_collection.insert_one({
        "tipo": "limite_vendedor",
        "vendedor_id": "v3",
        "vendedor_nome": "Carlos",
        "limite": 1500.0
    })
    # Atualiza
    salvar_limite_vendedor(
        vendedor_id="v3",
        vendedor_nome="Carlos Silva",
        limite=2000.0
    )
    doc = fake_configs_collection.find_one({"tipo": "limite_vendedor", "vendedor_id": "v3"})
    assert doc is not None
    assert doc["vendedor_nome"] == "Carlos Silva"
    assert doc["limite"] == 2000.0

