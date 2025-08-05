import pytest

@pytest.fixture
def produtos_url():
    return '/produtos'

def test_get_produtos_renderiza_template(client, mocker, produtos_url):
    mocker.patch('app.routes.produtos.verificar_permissao_acesso', return_value=True)
    produtos_mock = [
        {"codigo": "001", "nome": "Produto 1", "formas_pagamento": []},
        {"codigo": "002", "nome": "Produto 2", "formas_pagamento": []},
    ]
    mocker.patch('app.routes.produtos.listar_produtos', return_value=produtos_mock)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}
    resp = client.get(produtos_url)
    assert resp.status_code == 200

def test_get_produtos_sem_permissao(client, mocker, produtos_url):
    mocker.patch('app.services.verificar_permissao_acesso', return_value=False)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'fulano', 'tipo': 'vendedor'}
    resp = client.get(produtos_url, follow_redirects=False)
    assert resp.status_code == 302
    assert "/index.html" in resp.headers["Location"]

def test_get_produtos_sem_user(client, mocker, produtos_url):
    mocker.patch('app.services.verificar_permissao_acesso', return_value=True)
    # não põe user na session
    resp = client.get(produtos_url, follow_redirects=False)
    assert resp.status_code == 302
    assert "/index.html" in resp.headers["Location"]

def test_post_produto_json_sucesso(client, mocker, produtos_url):
    mocker.patch('app.routes.produtos.verificar_permissao_acesso', return_value=True)
    mocker.patch('app.routes.produtos.produtos_collection.find_one', return_value=None)
    mocker.patch('app.routes.produtos.cadastrar_produto_service', return_value=True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    data = {
        "codigo": "XYZ1",
        "nome": "Novo Produto",
        "formas_pagamento": [{"tipo": "A/C", "valor_total": "1000", "parcelas": "1", "valor_parcela": "1000"}]
    }
    resp = client.post(produtos_url, json=data)
    assert resp.status_code == 200
    assert resp.json["success"] is True

def test_post_produto_form_sucesso(client, mocker, produtos_url):
    mocker.patch('app.routes.produtos.verificar_permissao_acesso', return_value=True)
    mocker.patch('app.routes.produtos.produtos_collection.find_one', return_value=None)
    mocker.patch('app.routes.produtos.cadastrar_produto_service', return_value=True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    formdata = {
        "codigo": "XYZ2",
        "nome": "Produto Form",
        "valor_total_1": "500",
        "parcelas_1": "1",
        "valor_parcela_1": "500",
    }
    resp = client.post(produtos_url, data=formdata)
    assert resp.status_code == 200
    assert resp.json["success"] is True

def test_post_produto_sem_codigo(client, mocker, produtos_url):
    mocker.patch('app.routes.produtos.verificar_permissao_acesso', return_value=True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.post(produtos_url, json={"nome": "Produto sem código"})
    assert resp.status_code == 400
    assert resp.json["success"] is False
    assert "código" in resp.json["erro"]

def test_post_produto_codigo_duplicado(client, mocker, produtos_url):
    mocker.patch('app.routes.produtos.verificar_permissao_acesso', return_value=True)
    mocker.patch('app.routes.produtos.produtos_collection.find_one', return_value={"codigo": "REPETIDO"})
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    data = {"codigo": "REPETIDO", "nome": "Produto Duplicado", "formas_pagamento": []}
    resp = client.post(produtos_url, json=data)
    assert resp.status_code == 400
    assert resp.json["success"] is False
    assert "Já existe" in resp.json["erro"]

def test_post_produto_sem_permissao(client, mocker, produtos_url):
    mocker.patch('app.services.verificar_permissao_acesso', return_value=False)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'sempermissao', 'tipo': 'vendedor'}
    resp = client.post(produtos_url, json={"codigo": "NAOIMPORTA"})
    assert resp.status_code == 302
    assert "/index.html" in resp.headers["Location"]

def test_post_produto_erro_interno(client, mocker, produtos_url):
    mocker.patch('app.routes.produtos.verificar_permissao_acesso', return_value=True)
    mocker.patch('app.routes.produtos.produtos_collection.find_one', side_effect=Exception("Falha interna"))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}
    resp = client.post(produtos_url)
    assert resp.status_code == 400

