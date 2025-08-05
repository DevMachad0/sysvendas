from app.utils import soma_vendas

def test_soma_vendas_varios_formatos():
    todas_vendas = [
        {"status": "Aprovada", "valor_real": "1000.50"},
        {"status": "Aprovada", "valor_real": "2.500,75"},
        {"status": "Aprovada", "valor_real": "300,25"},
        {"status": "Cancelada", "valor_real": "9999,99"},  # Não deve contar
        {"status": "Aprovada", "valor_real": "1,500.00"}
    ]
    # "1000.50" + "2500.75" + "300.25" + "1500.00" = 5301.5
    resultado = soma_vendas(todas_vendas)
    assert abs(resultado - 5301.5) < 1e-2  # Considera arredondamento

def test_soma_vendas_tudo_cancelado():
    todas_vendas = [
        {"status": "Cancelada", "valor_real": "100"},
        {"status": "Cancelada", "valor_real": "200,50"}
    ]
    resultado = soma_vendas(todas_vendas)
    assert resultado == 0.0

def test_soma_vendas_lista_vazia():
    resultado = soma_vendas([])
    assert resultado == 0.0

def test_soma_vendas_valores_puros():
    todas_vendas = [
        {"status": "Aprovada", "valor_real": "100"},
        {"status": "Aprovada", "valor_real": "200.25"},
        {"status": "Aprovada", "valor_real": "300,50"}
    ]
    # 100 + 200.25 + 300.50 = 600.75
    resultado = soma_vendas(todas_vendas)
    assert abs(resultado - 600.75) < 1e-2

def test_soma_vendas_valores_com_espaco():
    todas_vendas = [
        {"status": "Aprovada", "valor_real": " 1.234,56 "},  # deve remover espaços
    ]
    resultado = soma_vendas(todas_vendas)
    assert abs(resultado - 1234.56) < 1e-2
