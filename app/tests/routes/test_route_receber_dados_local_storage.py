import pytest

@pytest.fixture
def url_receber_dados_ls():
    return '/receber-dados-localstorage'

def test_receber_dados_localstorage_ok(client, url_receber_dados_ls):
    user_data = {
        "username": "joao",
        "tipo": "vendedor",
        "token": "123456"
    }
    resp = client.post(url_receber_dados_ls, json=user_data)
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}
    # Verifica se salvou na sessão (precisa de contexto)
    with client.session_transaction() as sess:
        assert sess["user"]["username"] == "joao"
        assert sess["user"]["tipo"] == "vendedor"
        assert sess["user"]["token"] == "123456"

def test_receber_dados_localstorage_json_vazio(client, url_receber_dados_ls):
    resp = client.post(url_receber_dados_ls, json={})
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}
    with client.session_transaction() as sess:
        assert sess["user"] == {}

def test_receber_dados_localstorage_sem_json(client, url_receber_dados_ls):
    # Quando não envia JSON, request.get_json() retorna None e vai salvar None na session
    resp = client.post(url_receber_dados_ls)
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}
    with client.session_transaction() as sess:
        assert sess["user"] is None

def test_receber_dados_localstorage_metodo_nao_permitido(client, url_receber_dados_ls):
    resp = client.get(url_receber_dados_ls)
    assert resp.status_code == 405  # Method Not Allowed

