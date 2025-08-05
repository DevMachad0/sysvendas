import pytest
from flask import session
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

@pytest.fixture
def user_logged(monkeypatch, client):
    # Mocka user na session e permissão de acesso
    with client.session_transaction() as sess:
        sess['user'] = {
            'username': 'testeuser',
            'tipo': 'vendedor'
        }
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    return client

@pytest.fixture
def info_vendas(monkeypatch):
    monkeypatch.setattr('app.routes.cadastrarVendas.dados_valores_venda', lambda: {"condicoes": ["cond1"], "produtos": ["prod1"]})

@pytest.fixture
def configs(monkeypatch):
    fake_config = {
        'tipo': 'fim_expediente',
        'data': '01/01/2024',
        'hora': '18:15:00',
        'trabalha_sabado': False
    }
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda f, p=None: fake_config)

def test_get_cadastrar_vendas_redirect(client, monkeypatch):
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: False)
    # Não põe user na session
    resp = client.get('/cadastrar_vendas', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/index.html')

def test_get_cadastrar_vendas(client, monkeypatch):
    # Mocka permissão e adiciona usuário na sessão
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    resp = client.get('/cadastrar_vendas')
    assert resp.status_code == 200
    assert b'form' in resp.data  # ou outro conteúdo do template

def test_get_cadastrar_vendas_faturamento(client, monkeypatch):
    # Mocka permissão e adiciona usuário na sessão
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'faturamento'}

    resp = client.get('/cadastrar_vendas')
    assert resp.status_code == 302

def test_post_venda_ok(client, monkeypatch, user_logged, info_vendas, configs):
    """POST sucesso: todos os campos válidos"""
    # Mocks
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 'NUMERO123')
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda f, p: [{'username': 'vuser', 'pos_vendas': 'p1'}])
    monkeypatch.setattr('app.routes.cadastrarVendas.cadastrar_venda', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.registrar_notificacao', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    dados = {
        "usuario_id": "682f804e2c64910a1b2ffc41",
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
    }
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    json_resp = resp.get_json()
    assert resp.status_code == 200
    assert json_resp["success"] is True
    assert "numero_da_venda" in json_resp

def test_post_venda_eh_sabado_e_trabalha_sabado(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sábado, 13/07/2024, 10:00
            return datetime(2024, 7, 13, 10, 0, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '13/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': True
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_sabado_mas_nao_trabalha_sabado(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sábado, 13/07/2024, 10:00
            return datetime(2024, 7, 13, 10, 0, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '12/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_domingo(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Domingo, 14/07/2024, 10:00
            return datetime(2024, 7, 14, 10, 0, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '12/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_sexta_feira_depois_fim_expediente_e_trabalha_sabado(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sexta-feira, 12/07/2024, 19:00
            return datetime(2024, 7, 12, 19, 0, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '12/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': True
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_sexta_feira_depois_fim_expediente_mas_nao_trabalha_sabado(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sexta-feira, 12/07/2024, 19:00
            return datetime(2024, 7, 12, 19, 0, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '12/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_sexta_feira_antes_fim_expediente_mesmo_dia(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sexta-feira, 12/07/2024, 10:01
            return datetime(2024, 7, 12, 10, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '12/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_sexta_feira_antes_fim_expediente(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sexta-feira, 12/07/2024, 18:01
            return datetime(2024, 7, 12, 18, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '11/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_sexta_feira_dia_diferente_depois_hora_padrao_e_trabalha_sabado(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sexta-feira, 12/07/2024, 19:01
            return datetime(2024, 7, 12, 19, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '11/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': True
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_sexta_feira_dia_diferente_depois_hora_padrao_mas_nao_trabalha_sabado(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Sexta-feira, 12/07/2024, 19:01
            return datetime(2024, 7, 12, 19, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '11/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_segunda_a_quinta_dia_diferente(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Quarta-feira, 10/07/2024, 19:01
            return datetime(2024, 7, 10, 19, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '09/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_segunda_a_quinta_dia_diferente_antes_fim_expediente(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Quarta-feira, 10/07/2024, 10:01
            return datetime(2024, 7, 10, 10, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '09/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_eh_segunda_a_quinta_mesmo_dia_antes_fim_expediente(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Quarta-feira, 10/07/2024, 10:01
            return datetime(2024, 7, 10, 10, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '10/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_quantidade_acessos(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Quarta-feira, 10/07/2024, 10:01
            return datetime(2024, 7, 10, 10, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '10/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 0,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": "",
        "quantidade_acessos": "2"
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_erro_quantidade_acessos(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Quarta-feira, 10/07/2024, 10:01
            return datetime(2024, 7, 10, 10, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '10/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": "",
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 400

def test_post_venda_eh_segunda_a_quinta_mesmo_dia_depois_fim_expediente(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Quarta-feira, 10/07/2024, 19:01
            return datetime(2024, 7, 10, 19, 1, 0)
        @classmethod
        def strptime(cls, data, fmt):
            return datetime.strptime(data, fmt)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {
        'tipo': 'fim_expediente',
        'data': '10/07/2024',
        'hora': '18:00:00',
        'trabalha_sabado': False
    })
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_erro_data(client, monkeypatch, user_logged, info_vendas, configs):
    # Força datetime.now para um sábado 10h da manhã
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Quarta-feira, 10/07/2024, 19:01
            return datetime(2024, 7, 10, 19, 1, 0)

    # Monkeypatch datetime no módulo da rota
    monkeypatch.setattr("app.routes.cadastrarVendas.datetime", FakeDatetime)

    # Mock do config, para cair no caminho "trabalha_sabado == True"
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {})
    
    # Mock de todas as validações anteriores!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *a, **kw: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])
    
    # Monta payload com todos campos obrigatórios (veja exemplos anteriores)
    dados = {
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Empresa",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    assert resp.status_code == 200

def test_post_venda_emails_list(client, monkeypatch, user_logged, info_vendas, configs):
    """POST sucesso: todos os campos válidos"""
    # Mocks
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 'NUMERO123')
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda f, p: [{'username': 'vuser', 'pos_vendas': 'p1'}])
    monkeypatch.setattr('app.routes.cadastrarVendas.cadastrar_venda', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.registrar_notificacao', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    dados = {
        "emails": ["a@b.com", "  c@d.com   "],
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
    }
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    json_resp = resp.get_json()
    assert resp.status_code == 200
    assert json_resp["success"] is True
    assert "numero_da_venda" in json_resp

def test_post_venda_fones_list(client, monkeypatch, user_logged, info_vendas, configs):
    """POST sucesso: todos os campos válidos"""
    # Mocks
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 'NUMERO123')
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda f, p: [{'username': 'vuser', 'pos_vendas': 'p1'}])
    monkeypatch.setattr('app.routes.cadastrarVendas.cadastrar_venda', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.registrar_notificacao', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    dados = {
        "emails": [" a@b.com", "  c@d.com   "],
        "fones": [" 11999999999 ", " 11999999998 "],
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
    }
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    json_resp = resp.get_json()
    assert resp.status_code == 200
    assert json_resp["success"] is True
    assert "numero_da_venda" in json_resp

def test_post_venda_desconto_autorizado_str_true(client, monkeypatch, user_logged, info_vendas, configs):
    """POST sucesso: todos os campos válidos"""
    # Mocks
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 'NUMERO123')
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda f, p: [{'username': 'vuser', 'pos_vendas': 'p1'}])
    monkeypatch.setattr('app.routes.cadastrarVendas.cadastrar_venda', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.registrar_notificacao', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    dados = {
        "emails": [" a@b.com", "  c@d.com   "],
        "fones": [" 11999999999 ", " 11999999998 "],
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "desconto_autorizado": "true"
    }
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    json_resp = resp.get_json()
    assert resp.status_code == 200
    assert json_resp["success"] is True
    assert "numero_da_venda" in json_resp

def test_post_venda_desconto_autorizado_str_on(client, monkeypatch, user_logged, info_vendas, configs):
    """POST sucesso: todos os campos válidos"""
    # Mocks
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 'NUMERO123')
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda f, p: [{'username': 'vuser', 'pos_vendas': 'p1'}])
    monkeypatch.setattr('app.routes.cadastrarVendas.cadastrar_venda', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.registrar_notificacao', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    dados = {
        "emails": [" a@b.com", "  c@d.com   "],
        "fones": [" 11999999999 ", " 11999999998 "],
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "desconto_autorizado": "on"
    }
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    json_resp = resp.get_json()
    assert resp.status_code == 200
    assert json_resp["success"] is True
    assert "numero_da_venda" in json_resp

def test_post_venda_desconto_autorizado_str_1(client, monkeypatch, user_logged, info_vendas, configs):
    """POST sucesso: todos os campos válidos"""
    # Mocks
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 'NUMERO123')
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda f, p: [{'username': 'vuser', 'pos_vendas': 'p1'}])
    monkeypatch.setattr('app.routes.cadastrarVendas.cadastrar_venda', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.registrar_notificacao', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    dados = {
        "emails": [" a@b.com", "  c@d.com   "],
        "fones": [" 11999999999 ", " 11999999998 "],
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "desconto_autorizado": "1"
    }
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    json_resp = resp.get_json()
    assert resp.status_code == 200
    assert json_resp["success"] is True
    assert "numero_da_venda" in json_resp

def test_post_venda_produto_personalizado(client, monkeypatch, user_logged, info_vendas, configs):
    """POST sucesso: todos os campos válidos"""
    # Mocks
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 'NUMERO123')
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda f, p: [{'username': 'vuser', 'pos_vendas': 'p1'}])
    monkeypatch.setattr('app.routes.cadastrarVendas.cadastrar_venda', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.registrar_notificacao', lambda **kwargs: None)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}

    dados = {
        "emails": [" a@b.com", "  c@d.com   "],
        "fones": [" 11999999999 ", " 11999999998 "],
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "produto": "",
        "produtos_personalizados": "Personalizado: Teste, Teste1"
    }
    resp = user_logged.post('/cadastrar_vendas', json=dados)
    json_resp = resp.get_json()
    assert resp.status_code == 200
    assert json_resp["success"] is True
    assert "numero_da_venda" in json_resp

def test_post_venda_sem_email(client, monkeypatch, user_logged, info_vendas, configs):
    """POST erro: Sem email"""
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor"
    })
    assert resp.status_code == 400
    assert not resp.get_json()["success"]

def test_post_venda_valor_nao_eh_numero(client, monkeypatch, user_logged, info_vendas, configs):
    # Mocka todas as funções que podem barrar antes!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *args, **kwargs: False)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {'tipo':'fim_expediente','data':'01/01/2024','hora':'18:00:00','trabalha_sabado':False})
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "a@b.com",
        "fones": "+5511999999999",
        "tipo_cliente": "verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "erro",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",  # <--- garanta campos obrigatórios!
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    })
    data = resp.get_json()
    assert resp.status_code == 400
    assert not resp.get_json()["success"]
    assert "Algum valor não é um número." in data['erro']

def test_post_venda_sem_fone(client, monkeypatch, user_logged, info_vendas, configs):
    """POST erro: Sem email"""
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": [" a@b.com", "  c@d.com   "],
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor"
    })
    assert resp.status_code == 400
    assert not resp.get_json()["success"]

def test_post_venda_email_invalido(client, monkeypatch, user_logged, info_vendas, configs):
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (False, 0))
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "email_invalido",
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor"
    })
    assert resp.status_code == 400
    assert not resp.get_json()["success"]

def test_post_venda_fone_invalido(client, monkeypatch, user_logged, info_vendas, configs):
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (False, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "a@b.com",
        "fones": "fone_invalido",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor"
    })
    assert resp.status_code == 400
    assert not resp.get_json()["success"]

def test_post_venda_tipo_cliente_invalido(client, monkeypatch, user_logged, info_vendas, configs):
    # Mocka todas as funções que podem barrar antes!
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: False)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.eh_numero', lambda *args, **kwargs: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.gerar_numero_venda', lambda: 1)
    monkeypatch.setattr('app.routes.cadastrarVendas.normalizar_valor', lambda x: x)
    monkeypatch.setattr('app.routes.cadastrarVendas.configs_collection.find_one', lambda *a, **kw: {'tipo':'fim_expediente','data':'01/01/2024','hora':'18:00:00','trabalha_sabado':False})
    monkeypatch.setattr('app.routes.cadastrarVendas.usuarios_collection.find', lambda *a, **k: [])

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "a@b.com",
        "fones": "+5511999999999",
        "tipo_cliente": "Inválido",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor",
        "nome": "Teste Nome",  # <--- garanta campos obrigatórios!
        "nome_do_contato": "Contato",
        "rua": "Rua X",
        "bairro": "Bairro Y",
        "numero": "123",
        "cidade": "Cidade Z",
        "estado": "SP",
        "cep": "12345-678",
        "cnpj_cpf": "12345678900",
        "razao_social": "Razão",
        "inscricao_estadual_identidade": "123",
        "data_prestacao_inicial": "2024-07-01",
        "tipo_remessa": "",
        "obs": "",
        "posvendas": "",
        "obs_vendas": ""
    })
    data = resp.get_json()
    assert resp.status_code == 400
    assert not resp.get_json()["success"]
    assert "O tipo de cliente" in data['erro']

def test_post_venda_produto_invalido(client, monkeypatch, user_logged, info_vendas, configs):
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: False)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": None,
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor"
    })
    data = resp.get_json()
    assert resp.status_code == 400
    assert "O produto" in data['erro']

def test_post_venda_condicao_invalida(client, monkeypatch, user_logged, info_vendas, configs):
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: False)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "ncond",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor"
    })
    assert resp.status_code == 400
    assert not resp.get_json()["success"]

def test_post_venda_status_invalido(client, monkeypatch, user_logged, info_vendas, configs):
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: False)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Errado",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 2,
        "nome_vendedor": "vendedor"
    })
    assert resp.status_code == 400
    assert not resp.get_json()["success"]

def test_post_venda_acessos_invalido(client, monkeypatch, user_logged, info_vendas, configs):
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_email', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_fone', lambda x: (True, 0))
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_tipo_cliente', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_produto', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_condicoes', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verifica_status_vendas', lambda x: True)
    monkeypatch.setattr('app.routes.cadastrarVendas.verificar_permissao_acesso', lambda username: True)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'testeuser', 'tipo': 'vendedor'}
    resp = user_logged.post('/cadastrar_vendas', json={
        "emails": "a@b.com",
        "fones": "11999999999",
        "tipo_cliente": "Verde",
        "produto": "prod1",
        "condicoes": "1",
        "status": "Aguardando",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_parcelas": "100",
        "quantidade_acessos": 0,
        "nome_vendedor": "vendedor"
    })
    assert resp.status_code == 400
    assert not resp.get_json()["success"]
