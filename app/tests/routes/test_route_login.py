import pytest

@pytest.fixture
def login_url():
    return '/login'

def test_login_sucesso(client, mocker, login_url):
    usuario_mock = {
        "_id": "abc123",
        "username": "vendedor",
        "nome_completo": "Vendedor Teste",
        "tipo": "vendedor",
        "foto": None,
        "email": "teste@teste.com",
        "fone": "11999999999",
        "pos_vendas": "pv1",
        "meta_mes": 10
    }
    mocker.patch('app.routes.login.is_sessao_bloqueada', return_value=(False, 0))
    mocker.patch('app.routes.login.autenticar_usuario', return_value=usuario_mock)
    update_one = mocker.patch('app.routes.login.usuarios_collection.update_one', return_value=None)

    resp = client.post(login_url, json={"username": "vendedor", "senha": "senha123"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["user"]["username"] == "vendedor"
    update_one.assert_called_once()

def test_login_erro_sessao_bloqueada(client, mocker, login_url):
    mocker.patch('app.routes.login.is_sessao_bloqueada', return_value=(True, 300))
    resp = client.post(login_url, json={"username": "qualquer", "senha": "senha"})
    data = resp.get_json()
    assert resp.status_code == 401
    assert data["success"] is False
    assert "bloqueada" in data["message"]

def test_login_erro_sessao_bloqueada_usuario(client, mocker, login_url):
    mocker.patch('app.routes.login.is_sessao_bloqueada', return_value=(False, 0))
    mocker.patch('app.routes.login.autenticar_usuario', return_value={"sessao_bloqueada": True, "tempo": 120})
    resp = client.post(login_url, json={"username": "teste", "senha": "senha"})
    data = resp.get_json()
    assert resp.status_code == 401
    assert data["success"] is False
    assert "bloqueada" in data["message"]

def test_login_usuario_bloqueado_no_banco(client, mocker, login_url):
    mocker.patch('app.routes.login.is_sessao_bloqueada', return_value=(False, 0))
    mocker.patch('app.routes.login.autenticar_usuario', return_value=None)
    # Simula usuário bloqueado no banco
    mocker.patch('app.routes.login.usuarios_collection.find_one', return_value={"username": "teste", "status": "bloqueado"})
    resp = client.post(login_url, json={"username": "teste", "senha": "senha"})
    data = resp.get_json()
    assert resp.status_code == 401
    assert data["success"] is False
    assert "bloqueado" in data["message"]

def test_login_usuario_invalido_ou_inativo(client, mocker, login_url):
    mocker.patch('app.routes.login.is_sessao_bloqueada', return_value=(False, 0))
    mocker.patch('app.routes.login.autenticar_usuario', return_value=None)
    mocker.patch('app.routes.login.usuarios_collection.find_one', return_value=None)
    resp = client.post(login_url, json={"username": "naoexiste", "senha": "senha"})
    data = resp.get_json()
    assert resp.status_code == 401
    assert data["success"] is False
    assert "inválidos" in data["message"]
