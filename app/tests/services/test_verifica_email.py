from app.services import verifica_email

def test_verifica_email_todos_validos():
    lista = ["fulano@email.com", "teste@x.com", "outra@dominio.org"]
    assert verifica_email(lista) == (True, None)

def test_verifica_email_primeiro_invalido():
    lista = ["naoemail", "fulano@email.com", "teste@x.com"]
    assert verifica_email(lista) == (False, 0)

def test_verifica_email_um_invalido_no_meio():
    lista = ["valido@email.com", "errado", "outro@email.com"]
    assert verifica_email(lista) == (False, 1)

def test_verifica_email_ultimo_invalido():
    lista = ["a@b.com", "b@c.com", "invalido"]
    assert verifica_email(lista) == (False, 2)

def test_verifica_email_lista_vazia():
    lista = []
    assert verifica_email(lista) == (True, None)
