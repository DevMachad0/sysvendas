from app.services import verifica_status_vendas

def test_verifica_status_vendas_aceitos():
    assert verifica_status_vendas("aguardando") is True
    assert verifica_status_vendas("Aguardando") is True
    assert verifica_status_vendas("APROVADA") is True
    assert verifica_status_vendas("faturado") is True
    assert verifica_status_vendas("cancelada") is True
    assert verifica_status_vendas("") is True
    assert verifica_status_vendas(None) is True

def test_verifica_status_vendas_com_espaco():
    assert verifica_status_vendas("  aguardando  ") is True
    assert verifica_status_vendas("  faturado") is True

def test_verifica_status_vendas_invalido():
    assert verifica_status_vendas("em análise") is False
    assert verifica_status_vendas("finalizado") is False
    assert verifica_status_vendas("CANCELADAS") is False  # plural, não aceito
