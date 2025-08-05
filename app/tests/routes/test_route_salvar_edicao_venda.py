import pytest
from bson import ObjectId


@pytest.fixture
def venda_mock():
    """Venda fake para edição."""
    return {
        "numero_da_venda": "001-2025",
        "endereco": {
            "rua": "Rua XPTO",
            "bairro": "Centro",
            "numero": "100",
            "cidade": "Exemplo",
            "estado": "SP"
        },
        "produto": "Produto A",
        "valor_real": "1000",
        "valor_tabela": "1100",
        "valor_entrada": "0",
        "valor_venda_avista": "0",
        "valor_parcelas": "0",
        "condicoes": "A/C | 1+1",
        "data_prestacao_inicial": "2025-01-10",
        "tipo_cliente": "empresa",
        "status": "Aguardando",
        "obs_vendas": "obs antiga",
        "quantidade_acessos": 2,
        "logs": [],
        "vendedor": "Vendedor Teste",
        "posvendas": "pv_user"
    }

@pytest.fixture
def user_vendedor():
    return {"username": "vend_user", "tipo": "vendedor"}

@pytest.fixture
def user_faturamento():
    return {"username": "fat_user", "tipo": "faturamento"}

@pytest.fixture
def user_admin():
    return {"username": "admin", "tipo": "admin"}

def make_valid_payload(venda):
    return {
        "numero_da_venda": venda["numero_da_venda"],
        "produto": venda["produto"],
        "valor_real": "1200",
        "valor_tabela": "1200",
        "valor_entrada": "100",
        "valor_venda_avista": "1000",
        "valor_parcelas": "0",
        "condicoes": venda["condicoes"],
        "data_prestacao_inicial": "2025-01-20",
        "tipo_cliente": venda["tipo_cliente"],
        "status": "Aguardando",
        "obs_vendas": "Edição ok",
        "quantidade_acessos": 2
    }

def test_salvar_edicao_venda_sucesso(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    payload = make_valid_payload(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_venda_nao_encontrada(client, monkeypatch, user_admin):
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    resp = client.post('/salvar_edicao_venda', json={"numero_da_venda": "999"})
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False

def test_salvar_edicao_venda_permissao_faturamento(client, monkeypatch, venda_mock, user_faturamento):
    """Faturamento não pode editar para status refazer/aguardando/cancelada"""
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    with client.session_transaction() as sess:
        sess['user'] = user_faturamento
    payload = make_valid_payload(venda_mock)
    payload['status'] = 'Refazer'
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 403
    assert "Sem permissão" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_permissao_vendedor(client, monkeypatch, venda_mock, user_vendedor):
    """Vendedor não pode editar para status aprovada/faturado/cancelada"""
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    with client.session_transaction() as sess:
        sess['user'] = user_vendedor
    payload = make_valid_payload(venda_mock)
    payload['status'] = 'Aprovada'
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 403
    assert "Sem permissão" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_cancelada_sem_obs(client, monkeypatch, venda_mock, user_admin):
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    payload = make_valid_payload(venda_mock)
    payload['status'] = 'Cancelada'
    payload['obs_vendas'] = ''
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 403
    assert "motivo do cancelamento" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_condicao_invalida(client, monkeypatch, venda_mock, user_admin):
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: False)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    payload = make_valid_payload(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert "não está cadastrada" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_tipo_cliente_invalido(client, monkeypatch, venda_mock, user_admin):
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: False)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    payload = make_valid_payload(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert "tipo de cliente" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_status_invalido(client, monkeypatch, venda_mock, user_admin):
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: False)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    payload = make_valid_payload(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert "Status da Venda" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_produto_invalido(client, monkeypatch, venda_mock, user_admin):
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: False)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    payload = make_valid_payload(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert "não está cadastrado" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_valores_invalidos(client, monkeypatch, venda_mock, user_admin):
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: False)
    with client.session_transaction() as sess:
        sess['user'] = user_admin
    payload = make_valid_payload(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert "não é um número" in resp.get_json().get('erro', '')

def test_salvar_edicao_venda_email_reenviado(client, monkeypatch, venda_mock, user_vendedor):
    """Se status == aguardando e user é vendedor, deve reenviar email e retornar sucesso"""
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_vendedor
    payload = make_valid_payload(venda_mock)
    payload['status'] = 'Aguardando'
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert "Email de pedido de venda reenviado" in resp.get_json().get('success', '')


def test_salvar_edicao_venda_produto_personalizado(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": venda["condicoes"],
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 2
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_erro_quantidade_acessos_avista(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "avista",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": "erro"
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False

def test_salvar_edicao_venda_quantidade_acessos_avista(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "avista",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": "2"
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_erro_quantidade_acessos_entrada(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "entrada_parcela",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": "erro"
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False

def test_salvar_edicao_venda_desconto_autorizado_bool(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "entrada_parcela",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 2,
            "desconto_autorizado": True
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_quantidade_acessos_menor_que_1(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "avista",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 0,
            "desconto_autorizado": True
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False

def test_salvar_edicao_venda_desconto_autorizado_outro(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "entrada_parcela",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 2,
            "desconto_autorizado": []
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_desconto_live_bool(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "entrada_parcela",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 2,
            "desconto_live": True
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_desconto_live_outro(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "entrada_parcela",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "Aguardando",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 2,
            "desconto_live": []
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_status_faturado(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "entrada_parcela",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "faturado",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 2,
            "desconto_live": []
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_status_aprovada(client, monkeypatch, venda_mock, user_admin):
    """Teste de sucesso básico (admin pode editar qualquer status)"""
    # Mock de busca da venda no banco
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.find_one', lambda f: venda_mock)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.vendas_collection.update_one', lambda f, u: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find_one', lambda f, *a, **kw: {"username": "vend_user"})
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.usuarios_collection.find', lambda f, *a, **kw: [])
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_condicoes', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_tipo_cliente', lambda c: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_status_vendas', lambda s: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.verifica_produto', lambda p: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.eh_numero', lambda *a: True)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.normalizar_valor', lambda v: v)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.registrar_notificacao', lambda **k: None)
    monkeypatch.setattr('app.routes.salvarEdicaoVenda.reenviar_venda', lambda data=None: None)
    with client.session_transaction() as sess:
        sess['user'] = user_admin

    def make_valid_payload_personalizado(venda):
        return {
            "numero_da_venda": venda["numero_da_venda"],
            "produto": "",
            "produtos_personalizados": "Personalizado: Teste, Teste1",
            "valor_real": "1200",
            "valor_tabela": "1200",
            "valor_entrada": "100",
            "valor_venda_avista": "1000",
            "valor_parcelas": "0",
            "condicoes": "A/C | 1+1",
            "condicoes_venda": "entrada_parcela",
            "data_prestacao_inicial": "2025-01-20",
            "tipo_cliente": venda["tipo_cliente"],
            "status": "aprovada",
            "obs_vendas": "Edição ok",
            "quantidade_acessos": 2,
            "desconto_live": []
        }
    
    payload = make_valid_payload_personalizado(venda_mock)
    resp = client.post('/salvar_edicao_venda', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_salvar_edicao_venda_objectid_serializacao(client, monkeypatch):
    # --- Fake venda com ObjectId na raiz, em dict e em logs ---
    fake_objid_1 = ObjectId()
    fake_objid_2 = ObjectId()
    fake_objid_3 = ObjectId()
    fake_venda = {
        "numero_da_venda": "V123",
        "campo_objectid": fake_objid_1,  # <-- Força linha 171
        "endereco": {"cidade": "São Paulo", "obj": fake_objid_2},  # <-- Força linha 173
        "logs": [
            {"acao": "editou", "obj_log": fake_objid_3}  # <-- Força linha 183
        ]
    }
    # Monkeypatch do find_one e update_one
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.vendas_collection.find_one", lambda filtro: fake_venda.copy())
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.vendas_collection.update_one", lambda f, u: None)
    # Fakes para todos os serviços necessários
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.verifica_condicoes", lambda x: True)
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.verifica_tipo_cliente", lambda x: True)
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.verifica_status_vendas", lambda x: True)
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.verifica_produto", lambda x: True)
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.eh_numero", lambda *args: True)
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.normalizar_valor", lambda x: x)
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.registrar_notificacao", lambda **kwargs: None)
    monkeypatch.setattr("app.routes.salvarEdicaoVenda.reenviar_venda", lambda **kwargs: None)
    monkeypatch.setattr("app.models.usuarios_collection.find_one", lambda *a, **k: {"username": "admin"})
    monkeypatch.setattr("app.models.usuarios_collection.find", lambda *a, **k: [])

    # Cria sessão autenticada
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'tipo': 'admin'}

    resp = client.post("/salvar_edicao_venda", json={
        "numero_da_venda": "V123",
        "status": "Aguardando",
        "tipo_cliente": "Normal",
        "condicoes": "1",
        "produto": "Produto Teste",
        "valor_real": "100",
        "valor_tabela": "100",
        "valor_entrada": "0",
        "valor_venda_avista": "0",
        "valor_parcelas": "0",
        "quantidade_acessos": 2
    })

    # --- Verificações ---
    assert resp.status_code == 200
    # Busca a venda serializada salva na sessão
    with client.session_transaction() as sess:
        venda_edicao = sess['venda_edicao']
        # O campo que era ObjectId agora deve ser str
        assert isinstance(venda_edicao['campo_objectid'], str)
        assert isinstance(venda_edicao['endereco']['obj'], str)
        assert isinstance(venda_edicao['logs'][0]['obj_log'], str)
