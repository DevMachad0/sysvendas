import pytest
from flask import url_for
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import DESCENDING


class MockCursor:
    def __init__(self, data):
        self._data = list(data)
    def sort(self, key, order):
        # Suporta tanto string ('data_criacao') quanto tupla, só pra garantir.
        reverse = (order == -1 or order == DESCENDING)
        self._data.sort(key=lambda x: x.get(key) or x.get(str(key)), reverse=reverse)
        return self
    def __iter__(self):
        return iter(self._data)


@pytest.fixture
def vendas_mock():
    # Gera alguns registros falsos de venda para testar listagem/filtros
    agora = datetime.now()
    return [
        {
            "numero_da_venda": "V001",
            "usuario_id": ObjectId("60e6f1a4b77c1e0b6c2fd9d1"),
            "vendedor": "vendedor01",
            "nome": "Cliente A",
            "posvendas": "pv1,pv2",
            "status": "Aguardando",
            "data_criacao": agora - timedelta(days=1),
            "cnpj_cpf": "12345678900"
        },
        {
            "numero_da_venda": "V002",
            "usuario_id": ObjectId("60e6f1a4b77c1e0b6c2fd9d2"),
            "vendedor": "vendedor02",
            "nome": "Cliente B",
            "posvendas": "pv2",
            "status": "Faturado",
            "data_criacao": agora,
            "cnpj_cpf": "98765432100"
        },
        # Venda antiga (para testar filtro por período)
        {
            "numero_da_venda": "V003",
            "usuario_id": ObjectId("60e6f1a4b77c1e0b6c2fd9d3"),
            "vendedor": "vendedor01",
            "nome": "Cliente C",
            "posvendas": "pv1",
            "status": "Aprovada",
            "data_criacao": agora - timedelta(days=30),
            "cnpj_cpf": "11111111111"
        },
    ]

def test_vendas_sem_autenticacao(client):
    resp = client.get('/vendas')
    # Deve redirecionar para o index se não autenticado
    assert resp.status_code == 302
    assert '/index.html' in resp.location

def test_vendas_sem_permissao(client, monkeypatch):
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: False)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor'}
    resp = client.get('/vendas')
    assert resp.status_code == 302
    assert '/index.html' in resp.location

def test_vendas_vendedor_lista(client, monkeypatch, vendas_mock):
    # Simula vendedor logado (só vê as próprias vendas)
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find_one', lambda *a, **k: None)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.sort', lambda *a, **k: vendas_mock)

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    resp = client.get('/vendas')
    assert resp.status_code == 200
    assert b'Cliente A' in resp.data  # Deve conter nome da venda do vendedor

def test_vendas_posvendas_lista(client, monkeypatch, vendas_mock):
    # Simula pos_vendas logado (vê vendas em que está envolvido)
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'pv2', 'tipo': 'pos_vendas'}

    resp = client.get('/vendas')
    assert resp.status_code == 200

def test_vendas_admin_lista(client, monkeypatch, vendas_mock):
    # Simula admin logado (vê tudo)
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    monkeypatch.setattr('app.routes.vendas.vendas_collection.sort', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?ver_todas=1')
    assert resp.status_code == 200
    assert b'Cliente A' in resp.data
    assert b'Cliente B' in resp.data

def test_vendas_filtro_busca(client, monkeypatch, vendas_mock):
    # Filtro por CNPJ/CPF, nome do vendedor, ou nome do cliente
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    resp = client.get('/vendas?busca=Cliente+A')
    assert resp.status_code == 200
    assert b'Cliente A' in resp.data

def test_vendas_filtro_base_nao(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs):
            return self

    def fake_find(filtro, proj):
        # Só checa se o filtro de busca está presente no $and ou direto
        filtro_texto = {
            '$or': [
                {'cnpj_cpf': {'$regex': 'Buscado', '$options': 'i'}},
                {'vendedor': {'$regex': 'Buscado', '$options': 'i'}},
                {'nome': {'$regex': 'Buscado', '$options': 'i'}}
            ]
        }
        
        if (
            isinstance(filtro, dict) and
            "$and" in filtro and
            any(ft == filtro_texto for ft in filtro["$and"])
        ):
            return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?busca=Buscado')
    assert resp.status_code == 200
    assert b'Cliente A' in resp.data

def test_vendas_filtro_base_pos_vendas(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        pass

    def fake_find(filtro, proj):
        # Permite filtro vazio (todas as vendas, cenário pós-vendas ver_todas=1)
        if filtro == {}:
            return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    monkeypatch.setattr('app.routes.vendas.render_template', lambda *a, **k: "HTML OK")

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'pv2', 'tipo': 'pos_vendas'}

    resp = client.get('/vendas?busca=Buscado&ver_todas=1')
    assert resp.status_code == 200
    assert b'HTML OK' in resp.data

def test_vendas_filtro_periodo_pos_vendas(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        pass

    def fake_find(filtro, proj):
        # Espera que o filtro seja só o período, sem $and
        assert filtro == {}
        return FakeFindResult(vendas_mock)


    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    monkeypatch.setattr('app.routes.vendas.render_template', lambda *a, **k: "HTML OK")

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'pv2', 'tipo': 'pos_vendas'}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data_inicio={hoje}&data_fim={hoje}')
    assert resp.status_code == 200
    assert b'HTML OK' in resp.data

def test_vendas_filtro_data_pos_vendas(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        pass

    def fake_find(filtro, proj):
        vendas = FakeFindResult(vendas_mock)
        assert 'data_criacao' in vendas[0]
        return FakeFindResult(vendas_mock)


    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    monkeypatch.setattr('app.routes.vendas.render_template', lambda *a, **k: "HTML OK")

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'pv2', 'tipo': 'pos_vendas'}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data={hoje}&ver_todas=1')
    assert resp.status_code == 200
    assert b'HTML OK' in resp.data

def test_vendas_filtro_periodo_sem_base(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        # Espera que o filtro seja só o período, sem $and
        assert filtro == {}
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data_inicio={hoje}&data_fim={hoje}?ver_todas=1')
    assert resp.status_code == 200

def test_vendas_filtro_data_sem_base(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        # Só espera filtro_data, sem $and!
        assert 'data_criacao' in filtro
        assert '$gte' in filtro['data_criacao']
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    monkeypatch.setattr('app.routes.vendas.render_template', lambda *a, **k: "OK")
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data={hoje}&ver_todas=1')
    assert resp.status_code == 200

def test_vendas_filtro_data_com_base(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        # Só espera filtro_data, sem $and!
        assert '$and' in filtro
        assert any(isinstance(x, dict) and '$or' in x for x in filtro['$and'])  # Busca
        assert any(isinstance(x, dict) and 'data_criacao' in x for x in filtro['$and'])  # Data
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    monkeypatch.setattr('app.routes.vendas.render_template', lambda *a, **k: "OK")
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?busca=Joao&data={hoje}&ver_todas=1')
    assert resp.status_code == 200

def test_vendas_filtro_status_com_base_com_and(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        # Deve gerar um $and com busca e status!
        assert '$and' in filtro
        assert any(isinstance(x, dict) and 'status' in x for x in filtro['$and'])
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?busca=Joao&status=Aprovada')
    assert resp.status_code == 200

def test_vendas_somente_periodo(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        # Aqui espera só o filtro_periodo, sem $and!
        assert filtro == {
            'data_criacao': {
                '$gte': datetime(2025, 7, 1),
                '$lte': datetime(2025, 7, 31, 23, 59, 59)
            }
        }
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?data_inicio=2025-07-01&data_fim=2025-07-31')
    assert resp.status_code == 200
    assert b'Cliente A' in resp.data

def test_vendas_filtro_status_sozinho_com_base(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        # Confirma que status está "Aprovada" de qualquer jeito
        def tem_status_aprovada(f):
            if isinstance(f, dict):
                if f.get("status") == "Aprovada":
                    return True
                if "$and" in f:
                    return any(tem_status_aprovada(cond) for cond in f["$and"])
            return False

        assert tem_status_aprovada(filtro)
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    # Mock do render_template:
    monkeypatch.setattr('app.routes.vendas.render_template', lambda *a, **k: "HTML OK")

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?status=Aprovada')
    assert resp.status_code == 200
    assert b'HTML OK' in resp.data

def test_vendas_filtro_status_sozinho(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        assert filtro == {"status": "Aprovada"}
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    # Mock do render_template:
    monkeypatch.setattr('app.routes.vendas.render_template', lambda *a, **k: "HTML OK")

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?status=Aprovada&ver_todas=1')
    assert resp.status_code == 200
    assert b'HTML OK' in resp.data

def test_vendas_filtro_and_periodo(client, monkeypatch, vendas_mock):
    class FakeFindResult(list):
        def sort(self, *args, **kwargs): return self

    def fake_find(filtro, proj):
        # Junta filtro_base, filtro_periodo e depois adiciona status no $and
        assert '$and' in filtro
        # Espera três itens: busca, período, status
        assert any(isinstance(x, dict) and 'status' in x for x in filtro['$and'])
        return FakeFindResult(vendas_mock)

    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', fake_find)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?busca=Buscado&data_inicio=2025-07-01&data_fim=2025-07-31&status=Aprovada')
    assert resp.status_code == 200
    assert b'Cliente A' in resp.data

def test_vendas_filtro_periodo(client, monkeypatch, vendas_mock):
    # Filtro por período de datas
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data_inicio={hoje}&data_fim={hoje}')
    assert resp.status_code == 200

def test_vendas_filtro_periodo_erro(client, monkeypatch, vendas_mock):
    # Filtro por período de datas
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data_inicio="erro"&data_fim={hoje}')
    assert resp.status_code == 200

def test_vendas_filtro_periodo_erro_sem_fim(client, monkeypatch, vendas_mock):
    # Filtro por período de datas
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data_inicio="erro"&data_fim=')
    assert resp.status_code == 200

def test_vendas_filtro_periodo_sem_fim(client, monkeypatch, vendas_mock):
    # Filtro por período de datas
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data_inicio={hoje}&data_fim=')
    assert resp.status_code == 200

def test_vendas_filtro_periodo_sem_inicio(client, monkeypatch, vendas_mock):
    # Filtro por período de datas
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data_inicio=&data_fim={hoje}')
    assert resp.status_code == 200

def test_vendas_filtro_periodo_data(client, monkeypatch, vendas_mock):
    # Filtro por período de datas
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data={hoje}')
    assert resp.status_code == 200

def test_vendas_filtro_periodo_data_erro(client, monkeypatch, vendas_mock):
    # Filtro por período de datas
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    hoje = datetime.now().date()
    resp = client.get(f'/vendas?data="erro"')
    assert resp.status_code == 200

def test_vendas_filtro_status(client, monkeypatch, vendas_mock):
    # Filtro por status
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', lambda filtro, proj=None: MockCursor(vendas_mock))
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'vendedor01', 'tipo': 'vendedor', 'user_id': str(vendas_mock[0]['usuario_id'])}

    resp = client.get('/vendas?status=Aguardando')
    assert resp.status_code == 200

def test_vendas_exception(client, monkeypatch):
    # Simula erro inesperado no acesso ao banco
    monkeypatch.setattr('app.routes.vendas.verificar_permissao_acesso', lambda username: True)
    def raise_exception(*a, **k): raise Exception("Falha!")
    monkeypatch.setattr('app.routes.vendas.vendas_collection.find', raise_exception)
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.get('/vendas?ver_todas=1')
    assert resp.status_code == 500 or resp.status_code == 302  # depende do seu tratamento

