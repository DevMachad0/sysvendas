import pytest
import mongomock

# Importe a função conforme sua estrutura de projeto!
from app.models import cadastrar_produto

@pytest.fixture
def fake_produtos_collection(monkeypatch):
    # Cria uma coleção fake em memória
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.produtos_collection", mock_db.produtos)
    return mock_db.produtos

def test_cadastrar_produto_insercao(fake_produtos_collection):
    # Monta uma lista de formas de pagamento simuladas
    formas = [
        {"tipo": "A/C", "valor_total": 1500, "parcelas": '1+1', "valor_parcelas": 750},
        {"tipo": "B/C", "valor_total": 1700, "parcelas": '10x', "valor_parcelas": 170}
    ]
    # Chama a função de cadastro
    resultado = cadastrar_produto("ABC123", "Produto Teste", formas)
    # Verifica se retornou um ID
    assert resultado.inserted_id is not None

    # Busca o produto inserido
    produto_db = fake_produtos_collection.find_one({"codigo": "ABC123"})
    assert produto_db is not None
    assert produto_db["nome"] == "Produto Teste"
    assert produto_db["formas_pagamento"] == formas

def test_cadastrar_produto_max_formas_pagamento(fake_produtos_collection):
    # Cria uma lista com 13 formas de pagamento diferentes
    formas = [{"tipo": "A/C", "valor_total": 100*i, "parcelas": f'{i}x', "valor_parcelas": 10*i} for i in range(1, 14)]
    resultado = cadastrar_produto("XYZ789", "Produto Completo", formas)
    assert resultado.inserted_id is not None
    produto_db = fake_produtos_collection.find_one({"codigo": "XYZ789"})
    assert produto_db is not None
    assert len(produto_db["formas_pagamento"]) == 13
