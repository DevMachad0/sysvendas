from app.services import normalizar_valor

def test_normalizar_valor_decimal_virgula():
    assert normalizar_valor("10,50") == "10.50"

def test_normalizar_valor_decimal_ponto():
    assert normalizar_valor("123.45") == "123.45"

def test_normalizar_valor_com_espacos():
    assert normalizar_valor("   99,9   ") == "99.9"

def test_normalizar_valor_inteiro():
    assert normalizar_valor(100) == "100"

def test_normalizar_valor_string_vazia():
    assert normalizar_valor("") == "0"
    assert normalizar_valor("", padrao="42") == "42"

def test_normalizar_valor_none():
    assert normalizar_valor(None) == "0"
    assert normalizar_valor(None, padrao="xxx") == "xxx"

def test_normalizar_valor_invalido():
    assert normalizar_valor("errado") == "0"
    assert normalizar_valor("R$ 100") == "0"
    assert normalizar_valor("15-09") == "0"
    assert normalizar_valor("errado", padrao="nao") == "nao"
