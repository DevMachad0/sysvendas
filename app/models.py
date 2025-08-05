"""
Módulo de inicialização do banco de dados e funções auxiliares do sistema de vendas.
Gerencia conexão MongoDB, hash de senhas e collections do sistema.
"""

import os                  # Módulo padrão para manipulação de variáveis de ambiente e arquivos
from dotenv import load_dotenv  # Carrega variáveis do arquivo .env, mantendo credenciais fora do código
from pymongo import MongoClient # Cliente para conectar e interagir com o MongoDB
import bcrypt             # Biblioteca para hash e verificação segura de senhas
from datetime import datetime

# Carrega as variáveis de ambiente definidas no arquivo .env
load_dotenv()

# Recupera a URI de conexão do MongoDB a partir das variáveis de ambiente
MONGO_URI = os.getenv("MONGO_URI")

# Cria o cliente MongoDB usando a URI configurada
client = MongoClient(MONGO_URI)

# Seleciona o banco de dados principal do sistema
db = client['sistemaVendas']

# Coleção de usuários do sistema
usuarios_collection = db['usuarios']

# Coleção de vendas realizadas (nova coleção dedicada para vendas)
vendas_collection = db['vendas']

# Coleção de produtos cadastrados
produtos_collection = db['produtos']

# Coleção para configurações do sistema (metas, limites, SMTP, etc)
configs_collection = db['configs']

# Coleção de logs de modificações e auditoria (nova coleção)
logs_collection = db['logs']

# Coleção de notificações para o sistema (nova coleção)
notificacoes_collection = db['notificacoes']


def criar_usuario(
    nome_completo,
    username,
    email,
    senha,
    fone,
    tipo,
    status='ativo',
    foto=None,
    pos_vendas=None,
    meta_mes=None,
    permissa_acesso='aceito'
):
    """
    Cria e insere um novo usuário na coleção 'usuarios' do banco de dados.

    Parâmetros:
        nome_completo (str): Nome completo do usuário.
        username (str): Nome de usuário (login).
        email (str): Endereço de e-mail do usuário.
        senha (str): Senha do usuário (em texto plano).
        senha_email (str): Senha do e-mail (para envio de e-mails SMTP, opcional).
        fone (str): Telefone de contato do usuário.
        tipo (str): Tipo do usuário (ex: 'admin', 'vendedor').
        status (str, opcional): Status do usuário, padrão 'ativo'.
        foto (str, opcional): Nome do arquivo ou caminho da foto do usuário.
        pos_vendas (str, opcional): Nome do responsável pós-venda.
        meta_mes (float, opcional): Meta mensal do vendedor.

    Retorno:
        pymongo.results.InsertOneResult: Resultado da operação de inserção no MongoDB.
    """
    # Gera um hash seguro da senha para armazenamento
    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

    # Monta o documento do usuário a ser inserido
    usuario = {
        "nome_completo": nome_completo,  # Nome completo do usuário
        "username": username,            # Nome de usuário (login)
        "email": email,                  # E-mail do usuário
        "senha": senha_hash,             # Senha criptografada    # Senha do e-mail (para SMTP, opcional)
        "fone": fone,                    # Telefone para contato
        "tipo": tipo,                    # Tipo do usuário
        "status": status,                # Status do usuário (ativo/inativo)
        "foto": foto,                    # Caminho da foto (opcional)
        "pos_vendas": pos_vendas,        # Responsável pós-venda (opcional)
        "meta_mes": meta_mes,            # Meta mensal do vendedor (opcional)
        "permissa_acesso": permissa_acesso,  # NOVO: Permissão de acesso
        "tentativas_login": 0            # NOVO: contador de tentativas de login
    }

    # Insere o usuário no banco de dados e retorna o resultado
    return usuarios_collection.insert_one(usuario)


# Agora salva a venda na coleção de vendas, vinculando ao usuário
def nova_venda(
    usuario_id,
    numero_da_venda,
    nome,
    nome_do_contato,
    endereco,
    cep,
    cnpj_cpf,
    razao_social,
    inscricao_estadual_identidade,
    produto,
    valor_tabela,
    condicoes,
    valor_parcelas,
    data_prestacao_inicial,
    tipo_envio_boleto,
    tipo_remessa,
    email,
    fones,
    fone_vendedor,
    email_vendedor,
    vendedor,
    obs,
    status,
    posvendas,
    data_criacao,
    data_real,
    valor_real,
    tipo_cliente=None,
    logs=None,
    desconto_autorizado=None,
    caminho_arquivos="",
    obs_vendas="",
    valor_entrada=None,           # NOVO
    valor_venda_avista=None,      # NOVO
    condicoes_venda=None,          # NOVO
    desconto_live=None,            # NOVO
    percentual_desconto_live=None, # NOVO
    quantidade_acessos=None        # NOVO
):
    """
    Cria e insere um novo documento de venda na coleção 'vendas' do banco de dados.

    Parâmetros:
        usuario_id (str): ID do usuário responsável pela venda.
        numero_da_venda (str/int): Número identificador da venda.
        nome (str): Nome do cliente.
        nome_do_contato (str): Nome do contato da empresa/cliente.
        endereco (dict/str): Endereço do cliente.
        cep (str): CEP do endereço.
        cnpj_cpf (str): CNPJ ou CPF do cliente.
        razao_social (str): Razão social do cliente.
        inscricao_estadual_identidade (str): Inscrição estadual ou identidade.
        produto (str): Nome do produto vendido.
        valor_tabela (float): Valor de tabela do produto.
        condicoes (str): Condições de pagamento.
        valor_parcelas (str): Valor das parcelas.
        data_prestacao_inicial (str/data): Data da prestação inicial.
        tipo_envio_boleto (str): Tipo de envio do boleto.
        tipo_remessa (str): Tipo de remessa.
        email (str): Endereço de e-mail do cliente.
        fones (list): Lista de telefones do cliente.
        fone_vendedor (str): Telefone do vendedor.
        email_vendedor (str): E-mail do vendedor.
        vendedor (str): Nome do vendedor.
        obs (str): Observações gerais sobre a venda.
        status (str): Status da venda.
        posvendas (str): Responsável pelo pós-vendas.
        data_criacao (datetime): Data de criação da venda.
        valor_real (float): Valor real negociado (pode ter desconto ou acréscimo).
        tipo_cliente (str, opcional): Tipo do cliente ("Verde", "Vermelho", etc).
        logs (list, opcional): Lista de logs de alterações/ocorrências da venda.
        desconto_autorizado (bool, opcional): Indica se houve desconto autorizado.
        caminho_arquivos (str, opcional): Caminho dos arquivos anexados à venda (visível só para admin, pos_vendas, faturamento).
        obs_vendas (str, opcional): Observações internas da venda (visível só para admin, pos_vendas, faturamento).
        valor_entrada (float, opcional): Valor de entrada para a venda.
        valor_venda_avista (float, opcional): Valor da venda à vista.
        condicoes_venda (str, opcional): Condições específicas da venda.
        desconto_live (bool, opcional): Indica se houve desconto da live.
        percentual_desconto_live (float, opcional): Percentual do desconto da live.
        quantidade_acessos (int, opcional): Quantidade de acessos contratados.

    Retorno:
        pymongo.results.InsertOneResult: Resultado da operação de inserção no MongoDB.
    """
    venda = {
        # --- Identificação ---
        "usuario_id": usuario_id,
        "numero_da_venda": numero_da_venda,
        "data_criacao": data_criacao,
        "status": status,

        # --- Cliente ---
        "nome": nome,
        "nome_do_contato": nome_do_contato,
        "cnpj_cpf": cnpj_cpf,
        "razao_social": razao_social,
        "inscricao_estadual_identidade": inscricao_estadual_identidade,
        "tipo_cliente": tipo_cliente,
        "email": email,
        "fones": fones,

        # --- Endereço ---
        "endereco": endereco,
        "cep": cep,

        # --- Produto/Venda ---
        "produto": produto,
        "valor_tabela": valor_tabela,
        "valor_real": valor_real,
        "condicoes": condicoes,
        "condicoes_venda": condicoes_venda,              # NOVO
        "valor_parcelas": valor_parcelas,
        "valor_entrada": valor_entrada,                  # NOVO
        "valor_venda_avista": valor_venda_avista,        # NOVO
        "data_prestacao_inicial": data_prestacao_inicial,
        "tipo_envio_boleto": tipo_envio_boleto,
        "tipo_remessa": tipo_remessa,
        "data_real": data_real,  # Data real da venda (pode ser diferente da criação)

        # --- Vendedor ---
        "vendedor": vendedor,
        "fone_vendedor": fone_vendedor,
        "email_vendedor": email_vendedor,
        "posvendas": posvendas,

        # --- Observações e controle ---
        "obs": obs,
        "obs_vendas": obs_vendas,
        "caminho_arquivos": caminho_arquivos,
        "logs": logs or [],
        "desconto_autorizado": desconto_autorizado,
        "desconto_live": desconto_live,                     # NOVO
        "percentual_desconto_live": percentual_desconto_live,  # NOVO
        "quantidade_acessos": quantidade_acessos          # NOVO
    }
    # Insere a venda no banco de dados e retorna o resultado
    return vendas_collection.insert_one(venda)

def cadastrar_produto(codigo, nome, formas_pagamento):
    """
    Cadastra um novo produto na coleção 'produtos' do banco de dados.

    Parâmetros:
        codigo (str/int): Código identificador único do produto.
        nome (str): Nome do produto.
        formas_pagamento (list): Lista de dicionários contendo as formas de pagamento disponíveis para o produto.
        (Agora aceita até 13 formas de pagamento.)

    Retorno:
        pymongo.results.InsertOneResult: Resultado da operação de inserção no MongoDB.
    """
    produto = {
        "codigo": codigo,                     # Código identificador do produto
        "nome": nome,                         # Nome do produto
        "formas_pagamento": formas_pagamento  # Lista de formas de pagamento (ex: [{'tipo': 'à vista', ...}, ...])
    }
    return produtos_collection.insert_one(produto)

def listar_produtos():
    """
    Lista todos os produtos cadastrados na coleção 'produtos'.

    Retorno:
        list: Lista de dicionários contendo os dados dos produtos, sem o campo '_id'.
    """
    # Busca todos os produtos e remove o campo '_id' de cada documento retornado
    return list(produtos_collection.find({}, {"_id": 0}))

def consultar_config_geral():
    """
    Consulta as configurações gerais do sistema.
    """
    return configs_collection.find_one({"tipo": "geral"}, {"_id": 0})

def salvar_limite_vendedor(vendedor_id, vendedor_nome, limite):
    """
    Salva ou atualiza o limite financeiro de um vendedor específico na coleção 'configs'.

    Args:
        vendedor_id (str): Identificador único do vendedor.
        vendedor_nome (str): Nome completo do vendedor.
        limite (float): Valor do limite financeiro definido para o vendedor.

    Observação:
        Esta função garante que só exista um documento de limite para cada vendedor, atualizando se já existir.
    """
    doc = {
        "tipo": "limite_vendedor",
        "vendedor_id": vendedor_id,
        "vendedor_nome": vendedor_nome,
        "limite": limite if limite else "0"
    }
    configs_collection.update_one(
        {"tipo": "limite_vendedor", "vendedor_id": vendedor_id},
        {"$set": doc},
        upsert=True
    )

def consultar_limites_vendedores():
    """
    Consulta todos os limites financeiros cadastrados para vendedores.

    Returns:
        list: Uma lista de dicionários, cada um contendo informações de limite de um vendedor.
              O campo '_id' do MongoDB é omitido no retorno.
    """
    return list(configs_collection.find({"tipo": "limite_vendedor"}, {"_id": 0}))

def salvar_meta_vendedor(vendedor_id, vendedor_nome, meta_dia_quantidade, meta_dia_valor, meta_semana):
    """
    Salva ou atualiza as metas de vendas diárias e semanais para um vendedor específico.

    Args:
        vendedor_id (str): Identificador único do vendedor.
        vendedor_nome (str): Nome completo do vendedor.
        meta_dia_quantidade (int): Meta de quantidade de vendas por dia.
        meta_dia_valor (float): Meta de valor vendido por dia.
        meta_semana (float): Meta de valor vendido por semana.

    Side Effects:
        Atualiza (ou cria, se não existir) o documento de meta do vendedor na coleção de configurações.
    """
    doc = {
        "tipo": "meta_vendedor",
        "vendedor_id": vendedor_id,
        "vendedor_nome": vendedor_nome,
        "meta_dia_quantidade": meta_dia_quantidade if meta_dia_quantidade else "0",
        "meta_dia_valor": meta_dia_valor if meta_dia_valor else "0",
        "meta_semana": meta_semana if meta_semana else "0"
    }
    configs_collection.update_one(
        {"tipo": "meta_vendedor", "vendedor_id": vendedor_id},
        {"$set": doc},
        upsert=True
    )

def consultar_metas_vendedores():
    """
    Consulta todas as metas cadastradas para vendedores.

    Returns:
        list: Lista de dicionários contendo as metas de todos os vendedores, excluindo o campo '_id'.

    Side Effects:
        Nenhum.
    """
    return list(configs_collection.find({"tipo": "meta_vendedor"}, {"_id": 0}))

def inserir_log(data, hora, modificacao, usuario):
    """
    Insere um novo registro de log na coleção 'logs'.

    Args:
        data (str): Data do evento (formato livre, ex: '2025-06-03').
        hora (str): Hora do evento (formato livre, ex: '14:35').
        modificacao (str): Descrição da modificação realizada.
        usuario (str): Usuário responsável pela modificação.

    Returns:
        InsertOneResult: Resultado da operação de inserção no MongoDB.

    Side Effects:
        Adiciona um novo documento na coleção 'logs'.
    """
    log = {
        "data": data,
        "hora": hora,
        "modificacao": modificacao,
        "usuario": usuario
    }
    return logs_collection.insert_one(log)

def registrar_fim_expediente():
    """
    Atualiza (ou cria) um documento na coleção configs do tipo 'fim_expediente',
    registrando data e hora do clique no botão Fim do expediente.
    """
    agora = datetime.now()
    data_str = agora.strftime('%d/%m/%Y')
    hora_str = agora.strftime('%H:%M:%S')
    configs_collection.update_one(
        {"tipo": "fim_expediente"},
        {"$set": {"data": data_str, "hora": hora_str}},
        upsert=True
    )

# Exemplo de estrutura de uma venda (documentação/modelo)
VENDA_EXEMPLO = {
    "usuario_id": "",                             # ID do usuário responsável
    "numero_da_venda": "",                       # Número identificador da venda
    "nome": "",                                   # Nome do cliente
    "nome_do_contato": "",                       # Nome do contato na empresa
    "endereco": "",                               # Endereço (dict/str)
    "cep": "",                                   # CEP
    "cnpj_cpf": "",                               # CNPJ ou CPF
    "razao_social": "",                           # Razão social
    "inscricao_estadual_identidade": "",         # IE ou identidade
    "produto": "",                               # Produto vendido
    "valor_tabela": 0.0,                         # Valor de tabela
    "condicoes": "",                             # Condições de pagamento
    "valor_parcelas": "",                         # Valor das parcelas
    "quantidade_acessos": 2,                      # Quantidade de acessos (padrão 2)
    "data_prestacao_inicial": "",                 # Data de início do serviço
    "tipo_envio_boleto": "",                     # Tipo de envio do boleto
    "tipo_remessa": "",                         # Tipo de remessa
    "email": "",                                 # E-mail do cliente
    "fone_vendedor": "",                         # Telefone do vendedor
    "email_vendedor": "",                         # E-mail do vendedor
    "fones": [],                                 # Lista de fones do cliente
    "vendedor": "",                               # Nome do vendedor
    "obs": "",                                   # Observações
    "status": "",                                 # Status da venda
    "posvendas": "",                             # Responsável pós-venda
    "data_criacao": "",                          # Data da venda
    "valor_real": 0.0,                           # Valor final negociado
    "tipo_cliente": "",                          # Tipo do cliente
    "logs": [],                                  # Array de logs (padrão: vazio)
    "desconto_autorizado": False,                # Se teve desconto autorizado
    "caminho_arquivos": "",                      # Caminho dos arquivos anexados à venda
    "obs_vendas": "",
    "data_real": None,                            # Data real da venda (pode ser diferente da criação)
    "valor_entrada": None,           # NOVO
    "valor_venda_avista": None,      # NOVO
    "condicoes_venda": None,          # NOVO
    "desconto_live": None,            # NOVO
    "percentual_desconto_live": None,   # NOVO
    # Campos extras para venda:
    #   desconto_live: bool (se foi aplicado desconto da live)
    #   percentual_desconto_live: float (percentual do desconto aplicado)
}

# Se houver funções como criar_venda ou atualizar_venda, inclua os campos:
def criar_venda_dict(
    usuario_id, numero_da_venda, nome, nome_do_contato,
    endereco, cep, cnpj_cpf, razao_social,
    inscricao_estadual_identidade, produto, valor_tabela,
    condicoes, valor_parcelas, data_prestacao_inicial,
    tipo_envio_boleto, tipo_remessa, email, fones,
    fone_vendedor, email_vendedor, vendedor, obs,
    status, posvendas, data_criacao, valor_real,
    tipo_cliente=None, logs=None, desconto_autorizado=None,
    caminho_arquivos="", obs_vendas="",
    valor_entrada=None,           # NOVO
    valor_venda_avista=None,      # NOVO
    condicoes_venda=None,          # NOVO
    desconto_live=None,            # NOVO
    percentual_desconto_live=None,  # NOVO
    quantidade_acessos=None        # NOVO
):
    return {
        "usuario_id": usuario_id,
        "numero_da_venda": numero_da_venda,
        "nome": nome,
        "nome_do_contato": nome_do_contato,
        "endereco": endereco,
        "cep": cep,
        "cnpj_cpf": cnpj_cpf,
        "razao_social": razao_social,
        "inscricao_estadual_identidade": inscricao_estadual_identidade,
        "produto": produto,
        "valor_tabela": valor_tabela,
        "condicoes": condicoes,
        "valor_parcelas": valor_parcelas,
        "data_prestacao_inicial": data_prestacao_inicial,
        "tipo_envio_boleto": tipo_envio_boleto,
        "tipo_remessa": tipo_remessa,
        "email": email,
        "fone_vendedor": fone_vendedor,
        "email_vendedor": email_vendedor,
        "fones": fones,
        "vendedor": vendedor,
        "obs": obs,
        "status": status,
        "posvendas": posvendas,
        "data_criacao": data_criacao,
        "data_real": datetime.now(),  # Data real da venda (pode ser diferente da criação)
        "valor_real": valor_real,
        "tipo_cliente": tipo_cliente,
        "logs": logs or [],
        "desconto_autorizado": desconto_autorizado,
        "caminho_arquivos": caminho_arquivos,
        "obs_vendas": obs_vendas,
        "valor_entrada": valor_entrada,                 # NOVO
        "valor_venda_avista": valor_venda_avista,       # NOVO
        "condicoes_venda": condicoes_venda,              # NOVO
        "desconto_live": desconto_live,                     # NOVO
        "percentual_desconto_live": percentual_desconto_live,  # NOVO
        "quantidade_acessos": quantidade_acessos          # NOVO
    }
