import pytest
from app.services import verifica_condicoes

def test_verifica_condicoes_existente(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [
                {
                    "formas_pagamento": [
                        {"tipo": "À vista", "parcelas": "1"},
                        {"tipo": "Cartão", "parcelas": "3"}
                    ]
                },
                {
                    "formas_pagamento": [
                        {"tipo": "Boleto", "parcelas": "5"}
                    ]
                }
            ]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    # Testa cada condição válida
    assert verifica_condicoes("À vista | 1") is True
    assert verifica_condicoes("Cartão | 3") is True
    assert verifica_condicoes("Boleto | 5") is True

def test_verifica_condicoes_inexistente(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [
                {"formas_pagamento": [{"tipo": "À vista", "parcelas": "1"}]}
            ]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    assert verifica_condicoes("Cartão | 3") is False
    assert verifica_condicoes("Boleto | 2") is False

def test_verifica_condicoes_vazio(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return []
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())
    assert verifica_condicoes("À vista | 1") is False

def test_verifica_condicoes_forma_sem_tipo(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [
                {"formas_pagamento": [{}]}  # Falta tipo e parcelas
            ]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())
    # Vai montar " | " na lista, mas só retorna True se exatamente igual
    assert verifica_condicoes(" | ") is True
    assert verifica_condicoes("À vista | 1") is False
