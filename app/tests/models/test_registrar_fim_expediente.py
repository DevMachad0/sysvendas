import pytest
import mongomock
import re
from datetime import datetime
from app.models import registrar_fim_expediente

@pytest.fixture
def fake_configs_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.configs_collection", mock_db.configs)
    return mock_db.configs

def test_registrar_fim_expediente_insercao(fake_configs_collection):
    # Chama a função
    registrar_fim_expediente()
    doc = fake_configs_collection.find_one({"tipo": "fim_expediente"})
    assert doc is not None

    # Checa se os campos data e hora estão presentes e no formato básico
    # data_str no formato DD/MM/YYYY
    assert re.match(r'\d{2}/\d{2}/\d{4}', doc["data"])
    # hora_str no formato HH:MM:SS
    assert re.match(r'\d{2}:\d{2}:\d{2}', doc["hora"])

def test_registrar_fim_expediente_update(fake_configs_collection):
    # Insere um documento antigo
    fake_configs_collection.insert_one({
        "tipo": "fim_expediente",
        "data": "01/01/2000",
        "hora": "00:00:00"
    })
    # Chama a função (deve atualizar, não duplicar)
    registrar_fim_expediente()
    docs = list(fake_configs_collection.find({"tipo": "fim_expediente"}))
    assert len(docs) == 1  # Só um documento
    # Checa se a data foi realmente atualizada
    agora = datetime.now()
    data_hoje = agora.strftime('%d/%m/%Y')
    assert docs[0]["data"] == data_hoje
