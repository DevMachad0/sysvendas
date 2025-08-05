from app.services import eh_numero

def test_eh_numero_todos_validos():
    assert eh_numero("100", "200.5", "0", "150.00", "50") is True
    assert eh_numero(10, 20, 30, 40, 50) is True
    assert eh_numero("0.0", "1.1", "2.2", "3.3", "4.4") is True

def test_eh_numero_um_invalido():
    assert eh_numero("100", "abc", "0", "150.00", "50") is False
    assert eh_numero("a", "200.5", "0", "150.00", "50") is False
    assert eh_numero("100", "200.5", "xpto", "150.00", "50") is False

def test_eh_numero_vazio():
    assert eh_numero("", "200", "0", "1", "2") is False

def test_eh_numero_valor_none():
    # None não pode ser convertido para float
    assert eh_numero(None, "200", "0", "1", "2") is False

def test_eh_numero_valor_virgula():
    # Float do python não aceita "10,5" (vírgula) -- vai dar False
    assert eh_numero("10,5", "20", "0", "1", "2") is False
