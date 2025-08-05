import pytest
import mongomock

from app.models import inserir_log

@pytest.fixture
def fake_logs_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.logs_collection", mock_db.logs)
    return mock_db.logs

def test_inserir_log(fake_logs_collection):
    data = "2025-07-07"
    hora = "14:00"
    modificacao = "Cadastro alterado"
    usuario = "admin"

    resultado = inserir_log(data, hora, modificacao, usuario)

    # Checa se retornou inserted_id válido
    assert resultado.inserted_id is not None

    # Busca o log inserido
    log_db = fake_logs_collection.find_one({"_id": resultado.inserted_id})
    assert log_db is not None
    assert log_db["data"] == data
    assert log_db["hora"] == hora
    assert log_db["modificacao"] == modificacao
    assert log_db["usuario"] == usuario
