import pytest
from datetime import datetime

@pytest.fixture
def logs_url():
    return '/logs'

def test_logs_renderiza_com_sucesso(client, mocker, logs_url):
    # Prepara mocks
    mocker.patch('app.routes.logs.verificar_permissao_acesso', return_value=True)
    # 2 logs com datas diferentes para testar ordenação
    logs_mock = [
        {'data': '05/07/2024', 'hora': '09:00:01', 'modificacao': 'Alterou senha', 'usuario': 'Joao'},
        {'data': '06/07/2024', 'hora': '10:12:10', 'modificacao': 'Login', 'usuario': 'Maria'},
    ]
    mocker.patch('app.routes.logs.logs_collection.find', return_value=logs_mock)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'maria', 'tipo': 'admin'}

    resp = client.get(logs_url)
    assert resp.status_code == 200
    # O template renderizado deve conter os logs ordenados (mais recente primeiro)
    data = resp.data.decode()
    assert "Maria" in data and "Joao" in data
    assert data.index('Maria') < data.index('Joao')  # Ordem correta

def test_logs_redirect_sem_user(client, mocker, logs_url):
    mocker.patch('app.routes.logs.verificar_permissao_acesso', return_value=True)
    # Não coloca user na session
    resp = client.get(logs_url, follow_redirects=False)
    assert resp.status_code == 302
    assert "/index.html" in resp.headers["Location"]

def test_logs_redirect_sem_permissao(client, mocker, logs_url):
    mocker.patch('app.routes.logs.verificar_permissao_acesso', return_value=False)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'sempermissao', 'tipo': 'vendedor'}
    resp = client.get(logs_url, follow_redirects=False)
    assert resp.status_code == 302
    assert "/index.html" in resp.headers["Location"]

def test_logs_lista_vazia(client, mocker, logs_url):
    mocker.patch('app.routes.logs.verificar_permissao_acesso', return_value=True)
    mocker.patch('app.routes.logs.logs_collection.find', return_value=[])
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get(logs_url)
    assert resp.status_code == 200
    data = resp.data.decode()
    # Não deve conter nome de usuário de exemplo se lista vazia
    assert 'Maria' not in data
    assert 'Joao' not in data

def test_logs_handle_data_hora_invalida(client, mocker, logs_url):
    mocker.patch('app.routes.logs.verificar_permissao_acesso', return_value=True)
    # Log com data/hora inválida: deve ordenar para o final
    logs_mock = [
        {'data': 'ABC', 'hora': 'DEFG', 'modificacao': 'Erro de data', 'usuario': 'Falho'},
        {'data': '06/07/2024', 'hora': '10:12:10', 'modificacao': 'Login', 'usuario': 'Maria'},
    ]
    mocker.patch('app.routes.logs.logs_collection.find', return_value=logs_mock)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get(logs_url)
    assert resp.status_code == 200
    data = resp.data.decode()
    # Maria vem antes do Falho
    assert data.index('Maria') < data.index('Falho')

def test_logs_erro_renderizacao(client, app, mocker, logs_url):
    mocker.patch('app.routes.logs.verificar_permissao_acesso', return_value=True)
    mocker.patch('app.routes.logs.logs_collection.find', side_effect=Exception("Falha inesperada!"))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    app.config['PROPAGATE_EXCEPTIONS'] = False
    resp = client.get(logs_url)
    assert resp.status_code == 500
    data = resp.data.decode()
    # O conteúdo pode variar, mas normalmente terá algum sinal de erro
    assert 'erro' in data.lower() or '500' in data or 'Falha' in data
