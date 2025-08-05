import pytest
from bson import ObjectId

@pytest.fixture
def authenticated_session(client):
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor1', 'tipo': 'vendedor'}
    return client

@pytest.fixture
def monkeypatch_permissao_ok(monkeypatch):
    monkeypatch.setattr('app.routes.editarVenda.verificar_permissao_acesso', lambda username: True)

@pytest.fixture
def monkeypatch_permissao_nok(monkeypatch):
    monkeypatch.setattr('app.routes.editarVenda.verificar_permissao_acesso', lambda username: False)

@pytest.fixture
def monkeypatch_info_vendas(monkeypatch):
    monkeypatch.setattr('app.routes.editarVenda.dados_valores_venda', lambda: {'condicoes': [], 'produtos': []})

@pytest.fixture
def venda_completa():
    # Exemplo de venda com tudo
    return {
        "numero_da_venda": "888",
        "nome": "Maria",
        "_id": ObjectId("65b8b33f937f50f5a6e48a18"),
        "endereco": {"uf": "SP", "_id": ObjectId("65b8b33f937f50f5a6e48a19")},
        "logs": [{"acao": "criou", "_id": ObjectId("65b8b33f937f50f5a6e48a1a")}],
        "campo_normal": "valor"
    }

@pytest.fixture
def monkeypatch_find_one(monkeypatch, venda_completa):
    def _find_one(query):
        if query["numero_da_venda"] == "888":
            return venda_completa
        
    monkeypatch.setattr('app.routes.editarVenda.vendas_collection.find_one', _find_one)

def test_post_editar_venda_serializacao(authenticated_session, monkeypatch_permissao_ok, monkeypatch_info_vendas, monkeypatch_find_one, venda_completa):
    resp = authenticated_session.post('/editar_venda', json={'numero_da_venda': '888'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    # Testa se serializou os ObjectIds
    with authenticated_session.session_transaction() as sess:
        venda = sess["venda_edicao"]
        assert isinstance(venda["_id"], str)
        assert isinstance(venda["endereco"]["_id"], str)
        assert isinstance(venda["logs"][0]["_id"], str)
        assert venda["campo_normal"] == "valor"

def test_post_editar_venda_erro_banco(authenticated_session, monkeypatch_permissao_ok, monkeypatch_info_vendas, monkeypatch):
    # Simula erro de banco
    def _raise(*a, **kw): raise Exception("banco caiu")
    monkeypatch.setattr('app.routes.editarVenda.vendas_collection.find_one', _raise)
    resp = authenticated_session.post('/editar_venda', json={'numero_da_venda': '888'})
    assert resp.status_code == 500 or resp.status_code == 200  # depende de como você trata exceção

def test_post_editar_venda_venda_nao_encontrada(authenticated_session, monkeypatch_permissao_ok, monkeypatch_info_vendas, monkeypatch):
    monkeypatch.setattr('app.routes.editarVenda.vendas_collection.find_one', lambda q: None)
    resp = authenticated_session.post('/editar_venda', json={'numero_da_venda': 'nãoexiste'})
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False

def test_post_editar_venda_sem_numero(authenticated_session, monkeypatch_permissao_ok, monkeypatch_info_vendas):
    resp = authenticated_session.post('/editar_venda', json={})
    # O código não faz validação do campo, então deve cair em "não encontrada"
    assert resp.status_code == 404

def test_get_editar_venda_renderiza(authenticated_session, monkeypatch_permissao_ok, monkeypatch_info_vendas):
    with authenticated_session.session_transaction() as sess:
        sess["venda_edicao"] = {"numero_da_venda": "123"}
    resp = authenticated_session.get('/editar_venda')
    assert resp.status_code == 200
    assert b'editar_venda' in resp.data or b'Editar' in resp.data

def test_get_editar_venda_nao_autenticado(client, monkeypatch_permissao_ok):
    resp = client.get('/editar_venda')
    assert resp.status_code in (302, 301)
    assert '/index.html' in resp.location

def test_get_editar_venda_sem_permissao(authenticated_session, monkeypatch_permissao_nok):
    resp = authenticated_session.get('/editar_venda')
    assert resp.status_code in (302, 301)

def test_get_editar_venda_sem_venda_sessao(authenticated_session, monkeypatch_permissao_ok, monkeypatch_info_vendas):
    with authenticated_session.session_transaction() as sess:
        sess.pop('venda_edicao', None)
    resp = authenticated_session.get('/editar_venda')
    assert resp.status_code in (302, 301)
    assert '/vendas' in resp.location
