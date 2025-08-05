import pytest

from app.services import cadastrar_produto_service

def test_cadastrar_produto_service_filtra_e_chama(monkeypatch):
    chamado = {}

    def fake_cadastrar_produto(codigo, nome, formas_pagamento):
        chamado["codigo"] = codigo
        chamado["nome"] = nome
        chamado["formas_pagamento"] = formas_pagamento
        return "inserido"

    # Monkeypatch para substituir a função real pela fake
    monkeypatch.setattr("app.services.cadastrar_produto", fake_cadastrar_produto)

    # Simula input de produto
    data = {
        "codigo": "001",
        "nome": "Produto Teste",
        "formas_pagamento": [
            {"valor_total": 1000, "parcelas": 2, "valor_parcela": 500},      # válido
            {"valor_total": "", "parcelas": 3, "valor_parcela": 333},        # inválido
            {"valor_total": 900, "parcelas": "", "valor_parcela": 900},      # inválido
            {"valor_total": 800, "parcelas": 2, "valor_parcela": None},      # inválido
            {"valor_total": 1200, "parcelas": 4, "valor_parcela": 300}       # válido
        ]
    }

    resultado = cadastrar_produto_service(data)

    assert resultado == "inserido"
    assert chamado["codigo"] == "001"
    assert chamado["nome"] == "Produto Teste"
    # Só 2 condições válidas devem passar
    assert chamado["formas_pagamento"] == [
        {"valor_total": 1000, "parcelas": 2, "valor_parcela": 500},
        {"valor_total": 1200, "parcelas": 4, "valor_parcela": 300}
    ]

def test_cadastrar_produto_service_vazio(monkeypatch):
    chamado = {}

    def fake_cadastrar_produto(codigo, nome, formas_pagamento):
        chamado["formas_pagamento"] = formas_pagamento
        return True

    monkeypatch.setattr("app.services.cadastrar_produto", fake_cadastrar_produto)
    data = {"codigo": "002", "nome": "Produto Vazio", "formas_pagamento": []}
    resultado = cadastrar_produto_service(data)
    assert chamado["formas_pagamento"] == []
    assert resultado is True
