import pytest
import mongomock

from app.models import listar_produtos

@pytest.fixture
def fake_produtos_collection(monkeypatch):
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.produtos_collection", mock_db.produtos)
    return mock_db.produtos

def test_listar_produtos_retorna_lista(fake_produtos_collection):
    # Insere produtos manualmente na coleção fake
    fake_produtos_collection.insert_many([
        {"codigo": "A1", "nome": "Produto A", "formas_pagamento": [{"tipo": "A/C", "valor_total": 1500, "parcelas": '1+1', "valor_parcelas": 750}]},
        {"codigo": "B2", "nome": "Produto B", "formas_pagamento": [{"tipo": "B/C", "valor_total": 1700, "parcelas": '10x', "valor_parcelas": 170}]}
    ])

    # Chama a função
    produtos = listar_produtos()

    # Esperado: lista de dicionários sem o campo _id
    esperado = [
        {"codigo": "A1", "nome": "Produto A", "formas_pagamento": [{"tipo": "A/C", "valor_total": 1500, "parcelas": '1+1', "valor_parcelas": 750}]},
        {"codigo": "B2", "nome": "Produto B", "formas_pagamento": [{"tipo": "B/C", "valor_total": 1700, "parcelas": '10x', "valor_parcelas": 170}]}
    ]

    # Checa se o retorno é correto
    assert isinstance(produtos, list)
    assert len(produtos) == 2
    assert produtos == esperado
    # Checa que _id não está presente em nenhum produto
    for produto in produtos:
        assert "_id" not in produto

def test_listar_produtos_vazio(fake_produtos_collection):
    # Não insere nada na coleção
    produtos = listar_produtos()
    assert produtos == []

