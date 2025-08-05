import pytest

from app.services import reenviar_venda

def test_reenviar_venda_com_entrada_1mais1_entrada(monkeypatch):
    # Simula vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "email": "joao@empresa.com"
    }

    # Simula configs de envio
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

    # Mock para buscar vendedor
    def fake_find_one_usuarios(query):
        return vendedor_fake

    # Mock para buscar configs
    def fake_find_one_configs(query):
        return configs_fake

    # Mock para enviar e-mail
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Monkeypatch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)

    # Dados de venda para reenvio
    data = {
        "quem": "João Vendedor",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "cnpj_cpf": "123.456.789-00",
        "inscricao_estadual_identidade": "ISENTO",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "endereco_rua": "Rua Y",
        "endereco_bairro": "Centro",
        "endereco_numero": "123",
        "endereco_cidade": "Cidade",
        "endereco_estado": "UF",
        "cep": "12345-000",
        "produto": "PRODUTO1",
        "condicoes": "a/c|1+1",
        "condicoes_venda": "entrada_parcela",
        "valor_entrada": "1000,00",
        "valor_parcelas": "2500,00",
        "valor_venda_avista": "",
        "data_prestacao_inicial": "2025-07-10",
        "valor_real": "5000,00",
        "tipo_envio_boleto": "email",
        "obs": "Sem observação"
    }

    # Executa a função
    reenviar_venda(data)

    # Checa argumentos do e-mail enviado
    assert email_enviado["assunto"].startswith("REENVIO - Cliente X")
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert email_enviado["copias"] == "copia@empresa.com"
    assert email_enviado["senha_email"] == "segredo"
    assert email_enviado["servidor"] == "smtp.empresa.com"
    assert email_enviado["porta"] == 587
    assert email_enviado["email_destinatario"] == "joao@empresa.com"
    # Confirma que corpo contém informações essenciais
    assert "CLIENTE X" in email_enviado["corpo"].upper()
    assert "PRODUTO1" in email_enviado["corpo"].upper()
    assert "SEM OBSERVAÇÃO" in email_enviado["corpo"].upper()

def test_reenviar_venda_sem_entrada_1mais1_avista(monkeypatch):
    # Simula vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "email": "joao@empresa.com"
    }

    # Simula configs de envio
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

    # Mock para buscar vendedor
    def fake_find_one_usuarios(query):
        return vendedor_fake

    # Mock para buscar configs
    def fake_find_one_configs(query):
        return configs_fake

    # Mock para enviar e-mail
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Monkeypatch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)

    # Dados de venda para reenvio
    data = {
        "quem": "João Vendedor",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "cnpj_cpf": "123.456.789-00",
        "inscricao_estadual_identidade": "ISENTO",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "endereco_rua": "Rua Y",
        "endereco_bairro": "Centro",
        "endereco_numero": "123",
        "endereco_cidade": "Cidade",
        "endereco_estado": "UF",
        "cep": "12345-000",
        "produto": "PRODUTO1",
        "condicoes": "a/c|1+1",
        "condicoes_venda": "avista",
        "valor_entrada": "",
        "valor_parcelas": "",
        "valor_venda_avista": "5000,00",
        "data_prestacao_inicial": "2025-07-10",
        "valor_real": "5000,00",
        "tipo_envio_boleto": "email",
        "obs": "Sem observação"
    }

    # Executa a função
    reenviar_venda(data)

    # Checa argumentos do e-mail enviado
    assert email_enviado["assunto"].startswith("REENVIO - Cliente X")
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert email_enviado["copias"] == "copia@empresa.com"
    assert email_enviado["senha_email"] == "segredo"
    assert email_enviado["servidor"] == "smtp.empresa.com"
    assert email_enviado["porta"] == 587
    assert email_enviado["email_destinatario"] == "joao@empresa.com"
    # Confirma que corpo contém informações essenciais
    assert "CLIENTE X" in email_enviado["corpo"].upper()
    assert "PRODUTO1" in email_enviado["corpo"].upper()
    assert "SEM OBSERVAÇÃO" in email_enviado["corpo"].upper()

def test_reenviar_venda_sem_entrada_condicao(monkeypatch):
    # Simula vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "email": "joao@empresa.com"
    }

    # Simula configs de envio
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

    # Mock para buscar vendedor
    def fake_find_one_usuarios(query):
        return vendedor_fake

    # Mock para buscar configs
    def fake_find_one_configs(query):
        return configs_fake

    # Mock para enviar e-mail
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Monkeypatch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)

    # Dados de venda para reenvio
    data = {
        "quem": "João Vendedor",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "cnpj_cpf": "123.456.789-00",
        "inscricao_estadual_identidade": "ISENTO",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "endereco_rua": "Rua Y",
        "endereco_bairro": "Centro",
        "endereco_numero": "123",
        "endereco_cidade": "Cidade",
        "endereco_estado": "UF",
        "cep": "12345-000",
        "produto": "PRODUTO1",
        "condicoes": "b/c|10x",
        "condicoes_venda": "",
        "valor_entrada": "",
        "valor_parcelas": "500,00",
        "valor_venda_avista": "",
        "data_prestacao_inicial": "2025-07-10",
        "valor_real": "5000,00",
        "tipo_envio_boleto": "email",
        "obs": "Sem observação"
    }

    # Executa a função
    reenviar_venda(data)

    # Checa argumentos do e-mail enviado
    assert email_enviado["assunto"].startswith("REENVIO - Cliente X")
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert email_enviado["copias"] == "copia@empresa.com"
    assert email_enviado["senha_email"] == "segredo"
    assert email_enviado["servidor"] == "smtp.empresa.com"
    assert email_enviado["porta"] == 587
    assert email_enviado["email_destinatario"] == "joao@empresa.com"
    # Confirma que corpo contém informações essenciais
    assert "CLIENTE X" in email_enviado["corpo"].upper()
    assert "PRODUTO1" in email_enviado["corpo"].upper()
    assert "SEM OBSERVAÇÃO" in email_enviado["corpo"].upper()

def test_reenviar_venda_com_entrada_condicao(monkeypatch):
    # Simula vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "email": "joao@empresa.com"
    }

    # Simula configs de envio
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

    # Mock para buscar vendedor
    def fake_find_one_usuarios(query):
        return vendedor_fake

    # Mock para buscar configs
    def fake_find_one_configs(query):
        return configs_fake

    # Mock para enviar e-mail
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Monkeypatch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)

    # Dados de venda para reenvio
    data = {
        "quem": "João Vendedor",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "cnpj_cpf": "123.456.789-00",
        "inscricao_estadual_identidade": "ISENTO",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "endereco_rua": "Rua Y",
        "endereco_bairro": "Centro",
        "endereco_numero": "123",
        "endereco_cidade": "Cidade",
        "endereco_estado": "UF",
        "cep": "12345-000",
        "produto": "PRODUTO1",
        "condicoes": "b/c|10x",
        "condicoes_venda": "",
        "valor_entrada": "1000,00",
        "valor_parcelas": "400,00",
        "valor_venda_avista": "",
        "data_prestacao_inicial": "2025-07-10",
        "valor_real": "5000,00",
        "tipo_envio_boleto": "email",
        "obs": "Sem observação"
    }

    # Executa a função
    reenviar_venda(data)

    # Checa argumentos do e-mail enviado
    assert email_enviado["assunto"].startswith("REENVIO - Cliente X")
    assert email_enviado["email_remetente"] == "vendas@empresa.com"
    assert email_enviado["copias"] == "copia@empresa.com"
    assert email_enviado["senha_email"] == "segredo"
    assert email_enviado["servidor"] == "smtp.empresa.com"
    assert email_enviado["porta"] == 587
    assert email_enviado["email_destinatario"] == "joao@empresa.com"
    # Confirma que corpo contém informações essenciais
    assert "CLIENTE X" in email_enviado["corpo"].upper()
    assert "PRODUTO1" in email_enviado["corpo"].upper()
    assert "SEM OBSERVAÇÃO" in email_enviado["corpo"].upper()

def test_reenviar_venda_email_secundario(monkeypatch):
    # Simula vendedor buscado
    vendedor_fake = {
        "nome_completo": "João Vendedor",
        "username": "joaovend",
        "tipo": "vendedor",
        "email": "joao@empresa.com"
    }

    # Simula configs de envio
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

    # Mock para buscar vendedor
    def fake_find_one_usuarios(query):
        return vendedor_fake

    # Mock para buscar configs
    def fake_find_one_configs(query):
        return configs_fake

    # Mock para enviar e-mail
    def fake_enviar_email(**kwargs):
        email_enviado.update(kwargs)
        return True

    # Monkeypatch nas dependências
    monkeypatch.setattr("app.services.usuarios_collection.find_one", fake_find_one_usuarios)
    monkeypatch.setattr("app.services.configs_collection.find_one", fake_find_one_configs)
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)

    # Dados de venda para reenvio
    data = {
        "quem": "João Vendedor",
        "nome": "Cliente X",
        "nome_do_contato": "Fulano",
        "cnpj_cpf": "123.456.789-00",
        "inscricao_estadual_identidade": "ISENTO",
        "email": "cli@cliente.com",
        "fones": ["11999999999"],
        "endereco_rua": "Rua Y",
        "endereco_bairro": "Centro",
        "endereco_numero": "123",
        "endereco_cidade": "Cidade",
        "endereco_estado": "UF",
        "cep": "12345-000",
        "produto": "PRODUTO1",
        "condicoes": "a/c|1+1",
        "condicoes_venda": "entrada_parcela",
        "valor_entrada": "1000,00",
        "valor_parcelas": "2500,00",
        "valor_venda_avista": "4000,00",
        "data_prestacao_inicial": "2025-07-10",
        "valor_real": "5000,00",
        "tipo_envio_boleto": "email",
        "obs": "Sem observação"
    }

    # Executa a função
    reenviar_venda(data)

    # Checa argumentos do e-mail enviado
    assert email_enviado["assunto"].startswith("REENVIO - Cliente X")
    assert email_enviado["email_remetente"] == "backup@empresa.com"
    assert email_enviado["copias"] == "copia@empresa.com"
    assert email_enviado["senha_email"] == "segredo"
    assert email_enviado["servidor"] == "smtp.empresa.com"
    assert email_enviado["porta"] == 587
    assert email_enviado["email_destinatario"] == "joao@empresa.com"
    # Confirma que corpo contém informações essenciais
    assert "CLIENTE X" in email_enviado["corpo"].upper()
    assert "PRODUTO1" in email_enviado["corpo"].upper()
    assert "R$1000,00" in email_enviado["corpo"].replace('.', ',')  # só para garantir
    assert "SEM OBSERVAÇÃO" in email_enviado["corpo"].upper()
