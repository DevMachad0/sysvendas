from app.services import verifica_tipo_cliente

def test_verifica_tipo_cliente_verde():
    assert verifica_tipo_cliente("verde") is True
    assert verifica_tipo_cliente("VERDE") is True
    assert verifica_tipo_cliente(" Verde ") is True

def test_verifica_tipo_cliente_vermelho():
    assert verifica_tipo_cliente("vermelho") is True
    assert verifica_tipo_cliente("VERMELHO") is True
    assert verifica_tipo_cliente("Vermelho") is True

def test_verifica_tipo_cliente_vazio():
    assert verifica_tipo_cliente("") is True
    assert verifica_tipo_cliente(None) is True

def test_verifica_tipo_cliente_invalido():
    assert verifica_tipo_cliente("azul") is False
    assert verifica_tipo_cliente("cliente vip") is False
