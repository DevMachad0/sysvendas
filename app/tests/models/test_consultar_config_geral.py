import pytest
import mongomock

from app.models import consultar_config_geral

@pytest.fixture
def fake_configs_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.configs_collection", mock_db.configs)
    return mock_db.configs

def test_consultar_config_geral_existe(fake_configs_collection):
    # Insere uma configuração geral fake
    fake_configs_collection.insert_one({
        "tipo": "geral",
        "smtp": "smtp.empresa.com",
        "porta": 465,
        "email_copia": "copia@empresa.com"
    })

    config = consultar_config_geral()
    assert config is not None
    # Deve conter os campos salvos (mas não _id)
    assert config["tipo"] == "geral"
    assert config["smtp"] == "smtp.empresa.com"
    assert config["porta"] == 465
    assert config["email_copia"] == "copia@empresa.com"
    assert "_id" not in config

def test_consultar_config_geral_vazio(fake_configs_collection):
    # Nenhuma configuração inserida
    config = consultar_config_geral()
    assert config is None
