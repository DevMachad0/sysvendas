import pytest
from datetime import datetime

from app.services import cadastrar_venda

def test_cadastrar_venda_com_entrada_1mais1_parcela(monkeypatch):
    # Simula o vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "pos_vendas": "Amanda Pós",
        "email": "joao@empresa.com"
    }
    # Simula configs
    configs_fake = {
        'tipo': 'geral',
        'email_smtp_principal': 'vendas@empresa.com:true',
        'email_smtp_secundario': 'backup@empresa.com:false',
        'smtp': 'smtp.empresa.com',
        'porta': 587,
        'email_copia': 'copia@empresa.com',
        'senha_email_smtp': 'segredo'
    }
    email_enviado = {}
    venda_inserida = {}

    # Mock do find_one das coleções
    def fake_find_one_usuarios(query):
        return vendedor_fake
    def fake_find_one_configs(query):
        return configs_fake

    # Mock do enviar_email: salva argumentos para inspeção
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Mock do nova_venda: salva argumentos e retorna valor fixo
    def fake_nova_venda(**kwargs):
        venda_inserida.update(kwargs)
        return "resultado_insert"

    # Patch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)
    monkeypatch.setattr("app.services.nova_venda", fake_nova_venda)

    # Dados da venda simulada
    venda_data = {
        "numero_da_venda": "VEND01",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "endereco": {"rua": "Rua Y", "bairro": "Centro", "numero": "123", "cidade": "Cidade", "estado": "UF"},
        "cep": "12345-000",
        "cnpj_cpf": "123.456.789-00",
        "razao_social": "Empresa X",
        "inscricao_estadual_identidade": "ISENTO",
        "produto": "PRODUTO1",
        "valor_tabela": 5000,
        "condicoes": "a/c|1+1",
        "valor_parcelas": "2500,00",
        "data_prestacao_inicial": "2025-07-10",
        "tipo_envio_boleto": "email",
        "tipo_remessa": "normal",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "fone_vendedor": "11988888888",
        "email_vendedor": "joao@empresa.com",
        "vendedor": "João Vendedor",
        "obs": "Sem observação",
        "status": "Aprovada",
        "valor_entrada": "1000,00",
        "condicoes_venda": "entrada_parcela",
        "valor_venda_avista": "4000,00",
        "valor_real": "5000,00",
        "data_criacao": datetime(2025, 7, 7, 15, 0, 0),
        "logs": [],
        "desconto_autorizado": True,
        "caminho_arquivos": "",
        "obs_vendas": "",
        "tipo_cliente": "Verde"
    }

    # Executa a função
    usuario_id = "user_id_fake"
    resultado = cadastrar_venda(usuario_id, venda_data)

    # Checa se chamou nova_venda com os argumentos esperados (exemplo, checa alguns)
    assert venda_inserida["usuario_id"] == usuario_id
    assert venda_inserida["nome"] == "Cliente X"
    assert venda_inserida["posvendas"] == "Amanda Pós"
    assert venda_inserida["vendedor"] == "João Vendedor"
    assert venda_inserida["valor_tabela"] == 5000
    assert venda_inserida["condicoes"] == "a/c|1+1"
    assert venda_inserida["condicoes_venda"] == "entrada_parcela"
    assert venda_inserida["valor_entrada"] == "1000,00"

    # Checa se o email foi enviado com email_remetente correto e outros campos
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert "Cliente X" in email_enviado["assunto"]
    assert email_enviado["email_destinatario"] == "joao@empresa.com"

    # Checa se retorna o resultado de nova_venda
    assert resultado == "resultado_insert"

def test_cadastrar_venda_sem_entrada_1mais1_avista(monkeypatch):
    # Simula o vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "pos_vendas": "Amanda Pós",
        "email": "joao@empresa.com"
    }
    # Simula configs
    configs_fake = {
        'tipo': 'geral',
        'email_smtp_principal': 'vendas@empresa.com:true',
        'email_smtp_secundario': 'backup@empresa.com:false',
        'smtp': 'smtp.empresa.com',
        'porta': 587,
        'email_copia': 'copia@empresa.com',
        'senha_email_smtp': 'segredo'
    }
    email_enviado = {}
    venda_inserida = {}

    # Mock do find_one das coleções
    def fake_find_one_usuarios(query):
        return vendedor_fake
    def fake_find_one_configs(query):
        return configs_fake

    # Mock do enviar_email: salva argumentos para inspeção
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Mock do nova_venda: salva argumentos e retorna valor fixo
    def fake_nova_venda(**kwargs):
        venda_inserida.update(kwargs)
        return "resultado_insert"

    # Patch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)
    monkeypatch.setattr("app.services.nova_venda", fake_nova_venda)

    # Dados da venda simulada
    venda_data = {
        "numero_da_venda": "VEND01",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "endereco": {"rua": "Rua Y", "bairro": "Centro", "numero": "123", "cidade": "Cidade", "estado": "UF"},
        "cep": "12345-000",
        "cnpj_cpf": "123.456.789-00",
        "razao_social": "Empresa X",
        "inscricao_estadual_identidade": "ISENTO",
        "produto": "PRODUTO1",
        "valor_tabela": 5000,
        "condicoes": "a/c|1+1",
        "valor_parcelas": "",
        "data_prestacao_inicial": "2025-07-10",
        "tipo_envio_boleto": "email",
        "tipo_remessa": "normal",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "fone_vendedor": "11988888888",
        "email_vendedor": "joao@empresa.com",
        "vendedor": "João Vendedor",
        "obs": "Sem observação",
        "status": "Aprovada",
        "valor_entrada": "",
        "condicoes_venda": "avista",
        "valor_venda_avista": "5000,00",
        "valor_real": "5000,00",
        "data_criacao": datetime(2025, 7, 7, 15, 0, 0),
        "logs": [],
        "desconto_autorizado": True,
        "caminho_arquivos": "",
        "obs_vendas": "",
        "tipo_cliente": "Verde"
    }

    # Executa a função
    usuario_id = "user_id_fake"
    resultado = cadastrar_venda(usuario_id, venda_data)

    # Checa se chamou nova_venda com os argumentos esperados (exemplo, checa alguns)
    assert venda_inserida["usuario_id"] == usuario_id
    assert venda_inserida["nome"] == "Cliente X"
    assert venda_inserida["posvendas"] == "Amanda Pós"
    assert venda_inserida["vendedor"] == "João Vendedor"
    assert venda_inserida["valor_tabela"] == 5000
    assert venda_inserida["condicoes"] == "a/c|1+1"
    assert venda_inserida["condicoes_venda"] == "avista"
    assert venda_inserida["valor_entrada"] == ""

    # Checa se o email foi enviado com email_remetente correto e outros campos
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert "Cliente X" in email_enviado["assunto"]
    assert email_enviado["email_destinatario"] == "joao@empresa.com"

    # Checa se retorna o resultado de nova_venda
    assert resultado == "resultado_insert"

def test_cadastrar_venda_sem_entrada_condicao(monkeypatch):
    # Simula o vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "pos_vendas": "Amanda Pós",
        "email": "joao@empresa.com"
    }
    # Simula configs
    configs_fake = {
        'tipo': 'geral',
        'email_smtp_principal': 'vendas@empresa.com:true',
        'email_smtp_secundario': 'backup@empresa.com:false',
        'smtp': 'smtp.empresa.com',
        'porta': 587,
        'email_copia': 'copia@empresa.com',
        'senha_email_smtp': 'segredo'
    }
    email_enviado = {}
    venda_inserida = {}

    # Mock do find_one das coleções
    def fake_find_one_usuarios(query):
        return vendedor_fake
    def fake_find_one_configs(query):
        return configs_fake

    # Mock do enviar_email: salva argumentos para inspeção
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Mock do nova_venda: salva argumentos e retorna valor fixo
    def fake_nova_venda(**kwargs):
        venda_inserida.update(kwargs)
        return "resultado_insert"

    # Patch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)
    monkeypatch.setattr("app.services.nova_venda", fake_nova_venda)

    # Dados da venda simulada
    venda_data = {
        "numero_da_venda": "VEND01",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "endereco": {"rua": "Rua Y", "bairro": "Centro", "numero": "123", "cidade": "Cidade", "estado": "UF"},
        "cep": "12345-000",
        "cnpj_cpf": "123.456.789-00",
        "razao_social": "Empresa X",
        "inscricao_estadual_identidade": "ISENTO",
        "produto": "PRODUTO1",
        "valor_tabela": 5000,
        "condicoes": "b/c|6x",
        "valor_parcelas": "835",
        "data_prestacao_inicial": "2025-07-10",
        "tipo_envio_boleto": "email",
        "tipo_remessa": "normal",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "fone_vendedor": "11988888888",
        "email_vendedor": "joao@empresa.com",
        "vendedor": "João Vendedor",
        "obs": "Sem observação",
        "status": "Aprovada",
        "valor_entrada": "",
        "condicoes_venda": "",
        "valor_venda_avista": "",
        "valor_real": "5010,00",
        "data_criacao": datetime(2025, 7, 7, 15, 0, 0),
        "logs": [],
        "desconto_autorizado": True,
        "caminho_arquivos": "",
        "obs_vendas": "",
        "tipo_cliente": "Verde"
    }

    # Executa a função
    usuario_id = "user_id_fake"
    resultado = cadastrar_venda(usuario_id, venda_data)

    # Checa se chamou nova_venda com os argumentos esperados (exemplo, checa alguns)
    assert venda_inserida["usuario_id"] == usuario_id
    assert venda_inserida["nome"] == "Cliente X"
    assert venda_inserida["posvendas"] == "Amanda Pós"
    assert venda_inserida["vendedor"] == "João Vendedor"
    assert venda_inserida["valor_tabela"] == 5000
    assert venda_inserida["condicoes"] == "b/c|6x"
    assert venda_inserida["valor_entrada"] == ""
    assert venda_inserida["valor_parcelas"] == "835"

    # Checa se o email foi enviado com email_remetente correto e outros campos
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert "Cliente X" in email_enviado["assunto"]
    assert email_enviado["email_destinatario"] == "joao@empresa.com"

    # Checa se retorna o resultado de nova_venda
    assert resultado == "resultado_insert"

def test_cadastrar_venda_com_entrada_condicao(monkeypatch):
    # Simula o vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "pos_vendas": "Amanda Pós",
        "email": "joao@empresa.com"
    }
    # Simula configs
    configs_fake = {
        'tipo': 'geral',
        'email_smtp_principal': 'vendas@empresa.com:true',
        'email_smtp_secundario': 'backup@empresa.com:false',
        'smtp': 'smtp.empresa.com',
        'porta': 587,
        'email_copia': 'copia@empresa.com',
        'senha_email_smtp': 'segredo'
    }
    email_enviado = {}
    venda_inserida = {}

    # Mock do find_one das coleções
    def fake_find_one_usuarios(query):
        return vendedor_fake
    def fake_find_one_configs(query):
        return configs_fake

    # Mock do enviar_email: salva argumentos para inspeção
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Mock do nova_venda: salva argumentos e retorna valor fixo
    def fake_nova_venda(**kwargs):
        venda_inserida.update(kwargs)
        return "resultado_insert"

    # Patch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)
    monkeypatch.setattr("app.services.nova_venda", fake_nova_venda)

    # Dados da venda simulada
    venda_data = {
        "numero_da_venda": "VEND01",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "endereco": {"rua": "Rua Y", "bairro": "Centro", "numero": "123", "cidade": "Cidade", "estado": "UF"},
        "cep": "12345-000",
        "cnpj_cpf": "123.456.789-00",
        "razao_social": "Empresa X",
        "inscricao_estadual_identidade": "ISENTO",
        "produto": "PRODUTO1",
        "valor_tabela": 5000,
        "condicoes": "b/c|10x",
        "valor_parcelas": "400,00",
        "data_prestacao_inicial": "2025-07-10",
        "tipo_envio_boleto": "email",
        "tipo_remessa": "normal",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "fone_vendedor": "11988888888",
        "email_vendedor": "joao@empresa.com",
        "vendedor": "João Vendedor",
        "obs": "Sem observação",
        "status": "Aprovada",
        "valor_entrada": "1000,00",
        "condicoes_venda": "",
        "valor_venda_avista": "",
        "valor_real": "5000,00",
        "data_criacao": datetime(2025, 7, 7, 15, 0, 0),
        "logs": [],
        "desconto_autorizado": True,
        "caminho_arquivos": "",
        "obs_vendas": "",
        "tipo_cliente": "Verde"
    }

    # Executa a função
    usuario_id = "user_id_fake"
    resultado = cadastrar_venda(usuario_id, venda_data)

    # Checa se chamou nova_venda com os argumentos esperados (exemplo, checa alguns)
    assert venda_inserida["usuario_id"] == usuario_id
    assert venda_inserida["nome"] == "Cliente X"
    assert venda_inserida["posvendas"] == "Amanda Pós"
    assert venda_inserida["vendedor"] == "João Vendedor"
    assert venda_inserida["valor_tabela"] == 5000
    assert venda_inserida["condicoes"] == "b/c|10x"
    assert venda_inserida["valor_entrada"] == "1000,00"
    assert venda_inserida["valor_parcelas"] == "400,00"

    # Checa se o email foi enviado com email_remetente correto e outros campos
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert "Cliente X" in email_enviado["assunto"]
    assert email_enviado["email_destinatario"] == "joao@empresa.com"

    # Checa se retorna o resultado de nova_venda
    assert resultado == "resultado_insert"

def test_cadastrar_venda_email_secundario(monkeypatch):
    # Simula o vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "pos_vendas": "Amanda Pós",
        "email": "joao@empresa.com"
    }
    # Simula configs
    configs_fake = {
        'tipo': 'geral',
        'email_smtp_principal': 'vendas@empresa.com:false',
        'email_smtp_secundario': 'backup@empresa.com:true',
        'smtp': 'smtp.empresa.com',
        'porta': 587,
        'email_copia': 'copia@empresa.com',
        'senha_email_smtp': 'segredo'
    }
    email_enviado = {}
    venda_inserida = {}

    # Mock do find_one das coleções
    def fake_find_one_usuarios(query):
        return vendedor_fake
    def fake_find_one_configs(query):
        return configs_fake

    # Mock do enviar_email: salva argumentos para inspeção
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Mock do nova_venda: salva argumentos e retorna valor fixo
    def fake_nova_venda(**kwargs):
        venda_inserida.update(kwargs)
        return "resultado_insert"

    # Patch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)
    monkeypatch.setattr("app.services.nova_venda", fake_nova_venda)

    # Dados da venda simulada
    venda_data = {
        "numero_da_venda": "VEND01",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "endereco": {"rua": "Rua Y", "bairro": "Centro", "numero": "123", "cidade": "Cidade", "estado": "UF"},
        "cep": "12345-000",
        "cnpj_cpf": "123.456.789-00",
        "razao_social": "Empresa X",
        "inscricao_estadual_identidade": "ISENTO",
        "produto": "PRODUTO1",
        "valor_tabela": 5000,
        "condicoes": "b/c|10x",
        "valor_parcelas": "400,00",
        "data_prestacao_inicial": "2025-07-10",
        "tipo_envio_boleto": "email",
        "tipo_remessa": "normal",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "fone_vendedor": "11988888888",
        "email_vendedor": "joao@empresa.com",
        "vendedor": "João Vendedor",
        "obs": "Sem observação",
        "status": "Aprovada",
        "valor_entrada": "1000,00",
        "condicoes_venda": "",
        "valor_venda_avista": "",
        "valor_real": "5000,00",
        "data_criacao": datetime(2025, 7, 7, 15, 0, 0),
        "logs": [],
        "desconto_autorizado": True,
        "caminho_arquivos": "",
        "obs_vendas": "",
        "tipo_cliente": "Verde"
    }

    # Executa a função
    usuario_id = "user_id_fake"
    resultado = cadastrar_venda(usuario_id, venda_data)

    # Checa se chamou nova_venda com os argumentos esperados (exemplo, checa alguns)
    assert venda_inserida["usuario_id"] == usuario_id
    assert venda_inserida["nome"] == "Cliente X"
    assert venda_inserida["posvendas"] == "Amanda Pós"
    assert venda_inserida["vendedor"] == "João Vendedor"
    assert venda_inserida["valor_tabela"] == 5000
    assert venda_inserida["condicoes"] == "b/c|10x"
    assert venda_inserida["valor_entrada"] == "1000,00"
    assert venda_inserida["valor_parcelas"] == "400,00"

    # Checa se o email foi enviado com email_remetente correto e outros campos
    assert email_enviado["email_remetente"] == "backup@empresa.com"
    assert "Cliente X" in email_enviado["assunto"]
    assert email_enviado["email_destinatario"] == "joao@empresa.com"

    # Checa se retorna o resultado de nova_venda
    assert resultado == "resultado_insert"
