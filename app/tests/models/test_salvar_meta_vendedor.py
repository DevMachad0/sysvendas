import pytest
import mongomock

from app.models import salvar_meta_vendedor

@pytest.fixture
def fake_configs_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.configs_collection", mock_db.configs)
    return mock_db.configs

def test_salvar_meta_vendedor_insercao(fake_configs_collection):
    salvar_meta_vendedor(
        vendedor_id="v1",
        vendedor_nome="Deivid",
        meta_dia_quantidade=4,
        meta_dia_valor=1000.0,
        meta_semana=4000.0
    )
    doc = fake_configs_collection.find_one({"tipo": "meta_vendedor", "vendedor_id": "v1"})
    assert doc is not None
    assert doc["vendedor_nome"] == "Deivid"
    assert doc["meta_dia_quantidade"] == 4
    assert doc["meta_dia_valor"] == 1000.0
    assert doc["meta_semana"] == 4000.0

def test_salvar_meta_vendedor_campos_zero(fake_configs_collection):
    # Testa valores falsos (todos devem virar string "0")
    salvar_meta_vendedor(
        vendedor_id="v2",
        vendedor_nome="Silva",
        meta_dia_quantidade=None,
        meta_dia_valor=0,
        meta_semana=""
    )
    doc = fake_configs_collection.find_one({"tipo": "meta_vendedor", "vendedor_id": "v2"})
    assert doc is not None
    assert doc["meta_dia_quantidade"] == "0"
    assert doc["meta_dia_valor"] == "0"
    assert doc["meta_semana"] == "0"

def test_salvar_meta_vendedor_update(fake_configs_collection):
    # Primeiro, salva meta antiga
    fake_configs_collection.insert_one({
        "tipo": "meta_vendedor",
        "vendedor_id": "v3",
        "vendedor_nome": "Lucas",
        "meta_dia_quantidade": 2,
        "meta_dia_valor": 500.0,
        "meta_semana": 2500.0
    })
    # Atualiza
    salvar_meta_vendedor(
        vendedor_id="v3",
        vendedor_nome="Lucas Oliveira",
        meta_dia_quantidade=6,
        meta_dia_valor=1200.0,
        meta_semana=6000.0
    )
    doc = fake_configs_collection.find_one({"tipo": "meta_vendedor", "vendedor_id": "v3"})
    assert doc is not None
    assert doc["vendedor_nome"] == "Lucas Oliveira"
    assert doc["meta_dia_quantidade"] == 6
    assert doc["meta_dia_valor"] == 1200.0
    assert doc["meta_semana"] == 6000.0
