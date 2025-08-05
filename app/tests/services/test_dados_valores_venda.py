import pytest
from app.services import dados_valores_venda

def test_dados_valores_venda_formata_corretamente(monkeypatch):
    # Simula retorno do banco
    fake_produtos = [
        {
            "nome": "Produto A",
            "formas_pagamento": [
                {"tipo": "À vista", "parcelas": 1, "valor_total": 1000},
                {"tipo": "Parcelado", "parcelas": 2, "valor_total": 1100},
            ]
        },
        {
            "nome": "Produto B",
            "formas_pagamento": [
                {"tipo": "Cartão", "parcelas": 3, "valor_total": 1200},
            ]
        },
        {
            "nome": "Produto Sem Condição",
            "formas_pagamento": []
        },
        {
            "nome": "Produto Sem Campo"
            # Não tem campo formas_pagamento
        }
    ]

    # Mocka o produtos_collection.find para retornar os dados simulados
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return fake_produtos
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    resultado = dados_valores_venda()
    # Checa o resultado para todos os produtos
    assert resultado == {
        "Produto A": [
            {"condicao": "À vista | 1", "valor": 1000},
            {"condicao": "Parcelado | 2", "valor": 1100},
        ],
        "Produto B": [
            {"condicao": "Cartão | 3", "valor": 1200}
        ],
        "Produto Sem Condição": [],
        "Produto Sem Campo": []
    }

def test_dados_valores_venda_vazio(monkeypatch):
    # Nenhum produto cadastrado
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())
    resultado = dados_valores_venda()
    assert resultado == {}
