import pytest

from app.services import verifica_produto

def test_verifica_produto_normal_existente(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Ar Condicionado"}, {"nome": "Ventilador"}]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    assert verifica_produto("Ar Condicionado") is True
    assert verifica_produto("Ventilador") is True

def test_verifica_produto_normal_inexistente(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Ar Condicionado"}]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    assert verifica_produto("Geladeira") is False

def test_verifica_produto_personalizado_todos_existem(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Ar Condicionado"}, {"nome": "Ventilador"}, {"nome": "Geladeira"}]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    produto = "Personalizado: Ar Condicionado, Geladeira"
    assert verifica_produto(produto) is True

def test_verifica_produto_personalizado_um_invalido(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Ar Condicionado"}, {"nome": "Ventilador"}]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    produto = "Personalizado: Ar Condicionado, Geladeira"
    assert verifica_produto(produto) is False

def test_verifica_produto_personalizado_lista_vazia(monkeypatch):
    class FakeProdutosCollection:
        def find(self, filtro, proj):
            return [{"nome": "Ar Condicionado"}]
    monkeypatch.setattr("app.services.produtos_collection", FakeProdutosCollection())

    produto = "Personalizado: "
    assert verifica_produto(produto) is False
