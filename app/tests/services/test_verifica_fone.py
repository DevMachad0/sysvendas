from app.services import verifica_fone

def test_verifica_fone_todos_validos():
    lista = ["+55 (11) 99999-9999", "+55 (21) 88888-8888", "+55 (85) 77777-7777"]
    # Todos têm len >= 17
    assert verifica_fone(lista) == (True, None)

def test_verifica_fone_primeiro_invalido():
    lista = ["12345", "+55 (21) 88888-8888"]
    # O primeiro é inválido
    assert verifica_fone(lista) == (False, 0)

def test_verifica_fone_invalido_no_meio():
    lista = ["+55 (11) 99999-9999", "errado", "+55 (85) 77777-7777"]
    # O segundo é inválido
    assert verifica_fone(lista) == (False, 1)

def test_verifica_fone_ultimo_invalido():
    lista = ["+55 (11) 99999-9999", "+55 (21) 88888-8888", "curto"]
    assert verifica_fone(lista) == (False, 2)

def test_verifica_fone_lista_vazia():
    lista = []
    assert verifica_fone(lista) == (True, None)
